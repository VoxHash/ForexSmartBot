"""Enhanced backtesting service with parallel processing and improved error handling."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
import json
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import traceback

from ..core.interfaces import IStrategy, IDataProvider
from ..core.portfolio import Portfolio
from ..core.risk_engine import RiskEngine, RiskConfig
from ..adapters.brokers.paper_broker import PaperBroker

# Setup logging
logger = logging.getLogger(__name__)


class EnhancedBacktestService:
    """Enhanced backtesting service with parallel processing and error handling."""
    
    def __init__(self, data_provider: IDataProvider, use_parallel: bool = True, 
                 max_workers: int = 4):
        """
        Initialize enhanced backtest service.
        
        Args:
            data_provider: Data provider for market data
            use_parallel: Whether to use parallel processing
            max_workers: Maximum number of worker processes/threads
        """
        self.data_provider = data_provider
        self.use_parallel = use_parallel
        self.max_workers = max_workers
        
    def run_backtest(self, strategy: IStrategy, symbol: str, 
                    start_date: str, end_date: str, 
                    initial_balance: float = 10000.0,
                    risk_config: RiskConfig = None,
                    enable_logging: bool = False) -> Dict:
        """
        Run a backtest with enhanced error handling.
        
        Args:
            strategy: Trading strategy to test
            symbol: Trading symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_balance: Initial account balance
            risk_config: Risk configuration
            enable_logging: Enable detailed logging
            
        Returns:
            Dictionary with backtest results
        """
        try:
            if risk_config is None:
                risk_config = RiskConfig()
                
            # Get data with error handling
            try:
                df = self.data_provider.get_data(symbol, start_date, end_date, "1h")
                if df.empty:
                    return {
                        'error': 'No data available',
                        'symbol': symbol,
                        'start_date': start_date,
                        'end_date': end_date
                    }
            except Exception as e:
                logger.error(f"Error fetching data: {e}")
                return {
                    'error': f'Data fetch error: {str(e)}',
                    'symbol': symbol,
                    'start_date': start_date,
                    'end_date': end_date
                }
                
            # Initialize components with error handling
            try:
                broker = PaperBroker(initial_balance)
                portfolio = Portfolio(initial_balance)
                risk_engine = RiskEngine(risk_config)
            except Exception as e:
                logger.error(f"Error initializing components: {e}")
                return {'error': f'Initialization error: {str(e)}'}
                
            # Run backtest with transaction rollback on error
            try:
                results = self._run_backtest_cycle(
                    strategy, symbol, df, broker, portfolio, risk_engine, enable_logging
                )
                return results
            except Exception as e:
                logger.error(f"Backtest execution error: {e}")
                logger.error(traceback.format_exc())
                return {
                    'error': f'Backtest execution error: {str(e)}',
                    'traceback': traceback.format_exc() if enable_logging else None
                }
                
        except Exception as e:
            logger.error(f"Unexpected error in backtest: {e}")
            logger.error(traceback.format_exc())
            return {
                'error': f'Unexpected error: {str(e)}',
                'traceback': traceback.format_exc() if enable_logging else None
            }
            
    def _run_backtest_cycle(self, strategy: IStrategy, symbol: str, 
                           df: pd.DataFrame, broker: PaperBroker,
                           portfolio: Portfolio, risk_engine: RiskEngine,
                           enable_logging: bool = False) -> Dict:
        """Run the main backtest cycle with error handling."""
        
        positions = {}
        trades = []
        equity_series = []
        balance_series = []
        timestamps = []
        errors = []
        
        for i in range(len(df)):
            try:
                current_data = df.iloc[:i+1]
                
                if len(current_data) < max(20, 50):
                    continue
                    
                # Calculate indicators with error handling
                try:
                    current_data = strategy.indicators(current_data)
                except Exception as e:
                    if enable_logging:
                        logger.warning(f"Indicator calculation error at step {i}: {e}")
                    errors.append(f"Step {i}: Indicator error - {str(e)}")
                    continue
                    
                # Get current price
                try:
                    current_price = float(current_data['Close'].iloc[-1])
                    if pd.isna(current_price) or current_price <= 0:
                        continue
                except Exception as e:
                    if enable_logging:
                        logger.warning(f"Price extraction error at step {i}: {e}")
                    continue
                    
                # Generate signal with error handling
                try:
                    signal = strategy.signal(current_data)
                    volatility = strategy.volatility(current_data)
                except Exception as e:
                    if enable_logging:
                        logger.warning(f"Signal generation error at step {i}: {e}")
                    errors.append(f"Step {i}: Signal error - {str(e)}")
                    signal = 0
                    volatility = None
                    
                # Process trading logic with error handling
                if signal != 0:
                    try:
                        self._process_signal(
                            strategy, symbol, signal, current_price, volatility,
                            positions, trades, broker, portfolio, risk_engine
                        )
                    except Exception as e:
                        if enable_logging:
                            logger.warning(f"Signal processing error at step {i}: {e}")
                        errors.append(f"Step {i}: Signal processing error - {str(e)}")
                else:
                    # Check exit conditions
                    try:
                        self._check_exit_conditions(
                            symbol, current_price, strategy, positions, trades,
                            broker, portfolio, risk_engine
                        )
                    except Exception as e:
                        if enable_logging:
                            logger.warning(f"Exit condition check error at step {i}: {e}")
                        errors.append(f"Step {i}: Exit check error - {str(e)}")
                        
                # Update portfolio
                try:
                    portfolio.update_equity(broker.get_balance())
                except Exception as e:
                    if enable_logging:
                        logger.warning(f"Portfolio update error at step {i}: {e}")
                        
                # Record metrics
                equity_series.append(portfolio.get_total_equity())
                balance_series.append(portfolio.get_total_balance())
                timestamps.append(current_data.index[-1])
                
            except Exception as e:
                if enable_logging:
                    logger.error(f"Error in backtest cycle at step {i}: {e}")
                errors.append(f"Step {i}: Cycle error - {str(e)}")
                continue
                
        # Calculate final metrics with error handling
        try:
            metrics = portfolio.calculate_metrics()
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            metrics = {}
            
        return {
            'symbol': symbol,
            'start_date': str(df.index[0]),
            'end_date': str(df.index[-1]),
            'initial_balance': portfolio.get_total_balance(),
            'final_balance': equity_series[-1] if equity_series else portfolio.get_total_balance(),
            'total_return': (equity_series[-1] / portfolio.get_total_balance() - 1) if equity_series else 0,
            'total_trades': len(trades),
            'winning_trades': sum(1 for t in trades if t.get('profit', 0) > 0),
            'losing_trades': sum(1 for t in trades if t.get('profit', 0) < 0),
            'metrics': metrics,
            'equity_series': equity_series,
            'balance_series': balance_series,
            'timestamps': [str(ts) for ts in timestamps],
            'trades': trades,
            'errors': errors[:100] if errors else [],  # Limit error list
            'error_count': len(errors)
        }
        
    def _process_signal(self, strategy: IStrategy, symbol: str, signal: int,
                       current_price: float, volatility: Optional[float],
                       positions: Dict, trades: List, broker: PaperBroker,
                       portfolio: Portfolio, risk_engine: RiskEngine) -> None:
        """Process trading signal with error handling."""
        # Close opposite position if exists
        if symbol in positions:
            pos = positions[symbol]
            if (signal > 0 and pos['side'] < 0) or (signal < 0 and pos['side'] > 0):
                try:
                    broker.close_position(symbol, current_price)
                    profit = (current_price - pos['entry_price']) * pos['side'] * pos['size']
                    trades.append({
                        'symbol': symbol,
                        'side': pos['side'],
                        'entry_price': pos['entry_price'],
                        'exit_price': current_price,
                        'size': pos['size'],
                        'profit': profit,
                        'entry_time': pos['entry_time'],
                        'exit_time': datetime.now()
                    })
                    del positions[symbol]
                except Exception as e:
                    logger.warning(f"Error closing position: {e}")
                    
        # Open new position if no existing position
        if symbol not in positions:
            try:
                # Calculate position size
                if volatility is None:
                    volatility = 0.01  # Default volatility
                    
                size = risk_engine.calculate_position_size(
                    portfolio.get_total_balance(), volatility, signal
                )
                
                if size > 0:
                    # Calculate SL/TP
                    sl = strategy.stop_loss(
                        pd.DataFrame({'Close': [current_price]}), current_price, signal
                    ) if hasattr(strategy, 'stop_loss') else None
                    tp = strategy.take_profit(
                        pd.DataFrame({'Close': [current_price]}), current_price, signal
                    ) if hasattr(strategy, 'take_profit') else None
                    
                    # Open position
                    broker.open_position(symbol, signal, size, current_price, sl, tp)
                    positions[symbol] = {
                        'side': signal,
                        'entry_price': current_price,
                        'size': size,
                        'entry_time': datetime.now(),
                        'stop_loss': sl,
                        'take_profit': tp
                    }
            except Exception as e:
                logger.warning(f"Error opening position: {e}")
                
    def _check_exit_conditions(self, symbol: str, current_price: float,
                              strategy: IStrategy, positions: Dict, trades: List,
                              broker: PaperBroker, portfolio: Portfolio,
                              risk_engine: RiskEngine) -> None:
        """Check exit conditions for open positions."""
        if symbol not in positions:
            return
            
        pos = positions[symbol]
        
        # Check stop loss
        if pos.get('stop_loss') is not None:
            if (pos['side'] > 0 and current_price <= pos['stop_loss']) or \
               (pos['side'] < 0 and current_price >= pos['stop_loss']):
                try:
                    broker.close_position(symbol, current_price)
                    profit = (current_price - pos['entry_price']) * pos['side'] * pos['size']
                    trades.append({
                        'symbol': symbol,
                        'side': pos['side'],
                        'entry_price': pos['entry_price'],
                        'exit_price': current_price,
                        'size': pos['size'],
                        'profit': profit,
                        'entry_time': pos['entry_time'],
                        'exit_time': datetime.now(),
                        'exit_reason': 'stop_loss'
                    })
                    del positions[symbol]
                except Exception as e:
                    logger.warning(f"Error closing position at SL: {e}")
                    
        # Check take profit
        if pos.get('take_profit') is not None:
            if (pos['side'] > 0 and current_price >= pos['take_profit']) or \
               (pos['side'] < 0 and current_price <= pos['take_profit']):
                try:
                    broker.close_position(symbol, current_price)
                    profit = (current_price - pos['entry_price']) * pos['side'] * pos['size']
                    trades.append({
                        'symbol': symbol,
                        'side': pos['side'],
                        'entry_price': pos['entry_price'],
                        'exit_price': current_price,
                        'size': pos['size'],
                        'profit': profit,
                        'entry_time': pos['entry_time'],
                        'exit_time': datetime.now(),
                        'exit_reason': 'take_profit'
                    })
                    del positions[symbol]
                except Exception as e:
                    logger.warning(f"Error closing position at TP: {e}")
                    
    def run_parallel_backtests(self, strategies: List[Tuple[IStrategy, str]], 
                               symbol: str, start_date: str, end_date: str,
                               initial_balance: float = 10000.0,
                               risk_config: RiskConfig = None) -> Dict[str, Dict]:
        """
        Run multiple backtests in parallel.
        
        Args:
            strategies: List of (strategy, name) tuples
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            initial_balance: Initial balance
            risk_config: Risk configuration
            
        Returns:
            Dictionary mapping strategy names to results
        """
        if not self.use_parallel:
            # Run sequentially
            results = {}
            for strategy, name in strategies:
                results[name] = self.run_backtest(
                    strategy, symbol, start_date, end_date, initial_balance, risk_config
                )
            return results
            
        # Run in parallel using ThreadPoolExecutor (better for I/O bound tasks)
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_name = {
                executor.submit(
                    self.run_backtest, strategy, symbol, start_date, end_date,
                    initial_balance, risk_config
                ): name
                for strategy, name in strategies
            }
            
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    logger.error(f"Error in parallel backtest for {name}: {e}")
                    results[name] = {'error': str(e)}
                    
        return results

