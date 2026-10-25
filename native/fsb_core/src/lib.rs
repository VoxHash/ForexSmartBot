//! Native CPU-bound helpers for ForexSmartBot.
//!
//! Implements rolling indicators (SMA, EMA, ATR, RSI, MACD), batch SMA via rayon,
//! SMA/EMA-crossover equity, MACD-signal crossover equity, walk-forward sweeps,
//! multi-symbol portfolio aggregation, and RSI mean-reversion equity/sweeps so
//! indicator/backtest hot paths can run with lower overhead than pure
//! pandas while the PyQt UI stays responsive.

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use rayon::prelude::*;

/// O(n) simple moving average. Leading `window-1` samples are NaN.
fn sma_slice(values: &[f64], window: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if window == 0 || n < window {
        return out;
    }
    let mut sum = 0.0_f64;
    for i in 0..n {
        sum += values[i];
        if i + 1 >= window {
            if i + 1 > window {
                sum -= values[i - window];
            }
            out[i] = sum / window as f64;
        }
    }
    out
}


/// Exponential moving average. Leading `period-1` samples are NaN; seed uses SMA.
fn ema_slice(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if period == 0 || n < period {
        return out;
    }
    let mut sum = 0.0_f64;
    for i in 0..period {
        sum += values[i];
    }
    let mut prev = sum / period as f64;
    out[period - 1] = prev;
    let alpha = 2.0 / (period as f64 + 1.0);
    for i in period..n {
        prev = alpha * values[i] + (1.0 - alpha) * prev;
        out[i] = prev;
    }
    out
}

/// MACD line, signal line, and histogram. Fast/slow/signal periods must be >= 1
/// and `fast < slow`.
fn macd_slices(
    close: &[f64],
    fast: usize,
    slow: usize,
    signal: usize,
) -> Result<(Vec<f64>, Vec<f64>, Vec<f64>), String> {
    if fast == 0 || slow == 0 || signal == 0 || fast >= slow {
        return Err("require fast >= 1, slow >= 1, signal >= 1, and fast < slow".into());
    }
    let ema_f = ema_slice(close, fast);
    let ema_s = ema_slice(close, slow);
    let n = close.len();
    let mut macd = vec![f64::NAN; n];
    for i in 0..n {
        let f = ema_f[i];
        let s = ema_s[i];
        if !f.is_nan() && !s.is_nan() {
            macd[i] = f - s;
        }
    }
    // Signal EMA over the MACD series, skipping leading NaNs.
    let mut signal_line = vec![f64::NAN; n];
    let mut hist = vec![f64::NAN; n];
    let mut seed_sum = 0.0_f64;
    let mut seed_count = 0_usize;
    let mut prev_signal = f64::NAN;
    let alpha = 2.0 / (signal as f64 + 1.0);
    for i in 0..n {
        let m = macd[i];
        if m.is_nan() {
            continue;
        }
        if seed_count < signal {
            seed_sum += m;
            seed_count += 1;
            if seed_count == signal {
                prev_signal = seed_sum / signal as f64;
                signal_line[i] = prev_signal;
                hist[i] = m - prev_signal;
            }
            continue;
        }
        prev_signal = alpha * m + (1.0 - alpha) * prev_signal;
        signal_line[i] = prev_signal;
        hist[i] = m - prev_signal;
    }
    Ok((macd, signal_line, hist))
}
/// Average True Range over OHLC series (Wilder-style simple mean of TR).
fn atr_slice(high: &[f64], low: &[f64], close: &[f64], period: usize) -> Result<Vec<f64>, String> {
    let n = high.len();
    if low.len() != n || close.len() != n {
        return Err("high, low, and close must have the same length".into());
    }
    let mut tr = vec![0.0_f64; n];
    for i in 0..n {
        let hl = high[i] - low[i];
        if i == 0 {
            tr[i] = hl;
        } else {
            let hc = (high[i] - close[i - 1]).abs();
            let lc = (low[i] - close[i - 1]).abs();
            tr[i] = hl.max(hc).max(lc);
        }
    }
    Ok(sma_slice(&tr, period))
}

