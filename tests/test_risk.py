"""Tests for RiskEngine and RiskManager sizing helpers."""

from __future__ import annotations

import pytest

from forexsmartbot.core.risk import RiskManager
from forexsmartbot.core.risk_engine import RiskConfig, RiskEngine


class TestRiskManager:
    def test_clips_to_bounds(self):
        mgr = RiskManager(min_amt=10.0, max_amt=100.0, risk_pct=0.02)
        assert mgr.adaptive_amount(10_000.0, None) == pytest.approx(100.0)
        tiny = RiskManager(min_amt=10.0, max_amt=100.0, risk_pct=0.0001)
        assert tiny.adaptive_amount(1_000.0, None) == pytest.approx(10.0)

    def test_higher_vol_reduces_size(self):
        mgr = RiskManager(min_amt=1.0, max_amt=10_000.0, risk_pct=0.02)
        low = mgr.adaptive_amount(10_000.0, 0.01)
        high = mgr.adaptive_amount(10_000.0, 0.05)
        assert high < low

    def test_winrate_hint_increases_size(self):
        mgr = RiskManager(min_amt=1.0, max_amt=10_000.0, risk_pct=0.02)
        base = mgr.adaptive_amount(10_000.0, None, winrate_hint=0.5)
        better = mgr.adaptive_amount(10_000.0, None, winrate_hint=0.7)
        assert better >= base


class TestRiskEngine:
    def test_risk_config_defaults(self):
        config = RiskConfig()
        assert config.base_risk_pct == 0.02
        assert config.max_risk_pct == 0.05
        assert config.daily_risk_cap == 0.05
        assert config.max_drawdown_pct == 0.25

    def test_position_size_calculation(self):
        engine = RiskEngine(RiskConfig())
        size = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10_000, 0.01)
        assert size > 0
        assert size <= engine.config.max_trade_amount

    def test_volatility_targeting(self):
        # High vol must make vol-target risk < base risk so the min() path differs
        config = RiskConfig(
            base_risk_pct=0.05,
            max_risk_pct=0.20,
            min_trade_amount=1.0,
            max_trade_amount=10_000.0,
            volatility_target=0.01,
        )
        engine = RiskEngine(config)
        size_high_vol = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10_000, 0.5)
        size_low_vol = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10_000, 0.05)
        assert size_high_vol < size_low_vol
        assert size_high_vol == pytest.approx(200.0)  # 10000 * 0.01 / 0.5

    def test_daily_and_drawdown_limits(self):
        config = RiskConfig()
        engine = RiskEngine(config)
        balance = 10_000
        daily_limit = balance * config.daily_risk_cap
        assert not engine.check_daily_risk_limit(-daily_limit + 1, balance)
        assert engine.check_daily_risk_limit(-daily_limit - 1, balance)

        peak = 10_000
        max_dd = peak * config.max_drawdown_pct
        assert not engine.check_drawdown_limit(peak - max_dd + 1, peak)
        assert engine.check_drawdown_limit(peak - max_dd - 1, peak)

    def test_drawdown_throttle_reduces_size(self):
        config = RiskConfig(max_trade_amount=1000.0)
        engine = RiskEngine(config)
        peak = 10_000
        current = peak * (1 - config.max_drawdown_pct - 0.01)
        engine.check_drawdown_limit(current, peak)
        assert engine._drawdown_throttle
        size = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10_000, 0.01)
        assert size < config.max_trade_amount

    def test_kelly_and_multipliers(self):
        config = RiskConfig(max_trade_amount=1000.0)
        config.symbol_risk_multipliers = {"EURUSD": 1.5, "USDJPY": 0.8}
        config.strategy_risk_multipliers = {"SMA_Crossover": 1.2, "RSI_Reversion": 0.9}
        engine = RiskEngine(config)

        size_50 = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10_000, 0.01, 0.5)
        size_60 = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10_000, 0.01, 0.6)
        assert size_60 > size_50

        size_eur = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10_000, 0.01)
        size_jpy = engine.calculate_position_size("USDJPY", "SMA_Crossover", 10_000, 0.01)
        assert size_eur > size_jpy

        size_sma = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10_000, 0.01)
        size_rsi = engine.calculate_position_size("EURUSD", "RSI_Reversion", 10_000, 0.01)
        assert size_sma > size_rsi

    def test_trade_tracking_and_summary(self):
        engine = RiskEngine(RiskConfig())
        engine.add_trade_result(100, "EURUSD", "SMA_Crossover")
        engine.add_trade_result(-50, "EURUSD", "SMA_Crossover")
        engine.add_trade_result(75, "EURUSD", "SMA_Crossover")
        assert engine.get_recent_win_rate("EURUSD", "SMA_Crossover") == pytest.approx(2 / 3)
        assert engine.get_recent_volatility("EURUSD") > 0

        engine._daily_pnl = -100
        engine._current_equity = 9500
        engine._peak_equity = 10_000
        summary = engine.get_risk_summary()
        for key in (
            "daily_pnl",
            "current_equity",
            "peak_equity",
            "current_drawdown",
            "recent_trades_count",
            "recent_win_rate",
        ):
            assert key in summary
