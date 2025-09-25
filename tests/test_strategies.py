"""Tests for trading strategies."""

import pytest
import pandas as pd
import numpy as np
from forexsmartbot.strategies import get_strategy, list_strategies
from forexsmartbot.strategies.sma_crossover import SMACrossover
from forexsmartbot.strategies.breakout_atr import BreakoutATR
from forexsmartbot.strategies.rsi_reversion import RSIRevertion


class TestStrategyRegistry:
    """Test strategy registry functionality."""
    
    def test_list_strategies(self):
        """Test listing available strategies."""
        strategies = list_strategies()
        assert 'SMA_Crossover' in strategies
        assert 'BreakoutATR' in strategies
        assert 'RSI_Reversion' in strategies
        
    def test_get_strategy(self):
        """Test getting strategy instances."""
        # Test valid strategy
        strategy = get_strategy('SMA_Crossover')
        assert isinstance(strategy, SMACrossover)
        
        # Test invalid strategy
        with pytest.raises(ValueError):
            get_strategy('InvalidStrategy')


class TestSMACrossover:
    """Test SMA Crossover strategy."""
    
    def setup_method(self):
        """Setup test data."""
        self.strategy = SMACrossover(fast_period=5, slow_period=10, atr_period=5)
        
        # Create test data
        dates = pd.date_range('2023-01-01', periods=20, freq='H')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(20) * 0.1)
        
        self.df = pd.DataFrame({
            'Open': prices,
            'High': prices + np.random.rand(20) * 0.5,
            'Low': prices - np.random.rand(20) * 0.5,
            'Close': prices,
            'Volume': np.random.randint(1000, 5000, 20)
        }, index=dates)
        
    def test_indicators(self):
        """Test indicator calculation."""
        result_df = self.strategy.indicators(self.df)
        
        assert 'SMA_fast' in result_df.columns
        assert 'SMA_slow' in result_df.columns
        assert 'ATR' in result_df.columns
        
        # Check that SMAs are calculated
        assert not result_df['SMA_fast'].isna().all()
        assert not result_df['SMA_slow'].isna().all()
        assert not result_df['ATR'].isna().all()
        
    def test_signal_generation(self):
        """Test signal generation."""
        df_with_indicators = self.strategy.indicators(self.df)
        
        signal = self.strategy.signal(df_with_indicators)
        assert signal in [-1, 0, 1]
        
    def test_volatility_calculation(self):
        """Test volatility calculation."""
        df_with_indicators = self.strategy.indicators(self.df)
        
        volatility = self.strategy.volatility(df_with_indicators)
        assert volatility is None or volatility > 0
        
    def test_stop_loss_calculation(self):
        """Test stop loss calculation."""
        df_with_indicators = self.strategy.indicators(self.df)
        entry_price = 100.0
        
        # Test long position
        sl_long = self.strategy.stop_loss(df_with_indicators, entry_price, 1)
        if sl_long is not None:
            assert sl_long < entry_price
            
        # Test short position
        sl_short = self.strategy.stop_loss(df_with_indicators, entry_price, -1)
        if sl_short is not None:
            assert sl_short > entry_price
            
    def test_take_profit_calculation(self):
        """Test take profit calculation."""
        df_with_indicators = self.strategy.indicators(self.df)
        entry_price = 100.0
        
        # Test long position
        tp_long = self.strategy.take_profit(df_with_indicators, entry_price, 1)
        if tp_long is not None:
            assert tp_long > entry_price
            
        # Test short position
        tp_short = self.strategy.take_profit(df_with_indicators, entry_price, -1)
        if tp_short is not None:
            assert tp_short < entry_price
            
    def test_parameters(self):
        """Test strategy parameters."""
        assert self.strategy.name == "SMA Crossover"
        assert 'fast_period' in self.strategy.params
        assert 'slow_period' in self.strategy.params
        assert 'atr_period' in self.strategy.params
        
    def test_parameter_update(self):
        """Test parameter updating."""
        self.strategy.set_params(fast_period=10, slow_period=20)
        assert self.strategy._fast_period == 10
        assert self.strategy._slow_period == 20


