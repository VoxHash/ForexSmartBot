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


def test_sweep_sma_crossover_grid():
    close = _close(n=120, seed=21)
    rows = ni.sweep_sma_crossover(
        close,
        fast_periods=[3, 5, 8],
        slow_periods=[10, 15, 20],
        initial_balance=10_000.0,
    )
    assert rows.ndim == 2 and rows.shape[1] == 5
    assert rows.shape[0] == 9  # all fast < slow
    assert np.all(rows[:, 0] < rows[:, 1])
    assert np.all(np.isfinite(rows[:, 2:]))


def test_walk_forward_sma_sweep():
    close = _close(n=200, seed=31)
    windows = ni.walk_forward_windows(len(close), train_size=60, test_size=20, step_size=20)
    assert len(windows) >= 2
    rows = ni.walk_forward_sma_sweep(
        close,
        fast_periods=[4, 6],
        slow_periods=[12, 18],
        windows=windows,
        initial_balance=10_000.0,
    )
    assert rows.shape == (len(windows), 6)
    assert np.all(rows[:, 0] < rows[:, 1])
    assert np.all(np.isfinite(rows[:, 2:]))


def test_multi_symbol_equity_aggregate():
    closes = [_close(n=80, seed=40 + i) for i in range(3)]
    out = ni.multi_symbol_equity_aggregate(
        closes,
        fast_period=5,
        slow_period=15,
        initial_balance=10_000.0,
        weights=[0.5, 0.3, 0.2],
    )
    assert len(out["per_symbol"]) == 3
    assert out["portfolio"].shape == (80,)
    assert np.all(np.isfinite(out["portfolio"]))
    assert out["portfolio"][0] == pytest.approx(10_000.0)


def test_sweep_and_multi_symbol_numpy_fallback(monkeypatch):
    monkeypatch.setattr(ni, "_NATIVE", None)
    monkeypatch.setattr(ni, "_NATIVE_ERR", "forced-off-for-test")
    close = _close(n=90, seed=51)
    rows = ni.sweep_sma_crossover(close, [5], [15], initial_balance=5_000.0)
    assert rows.shape == (1, 5)
    assert rows[0, 2] == pytest.approx(5_000.0) or np.isfinite(rows[0, 2])

    windows = ni.walk_forward_windows(len(close), 40, 15, 15)
    wf = ni.walk_forward_sma_sweep(close, [5], [15], windows, initial_balance=5_000.0)
    assert wf.shape[0] == len(windows)

    multi = ni.multi_symbol_equity_aggregate(
        [close, _close(n=90, seed=52)],
        fast_period=5,
        slow_period=15,
        initial_balance=5_000.0,
    )
    assert len(multi["per_symbol"]) == 2
    assert multi["portfolio"].shape == (90,)


def test_equity_rsi_mean_reversion_runs():
    close = _close(n=80, seed=61)
    rsi_vals = ni.rsi(close, 14)
    equity = ni.equity_rsi_mean_reversion(
        close, rsi_vals, oversold=30.0, overbought=70.0, initial_balance=10_000.0
    )
    assert equity.shape == close.shape
    assert np.all(np.isfinite(equity))
    assert equity[0] == pytest.approx(10_000.0)


def test_sweep_rsi_mean_reversion_grid():
    close = _close(n=120, seed=71)
    rows = ni.sweep_rsi_mean_reversion(
        close,
        rsi_periods=[7, 14],
        oversold_levels=[25.0, 30.0],
        overbought_levels=[70.0, 75.0],
        initial_balance=10_000.0,
    )
    assert rows.ndim == 2 and rows.shape[1] == 6
    assert rows.shape[0] == 8
    assert np.all(rows[:, 1] < rows[:, 2])
    assert np.all(np.isfinite(rows[:, 3:]))


def test_rsi_mean_reversion_numpy_fallback(monkeypatch):
    monkeypatch.setattr(ni, "_NATIVE", None)
    monkeypatch.setattr(ni, "_NATIVE_ERR", "forced-off-for-test")
    close = _close(n=90, seed=81)
    rows = ni.sweep_rsi_mean_reversion(
        close, [14], [30.0], [70.0], initial_balance=5_000.0
    )
    assert rows.shape == (1, 6)
    assert np.isfinite(rows[0, 3])
    equity = ni.equity_rsi_mean_reversion(close, ni.rsi(close, 14), 30.0, 70.0, 5_000.0)
    assert equity.shape == close.shape


def test_ema_finite_after_warmup():
    close = _close(n=50, seed=91)
    out = ni.ema(close, 10)
    assert out.shape == close.shape
    assert np.all(np.isnan(out[:9]))
    assert np.all(np.isfinite(out[9:]))


