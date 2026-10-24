"""Unit tests for backtest dialog helpers (no Qt event loop required)."""

from forexsmartbot.utils.backtest_utils import parse_strategy_label


def test_parse_strategy_label_strips_emoji_and_risk():
    assert parse_strategy_label("🟢 SMA_Crossover (Low Risk)") == "SMA_Crossover"
    assert parse_strategy_label("🟡 RSI_Reversion (Medium Risk)") == "RSI_Reversion"
    assert parse_strategy_label("🔴 Momentum_Breakout (High Risk)") == "Momentum_Breakout"
    assert parse_strategy_label("⚪ Custom_Strategy") == "Custom_Strategy"
    assert parse_strategy_label("SMA_Crossover") == "SMA_Crossover"