/// Classic RSI using simple rolling mean of gains/losses.
fn rsi_slice(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![f64::NAN; n];
    if period == 0 || n < period + 1 {
        return out;
    }
    let mut gains = vec![0.0_f64; n];
    let mut losses = vec![0.0_f64; n];
    for i in 1..n {
        let d = values[i] - values[i - 1];
        if d >= 0.0 {
            gains[i] = d;
        } else {
            losses[i] = -d;
        }
    }
    let avg_gain = sma_slice(&gains, period);
    let avg_loss = sma_slice(&losses, period);
    for i in 0..n {
        let g = avg_gain[i];
        let l = avg_loss[i];
        if g.is_nan() || l.is_nan() {
            continue;
        }
        if l == 0.0 {
            out[i] = if g == 0.0 { 50.0 } else { 100.0 };
        } else {
            let rs = g / l;
            out[i] = 100.0 - (100.0 / (1.0 + rs));
        }
    }
    out
}

/// Compact SMA crossover equity over aligned series. Returns mark-to-market curve.
fn equity_sma_crossover_slice(
    close: &[f64],
    sma_fast: &[f64],
    sma_slow: &[f64],
    initial_balance: f64,
    position_fraction: f64,
) -> Vec<f64> {
    let n = close.len();
    let mut balance = initial_balance;
    let mut side: i8 = 0;
    let mut size = 0.0_f64;
    let mut entry = 0.0_f64;
    let mut equity = Vec::with_capacity(n);

    for i in 0..n {
        let px = close[i];
        if i >= 1 {
            let f = sma_fast[i];
            let s = sma_slow[i];
            let pf = sma_fast[i - 1];
            let ps = sma_slow[i - 1];
            if !f.is_nan() && !s.is_nan() && !pf.is_nan() && !ps.is_nan() {
                let cross_up = f > s && pf <= ps;
                let cross_dn = f < s && pf >= ps;
                if cross_up && side <= 0 {
                    if side < 0 {
                        balance += -size * (px - entry);
                    }
                    size = (balance * position_fraction) / px;
                    entry = px;
                    side = 1;
                } else if cross_dn && side >= 0 {
                    if side > 0 {
                        balance += size * (px - entry);
                    }
                    size = (balance * position_fraction) / px;
                    entry = px;
                    side = -1;
                }
            }
        }
        let mtm = if side != 0 {
            side as f64 * size * (px - entry)
        } else {
            0.0
        };
        equity.push(balance + mtm);
    }
    equity
}

fn max_drawdown(equity: &[f64]) -> f64 {
    let mut peak = f64::NEG_INFINITY;
    let mut max_dd = 0.0_f64;
    for &e in equity {
        if e > peak {
            peak = e;
        }
        if peak > 0.0 {
            let dd = (peak - e) / peak;
            if dd > max_dd {
                max_dd = dd;
            }
        }
    }
    max_dd
}

/// Run one SMA-crossover backtest; return (final_equity, total_return, max_drawdown).
fn sma_crossover_metrics(
    close: &[f64],
    fast: usize,
    slow: usize,
    initial_balance: f64,
    position_fraction: f64,
) -> (f64, f64, f64) {
    if close.is_empty() || fast == 0 || slow == 0 || fast >= slow {
        return (initial_balance, 0.0, 0.0);
    }
    let sma_f = sma_slice(close, fast);
    let sma_s = sma_slice(close, slow);
    let equity = equity_sma_crossover_slice(close, &sma_f, &sma_s, initial_balance, position_fraction);
    let final_eq = *equity.last().unwrap_or(&initial_balance);
    let total_return = if initial_balance != 0.0 {
        (final_eq - initial_balance) / initial_balance
    } else {
        0.0
    };
    (final_eq, total_return, max_drawdown(&equity))
}

fn build_param_pairs(fast_periods: &[usize], slow_periods: &[usize]) -> Vec<(usize, usize)> {
    let mut pairs = Vec::new();
    for &f in fast_periods {
        for &s in slow_periods {
            if f >= 1 && s >= 1 && f < s {
                pairs.push((f, s));
            }
        }
    }
    pairs
}

