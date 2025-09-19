"""Tests for backtesting service."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.strategies import get_strategy
from forexsmartbot.core.risk_engine import RiskConfig


class TestBacktestService:
    """Test cases for BacktestService."""
    
    def setup_method(self):
        """Setup test data and services."""
        # Create mock data provider
        self.data_provider = MockDataProvider()
        self.backtest_service = BacktestService(self.data_provider)
        
        # Create test strategy
        self.strategy = get_strategy('SMA_Crossover')
        
        # Create risk config
        self.risk_config = RiskConfig()
        
    def test_run_backtest_basic(self):
        """Test basic backtest execution."""
        result = self.backtest_service.run_backtest(
            strategy=self.strategy,
            symbol='EURUSD',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_balance=10000.0,
            risk_config=self.risk_config
        )
        
        assert 'error' not in result
        assert result['symbol'] == 'EURUSD'
        assert result['strategy'] == 'SMA Crossover'
        assert result['initial_balance'] == 10000.0
        assert 'final_balance' in result
        assert 'final_equity' in result
        assert 'total_return' in result
        assert 'max_drawdown' in result
        assert 'win_rate' in result
        assert 'total_trades' in result
        assert 'equity_series' in result
        assert 'trades' in result
        
    def test_run_backtest_no_data(self):
        """Test backtest with no data."""
        # Create empty data provider
        empty_provider = MockDataProvider(empty=True)
        backtest_service = BacktestService(empty_provider)
        
        result = backtest_service.run_backtest(
            strategy=self.strategy,
            symbol='EURUSD',
            start_date='2023-01-01',
            end_date='2023-01-31'
        )
        
        assert 'error' in result
        assert 'No data available' in result['error']
        
    def test_walk_forward_analysis(self):
        """Test walk-forward analysis."""
        result = self.backtest_service.run_walk_forward_analysis(
            strategy=self.strategy,
            symbol='EURUSD',
            start_date='2023-01-01',
            end_date='2023-03-31',
            training_period=30,
            testing_period=15,
            step_size=10,
            risk_config=self.risk_config
        )
        
        assert 'error' not in result
        assert result['symbol'] == 'EURUSD'
        assert result['strategy'] == 'SMA Crossover'
        assert 'splits' in result
        assert 'results' in result
        assert 'aggregate_metrics' in result
        
        # Check that we have some splits
        assert result['splits'] > 0
        assert len(result['results']) == result['splits']
        
        # Check aggregate metrics
        agg_metrics = result['aggregate_metrics']
        assert 'avg_return' in agg_metrics
        assert 'std_return' in agg_metrics
        assert 'profitable_splits' in agg_metrics
        assert 'total_splits' in agg_metrics
        
    def test_time_splits_generation(self):
        """Test time splits generation."""
        # Create test data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        df = pd.DataFrame({'Close': np.random.randn(100)}, index=dates)
        
        splits = self.backtest_service._generate_time_splits(
            df, training_period=20, testing_period=10, step_size=5
        )
        
        assert len(splits) > 0
        
        # Check that splits don't overlap
        for i in range(len(splits) - 1):
            current_train_end = splits[i][1]
            next_test_start = splits[i + 1][2]
            assert current_train_end < next_test_start
            
    def test_aggregate_metrics_calculation(self):
        """Test aggregate metrics calculation."""
        # Create mock results
        results = [
            {'total_return': 0.05, 'max_drawdown': 0.02, 'win_rate': 0.6, 'profit_factor': 1.5, 'sharpe_ratio': 1.2},
            {'total_return': 0.03, 'max_drawdown': 0.01, 'win_rate': 0.7, 'profit_factor': 2.0, 'sharpe_ratio': 1.5},
            {'total_return': -0.01, 'max_drawdown': 0.05, 'win_rate': 0.4, 'profit_factor': 0.8, 'sharpe_ratio': -0.5},
        ]
        
        agg_metrics = self.backtest_service._calculate_aggregate_metrics(results)
        
        assert agg_metrics['avg_return'] == pytest.approx(0.0233, abs=1e-3)
        assert agg_metrics['profitable_splits'] == 2
        assert agg_metrics['total_splits'] == 3
        assert agg_metrics['avg_win_rate'] == pytest.approx(0.5667, abs=1e-3)
        
    def test_backtest_with_trades(self):
        """Test backtest that generates trades."""
        # Create data with clear trend for signal generation
        dates = pd.date_range('2023-01-01', periods=50, freq='H')
        # Create upward trend
        prices = 100 + np.linspace(0, 5, 50)
        
        trend_df = pd.DataFrame({
            'Open': prices,
            'High': prices + 0.5,
            'Low': prices - 0.5,
            'Close': prices,
            'Volume': np.random.randint(1000, 5000, 50)
        }, index=dates)
        
        # Mock the data provider to return this data
        self.data_provider.set_data('EURUSD', trend_df)
        
        result = self.backtest_service.run_backtest(
            strategy=self.strategy,
            symbol='EURUSD',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_balance=10000.0,
            risk_config=self.risk_config
        )
        
        assert 'error' not in result
        assert result['total_trades'] >= 0
        assert len(result['trades']) == result['total_trades']
        
        # If there are trades, check their structure
        if result['trades']:
            trade = result['trades'][0]
            assert 'symbol' in trade
            assert 'side' in trade
            assert 'quantity' in trade
            assert 'entry_price' in trade
            assert 'exit_price' in trade
            assert 'pnl' in trade
            assert 'strategy' in trade


class MockDataProvider:
    """Mock data provider for testing."""
    
    def __init__(self, empty=False):
        self.empty = empty
        self.data = {}
        
    def set_data(self, symbol, df):
        """Set data for a symbol."""
        self.data[symbol] = df
        
    def get_data(self, symbol, start, end, interval='1h'):
        """Get historical data."""
        if self.empty or symbol not in self.data:
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            
        df = self.data[symbol]
        
        # Filter by date range
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)
        
        return df[(df.index >= start_date) & (df.index <= end_date)]
        
    def get_latest_price(self, symbol):
        """Get latest price."""
        if self.empty or symbol not in self.data:
            return None
            
        df = self.data[symbol]
        if df.empty:
            return None
            
        return float(df['Close'].iloc[-1])
        
    def is_available(self):
        """Check if available."""
        return not self.empty
