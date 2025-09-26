"""Tests for risk management engine."""

import pytest
import numpy as np
from forexsmartbot.core.risk_engine import RiskEngine, RiskConfig


class TestRiskEngine:
    """Test cases for RiskEngine."""
    
    def test_risk_config_defaults(self):
        """Test default risk configuration."""
        config = RiskConfig()
        assert config.base_risk_pct == 0.02
        assert config.max_risk_pct == 0.05
        assert config.daily_risk_cap == 0.05
        assert config.max_drawdown_pct == 0.25
        
    def test_position_size_calculation(self):
        """Test position size calculation."""
        config = RiskConfig()
        engine = RiskEngine(config)
        
        # Test basic position size
        size = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10000, 0.01)
        assert size > 0
        assert size <= config.max_trade_amount
        
    def test_volatility_targeting(self):
        """Test volatility targeting."""
        config = RiskConfig(
            base_risk_pct=0.001,  # Very small base risk to allow volatility targeting
            max_risk_pct=0.20,    # Increase max risk to 20%
            min_trade_amount=1.0,  # Reduce min trade amount
            max_trade_amount=10000.0  # Increase max trade amount to allow volatility targeting
        )
        engine = RiskEngine(config)
        
        # High volatility should reduce position size
        size_high_vol = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10000, 0.05)
        size_low_vol = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10000, 0.01)
        
        assert size_high_vol < size_low_vol
        
    def test_daily_risk_limit(self):
        """Test daily risk limit checking."""
        config = RiskConfig()
        engine = RiskEngine(config)
        
        balance = 10000
        daily_limit = balance * config.daily_risk_cap
        
        # Should not exceed limit
        assert not engine.check_daily_risk_limit(-daily_limit + 1, balance)
        
        # Should exceed limit
        assert engine.check_daily_risk_limit(-daily_limit - 1, balance)
        
    def test_drawdown_limit(self):
        """Test drawdown limit checking."""
        config = RiskConfig()
        engine = RiskEngine(config)
        
        peak_equity = 10000
        max_drawdown = peak_equity * config.max_drawdown_pct
        
        # Should not exceed drawdown limit
        assert not engine.check_drawdown_limit(peak_equity - max_drawdown + 1, peak_equity)
        
        # Should exceed drawdown limit
        assert engine.check_drawdown_limit(peak_equity - max_drawdown - 1, peak_equity)
        
    def test_drawdown_throttle(self):
        """Test drawdown throttle mechanism."""
        config = RiskConfig(max_trade_amount=1000.0)  # Increase max trade amount
        engine = RiskEngine(config)
        
        peak_equity = 10000
        current_equity = peak_equity * (1 - config.max_drawdown_pct - 0.01)
        
        # Should trigger throttle
        engine.check_drawdown_limit(current_equity, peak_equity)
        assert engine._drawdown_throttle
        
        # Position size should be reduced
        size = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10000, 0.01)
        assert size < config.max_trade_amount
        
    def test_kelly_criterion(self):
        """Test Kelly Criterion calculation."""
        config = RiskConfig()
        engine = RiskEngine(config)
        
        # Test with different win rates
        size_50_win = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10000, 0.01, 0.5)
        size_60_win = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10000, 0.01, 0.6)
        
        # Higher win rate should allow larger position
        assert size_60_win > size_50_win
        
    def test_risk_multipliers(self):
        """Test symbol and strategy risk multipliers."""
        config = RiskConfig(max_trade_amount=1000.0)  # Increase max trade amount
        config.symbol_risk_multipliers = {"EURUSD": 1.5, "USDJPY": 0.8}
        config.strategy_risk_multipliers = {"SMA_Crossover": 1.2, "RSI_Reversion": 0.9}
        
        engine = RiskEngine(config)
        
        # Test symbol multiplier
        size_eur = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10000, 0.01)
        size_jpy = engine.calculate_position_size("USDJPY", "SMA_Crossover", 10000, 0.01)
        
        assert size_eur > size_jpy
        
        # Test strategy multiplier
        size_sma = engine.calculate_position_size("EURUSD", "SMA_Crossover", 10000, 0.01)
        size_rsi = engine.calculate_position_size("EURUSD", "RSI_Reversion", 10000, 0.01)
        
        assert size_sma > size_rsi
        
    def test_trade_result_tracking(self):
        """Test trade result tracking."""
        config = RiskConfig()
        engine = RiskEngine(config)
        
        # Add some trade results
        engine.add_trade_result(100, "EURUSD", "SMA_Crossover")
        engine.add_trade_result(-50, "EURUSD", "SMA_Crossover")
        engine.add_trade_result(75, "EURUSD", "SMA_Crossover")
        
        # Check win rate
        win_rate = engine.get_recent_win_rate("EURUSD", "SMA_Crossover")
        assert win_rate == 2/3  # 2 wins out of 3 trades
        
        # Check volatility
        volatility = engine.get_recent_volatility("EURUSD")
        assert volatility > 0
        
    def test_risk_summary(self):
        """Test risk summary generation."""
        config = RiskConfig()
        engine = RiskEngine(config)
        
        # Add some data
        engine._daily_pnl = -100
        engine._current_equity = 9500
        engine._peak_equity = 10000
        engine.add_trade_result(50, "EURUSD", "SMA_Crossover")
        
        summary = engine.get_risk_summary()
        
        assert 'daily_pnl' in summary
        assert 'current_equity' in summary
        assert 'peak_equity' in summary
        assert 'current_drawdown' in summary
        assert 'recent_trades_count' in summary
        assert 'recent_win_rate' in summary
