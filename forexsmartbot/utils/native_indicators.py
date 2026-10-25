"""Native (Rust/PyO3) indicator helpers with pure-Python/NumPy fallback.

Build optional extension from ``native/fsb_core``::

    cd native/fsb_core && maturin develop --release

When ``fsb_core`` is not installed, callers still get correct results via NumPy.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

_NATIVE = None
_NATIVE_ERR: Optional[str] = None

try:
    import fsb_core as _NATIVE  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency
    _NATIVE_ERR = str(exc)
    _NATIVE = None


def native_available() -> bool:
    """Return True if the Rust ``fsb_core`` extension is importable."""
    return _NATIVE is not None


def native_status() -> str:
    """Human-readable status for logs / settings."""
    if _NATIVE is not None:
        ver = getattr(_NATIVE, "__version__", "?")
        return f"fsb_core {ver} (Rust)"
    return f"unavailable ({_NATIVE_ERR or 'not built'})"


def _as_f64(values: Sequence[float] | np.ndarray | pd.Series) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError("values must be 1-D")
    return arr


def sma(values: Sequence[float] | np.ndarray | pd.Series, window: int) -> np.ndarray:
    """Simple moving average; leading values are NaN until ``window`` fills."""
    if window < 1:
        raise ValueError("window must be >= 1")
    arr = _as_f64(values)
    if _NATIVE is not None:
        return np.asarray(_NATIVE.sma(arr.tolist(), int(window)), dtype=np.float64)
    out = np.full(arr.shape[0], np.nan, dtype=np.float64)
    if arr.shape[0] < window:
        return out
    csum = np.cumsum(arr, dtype=np.float64)
    out[window - 1 :] = (csum[window - 1 :] - np.concatenate(([0.0], csum[:-window]))) / window
    return out


def atr(
    high: Sequence[float] | np.ndarray | pd.Series,
    low: Sequence[float] | np.ndarray | pd.Series,
    close: Sequence[float] | np.ndarray | pd.Series,
    period: int,
) -> np.ndarray:
    """Average True Range (simple mean of true range)."""
    if period < 1:
        raise ValueError("period must be >= 1")
    h = _as_f64(high)
    l = _as_f64(low)
    c = _as_f64(close)
    if not (h.shape == l.shape == c.shape):
        raise ValueError("high, low, and close must have the same length")
    if _NATIVE is not None:
        return np.asarray(
            _NATIVE.atr(h.tolist(), l.tolist(), c.tolist(), int(period)),
            dtype=np.float64,
        )
    prev_close = np.roll(c, 1)
    prev_close[0] = c[0]
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_close), np.abs(l - prev_close)))
    tr[0] = h[0] - l[0]
    return sma(tr, period)


def rsi(values: Sequence[float] | np.ndarray | pd.Series, period: int) -> np.ndarray:
    """Relative Strength Index using simple rolling means of gains/losses."""
    if period < 1:
        raise ValueError("period must be >= 1")
    arr = _as_f64(values)
    if _NATIVE is not None:
        return np.asarray(_NATIVE.rsi(arr.tolist(), int(period)), dtype=np.float64)
    n = arr.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    if n < period + 1:
        return out
    delta = np.diff(arr, prepend=arr[0])
    delta[0] = 0.0
    gains = np.where(delta > 0, delta, 0.0)
    losses = np.where(delta < 0, -delta, 0.0)
    avg_gain = sma(gains, period)
    avg_loss = sma(losses, period)
    for i in range(n):
        g, loss = avg_gain[i], avg_loss[i]
        if np.isnan(g) or np.isnan(loss):
            continue
        if loss == 0.0:
            out[i] = 50.0 if g == 0.0 else 100.0
        else:
            rs = g / loss
            out[i] = 100.0 - (100.0 / (1.0 + rs))
    return out


def batch_sma(
    series_list: List[Sequence[float] | np.ndarray | pd.Series],
    window: int,
) -> List[np.ndarray]:
    """SMA over many series; uses rayon inside ``fsb_core`` when available."""
    if window < 1:
        raise ValueError("window must be >= 1")
    prepared = [_as_f64(s).tolist() for s in series_list]
    if _NATIVE is not None:
        return [np.asarray(row, dtype=np.float64) for row in _NATIVE.batch_sma(prepared, int(window))]
    return [sma(s, window) for s in prepared]


def equity_sma_crossover(
    close: Sequence[float] | np.ndarray | pd.Series,
    sma_fast: Sequence[float] | np.ndarray | pd.Series,
    sma_slow: Sequence[float] | np.ndarray | pd.Series,
    initial_balance: float = 10_000.0,
    position_fraction: float = 0.1,
) -> np.ndarray:
    """Compact equity curve for SMA crossover (native loop when available)."""
    c = _as_f64(close)
    f = _as_f64(sma_fast)
    s = _as_f64(sma_slow)
    if not (c.shape == f.shape == s.shape):
        raise ValueError("close, sma_fast, and sma_slow lengths must match")
    if _NATIVE is not None:
        return np.asarray(
            _NATIVE.equity_sma_crossover(
                c.tolist(),
                f.tolist(),
                s.tolist(),
                float(initial_balance),
                float(position_fraction),
            ),
            dtype=np.float64,
        )
    n = c.shape[0]
    balance = float(initial_balance)
    side = 0
    size = 0.0
    entry = 0.0
    equity = np.empty(n, dtype=np.float64)
    for i in range(n):
        px = float(c[i])
        if i >= 1:
            fi, si, pf, ps = float(f[i]), float(s[i]), float(f[i - 1]), float(s[i - 1])
            if not any(map(np.isnan, (fi, si, pf, ps))):
                cross_up = fi > si and pf <= ps
                cross_dn = fi < si and pf >= ps
                if cross_up and side <= 0:
                    if side < 0:
                        balance += -size * (px - entry)
                        side = 0
                        size = 0.0
                    size = (balance * position_fraction) / px
                    entry = px
                    side = 1
                elif cross_dn and side >= 0:
                    if side > 0:
                        balance += size * (px - entry)
                        side = 0
                        size = 0.0
                    size = (balance * position_fraction) / px
                    entry = px
                    side = -1
        mtm = side * size * (px - entry) if side else 0.0
        equity[i] = balance + mtm
    return equity


def apply_sma_atr_indicators(
    df: pd.DataFrame,
    fast_period: int,
    slow_period: int,
    atr_period: int,
) -> pd.DataFrame:
    """Fill ``SMA_fast``, ``SMA_slow``, and ``ATR`` columns (native when possible)."""
    out = df.copy()
    close = out["Close"]
    out["SMA_fast"] = sma(close, fast_period)
    out["SMA_slow"] = sma(close, slow_period)
    out["ATR"] = atr(out["High"], out["Low"], close, atr_period)
    return out


def _max_drawdown(equity: np.ndarray) -> float:
    peak = -np.inf
    max_dd = 0.0
    for e in equity:
        if e > peak:
            peak = float(e)
        if peak > 0.0:
            dd = (peak - float(e)) / peak
            if dd > max_dd:
                max_dd = dd
    return max_dd


def _sma_crossover_metrics(
    close: np.ndarray,
    fast: int,
    slow: int,
    initial_balance: float,
    position_fraction: float,
) -> Tuple[float, float, float]:
    if close.size == 0 or fast < 1 or slow < 1 or fast >= slow:
        return float(initial_balance), 0.0, 0.0
    equity = equity_sma_crossover(
        close,
        sma(close, fast),
        sma(close, slow),
        initial_balance=initial_balance,
        position_fraction=position_fraction,
    )
    final_eq = float(equity[-1]) if equity.size else float(initial_balance)
    total_return = (
        (final_eq - initial_balance) / initial_balance if initial_balance != 0.0 else 0.0
    )
    return final_eq, total_return, _max_drawdown(equity)


def sweep_sma_crossover(
    close: Sequence[float] | np.ndarray | pd.Series,
    fast_periods: Sequence[int],
    slow_periods: Sequence[int],
    initial_balance: float = 10_000.0,
    position_fraction: float = 0.1,
) -> np.ndarray:
    """Parallel SMA-crossover parameter grid sweep.

    Returns rows ``[fast, slow, final_equity, total_return, max_drawdown]`` for
    every pair with ``fast < slow``. Uses rayon inside ``fsb_core`` when available.
    """
    arr = _as_f64(close)
    fasts = [int(x) for x in fast_periods]
    slows = [int(x) for x in slow_periods]
    if _NATIVE is not None and hasattr(_NATIVE, "sweep_sma_crossover"):
        rows = _NATIVE.sweep_sma_crossover(
            arr.tolist(),
            fasts,
            slows,
            float(initial_balance),
            float(position_fraction),
        )
        return np.asarray(rows, dtype=np.float64).reshape(-1, 5) if rows else np.zeros((0, 5))

    rows: List[List[float]] = []
    for fast in fasts:
        for slow in slows:
            if fast < 1 or slow < 1 or fast >= slow:
                continue
            final_eq, ret, dd = _sma_crossover_metrics(
                arr, fast, slow, float(initial_balance), float(position_fraction)
            )
            rows.append([float(fast), float(slow), final_eq, ret, dd])
    return np.asarray(rows, dtype=np.float64).reshape(-1, 5) if rows else np.zeros((0, 5))


def walk_forward_windows(
    n: int,
    train_size: int,
    test_size: int,
    step_size: int,
) -> List[Tuple[int, int, int, int]]:
    """Build rolling walk-forward index windows ``(train_start, train_end, test_start, test_end)``.

    Ends are exclusive. Windows advance by ``step_size`` bars.
    """
    if n < 1 or train_size < 1 or test_size < 1 or step_size < 1:
        raise ValueError("n, train_size, test_size, and step_size must be >= 1")
    windows: List[Tuple[int, int, int, int]] = []
    start = 0
    while True:
        train_start = start
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append((train_start, train_end, test_start, test_end))
        start += step_size
    return windows


def walk_forward_sma_sweep(
    close: Sequence[float] | np.ndarray | pd.Series,
    fast_periods: Sequence[int],
    slow_periods: Sequence[int],
    windows: Sequence[Sequence[int]],
    initial_balance: float = 10_000.0,
    position_fraction: float = 0.1,
) -> np.ndarray:
    """Walk-forward SMA parameter sweep (train grid → freeze → test).

    Each ``windows`` entry is ``[train_start, train_end, test_start, test_end]``
    (end exclusive). Result rows:
    ``[best_fast, best_slow, train_return, test_return, test_final_equity, test_max_dd]``.
    """
    arr = _as_f64(close)
    fasts = [int(x) for x in fast_periods]
    slows = [int(x) for x in slow_periods]
    parsed = [[int(x) for x in w] for w in windows]
    for i, w in enumerate(parsed):
        if len(w) != 4:
            raise ValueError(f"window {i} must have 4 indices")
    if _NATIVE is not None and hasattr(_NATIVE, "walk_forward_sma_sweep"):
        rows = _NATIVE.walk_forward_sma_sweep(
            arr.tolist(),
            fasts,
            slows,
            parsed,
            float(initial_balance),
            float(position_fraction),
        )
        return np.asarray(rows, dtype=np.float64).reshape(-1, 6) if rows else np.zeros((0, 6))

    pairs = [(f, s) for f in fasts for s in slows if f >= 1 and s >= 1 and f < s]
    if not pairs:
        return np.zeros((0, 6), dtype=np.float64)

    rows_out: List[List[float]] = []
    for ts, te, xs, xe in parsed:
        train = arr[ts:te]
        best_fast, best_slow = pairs[0]
        best_train_ret = -np.inf
        for fast, slow in pairs:
            _eq, ret, _dd = _sma_crossover_metrics(
                train, fast, slow, float(initial_balance), float(position_fraction)
            )
            if ret > best_train_ret:
                best_train_ret = ret
                best_fast, best_slow = fast, slow
        test = arr[xs:xe]
        test_eq, test_ret, test_dd = _sma_crossover_metrics(
            test, best_fast, best_slow, float(initial_balance), float(position_fraction)
        )
        rows_out.append(
            [
                float(best_fast),
                float(best_slow),
                float(best_train_ret),
                float(test_ret),
                float(test_eq),
                float(test_dd),
            ]
        )
    return np.asarray(rows_out, dtype=np.float64)


def multi_symbol_equity_aggregate(
    closes: Sequence[Sequence[float] | np.ndarray | pd.Series],
    fast_period: int,
    slow_period: int,
    initial_balance: float = 10_000.0,
    position_fraction: float = 0.1,
    weights: Optional[Sequence[float]] = None,
) -> Dict[str, Union[List[np.ndarray], np.ndarray]]:
    """Multi-symbol SMA-crossover workers with weighted portfolio equity.

    Returns ``{"per_symbol": [equity, ...], "portfolio": equity}``. Equal weight
    when ``weights`` is omitted. Uses rayon inside ``fsb_core`` when available.
    """
    if not closes:
        return {"per_symbol": [], "portfolio": np.zeros(0, dtype=np.float64)}
    if fast_period < 1 or slow_period < 1 or fast_period >= slow_period:
        raise ValueError("require fast_period >= 1, slow_period >= 1, and fast < slow")
    prepared = [_as_f64(c) for c in closes]
    n = prepared[0].shape[0]
    for i, arr in enumerate(prepared):
        if arr.shape[0] != n:
            raise ValueError(f"symbol {i} length {arr.shape[0]} != first symbol length {n}")

    weight_list: List[float]
    if weights is None:
        weight_list = []
    else:
        weight_list = [float(w) for w in weights]

    if _NATIVE is not None and hasattr(_NATIVE, "multi_symbol_equity_aggregate"):
        per, port = _NATIVE.multi_symbol_equity_aggregate(
            [a.tolist() for a in prepared],
            int(fast_period),
            int(slow_period),
            float(initial_balance),
            float(position_fraction),
            weight_list,
        )
        return {
            "per_symbol": [np.asarray(row, dtype=np.float64) for row in per],
            "portfolio": np.asarray(port, dtype=np.float64),
        }

    m = len(prepared)
    if not weight_list:
        w = np.full(m, 1.0 / m, dtype=np.float64)
    else:
        if len(weight_list) != m:
            raise ValueError("weights length must match number of symbols")
        w = np.asarray(weight_list, dtype=np.float64)
        wsum = float(w.sum())
        if wsum <= 0.0 or not np.isfinite(wsum):
            raise ValueError("weights must sum to a positive finite value")
        w = w / wsum

    per_symbol = [
        equity_sma_crossover(
            arr,
            sma(arr, fast_period),
            sma(arr, slow_period),
            initial_balance=initial_balance,
            position_fraction=position_fraction,
        )
        for arr in prepared
    ]
    portfolio = np.zeros(n, dtype=np.float64)
    for sym_eq, wi in zip(per_symbol, w):
        if initial_balance != 0.0:
            rets = (sym_eq / initial_balance) - 1.0
        else:
            rets = np.zeros_like(sym_eq)
        portfolio += wi * initial_balance * (1.0 + rets)
    return {"per_symbol": per_symbol, "portfolio": portfolio}


def equity_rsi_mean_reversion(
    close: Sequence[float] | np.ndarray | pd.Series,
    rsi_values: Sequence[float] | np.ndarray | pd.Series,
    oversold: float = 30.0,
    overbought: float = 70.0,
    initial_balance: float = 10_000.0,
    position_fraction: float = 0.1,
) -> np.ndarray:
    """RSI mean-reversion equity: long on cross up through oversold, short on cross down through overbought."""
    c = _as_f64(close)
    r = _as_f64(rsi_values)
    if c.shape != r.shape:
        raise ValueError("close and rsi lengths must match")
    if not (np.isfinite(oversold) and np.isfinite(overbought)) or oversold >= overbought:
        raise ValueError("require finite oversold < overbought")
    if _NATIVE is not None and hasattr(_NATIVE, "equity_rsi_mean_reversion"):
        return np.asarray(
            _NATIVE.equity_rsi_mean_reversion(
                c.tolist(),
                r.tolist(),
                float(oversold),
                float(overbought),
                float(initial_balance),
                float(position_fraction),
            ),
            dtype=np.float64,
        )
    n = c.shape[0]
    balance = float(initial_balance)
    side = 0
    size = 0.0
    entry = 0.0
    equity = np.empty(n, dtype=np.float64)
    for i in range(n):
        px = float(c[i])
        if i >= 1:
            ri, pr = float(r[i]), float(r[i - 1])
            if not (np.isnan(ri) or np.isnan(pr)):
                cross_up = pr <= oversold and ri > oversold
                cross_dn = pr >= overbought and ri < overbought
                if cross_up and side <= 0:
                    if side < 0:
                        balance += -size * (px - entry)
                    size = (balance * position_fraction) / px
                    entry = px
                    side = 1
                elif cross_dn and side >= 0:
                    if side > 0:
                        balance += size * (px - entry)
                    size = (balance * position_fraction) / px
                    entry = px
                    side = -1
        mtm = side * size * (px - entry) if side else 0.0
        equity[i] = balance + mtm
    return equity


def _rsi_mean_reversion_metrics(
    close: np.ndarray,
    period: int,
    oversold: float,
    overbought: float,
    initial_balance: float,
    position_fraction: float,
) -> Tuple[float, float, float]:
    if close.size == 0 or period < 1 or oversold >= overbought:
        return float(initial_balance), 0.0, 0.0
    equity = equity_rsi_mean_reversion(
        close,
        rsi(close, period),
        oversold=oversold,
        overbought=overbought,
        initial_balance=initial_balance,
        position_fraction=position_fraction,
    )
    final_eq = float(equity[-1]) if equity.size else float(initial_balance)
    total_return = (
        (final_eq - initial_balance) / initial_balance if initial_balance != 0.0 else 0.0
    )
    return final_eq, total_return, _max_drawdown(equity)


def sweep_rsi_mean_reversion(
    close: Sequence[float] | np.ndarray | pd.Series,
    rsi_periods: Sequence[int],
    oversold_levels: Sequence[float],
    overbought_levels: Sequence[float],
    initial_balance: float = 10_000.0,
    position_fraction: float = 0.1,
) -> np.ndarray:
    """Parallel RSI mean-reversion parameter grid sweep.

    Returns rows
    ``[period, oversold, overbought, final_equity, total_return, max_drawdown]``
    for every triple with ``period >= 1`` and ``oversold < overbought``.
    """
    arr = _as_f64(close)
    periods = [int(x) for x in rsi_periods]
    oversolds = [float(x) for x in oversold_levels]
    overboughts = [float(x) for x in overbought_levels]
    if _NATIVE is not None and hasattr(_NATIVE, "sweep_rsi_mean_reversion"):
        rows = _NATIVE.sweep_rsi_mean_reversion(
            arr.tolist(),
            periods,
            oversolds,
            overboughts,
            float(initial_balance),
            float(position_fraction),
        )
        return np.asarray(rows, dtype=np.float64).reshape(-1, 6) if rows else np.zeros((0, 6))

    rows: List[List[float]] = []
    for period in periods:
        if period < 1:
            continue
        for os in oversolds:
            for ob in overboughts:
                if not (np.isfinite(os) and np.isfinite(ob)) or os >= ob:
                    continue
                final_eq, ret, dd = _rsi_mean_reversion_metrics(
                    arr, period, os, ob, float(initial_balance), float(position_fraction)
                )
                rows.append([float(period), float(os), float(ob), final_eq, ret, dd])
    return np.asarray(rows, dtype=np.float64).reshape(-1, 6) if rows else np.zeros((0, 6))

def ema(values: Sequence[float] | np.ndarray | pd.Series, period: int) -> np.ndarray:
    """Exponential moving average; leading values are NaN until ``period`` fills."""
    if period < 1:
        raise ValueError("period must be >= 1")
    arr = _as_f64(values)
    if _NATIVE is not None and hasattr(_NATIVE, "ema"):
        return np.asarray(_NATIVE.ema(arr.tolist(), int(period)), dtype=np.float64)
    n = arr.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    if n < period:
        return out
    seed = float(np.mean(arr[:period]))
    out[period - 1] = seed
    alpha = 2.0 / (period + 1.0)
    prev = seed
    for i in range(period, n):
        prev = alpha * float(arr[i]) + (1.0 - alpha) * prev
        out[i] = prev
    return out


def macd(
    close: Sequence[float] | np.ndarray | pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Dict[str, np.ndarray]:
    """MACD line, signal line, and histogram.

    Returns ``{"macd", "signal", "histogram"}``.
    """
    if fast_period < 1 or slow_period < 1 or signal_period < 1 or fast_period >= slow_period:
        raise ValueError("require fast >= 1, slow >= 1, signal >= 1, and fast < slow")
    arr = _as_f64(close)
    if _NATIVE is not None and hasattr(_NATIVE, "macd"):
        m, s, h = _NATIVE.macd(
            arr.tolist(), int(fast_period), int(slow_period), int(signal_period)
        )
        return {
            "macd": np.asarray(m, dtype=np.float64),
            "signal": np.asarray(s, dtype=np.float64),
            "histogram": np.asarray(h, dtype=np.float64),
        }
    ema_f = ema(arr, fast_period)
    ema_s = ema(arr, slow_period)
    macd_line = ema_f - ema_s
    # Signal EMA over finite MACD values (match Rust seed behavior).
    n = arr.shape[0]
    signal = np.full(n, np.nan, dtype=np.float64)
    hist = np.full(n, np.nan, dtype=np.float64)
    seed_sum = 0.0
    seed_count = 0
    prev = np.nan
    alpha = 2.0 / (signal_period + 1.0)
    for i in range(n):
        m = float(macd_line[i])
        if np.isnan(m):
            continue
        if seed_count < signal_period:
            seed_sum += m
            seed_count += 1
            if seed_count == signal_period:
                prev = seed_sum / signal_period
                signal[i] = prev
                hist[i] = m - prev
            continue
        prev = alpha * m + (1.0 - alpha) * prev
        signal[i] = prev
        hist[i] = m - prev
    return {"macd": macd_line, "signal": signal, "histogram": hist}


def equity_ema_crossover(
    close: Sequence[float] | np.ndarray | pd.Series,
    ema_fast: Sequence[float] | np.ndarray | pd.Series,
    ema_slow: Sequence[float] | np.ndarray | pd.Series,
    initial_balance: float = 10_000.0,
    position_fraction: float = 0.1,
) -> np.ndarray:
    """EMA crossover equity (same side logic as SMA crossover)."""
    if _NATIVE is not None and hasattr(_NATIVE, "equity_ema_crossover"):
        c = _as_f64(close)
        f = _as_f64(ema_fast)
        s = _as_f64(ema_slow)
        if c.shape != f.shape or c.shape != s.shape:
            raise ValueError("close, ema_fast, and ema_slow lengths must match")
        return np.asarray(
            _NATIVE.equity_ema_crossover(
                c.tolist(),
                f.tolist(),
                s.tolist(),
                float(initial_balance),
                float(position_fraction),
            ),
            dtype=np.float64,
        )
    return equity_sma_crossover(
        close, ema_fast, ema_slow, initial_balance=initial_balance, position_fraction=position_fraction
    )


def _ema_crossover_metrics(
    close: np.ndarray,
    fast: int,
    slow: int,
    initial_balance: float,
    position_fraction: float,
) -> Tuple[float, float, float]:
    if close.size == 0 or fast < 1 or slow < 1 or fast >= slow:
        return float(initial_balance), 0.0, 0.0
    equity = equity_ema_crossover(
        close,
        ema(close, fast),
        ema(close, slow),
        initial_balance=initial_balance,
        position_fraction=position_fraction,
    )
    final_eq = float(equity[-1]) if equity.size else float(initial_balance)
    total_return = (
        (final_eq - initial_balance) / initial_balance if initial_balance != 0.0 else 0.0
    )
    return final_eq, total_return, _max_drawdown(equity)


def sweep_ema_crossover(
    close: Sequence[float] | np.ndarray | pd.Series,
    fast_periods: Sequence[int],
    slow_periods: Sequence[int],
    initial_balance: float = 10_000.0,
    position_fraction: float = 0.1,
) -> np.ndarray:
    """Parallel EMA-crossover parameter grid sweep.

    Returns rows ``[fast, slow, final_equity, total_return, max_drawdown]``
    for every pair with ``fast < slow``.
    """
    arr = _as_f64(close)
    fasts = [int(x) for x in fast_periods]
    slows = [int(x) for x in slow_periods]
    if _NATIVE is not None and hasattr(_NATIVE, "sweep_ema_crossover"):
        rows = _NATIVE.sweep_ema_crossover(
            arr.tolist(),
            fasts,
            slows,
            float(initial_balance),
            float(position_fraction),
        )
        return np.asarray(rows, dtype=np.float64).reshape(-1, 5) if rows else np.zeros((0, 5))

    rows: List[List[float]] = []
    for fast in fasts:
        for slow in slows:
            if fast < 1 or slow < 1 or fast >= slow:
                continue
            final_eq, ret, dd = _ema_crossover_metrics(
                arr, fast, slow, float(initial_balance), float(position_fraction)
            )
            rows.append([float(fast), float(slow), final_eq, ret, dd])
    return np.asarray(rows, dtype=np.float64).reshape(-1, 5) if rows else np.zeros((0, 5))


def equity_macd_crossover(
    close: Sequence[float] | np.ndarray | pd.Series,
    macd_line: Sequence[float] | np.ndarray | pd.Series,
    signal_line: Sequence[float] | np.ndarray | pd.Series,
    initial_balance: float = 10_000.0,
    position_fraction: float = 0.1,
) -> np.ndarray:
    """MACD vs signal crossover equity."""
    c = _as_f64(close)
    m = _as_f64(macd_line)
    s = _as_f64(signal_line)
    if c.shape != m.shape or c.shape != s.shape:
        raise ValueError("close, macd_line, and signal_line lengths must match")
    if _NATIVE is not None and hasattr(_NATIVE, "equity_macd_crossover"):
        return np.asarray(
            _NATIVE.equity_macd_crossover(
                c.tolist(),
                m.tolist(),
                s.tolist(),
                float(initial_balance),
                float(position_fraction),
            ),
            dtype=np.float64,
        )
    return equity_sma_crossover(
        c, m, s, initial_balance=initial_balance, position_fraction=position_fraction
    )


def _macd_crossover_metrics(
    close: np.ndarray,
    fast: int,
    slow: int,
    signal: int,
    initial_balance: float,
    position_fraction: float,
) -> Tuple[float, float, float]:
    if close.size == 0 or fast < 1 or slow < 1 or signal < 1 or fast >= slow:
        return float(initial_balance), 0.0, 0.0
    comps = macd(close, fast, slow, signal)
    equity = equity_macd_crossover(
        close,
        comps["macd"],
        comps["signal"],
        initial_balance=initial_balance,
        position_fraction=position_fraction,
    )
    final_eq = float(equity[-1]) if equity.size else float(initial_balance)
    total_return = (
        (final_eq - initial_balance) / initial_balance if initial_balance != 0.0 else 0.0
    )
    return final_eq, total_return, _max_drawdown(equity)


def sweep_macd(
    close: Sequence[float] | np.ndarray | pd.Series,
    fast_periods: Sequence[int],
    slow_periods: Sequence[int],
    signal_periods: Sequence[int],
    initial_balance: float = 10_000.0,
    position_fraction: float = 0.1,
) -> np.ndarray:
    """Parallel MACD parameter grid sweep.

    Returns rows
    ``[fast, slow, signal, final_equity, total_return, max_drawdown]``
    for every triple with ``fast < slow`` and all periods >= 1.
    """
    arr = _as_f64(close)
    fasts = [int(x) for x in fast_periods]
    slows = [int(x) for x in slow_periods]
    signals = [int(x) for x in signal_periods]
    if _NATIVE is not None and hasattr(_NATIVE, "sweep_macd"):
        rows = _NATIVE.sweep_macd(
            arr.tolist(),
            fasts,
            slows,
            signals,
            float(initial_balance),
            float(position_fraction),
        )
        return np.asarray(rows, dtype=np.float64).reshape(-1, 6) if rows else np.zeros((0, 6))

    rows: List[List[float]] = []
    for fast in fasts:
        for slow in slows:
            if fast < 1 or slow < 1 or fast >= slow:
                continue
            for sig in signals:
                if sig < 1:
                    continue
                final_eq, ret, dd = _macd_crossover_metrics(
                    arr, fast, slow, sig, float(initial_balance), float(position_fraction)
                )
                rows.append([float(fast), float(slow), float(sig), final_eq, ret, dd])
    return np.asarray(rows, dtype=np.float64).reshape(-1, 6) if rows else np.zeros((0, 6))

