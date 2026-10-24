"""Tests for Multi_Timeframe registration and IDataProvider contract."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from forexsmartbot.core.interfaces import IDataProvider, IStrategy
from forexsmartbot.strategies import (
    MULTI_TIMEFRAME_AVAILABLE,
    STRATEGIES,
    get_strategy,
    list_strategies,
)
from forexsmartbot.strategies.multi_timeframe_strategy import MultiTimeframeStrategy
from forexsmartbot.strategies.sma_crossover import SMACrossover


def _ohlcv(n: int = 80, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n, freq="h")
    close = 1.10 + np.cumsum(rng.normal(0, 0.0008, size=n))
    high = close + rng.uniform(0.0001, 0.0010, size=n)
    low = close - rng.uniform(0.0001, 0.0010, size=n)
    open_ = close + rng.normal(0, 0.0002, size=n)
    volume = rng.integers(100, 1000, size=n)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=idx,
    )


class RecordingProvider(IDataProvider):
    """Minimal real IDataProvider that returns synthetic bars per interval."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, str]] = []

    def get_data(
        self, symbol: str, start: str, end: str, interval: str = "1h"
    ) -> pd.DataFrame:
        self.calls.append((symbol, start, end, interval))
        # Distinct length per interval so callers can tell timeframes apart
        n = {"1h": 60, "4h": 40, "1d": 30}.get(interval, 50)
        return _ohlcv(n=n, seed=abs(hash(interval)) % 10_000)

    def get_latest_price(self, symbol: str) -> float | None:
        return 1.1050

    def get_historical_data(
        self, symbol: str, period: str = "1d", interval: str = "1h"
    ) -> pd.DataFrame:
        return _ohlcv(n=48, seed=7)

    def is_available(self) -> bool:
        return True


def test_idata_provider_imported_from_core_not_adapters():
    """Multi-timeframe must use the core contract, not adapters.data (avoids zmq)."""
    import inspect

    import forexsmartbot.strategies.multi_timeframe_strategy as mtf_mod

    assert mtf_mod.IDataProvider is IDataProvider
    source = inspect.getsource(mtf_mod)
    assert "from ..core.interfaces import" in source
    assert "IDataProvider" in source
    assert "adapters.data" not in source


def test_multi_timeframe_registered_and_available():
    assert MULTI_TIMEFRAME_AVAILABLE is True
    assert "Multi_Timeframe" in STRATEGIES
    assert "Multi_Timeframe" in list_strategies()
    assert STRATEGIES["Multi_Timeframe"] is MultiTimeframeStrategy


def test_get_strategy_multi_timeframe_without_kwargs():
    """UI / backtest call get_strategy(name) with no params."""
    strategy = get_strategy("Multi_Timeframe")
    assert isinstance(strategy, MultiTimeframeStrategy)
    assert isinstance(strategy, IStrategy)
    assert "SMA Crossover" in strategy.name
    assert strategy.params["base_strategy"] == "SMA Crossover"


def test_get_strategy_multi_timeframe_with_base_name():
    strategy = get_strategy("Multi_Timeframe", base_strategy="RSI_Reversion")
    assert "RSI" in strategy.name or "Reversion" in strategy.name
    assert strategy.params["base_strategy"]


def test_get_strategy_multi_timeframe_rejects_self_wrap():
    with pytest.raises(ValueError, match="cannot wrap itself"):
        get_strategy("Multi_Timeframe", base_strategy="Multi_Timeframe")


def test_indicators_and_signal_with_provider():
    strategy = get_strategy("Multi_Timeframe", timeframes=["1h", "4h"])
    provider = RecordingProvider()
    strategy.set_data_provider(provider)

    df = _ohlcv(n=80)
    out = strategy.indicators(df)
    assert "SMA_fast" in out.columns
    assert "SMA_slow" in out.columns
    assert "1h_trend" in out.columns
    assert "4h_trend" in out.columns
    assert len(provider.calls) == 2

    signal = strategy.signal(out)
    assert signal in (-1, 0, 1)


def test_default_base_is_sma_crossover_instance():
    strategy = MultiTimeframeStrategy()
    assert isinstance(strategy._base_strategy, SMACrossover)