class TestBreakoutATR:
    """Test Breakout ATR strategy."""
    
    def setup_method(self):
        """Setup test data."""
        self.strategy = BreakoutATR(lookback_period=5, atr_period=5)
        
        # Create test data with clear breakout pattern
        dates = pd.date_range('2023-01-01', periods=20, freq='H')
        prices = np.linspace(100, 105, 20)  # Upward trend
        
        self.df = pd.DataFrame({
            'Open': prices,
            'High': prices + 0.5,
            'Low': prices - 0.5,
            'Close': prices,
            'Volume': np.random.randint(1000, 5000, 20)
        }, index=dates)
        
    def test_indicators(self):
        """Test indicator calculation."""
        result_df = self.strategy.indicators(self.df)
        
        assert 'Donchian_high' in result_df.columns
        assert 'Donchian_low' in result_df.columns
        assert 'Donchian_mid' in result_df.columns
        assert 'ATR' in result_df.columns
        assert 'ATR_filter' in result_df.columns
        
    def test_signal_generation(self):
        """Test signal generation."""
        df_with_indicators = self.strategy.indicators(self.df)
        
        signal = self.strategy.signal(df_with_indicators)
        assert signal in [-1, 0, 1]
        
    def test_volatility_filtering(self):
        """Test volatility filtering."""
        # Create low volatility data
        low_vol_df = self.df.copy()
        low_vol_df['High'] = low_vol_df['Close'] + 0.01
        low_vol_df['Low'] = low_vol_df['Close'] - 0.01
        
        df_with_indicators = self.strategy.indicators(low_vol_df)
        signal = self.strategy.signal(df_with_indicators)
        
        # Should not generate signal due to low volatility
        assert signal == 0


class TestRSIRevertion:
    """Test RSI Reversion strategy."""
    
    def setup_method(self):
        """Setup test data."""
        self.strategy = RSIRevertion(rsi_period=5, oversold_level=30, overbought_level=70)
        
        # Create test data with RSI pattern
        dates = pd.date_range('2023-01-01', periods=20, freq='H')
        # Create oscillating prices for RSI calculation
        prices = 100 + 5 * np.sin(np.linspace(0, 4*np.pi, 20))
        
        self.df = pd.DataFrame({
            'Open': prices,
            'High': prices + 0.5,
            'Low': prices - 0.5,
            'Close': prices,
            'Volume': np.random.randint(1000, 5000, 20)
        }, index=dates)
        
    def test_indicators(self):
        """Test indicator calculation."""
        result_df = self.strategy.indicators(self.df)
        
        assert 'RSI' in result_df.columns
        assert 'Trend' in result_df.columns
        assert 'ATR' in result_df.columns
        
        # Check RSI values are in valid range
        rsi_values = result_df['RSI'].dropna()
        if len(rsi_values) > 0:
            assert rsi_values.min() >= 0
            assert rsi_values.max() <= 100
            
    def test_signal_generation(self):
        """Test signal generation."""
        df_with_indicators = self.strategy.indicators(self.df)
        
        signal = self.strategy.signal(df_with_indicators)
        assert signal in [-1, 0, 1]
        
    def test_rsi_levels(self):
        """Test RSI level detection."""
        # Create data with extreme RSI values
        extreme_df = self.df.copy()
        extreme_df['Close'] = 100  # Constant price for extreme RSI
        
        df_with_indicators = self.strategy.indicators(extreme_df)
        
        # RSI should be around 50 for constant price
        rsi_values = df_with_indicators['RSI'].dropna()
        if len(rsi_values) > 0:
            assert abs(rsi_values.iloc[-1] - 50) < 10  # Should be close to 50