def test_macd_components():
    close = _close(n=80, seed=92)
    comps = ni.macd(close, 8, 17, 5)
    assert set(comps) == {"macd", "signal", "histogram"}
    assert comps["macd"].shape == close.shape
    finite = np.isfinite(comps["signal"])
    assert finite.any()
    assert np.all(np.isfinite(comps["histogram"][finite]))


def test_equity_ema_and_sweep():
    close = _close(n=100, seed=93)
    equity = ni.equity_ema_crossover(
        close, ni.ema(close, 5), ni.ema(close, 15), initial_balance=10_000.0
    )
    assert equity.shape == close.shape
    assert np.all(np.isfinite(equity))
    rows = ni.sweep_ema_crossover(close, [5, 8], [15, 20], initial_balance=10_000.0)
    assert rows.ndim == 2 and rows.shape[1] == 5
    assert rows.shape[0] == 4
    assert np.all(rows[:, 0] < rows[:, 1])


def test_equity_macd_and_sweep():
    close = _close(n=120, seed=94)
    comps = ni.macd(close, 8, 17, 5)
    equity = ni.equity_macd_crossover(
        close, comps["macd"], comps["signal"], initial_balance=10_000.0
    )
    assert equity.shape == close.shape
    assert np.all(np.isfinite(equity))
    rows = ni.sweep_macd(
        close,
        fast_periods=[8, 10],
        slow_periods=[17, 21],
        signal_periods=[5, 7],
        initial_balance=10_000.0,
    )
    assert rows.ndim == 2 and rows.shape[1] == 6
    assert rows.shape[0] == 8
    assert np.all(rows[:, 0] < rows[:, 1])


def test_ema_macd_numpy_fallback(monkeypatch):
    monkeypatch.setattr(ni, "_NATIVE", None)
    monkeypatch.setattr(ni, "_NATIVE_ERR", "forced-off-for-test")
    close = _close(n=90, seed=95)
    assert ni.ema(close, 10).shape == close.shape
    comps = ni.macd(close, 8, 17, 5)
    assert comps["macd"].shape == close.shape
    rows = ni.sweep_ema_crossover(close, [5], [15], initial_balance=5_000.0)
    assert rows.shape == (1, 5)
    macd_rows = ni.sweep_macd(close, [8], [17], [5], initial_balance=5_000.0)
    assert macd_rows.shape == (1, 6)