#[pyfunction]
fn sma(values: Vec<f64>, window: usize) -> PyResult<Vec<f64>> {
    if window == 0 {
        return Err(PyValueError::new_err("window must be >= 1"));
    }
    Ok(sma_slice(&values, window))
}

#[pyfunction]
fn atr(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    if period == 0 {
        return Err(PyValueError::new_err("period must be >= 1"));
    }
    atr_slice(&high, &low, &close, period).map_err(PyValueError::new_err)
}

#[pyfunction]
fn rsi(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    if period == 0 {
        return Err(PyValueError::new_err("period must be >= 1"));
    }
    Ok(rsi_slice(&values, period))
}

/// Compute SMA for many series in parallel (rayon). Each series shares `window`.
#[pyfunction]
fn batch_sma(series: Vec<Vec<f64>>, window: usize) -> PyResult<Vec<Vec<f64>>> {
    if window == 0 {
        return Err(PyValueError::new_err("window must be >= 1"));
    }
    let out: Vec<Vec<f64>> = series
        .par_iter()
        .map(|s| sma_slice(s, window))
        .collect();
    Ok(out)
}

/// Compact SMA crossover backtest loop over precomputed series (no allocations per bar).
/// Returns mark-to-market equity curve starting from `initial_balance`.
#[pyfunction]
fn equity_sma_crossover(
    close: Vec<f64>,
    sma_fast: Vec<f64>,
    sma_slow: Vec<f64>,
    initial_balance: f64,
    position_fraction: f64,
) -> PyResult<Vec<f64>> {
    let n = close.len();
    if sma_fast.len() != n || sma_slow.len() != n {
        return Err(PyValueError::new_err("close, sma_fast, and sma_slow lengths must match"));
    }
    if n == 0 {
        return Ok(Vec::new());
    }
    Ok(equity_sma_crossover_slice(
        &close,
        &sma_fast,
        &sma_slow,
        initial_balance,
        position_fraction,
    ))
}

/// Parallel SMA-crossover parameter grid sweep.
///
/// Each result row: `[fast, slow, final_equity, total_return, max_drawdown]`.
/// Only pairs with `fast < slow` are evaluated (rayon over the grid).
#[pyfunction]
fn sweep_sma_crossover(
    close: Vec<f64>,
    fast_periods: Vec<usize>,
    slow_periods: Vec<usize>,
    initial_balance: f64,
    position_fraction: f64,
) -> PyResult<Vec<Vec<f64>>> {
    if close.is_empty() {
        return Ok(Vec::new());
    }
    let pairs = build_param_pairs(&fast_periods, &slow_periods);
    let out: Vec<Vec<f64>> = pairs
        .par_iter()
        .map(|&(fast, slow)| {
            let (final_eq, ret, dd) =
                sma_crossover_metrics(&close, fast, slow, initial_balance, position_fraction);
            vec![fast as f64, slow as f64, final_eq, ret, dd]
        })
        .collect();
    Ok(out)
}

