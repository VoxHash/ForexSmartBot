"""Real-time strategy testing on paper account."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..core.interfaces import IStrategy, IDataProvider
from ..adapters.brokers.paper_broker import PaperBroker
from ..core.portfolio import Portfolio
from ..core.risk_engine import RiskEngine, RiskConfig


@dataclass
class PaperTestResult:
    """Result of paper account test."""
    strategy_name: str
    test_duration: timedelta
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    final_balance: float
    trades: List[Dict[str, Any]]


class PaperAccountTester:
    """Test strategies in real-time on paper account."""
    
    def __init__(self, data_provider: IDataProvider,
                 initial_balance: float = 10000.0,
                 risk_config: Optional[RiskConfig] = None):
        """
        Initialize paper account tester.
        
        Args:
            data_provider: Data provider for market data
            initial_balance: Initial paper account balance
            risk_config: Risk management configuration
        """
        self.data_provider = data_provider
        self.initial_balance = initial_balance
        self.risk_config = risk_config or RiskConfig()
        self.broker = PaperBroker(initial_balance)
        self.portfolio = Portfolio(initial_balance)
        self.risk_engine = RiskEngine(self.risk_config)
        self.active_tests: Dict[str, Dict[str, Any]] = {}
        
    def start_test(self, strategy_name: str, strategy: IStrategy, 
                   symbol: str, update_interval: int = 60) -> str:
        """
        Start a paper account test for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            strategy: Strategy instance
            symbol: Trading symbol
            update_interval: Update interval in seconds
            
        Returns:
            Test ID
        """
        import uuid
        test_id = str(uuid.uuid4())
        
        self.active_tests[test_id] = {
            'strategy_name': strategy_name,
            'strategy': strategy,
            'symbol': symbol,
            'start_time': datetime.now(),
            'update_interval': update_interval,
            'trades': [],
            'equity_history': [],
            'last_update': datetime.now()
        }
        
        return test_id
        
    def update_test(self, test_id: str) -> Dict[str, Any]:
        """
        Update a paper account test with latest data.
        
        Args:
            test_id: Test ID
            
        Returns:
            Update result
        """
        if test_id not in self.active_tests:
            return {'error': 'Test not found'}
        
        test = self.active_tests[test_id]
        strategy = test['strategy']
        symbol = test['symbol']
        
        # Get latest data
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        try:
            df = self.data_provider.get_data(symbol, start_date, end_date, '1h')
            if df.empty:
                return {'error': 'No data available'}
            
            # Calculate indicators
            df = strategy.indicators(df)
            
            # Generate signal
            signal = strategy.signal(df)
            volatility = strategy.volatility(df)
            current_price = float(df['Close'].iloc[-1])
            
            # Process trading logic
            if signal != 0:
                self._process_signal(test_id, strategy, symbol, signal, current_price, volatility, df)
            else:
                self._check_exit_conditions(test_id, symbol, current_price, strategy, df)
            
            # Update portfolio
            self.portfolio.update_equity(self.broker.get_balance())
            
            # Record equity
            test['equity_history'].append({
                'timestamp': datetime.now(),
                'equity': self.portfolio.get_total_equity()
            })
            
            test['last_update'] = datetime.now()
            
            return {
                'test_id': test_id,
                'current_equity': self.portfolio.get_total_equity(),
                'total_return': (self.portfolio.get_total_equity() / self.initial_balance) - 1,
                'total_trades': len(test['trades']),
                'signal': signal
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    def _process_signal(self, test_id: str, strategy: IStrategy, symbol: str,
                       signal: int, current_price: float, volatility: Optional[float],
                       df: pd.DataFrame) -> None:
        """Process trading signal."""
        test = self.active_tests[test_id]
        positions = test.get('positions', {})
        
        # Close opposite position
        if symbol in positions:
            pos = positions[symbol]
            if (signal > 0 and pos['side'] < 0) or (signal < 0 and pos['side'] > 0):
                self.broker.close_position(symbol, current_price)
                profit = (current_price - pos['entry_price']) * pos['side'] * pos['size']
                test['trades'].append({
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
        
        # Open new position
        if symbol not in positions:
            size = self.risk_engine.calculate_position_size(
                self.portfolio.get_total_balance(), volatility or 0.01, signal
            )
            
            if size > 0:
                sl = strategy.stop_loss(df, current_price, signal)
                tp = strategy.take_profit(df, current_price, signal)
                
                self.broker.open_position(symbol, signal, size, current_price, sl, tp)
                positions[symbol] = {
                    'side': signal,
                    'entry_price': current_price,
                    'size': size,
                    'entry_time': datetime.now(),
                    'stop_loss': sl,
                    'take_profit': tp
                }
        
        test['positions'] = positions
        
    def _check_exit_conditions(self, test_id: str, symbol: str, current_price: float,
                              strategy: IStrategy, df: pd.DataFrame) -> None:
        """Check exit conditions for open positions."""
        test = self.active_tests[test_id]
        positions = test.get('positions', {})
        
        if symbol not in positions:
            return
        
        pos = positions[symbol]
        
        # Check stop loss
        if pos.get('stop_loss') and (
            (pos['side'] > 0 and current_price <= pos['stop_loss']) or
            (pos['side'] < 0 and current_price >= pos['stop_loss'])
        ):
            self.broker.close_position(symbol, current_price)
            profit = (current_price - pos['entry_price']) * pos['side'] * pos['size']
            test['trades'].append({
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
        
        # Check take profit
        if pos.get('take_profit') and (
            (pos['side'] > 0 and current_price >= pos['take_profit']) or
            (pos['side'] < 0 and current_price <= pos['take_profit'])
        ):
            self.broker.close_position(symbol, current_price)
            profit = (current_price - pos['entry_price']) * pos['side'] * pos['size']
            test['trades'].append({
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
        
        test['positions'] = positions
        
    def stop_test(self, test_id: str) -> PaperTestResult:
        """
        Stop a paper account test and get results.
        
        Args:
            test_id: Test ID
            
        Returns:
            PaperTestResult
        """
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        test = self.active_tests[test_id]
        test_duration = datetime.now() - test['start_time']
        
        trades = test['trades']
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in trades if t.get('profit', 0) < 0]
        
        # Calculate metrics
        returns = [t.get('profit', 0) / self.initial_balance for t in trades]
        total_return = sum(returns)
        
        if len(returns) > 1:
            sharpe_ratio = np.sqrt(252) * np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown from equity history
        equity_values = [e['equity'] for e in test['equity_history']]
        if equity_values:
            equity_series = pd.Series(equity_values)
            running_max = equity_series.expanding().max()
            drawdown = (equity_series - running_max) / running_max
            max_drawdown = abs(drawdown.min())
        else:
            max_drawdown = 0.0
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        result = PaperTestResult(
            strategy_name=test['strategy_name'],
            test_duration=test_duration,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            final_balance=self.portfolio.get_total_equity(),
            trades=trades
        )
        
        # Remove test
        del self.active_tests[test_id]
        
        return result
        
    def get_active_tests(self) -> List[str]:
        """Get list of active test IDs."""
        return list(self.active_tests.keys())
        
    def get_test_status(self, test_id: str) -> Dict[str, Any]:
        """Get current status of a test."""
        if test_id not in self.active_tests:
            return {'error': 'Test not found'}
        
        test = self.active_tests[test_id]
        return {
            'test_id': test_id,
            'strategy_name': test['strategy_name'],
            'symbol': test['symbol'],
            'start_time': test['start_time'],
            'duration': datetime.now() - test['start_time'],
            'total_trades': len(test['trades']),
            'current_equity': self.portfolio.get_total_equity(),
            'total_return': (self.portfolio.get_total_equity() / self.initial_balance) - 1,
            'last_update': test['last_update']
        }

