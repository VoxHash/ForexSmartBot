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