/// Walk-forward SMA parameter sweep.
///
/// `windows` rows are `[train_start, train_end, test_start, test_end]` (end exclusive).
/// For each window: grid-search on the train slice (max total_return), evaluate best
/// pair on the test slice. Result row:
/// `[best_fast, best_slow, train_return, test_return, test_final_equity, test_max_dd]`.
#[pyfunction]
fn walk_forward_sma_sweep(
    close: Vec<f64>,
    fast_periods: Vec<usize>,
    slow_periods: Vec<usize>,
    windows: Vec<Vec<usize>>,
    initial_balance: f64,
    position_fraction: f64,
) -> PyResult<Vec<Vec<f64>>> {
    let n = close.len();
    let pairs = build_param_pairs(&fast_periods, &slow_periods);
    if pairs.is_empty() {
        return Ok(Vec::new());
    }

    let mut parsed: Vec<(usize, usize, usize, usize)> = Vec::with_capacity(windows.len());
    for (i, w) in windows.iter().enumerate() {
        if w.len() != 4 {
            return Err(PyValueError::new_err(format!(
                "window {i} must have 4 indices [train_start, train_end, test_start, test_end]"
            )));
        }
        let (ts, te, xs, xe) = (w[0], w[1], w[2], w[3]);
        if te > n || xe > n || ts >= te || xs >= xe {
            return Err(PyValueError::new_err(format!(
                "window {i} has invalid bounds for series length {n}"
            )));
        }
        parsed.push((ts, te, xs, xe));
    }

    let out: Vec<Vec<f64>> = parsed
        .par_iter()
        .map(|&(ts, te, xs, xe)| {
            let train = &close[ts..te];
            let mut best_fast = pairs[0].0;
            let mut best_slow = pairs[0].1;
            let mut best_train_ret = f64::NEG_INFINITY;
            for &(fast, slow) in &pairs {
                let (_eq, ret, _dd) =
                    sma_crossover_metrics(train, fast, slow, initial_balance, position_fraction);
                if ret > best_train_ret {
                    best_train_ret = ret;
                    best_fast = fast;
                    best_slow = slow;
                }
            }
            let test = &close[xs..xe];
            let (test_eq, test_ret, test_dd) = sma_crossover_metrics(
                test,
                best_fast,
                best_slow,
                initial_balance,
                position_fraction,
            );
            vec![
                best_fast as f64,
                best_slow as f64,
                best_train_ret,
                test_ret,
                test_eq,
                test_dd,
            ]
        })
        .collect();
    Ok(out)
}

/// Multi-symbol SMA-crossover workers + portfolio aggregation.
///
/// Runs each symbol equity in parallel, then builds a weighted portfolio equity
/// (equal weight when `weights` is empty). Lengths must match across symbols.
///
/// Returns `(per_symbol_equity, portfolio_equity)`.
#[pyfunction]
fn multi_symbol_equity_aggregate(
    closes: Vec<Vec<f64>>,
    fast_period: usize,
    slow_period: usize,
    initial_balance: f64,
    position_fraction: f64,
    weights: Vec<f64>,
) -> PyResult<(Vec<Vec<f64>>, Vec<f64>)> {
    if closes.is_empty() {
        return Ok((Vec::new(), Vec::new()));
    }
    if fast_period == 0 || slow_period == 0 || fast_period >= slow_period {
        return Err(PyValueError::new_err(
            "require fast_period >= 1, slow_period >= 1, and fast_period < slow_period",
        ));
    }
    let n = closes[0].len();
    for (i, c) in closes.iter().enumerate() {
        if c.len() != n {
            return Err(PyValueError::new_err(format!(
                "symbol {i} length {} != first symbol length {n}",
                c.len()
            )));
        }
    }

    let m = closes.len();
    let mut w = weights;
    if w.is_empty() {
        w = vec![1.0 / m as f64; m];
    } else if w.len() != m {
        return Err(PyValueError::new_err(
            "weights length must match number of symbols (or be empty for equal weight)",
        ));
    }
    let wsum: f64 = w.iter().sum();
    if wsum <= 0.0 || !wsum.is_finite() {
        return Err(PyValueError::new_err("weights must sum to a positive finite value"));
    }
    for wi in &mut w {
        *wi /= wsum;
    }

    let per_symbol: Vec<Vec<f64>> = closes
        .par_iter()
        .map(|close| {
            let sma_f = sma_slice(close, fast_period);
            let sma_s = sma_slice(close, slow_period);
            equity_sma_crossover_slice(close, &sma_f, &sma_s, initial_balance, position_fraction)
        })
        .collect();

    let mut portfolio = vec![0.0_f64; n];
    for (sym_eq, &wi) in per_symbol.iter().zip(w.iter()) {
        for i in 0..n {
            // Normalize each curve to returns vs initial, then re-scale to portfolio capital.
            let ret = if initial_balance != 0.0 {
                (sym_eq[i] / initial_balance) - 1.0
            } else {
                0.0
            };
            portfolio[i] += wi * initial_balance * (1.0 + ret);
        }
    }
    Ok((per_symbol, portfolio))
}

