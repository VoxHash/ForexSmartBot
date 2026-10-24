"""Tests for strategy registry and core strategy signal paths."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from forexsmartbot.strategies import RISK_LEVELS, STRATEGIES, get_strategy, list_strategies
from forexsmartbot.strategies.breakout_atr import BreakoutATR
from forexsmartbot.strategies.rsi_reversion import RSIRevertion
from forexsmartbot.strategies.sma_crossover import SMACrossover


def _ohlcv(n: int = 40, seed: int = 42, trend: float = 0.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-01", periods=n, freq="h")
    close = 100.0 + np.cumsum(rng.normal(0.0, 0.1, size=n)) + np.linspace(0.0, trend, n)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + rng.uniform(0.1, 0.5, size=n),
            "Low": close - rng.uniform(0.1, 0.5, size=n),
            "Close": close,
            "Volume": rng.integers(1000, 5000, size=n),
        },
        index=idx,
    )


class TestStrategyRegistry:
    def test_list_core_strategies(self):
        names = list_strategies()
        for required in ("SMA_Crossover", "BreakoutATR", "RSI_Reversion", "Fear_Index"):
            assert required in names
            assert required in STRATEGIES

    def test_risk_levels_cover_registered_core(self):
        low_med_high = set(RISK_LEVELS["Low_Risk"] + RISK_LEVELS["Medium_Risk"] + RISK_LEVELS["High_Risk"])
        for name in ("SMA_Crossover", "BreakoutATR", "RSI_Reversion", "Fear_Index"):
            assert name in low_med_high

    def test_get_strategy_and_unknown(self):
        strategy = get_strategy("SMA_Crossover")
        assert isinstance(strategy, SMACrossover)
        with pytest.raises(ValueError, match="Unknown strategy"):
            get_strategy("InvalidStrategy")


class TestSMACrossover:
    def setup_method(self):
        self.strategy = SMACrossover(fast_period=5, slow_period=10, atr_period=5)
        self.df = _ohlcv(n=30, seed=42)

    def test_indicators_and_signal(self):
        result = self.strategy.indicators(self.df)
        assert {"SMA_fast", "SMA_slow", "ATR"}.issubset(result.columns)
        assert not result["SMA_fast"].isna().all()
        assert not result["ATR"].isna().all()
        assert self.strategy.signal(result) in (-1, 0, 1)

    def test_volatility_and_exits(self):
        result = self.strategy.indicators(self.df)
        vol = self.strategy.volatility(result)
        assert vol is None or vol > 0
        entry = 100.0
        sl_long = self.strategy.stop_loss(result, entry, 1)
        if sl_long is not None:
            assert sl_long < entry
        sl_short = self.strategy.stop_loss(result, entry, -1)
        if sl_short is not None:
            assert sl_short > entry
        tp_long = self.strategy.take_profit(result, entry, 1)
        if tp_long is not None:
            assert tp_long > entry
        tp_short = self.strategy.take_profit(result, entry, -1)
        if tp_short is not None:
            assert tp_short < entry

    def test_parameters(self):
        assert self.strategy.name == "SMA Crossover"
        self.strategy.set_params(fast_period=10, slow_period=20)
        assert self.strategy._fast_period == 10
        assert self.strategy._slow_period == 20


class TestBreakoutATR:
    def setup_method(self):
        self.strategy = BreakoutATR(lookback_period=5, atr_period=5)
        self.df = _ohlcv(n=30, seed=7, trend=5.0)

    def test_indicators_and_signal(self):
        result = self.strategy.indicators(self.df)
        assert {"Donchian_high", "Donchian_low", "Donchian_mid", "ATR", "ATR_filter"}.issubset(
            result.columns
        )
        assert self.strategy.signal(result) in (-1, 0, 1)

    def test_low_volatility_filters_signal(self):
        low_vol = self.df.copy()
        low_vol["High"] = low_vol["Close"] + 0.01
        low_vol["Low"] = low_vol["Close"] - 0.01
        assert self.strategy.signal(self.strategy.indicators(low_vol)) == 0


class TestRSIRevertion:
    def setup_method(self):
        self.strategy = RSIRevertion(rsi_period=5, oversold_level=30, overbought_level=70)
        idx = pd.date_range("2023-01-01", periods=30, freq="h")
        prices = 100 + 5 * np.sin(np.linspace(0, 4 * np.pi, 30))
        self.df = pd.DataFrame(
            {
                "Open": prices,
                "High": prices + 0.5,
                "Low": prices - 0.5,
                "Close": prices,
                "Volume": np.full(30, 2000),
            },
            index=idx,
        )

    def test_indicators_and_signal(self):
        result = self.strategy.indicators(self.df)
        assert {"RSI", "Trend", "ATR"}.issubset(result.columns)
        rsi_values = result["RSI"].dropna()
        if len(rsi_values) > 0:
            assert rsi_values.min() >= 0
            assert rsi_values.max() <= 100
        assert self.strategy.signal(result) in (-1, 0, 1)
