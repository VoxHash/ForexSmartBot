"""GPU-accelerated backtesting service."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings

from ..core.interfaces import IStrategy, IDataProvider
from ..core.portfolio import Portfolio
from ..core.risk_engine import RiskEngine, RiskConfig
from ..adapters.brokers.paper_broker import PaperBroker
from ..utils.gpu_utils import get_gpu_manager, CUPY_AVAILABLE
from ..utils.gpu_numpy import gpu_array, gpu_rolling_mean, gpu_rolling_std

if CUPY_AVAILABLE:
    import cupy as cp


class GPUBacktestService:
    """GPU-accelerated backtesting service for parallel strategy evaluation."""
    
    def __init__(self, data_provider: IDataProvider, use_gpu: bool = True):
        """
        Initialize GPU backtesting service.
        
        Args:
            data_provider: Data provider for market data
            use_gpu: Whether to use GPU acceleration
        """
        self.data_provider = data_provider
        self.gpu_manager = get_gpu_manager(use_gpu=use_gpu)
        self.use_gpu = self.gpu_manager.use_gpu and CUPY_AVAILABLE
        
    def run_backtest(self, strategy: IStrategy, symbol: str, 
                    start_date: str, end_date: str, 
                    initial_balance: float = 10000.0,
                    risk_config: RiskConfig = None) -> Dict:
        """
        Run GPU-accelerated backtest.
        
        Args:
            strategy: Trading strategy to test
            symbol: Trading symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_balance: Initial account balance
            risk_config: Risk configuration
            
        Returns:
            Dictionary with backtest results
        """
        if risk_config is None:
            risk_config = RiskConfig()
        
        # Get data
        df = self.data_provider.get_data(symbol, start_date, end_date, "1h")
        if df.empty:
            return {'error': 'No data available'}
        
        # Convert to GPU arrays if available
        if self.use_gpu:
            return self._run_gpu_backtest(strategy, symbol, df, initial_balance, risk_config)
        else:
            return self._run_cpu_backtest(strategy, symbol, df, initial_balance, risk_config)
    
    def _run_gpu_backtest(self, strategy: IStrategy, symbol: str,
                         df: pd.DataFrame, initial_balance: float,
                         risk_config: RiskConfig) -> Dict:
        """Run backtest using GPU acceleration."""
        try:
            # Initialize components
            broker = PaperBroker(initial_balance)
            portfolio = Portfolio(initial_balance)
            risk_engine = RiskEngine(risk_config)
            
            # Convert price data to GPU arrays
            prices = gpu_array(df['Close'].values, use_gpu=True)
            highs = gpu_array(df['High'].values, use_gpu=True)
            lows = gpu_array(df['Low'].values, use_gpu=True)
            
            # Pre-calculate indicators on GPU
            df_with_indicators = strategy.indicators(df)
            
            # Convert indicators to GPU arrays
            indicators = {}
            for col in ['ATR', 'RSI', 'SMA_20', 'SMA_50']:
                if col in df_with_indicators.columns:
                    indicators[col] = gpu_array(df_with_indicators[col].fillna(0).values, use_gpu=True)
            
            # Run backtest loop (vectorized where possible)
            positions = {}
            trades = []
            equity_series = []
            balance_series = []
            timestamps = []
            
            # Convert to numpy for iteration (some operations still need sequential logic)
            prices_np = prices.to_numpy()
            df_array = df_with_indicators.values
            
            for i in range(len(df)):
                if i < 50:  # Need enough data for indicators
                    continue
                
                current_data = df_with_indicators.iloc[:i+1]
                current_price = float(prices_np[i])
                
                # Calculate indicators (already done, but ensure they're available)
                if len(current_data) < 50:
                    continue
                
                # Generate signal
                signal = strategy.signal(current_data)
                volatility = strategy.volatility(current_data)
                
                # Process trading logic
                if signal != 0:
                    self._process_signal_gpu(
                        strategy, symbol, signal, current_price, volatility,
                        positions, trades, broker, portfolio, risk_engine, current_data
                    )
                else:
                    # Check exit conditions
                    self._check_exit_conditions_gpu(
                        symbol, current_price, strategy, positions, trades,
                        broker, portfolio, risk_engine, current_data
                    )
                
                # Update portfolio
                portfolio.update_equity(broker.get_balance())
                
                # Record metrics
                equity_series.append(portfolio.get_total_equity())
                balance_series.append(portfolio.get_total_balance())
                timestamps.append(df.index[i])
            
            # Synchronize GPU operations
            self.gpu_manager.synchronize()
            
            # Calculate final metrics
            metrics = portfolio.calculate_metrics()
            
            return {
                'symbol': symbol,
                'start_date': df.index[0].strftime('%Y-%m-%d'),
                'end_date': df.index[-1].strftime('%Y-%m-%d'),
                'initial_balance': initial_balance,
                'final_balance': portfolio.get_total_balance(),
                'total_return': metrics.get('total_return', 0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                'max_drawdown': metrics.get('max_drawdown', 0),
                'win_rate': metrics.get('win_rate', 0),
                'total_trades': len(trades),
                'equity_series': equity_series,
                'balance_series': balance_series,
                'timestamps': timestamps,
                'trades': trades,
                'gpu_accelerated': True
            }
            
        except Exception as e:
            warnings.warn(f"GPU backtest error: {e}, falling back to CPU")
            return self._run_cpu_backtest(strategy, symbol, df, initial_balance, risk_config)
    
    def _run_cpu_backtest(self, strategy: IStrategy, symbol: str,
                          df: pd.DataFrame, initial_balance: float,
                          risk_config: RiskConfig) -> Dict:
        """Run backtest on CPU (fallback)."""
        from .backtest import BacktestService
        backtest_service = BacktestService(self.data_provider)
        return backtest_service.run_backtest(
            strategy, symbol, df.index[0].strftime('%Y-%m-%d'),
            df.index[-1].strftime('%Y-%m-%d'), initial_balance, risk_config
        )
    
    def _process_signal_gpu(self, strategy: IStrategy, symbol: str, signal: int,
                           current_price: float, volatility: Optional[float],
                           positions: Dict, trades: List, broker: PaperBroker,
                           portfolio: Portfolio, risk_engine: RiskEngine,
                           current_data: pd.DataFrame):
        """Process trading signal (GPU-accelerated version)."""
        # Close opposite position if exists
        if symbol in positions:
            pos = positions[symbol]
            if (signal > 0 and pos['side'] < 0) or (signal < 0 and pos['side'] > 0):
                # Close position
                pnl = broker.close_all(symbol)
                if pnl:
                    portfolio.add_trade(pnl)
                    trades.append({
                        'symbol': symbol,
                        'side': 'Close',
                        'entry_price': pos['entry_price'],
                        'exit_price': current_price,
                        'pnl': pnl,
                        'timestamp': current_data.index[-1]
                    })
                del positions[symbol]
        
        # Open new position
        if symbol not in positions:
            # Calculate position size using risk engine
            position_size = risk_engine.calculate_position_size(
                portfolio.get_total_balance(), current_price, volatility or 0.01
            )
            
            if position_size > 0:
                # Calculate stop loss and take profit
                stop_loss = strategy.stop_loss(current_data, current_price, signal)
                take_profit = strategy.take_profit(current_data, current_price, signal)
                
                # Submit order
                order_id = broker.submit_order(
                    symbol, signal, position_size, stop_loss, take_profit
                )
                
                if order_id:
                    positions[symbol] = {
                        'side': signal,
                        'entry_price': current_price,
                        'quantity': position_size,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    }
    
    def _check_exit_conditions_gpu(self, symbol: str, current_price: float,
                                   strategy: IStrategy, positions: Dict,
                                   trades: List, broker: PaperBroker,
                                   portfolio: Portfolio, risk_engine: RiskEngine,
                                   current_data: pd.DataFrame):
        """Check exit conditions for open positions."""
        if symbol not in positions:
            return
        
        pos = positions[symbol]
        stop_loss = pos.get('stop_loss')
        take_profit = pos.get('take_profit')
        
        # Check stop loss
        if stop_loss:
            if (pos['side'] > 0 and current_price <= stop_loss) or \
               (pos['side'] < 0 and current_price >= stop_loss):
                pnl = broker.close_all(symbol)
                if pnl:
                    portfolio.add_trade(pnl)
                    trades.append({
                        'symbol': symbol,
                        'side': 'Stop Loss',
                        'entry_price': pos['entry_price'],
                        'exit_price': current_price,
                        'pnl': pnl,
                        'timestamp': current_data.index[-1]
                    })
                del positions[symbol]
                return
        
        # Check take profit
        if take_profit:
            if (pos['side'] > 0 and current_price >= take_profit) or \
               (pos['side'] < 0 and current_price <= take_profit):
                pnl = broker.close_all(symbol)
                if pnl:
                    portfolio.add_trade(pnl)
                    trades.append({
                        'symbol': symbol,
                        'side': 'Take Profit',
                        'entry_price': pos['entry_price'],
                        'exit_price': current_price,
                        'pnl': pnl,
                        'timestamp': current_data.index[-1]
                    })
                del positions[symbol]
    
    def run_parallel_backtests(self, strategies: List[IStrategy], symbol: str,
                              start_date: str, end_date: str,
                              initial_balance: float = 10000.0,
                              risk_config: RiskConfig = None) -> List[Dict]:
        """
        Run multiple backtests in parallel using GPU.
        
        Args:
            strategies: List of strategies to test
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            initial_balance: Initial balance
            risk_config: Risk configuration
            
        Returns:
            List of backtest results
        """
        results = []
        for strategy in strategies:
            result = self.run_backtest(
                strategy, symbol, start_date, end_date,
                initial_balance, risk_config
            )
            result['strategy_name'] = strategy.name
            results.append(result)
        
        return results

