//! Native CPU-bound helpers for ForexSmartBot.
//!
//! Implements rolling indicators (SMA, ATR, RSI) and batch SMA via rayon so
//! indicator/backtest hot paths can run with lower memory overhead than pure
//! pandas/numba while the PyQt UI stays responsive alongside other apps.

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
    Ok(equity)
}

#[pymodule]
fn fsb_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_function(wrap_pyfunction!(sma, m)?)?;
    m.add_function(wrap_pyfunction!(atr, m)?)?;
    m.add_function(wrap_pyfunction!(rsi, m)?)?;
    m.add_function(wrap_pyfunction!(batch_sma, m)?)?;
    m.add_function(wrap_pyfunction!(equity_sma_crossover, m)?)?;
    Ok(())
}
