"""Tests for native indicator helpers and NumPy fallback path."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from forexsmartbot.utils import native_indicators as ni


def _close(n: int = 64, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return 1.10 + np.cumsum(rng.normal(0.0, 0.0008, size=n))


def _ohlc(n: int = 64, seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    close = _close(n, seed)
    high = close + 0.0012
    low = close - 0.0010
    return high, low, close


def test_native_status_helpers():
    assert isinstance(ni.native_available(), bool)
    status = ni.native_status()
    assert isinstance(status, str)
    assert status  # non-empty


def test_sma_matches_rolling_mean():
    close = _close()
    window = 10
    out = ni.sma(close, window)
    assert out.shape == close.shape
    assert np.all(np.isnan(out[: window - 1]))
    expected = pd.Series(close).rolling(window).mean().to_numpy()
    np.testing.assert_allclose(out[window - 1 :], expected[window - 1 :], rtol=1e-9, atol=1e-12)


def test_sma_rejects_bad_window():
    with pytest.raises(ValueError, match="window"):
        ni.sma([1.0, 2.0, 3.0], 0)


def test_atr_finite_after_warmup():
    high, low, close = _ohlc()
    period = 14
    out = ni.atr(high, low, close, period)
    assert out.shape == close.shape
    warm = out[period - 1 :]
    assert np.all(np.isfinite(warm))
    assert np.all(warm > 0)


def test_rsi_bounded():
    close = _close(n=80, seed=3)
    period = 14
    out = ni.rsi(close, period)
    valid = out[~np.isnan(out)]
    assert len(valid) > 0
    assert valid.min() >= 0.0
    assert valid.max() <= 100.0


def test_numpy_fallback_path_when_native_disabled(monkeypatch):
    """Business math must work when fsb_core is absent (NumPy path)."""
    monkeypatch.setattr(ni, "_NATIVE", None)
    monkeypatch.setattr(ni, "_NATIVE_ERR", "forced-off-for-test")
    assert ni.native_available() is False
    assert "unavailable" in ni.native_status()

    close = _close(n=40, seed=9)
    window = 5
    out = ni.sma(close, window)
    expected = pd.Series(close).rolling(window).mean().to_numpy()
    np.testing.assert_allclose(out[window - 1 :], expected[window - 1 :], rtol=1e-9, atol=1e-12)

    high, low, c = _ohlc(n=40, seed=9)
    atr = ni.atr(high, low, c, 7)
    assert np.all(np.isfinite(atr[6:]))

    rsi = ni.rsi(close, 7)
    valid = rsi[~np.isnan(rsi)]
    assert len(valid) > 0
    assert valid.min() >= 0.0 and valid.max() <= 100.0


def test_batch_sma_and_apply_columns():
    series = [_close(n=30, seed=i) for i in range(3)]
    batch = ni.batch_sma(series, 5)
    assert len(batch) == 3
    np.testing.assert_allclose(batch[0], ni.sma(series[0], 5), equal_nan=True)

    high, low, close = _ohlc(n=30, seed=1)
    df = pd.DataFrame({"High": high, "Low": low, "Close": close})
    out = ni.apply_sma_atr_indicators(df, fast_period=3, slow_period=7, atr_period=5)
    assert {"SMA_fast", "SMA_slow", "ATR"}.issubset(out.columns)
    assert out is not df


def test_equity_sma_crossover_runs():
    close = _close(n=50, seed=11)
    fast = ni.sma(close, 5)
    slow = ni.sma(close, 15)
    equity = ni.equity_sma_crossover(close, fast, slow, initial_balance=10_000.0)
    assert equity.shape == close.shape
    assert np.all(np.isfinite(equity))
    assert equity[0] == pytest.approx(10_000.0)