/// RSI mean-reversion equity: long when RSI crosses up through `oversold`,
/// short when RSI crosses down through `overbought`.
fn equity_rsi_mean_reversion_slice(
    close: &[f64],
    rsi: &[f64],
    oversold: f64,
    overbought: f64,
    initial_balance: f64,
    position_fraction: f64,
) -> Vec<f64> {
    let n = close.len();
    let mut balance = initial_balance;
    let mut side: i8 = 0;
    let mut size = 0.0_f64;
    let mut entry = 0.0_f64;
    let mut equity = Vec::with_capacity(n);

    for i in 0..n {
        let px = close[i];
        if i >= 1 {
            let r = rsi[i];
            let pr = rsi[i - 1];
            if !r.is_nan() && !pr.is_nan() {
                let cross_up = pr <= oversold && r > oversold;
                let cross_dn = pr >= overbought && r < overbought;
                if cross_up && side <= 0 {
                    if side < 0 {
                        balance += -size * (px - entry);
                    }
                    size = (balance * position_fraction) / px;
                    entry = px;
                    side = 1;
                } else if cross_dn && side >= 0 {
                    if side > 0 {
                        balance += size * (px - entry);
                    }
                    size = (balance * position_fraction) / px;
                    entry = px;
                    side = -1;
                }
            }
        }
        let mtm = if side != 0 {
            side as f64 * size * (px - entry)
        } else {
            0.0
        };
        equity.push(balance + mtm);
    }
    equity
}

fn rsi_mean_reversion_metrics(
    close: &[f64],
    period: usize,
    oversold: f64,
    overbought: f64,
    initial_balance: f64,
    position_fraction: f64,
) -> (f64, f64, f64) {
    if close.is_empty()
        || period == 0
        || !(oversold.is_finite() && overbought.is_finite())
        || oversold >= overbought
    {
        return (initial_balance, 0.0, 0.0);
    }
    let rsi_vals = rsi_slice(close, period);
    let equity = equity_rsi_mean_reversion_slice(
        close,
        &rsi_vals,
        oversold,
        overbought,
        initial_balance,
        position_fraction,
    );
    let final_eq = *equity.last().unwrap_or(&initial_balance);
    let total_return = if initial_balance != 0.0 {
        (final_eq - initial_balance) / initial_balance
    } else {
        0.0
    };
    (final_eq, total_return, max_drawdown(&equity))
}

/// Compact RSI mean-reversion equity over aligned close/RSI series.
#[pyfunction]
fn equity_rsi_mean_reversion(
    close: Vec<f64>,
    rsi: Vec<f64>,
    oversold: f64,
    overbought: f64,
    initial_balance: f64,
    position_fraction: f64,
) -> PyResult<Vec<f64>> {
    let n = close.len();
    if rsi.len() != n {
        return Err(PyValueError::new_err("close and rsi lengths must match"));
    }
    if !(oversold.is_finite() && overbought.is_finite()) || oversold >= overbought {
        return Err(PyValueError::new_err(
            "require finite oversold < overbought",
        ));
    }
    if n == 0 {
        return Ok(Vec::new());
    }
    Ok(equity_rsi_mean_reversion_slice(
        &close,
        &rsi,
        oversold,
        overbought,
        initial_balance,
        position_fraction,
    ))
}

