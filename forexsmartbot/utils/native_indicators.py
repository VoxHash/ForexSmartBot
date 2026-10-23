"""Native (Rust/PyO3) indicator helpers with pure-Python/NumPy fallback.

Build optional extension from ``native/fsb_core``::

    cd native/fsb_core && maturin develop --release

When ``fsb_core`` is not installed, callers still get correct results via NumPy.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

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