def test_bollinger_matches_pandas():
    close = _close(n=80, seed=101)
    period, num_std = 20, 2.0
    bands = ni.bollinger(close, period, num_std)
    assert set(bands) == {"middle", "upper", "lower"}
    s = pd.Series(close)
    mid = s.rolling(period).mean().to_numpy()
    std = s.rolling(period).std().to_numpy()
    np.testing.assert_allclose(bands["middle"][period - 1 :], mid[period - 1 :], rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(
        bands["upper"][period - 1 :],
        (mid + num_std * std)[period - 1 :],
        rtol=1e-9,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        bands["lower"][period - 1 :],
        (mid - num_std * std)[period - 1 :],
        rtol=1e-9,
        atol=1e-12,
    )


def test_equity_bollinger_and_sweep():
    close = _close(n=120, seed=102)
    bands = ni.bollinger(close, 20, 2.0)
    equity = ni.equity_bollinger_mean_reversion(
        close, bands["upper"], bands["lower"], initial_balance=10_000.0
    )
    assert equity.shape == close.shape
    assert np.all(np.isfinite(equity))
    assert equity[0] == pytest.approx(10_000.0)
    rows = ni.sweep_bollinger_mean_reversion(
        close, periods=[10, 20], num_stds=[1.5, 2.0], initial_balance=10_000.0
    )
    assert rows.ndim == 2 and rows.shape[1] == 5
    assert rows.shape[0] == 4
    assert np.all(rows[:, 0] >= 10)
    assert np.all(np.isfinite(rows[:, 2:]))


def test_bollinger_numpy_fallback(monkeypatch):
    monkeypatch.setattr(ni, "_NATIVE", None)
    monkeypatch.setattr(ni, "_NATIVE_ERR", "forced-off-for-test")
    close = _close(n=90, seed=103)
    bands = ni.bollinger(close, 15, 2.0)
    assert bands["middle"].shape == close.shape
    rows = ni.sweep_bollinger_mean_reversion(
        close, [15], [2.0], initial_balance=5_000.0
    )
    assert rows.shape == (1, 5)
    assert np.isfinite(rows[0, 2])


def test_stochastic_matches_manual():
    close = _close(n=80, seed=201)
    high = close * 1.01
    low = close * 0.99
    k_period, d_period = 14, 3
    lines = ni.stochastic(high, low, close, k_period, d_period)
    assert set(lines) == {"k", "d"}
    assert lines["k"].shape == close.shape
    # Manual %K at last index
    i = len(close) - 1
    hh = float(np.max(high[i + 1 - k_period : i + 1]))
    ll = float(np.min(low[i + 1 - k_period : i + 1]))
    expected_k = 100.0 * (float(close[i]) - ll) / (hh - ll)
    assert lines["k"][i] == pytest.approx(expected_k, rel=1e-9, abs=1e-12)
    # %D is SMA of last d_period finite %K values
    expected_d = float(np.mean(lines["k"][i + 1 - d_period : i + 1]))
    assert lines["d"][i] == pytest.approx(expected_d, rel=1e-9, abs=1e-12)
    first_d = k_period + d_period - 2
    assert np.all(np.isnan(lines["d"][:first_d]))
    assert np.isfinite(lines["d"][first_d])


def test_equity_stochastic_and_sweep():
    close = _close(n=120, seed=202)
    lines = ni.stochastic(close, close, close, 14, 3)
    equity = ni.equity_stochastic_crossover(
        close, lines["k"], lines["d"], initial_balance=10_000.0
    )
    assert equity.shape == close.shape
    assert np.all(np.isfinite(equity))
    assert equity[0] == pytest.approx(10_000.0)
    rows = ni.sweep_stochastic_crossover(
        close, k_periods=[10, 14], d_periods=[3, 5], initial_balance=10_000.0
    )
    assert rows.ndim == 2 and rows.shape[1] == 5
    assert rows.shape[0] == 4
    assert np.all(rows[:, 0] >= 10)
    assert np.all(np.isfinite(rows[:, 2:]))


def test_stochastic_numpy_fallback(monkeypatch):
    monkeypatch.setattr(ni, "_NATIVE", None)
    monkeypatch.setattr(ni, "_NATIVE_ERR", "forced-off-for-test")
    close = _close(n=90, seed=203)
    lines = ni.stochastic(close, close, close, 14, 3)
    assert lines["k"].shape == close.shape
    rows = ni.sweep_stochastic_crossover(
        close, [14], [3], initial_balance=5_000.0
    )
    assert rows.shape == (1, 5)
    assert np.isfinite(rows[0, 2])


def test_donchian_matches_manual():
    close = _close(n=80, seed=301)
    high = close * 1.01
    low = close * 0.99
    period = 20
    bands = ni.donchian(high, low, period)
    assert set(bands) == {"middle", "upper", "lower"}
    assert bands["upper"].shape == close.shape
    i = len(close) - 1
    expected_u = float(np.max(high[i + 1 - period : i + 1]))
    expected_l = float(np.min(low[i + 1 - period : i + 1]))
    assert bands["upper"][i] == pytest.approx(expected_u, rel=1e-9, abs=1e-12)
    assert bands["lower"][i] == pytest.approx(expected_l, rel=1e-9, abs=1e-12)
    assert bands["middle"][i] == pytest.approx(0.5 * (expected_u + expected_l), rel=1e-9, abs=1e-12)
    assert np.all(np.isnan(bands["upper"][: period - 1]))
    assert np.isfinite(bands["upper"][period - 1])


def test_equity_donchian_and_sweep():
    close = _close(n=120, seed=302)
    bands = ni.donchian(close, close, 20)
    equity = ni.equity_donchian_breakout(
        close, bands["upper"], bands["lower"], initial_balance=10_000.0
    )
    assert equity.shape == close.shape
    assert np.all(np.isfinite(equity))
    assert equity[0] == pytest.approx(10_000.0)
    rows = ni.sweep_donchian_breakout(
        close, periods=[10, 20, 55], initial_balance=10_000.0
    )
    assert rows.ndim == 2 and rows.shape[1] == 4
    assert rows.shape[0] == 3
    assert np.all(rows[:, 0] >= 10)
    assert np.all(np.isfinite(rows[:, 1:]))


def test_donchian_numpy_fallback(monkeypatch):
    monkeypatch.setattr(ni, "_NATIVE", None)
    monkeypatch.setattr(ni, "_NATIVE_ERR", "forced-off-for-test")
    close = _close(n=90, seed=303)
    bands = ni.donchian(close, close, 15)
    assert bands["middle"].shape == close.shape
    rows = ni.sweep_donchian_breakout(close, [15], initial_balance=5_000.0)
    assert rows.shape == (1, 4)
    assert np.isfinite(rows[0, 1])