/// Parallel RSI mean-reversion parameter sweep.
///
/// Each result row:
/// `[period, oversold, overbought, final_equity, total_return, max_drawdown]`.
/// Only triples with `period >= 1` and `oversold < overbought` are evaluated.
#[pyfunction]
fn sweep_rsi_mean_reversion(
    close: Vec<f64>,
    rsi_periods: Vec<usize>,
    oversold_levels: Vec<f64>,
    overbought_levels: Vec<f64>,
    initial_balance: f64,
    position_fraction: f64,
) -> PyResult<Vec<Vec<f64>>> {
    if close.is_empty() {
        return Ok(Vec::new());
    }
    let mut triples: Vec<(usize, f64, f64)> = Vec::new();
    for &period in &rsi_periods {
        if period == 0 {
            continue;
        }
        for &os in &oversold_levels {
            for &ob in &overbought_levels {
                if os.is_finite() && ob.is_finite() && os < ob {
                    triples.push((period, os, ob));
                }
            }
        }
    }
    let out: Vec<Vec<f64>> = triples
        .par_iter()
        .map(|&(period, os, ob)| {
            let (final_eq, ret, dd) = rsi_mean_reversion_metrics(
                &close,
                period,
                os,
                ob,
                initial_balance,
                position_fraction,
            );
            vec![period as f64, os, ob, final_eq, ret, dd]
        })
        .collect();
    Ok(out)
}


/// EMA-crossover metrics (final_equity, total_return, max_drawdown).
fn ema_crossover_metrics(
    close: &[f64],
    fast: usize,
    slow: usize,
    initial_balance: f64,
    position_fraction: f64,
) -> (f64, f64, f64) {
    if close.is_empty() || fast == 0 || slow == 0 || fast >= slow {
        return (initial_balance, 0.0, 0.0);
    }
    let ema_f = ema_slice(close, fast);
    let ema_s = ema_slice(close, slow);
    let equity = equity_sma_crossover_slice(close, &ema_f, &ema_s, initial_balance, position_fraction);
    let final_eq = *equity.last().unwrap_or(&initial_balance);
    let total_return = if initial_balance != 0.0 {
        (final_eq - initial_balance) / initial_balance
    } else {
        0.0
    };
    (final_eq, total_return, max_drawdown(&equity))
}

/// MACD vs signal crossover equity (same side logic as SMA crossover).
fn equity_macd_crossover_slice(
    close: &[f64],
    macd: &[f64],
    signal: &[f64],
    initial_balance: f64,
    position_fraction: f64,
) -> Vec<f64> {
    equity_sma_crossover_slice(close, macd, signal, initial_balance, position_fraction)
}

fn macd_crossover_metrics(
    close: &[f64],
    fast: usize,
    slow: usize,
    signal: usize,
    initial_balance: f64,
    position_fraction: f64,
) -> (f64, f64, f64) {
    if close.is_empty() {
        return (initial_balance, 0.0, 0.0);
    }
    let Ok((macd, sig, _)) = macd_slices(close, fast, slow, signal) else {
        return (initial_balance, 0.0, 0.0);
    };
    let equity = equity_macd_crossover_slice(
        close,
        &macd,
        &sig,
        initial_balance,
        position_fraction,
    );
    let final_eq = *equity.last().unwrap_or(&initial_balance);
    let total_return = if initial_balance != 0.0 {
        (final_eq - initial_balance) / initial_balance
    } else {
        0.0
    };
    (final_eq, total_return, max_drawdown(&equity))
}

#[pyfunction]
fn ema(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    if period == 0 {
        return Err(PyValueError::new_err("period must be >= 1"));
    }
    Ok(ema_slice(&values, period))
}

/// Returns `(macd_line, signal_line, histogram)`.
#[pyfunction]
fn macd(
    close: Vec<f64>,
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    macd_slices(&close, fast_period, slow_period, signal_period).map_err(PyValueError::new_err)
}

/// Compact EMA crossover equity over aligned close/EMA series.
#[pyfunction]
fn equity_ema_crossover(
    close: Vec<f64>,
    ema_fast: Vec<f64>,
    ema_slow: Vec<f64>,
    initial_balance: f64,
    position_fraction: f64,
) -> PyResult<Vec<f64>> {
    equity_sma_crossover(close, ema_fast, ema_slow, initial_balance, position_fraction)
}

/// Parallel EMA-crossover parameter grid sweep.
///
/// Each result row: `[fast, slow, final_equity, total_return, max_drawdown]`.
#[pyfunction]
fn sweep_ema_crossover(
    close: Vec<f64>,
    fast_periods: Vec<usize>,
    slow_periods: Vec<usize>,
    initial_balance: f64,
    position_fraction: f64,
) -> PyResult<Vec<Vec<f64>>> {
    if close.is_empty() {
        return Ok(Vec::new());
    }
    let pairs = build_param_pairs(&fast_periods, &slow_periods);
    let out: Vec<Vec<f64>> = pairs
        .par_iter()
        .map(|&(fast, slow)| {
            let (final_eq, ret, dd) =
                ema_crossover_metrics(&close, fast, slow, initial_balance, position_fraction);
            vec![fast as f64, slow as f64, final_eq, ret, dd]
        })
        .collect();
    Ok(out)
}

/// Compact MACD vs signal crossover equity.
#[pyfunction]
fn equity_macd_crossover(
    close: Vec<f64>,
    macd_line: Vec<f64>,
    signal_line: Vec<f64>,
    initial_balance: f64,
    position_fraction: f64,
) -> PyResult<Vec<f64>> {
    let n = close.len();
    if macd_line.len() != n || signal_line.len() != n {
        return Err(PyValueError::new_err(
            "close, macd_line, and signal_line lengths must match",
        ));
    }
    if n == 0 {
        return Ok(Vec::new());
    }
    Ok(equity_macd_crossover_slice(
        &close,
        &macd_line,
        &signal_line,
        initial_balance,
        position_fraction,
    ))
}

/// Parallel MACD parameter sweep.
///
/// Each result row:
/// `[fast, slow, signal, final_equity, total_return, max_drawdown]`.
/// Only triples with `fast < slow` and all periods >= 1 are evaluated.
#[pyfunction]
fn sweep_macd(
    close: Vec<f64>,
    fast_periods: Vec<usize>,
    slow_periods: Vec<usize>,
    signal_periods: Vec<usize>,
    initial_balance: f64,
    position_fraction: f64,
) -> PyResult<Vec<Vec<f64>>> {
    if close.is_empty() {
        return Ok(Vec::new());
    }
    let mut triples: Vec<(usize, usize, usize)> = Vec::new();
    for &fast in &fast_periods {
        for &slow in &slow_periods {
            if fast == 0 || slow == 0 || fast >= slow {
                continue;
            }
            for &sig in &signal_periods {
                if sig >= 1 {
                    triples.push((fast, slow, sig));
                }
            }
        }
    }
    let out: Vec<Vec<f64>> = triples
        .par_iter()
        .map(|&(fast, slow, sig)| {
            let (final_eq, ret, dd) = macd_crossover_metrics(
                &close,
                fast,
                slow,
                sig,
                initial_balance,
                position_fraction,
            );
            vec![fast as f64, slow as f64, sig as f64, final_eq, ret, dd]
        })
        .collect();
    Ok(out)
}

#[pymodule]
fn fsb_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_function(wrap_pyfunction!(sma, m)?)?;
    m.add_function(wrap_pyfunction!(atr, m)?)?;
    m.add_function(wrap_pyfunction!(rsi, m)?)?;
    m.add_function(wrap_pyfunction!(batch_sma, m)?)?;
    m.add_function(wrap_pyfunction!(equity_sma_crossover, m)?)?;
    m.add_function(wrap_pyfunction!(sweep_sma_crossover, m)?)?;
    m.add_function(wrap_pyfunction!(walk_forward_sma_sweep, m)?)?;
    m.add_function(wrap_pyfunction!(multi_symbol_equity_aggregate, m)?)?;
    m.add_function(wrap_pyfunction!(equity_rsi_mean_reversion, m)?)?;
    m.add_function(wrap_pyfunction!(sweep_rsi_mean_reversion, m)?)?;
    m.add_function(wrap_pyfunction!(ema, m)?)?;
    m.add_function(wrap_pyfunction!(macd, m)?)?;
    m.add_function(wrap_pyfunction!(equity_ema_crossover, m)?)?;
    m.add_function(wrap_pyfunction!(sweep_ema_crossover, m)?)?;
    m.add_function(wrap_pyfunction!(equity_macd_crossover, m)?)?;
    m.add_function(wrap_pyfunction!(sweep_macd, m)?)?;
    Ok(())
}
