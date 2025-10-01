"""Backtesting service for strategy evaluation."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

from ..core.interfaces import IStrategy, IDataProvider
from ..core.portfolio import Portfolio
from ..core.risk_engine import RiskEngine, RiskConfig
from ..adapters.brokers.paper_broker import PaperBroker


class BacktestService:
    """Service for running backtests and walk-forward analysis."""
    
    def __init__(self, data_provider: IDataProvider):
        self.data_provider = data_provider
        
    def run_backtest(self, strategy: IStrategy, symbol: str, 
                    start_date: str, end_date: str, 
                    initial_balance: float = 10000.0,
                    risk_config: RiskConfig = None) -> Dict:
        """Run a backtest for a strategy."""
        
        if risk_config is None:
            risk_config = RiskConfig()
            
        # Get data
        df = self.data_provider.get_data(symbol, start_date, end_date, "1h")
        if df.empty:
            return {'error': 'No data available'}
            
        # Initialize components
        broker = PaperBroker(initial_balance)
        portfolio = Portfolio(initial_balance)
        risk_engine = RiskEngine(risk_config)
        
        # Run backtest
        results = self._run_backtest_cycle(
            strategy, symbol, df, broker, portfolio, risk_engine
        )
        
        return results
        
    def _run_backtest_cycle(self, strategy: IStrategy, symbol: str, 
                           df: pd.DataFrame, broker: PaperBroker,
                           portfolio: Portfolio, risk_engine: RiskEngine) -> Dict:
        """Run the main backtest cycle."""
        
        positions = {}
        trades = []
        equity_series = []
        balance_series = []
        timestamps = []
        
        for i in range(len(df)):
            current_data = df.iloc[:i+1]
            
            if len(current_data) < max(20, 50):  # Need enough data for indicators
                continue
                
            # Calculate indicators
            current_data = strategy.indicators(current_data)
            
            # Get current price
            current_price = float(current_data['Close'].iloc[-1])
            
            # Generate signal
            signal = strategy.signal(current_data)
            volatility = strategy.volatility(current_data)
            
            # Process trading logic
            if signal != 0:
                self._process_signal(
                    strategy, symbol, signal, current_price, volatility,
                    positions, trades, broker, portfolio, risk_engine
                )
            else:
                # Check exit conditions
                self._check_exit_conditions(
                    symbol, current_price, strategy, positions, trades,
                    broker, portfolio, risk_engine
                )
                
            # Update portfolio
            portfolio.update_equity(broker.get_balance())
            
            # Record metrics
            equity_series.append(portfolio.get_total_equity())
            balance_series.append(portfolio.get_total_balance())
            timestamps.append(current_data.index[-1])
            
        # Calculate final metrics
        metrics = portfolio.calculate_metrics()
        
        return {
            'symbol': symbol,
            'strategy': strategy.name,
            'start_date': df.index[0].strftime('%Y-%m-%d'),
            'end_date': df.index[-1].strftime('%Y-%m-%d'),
            'initial_balance': portfolio.initial_balance,
            'final_balance': metrics.total_balance,
            'final_equity': metrics.total_equity,
            'total_return': (metrics.total_equity - portfolio.initial_balance) / portfolio.initial_balance,
            'max_drawdown': metrics.max_drawdown,
            'win_rate': metrics.win_rate,
            'profit_factor': metrics.profit_factor,
            'sharpe_ratio': metrics.sharpe_ratio,
            'total_trades': metrics.total_trades,
            'winning_trades': metrics.winning_trades,
            'losing_trades': metrics.losing_trades,
            'avg_win': metrics.avg_win,
            'avg_loss': metrics.avg_loss,
            'largest_win': metrics.largest_win,
            'largest_loss': metrics.largest_loss,
            'equity_series': equity_series,
            'balance_series': balance_series,
            'timestamps': [t.isoformat() for t in timestamps],
            'trades': [
                {
                    'symbol': t.symbol,
                    'side': t.side,
                    'quantity': t.quantity,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'pnl': t.pnl,
                    'strategy': t.strategy,
                    'entry_time': t.entry_time.isoformat(),
                    'exit_time': t.exit_time.isoformat(),
                    'notes': t.notes
                }
                for t in portfolio.trades
            ]
        }
        
    def _process_signal(self, strategy: IStrategy, symbol: str, signal: int,
                       price: float, volatility: Optional[float],
                       positions: Dict, trades: List, broker: PaperBroker,
                       portfolio: Portfolio, risk_engine: RiskEngine) -> None:
        """Process a trading signal."""
        
        # Check if we already have a position
        if symbol in positions:
            current_pos = positions[symbol]
            
            # If signal is opposite, close current position
            if (signal > 0 and current_pos.side < 0) or (signal < 0 and current_pos.side > 0):
                self._close_position(symbol, price, positions, trades, broker, portfolio, risk_engine)
                
            # If signal is same direction, don't open new position
            elif (signal > 0 and current_pos.side > 0) or (signal < 0 and current_pos.side < 0):
                return
                
        # Calculate position size
        balance = portfolio.get_total_balance()
        win_rate = risk_engine.get_recent_win_rate(symbol, strategy.name)
        
        position_size = risk_engine.calculate_position_size(
            symbol, strategy.name, balance, volatility, win_rate
        )
        
        # Calculate quantity
        quantity = position_size / price
        
        # Get stop loss and take profit
        df = pd.DataFrame({'Close': [price]})  # Minimal dataframe for stop/take calculation
        stop_loss = strategy.stop_loss(df, price, signal)
        take_profit = strategy.take_profit(df, price, signal)
        
        # Create position
        from ..core.interfaces import Position
        position = Position(
            symbol=symbol,
            side=signal,
            quantity=quantity,
            entry_price=price,
            current_price=price,
            unrealized_pnl=0.0,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        positions[symbol] = position
        
        # Update broker and portfolio
        broker.update_position(symbol, signal, quantity, price, price)
        portfolio.add_position(position)
        
    def _check_exit_conditions(self, symbol: str, price: float, strategy: IStrategy,
                              positions: Dict, trades: List, broker: PaperBroker,
                              portfolio: Portfolio, risk_engine: RiskEngine) -> None:
        """Check exit conditions for existing positions."""
        
        if symbol not in positions:
            return
            
        position = positions[symbol]
        
        # Check stop loss
        if position.stop_loss is not None:
            if (position.side > 0 and price <= position.stop_loss) or \
               (position.side < 0 and price >= position.stop_loss):
                self._close_position(symbol, price, positions, trades, broker, portfolio, risk_engine, "Stop Loss")
                return
                
        # Check take profit
        if position.take_profit is not None:
            if (position.side > 0 and price >= position.take_profit) or \
               (position.side < 0 and price <= position.take_profit):
                self._close_position(symbol, price, positions, trades, broker, portfolio, risk_engine, "Take Profit")
                return
                
    def _close_position(self, symbol: str, price: float, positions: Dict, trades: List,
                       broker: PaperBroker, portfolio: Portfolio, risk_engine: RiskEngine,
                       reason: str = "Manual") -> None:
        """Close a position."""
        
        if symbol not in positions:
            return
            
        position = positions[symbol]
        
        # Calculate PnL
        pnl = position.side * position.quantity * (price - position.entry_price)
        
        # Create trade record
        from ..core.interfaces import Trade
        trade = Trade(
            symbol=symbol,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=price,
            pnl=pnl,
            strategy="Unknown",  # Would need to track this
            entry_time=position.timestamp,
            exit_time=datetime.now(),
            notes=reason
        )
        
        # Add to portfolio and trades
        portfolio.add_trade(trade)
        trades.append(trade)
        
        # Update risk manager
        risk_engine.add_trade_result(pnl, symbol, "Unknown")
        
        # Remove position
        del positions[symbol]
        portfolio.remove_position(symbol)
        broker.close_position(symbol, price)
        
    def run_walk_forward_analysis(self, strategy: IStrategy, symbol: str,
                                 start_date: str, end_date: str,
                                 training_period: int = 252,  # 1 year
                                 testing_period: int = 63,   # 3 months
                                 step_size: int = 21,        # 1 month
                                 initial_balance: float = 10000.0,
                                 risk_config: RiskConfig = None) -> Dict:
        """Run walk-forward analysis."""
        
        if risk_config is None:
            risk_config = RiskConfig()
            
        # Get full dataset
        df = self.data_provider.get_data(symbol, start_date, end_date, "1h")
        if df.empty:
            return {'error': 'No data available'}
            
        # Generate time splits
        splits = self._generate_time_splits(df, training_period, testing_period, step_size)
        
        results = []
        
        for i, (train_start, train_end, test_start, test_end) in enumerate(splits):
            # Run backtest on test period
            test_df = df[(df.index >= test_start) & (df.index <= test_end)]
            
            if test_df.empty:
                continue
                
            # Run backtest
            broker = PaperBroker(initial_balance)
            portfolio = Portfolio(initial_balance)
            risk_engine = RiskEngine(risk_config)
            
            backtest_result = self._run_backtest_cycle(
                strategy, symbol, test_df, broker, portfolio, risk_engine
            )
            
            backtest_result['split'] = i
            backtest_result['train_start'] = train_start.strftime('%Y-%m-%d')
            backtest_result['train_end'] = train_end.strftime('%Y-%m-%d')
            backtest_result['test_start'] = test_start.strftime('%Y-%m-%d')
            backtest_result['test_end'] = test_end.strftime('%Y-%m-%d')
            
            results.append(backtest_result)
            
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(results)
        
        return {
            'symbol': symbol,
            'strategy': strategy.name,
            'splits': len(splits),
            'results': results,
            'aggregate_metrics': aggregate_metrics
        }
        
    def _generate_time_splits(self, df: pd.DataFrame, training_period: int,
                             testing_period: int, step_size: int) -> List[Tuple]:
        """Generate time splits for walk-forward analysis."""
        
        splits = []
        start_idx = 0
        
        while start_idx + training_period + testing_period < len(df):
            train_start = df.index[start_idx]
            train_end = df.index[start_idx + training_period - 1]
            test_start = df.index[start_idx + training_period]
            test_end = df.index[min(start_idx + training_period + testing_period - 1, len(df) - 1)]
            
            splits.append((train_start, train_end, test_start, test_end))
            start_idx += step_size
            
        return splits
        
    def _calculate_aggregate_metrics(self, results: List[Dict]) -> Dict:
        """Calculate aggregate metrics across all splits."""
        
        if not results:
            return {}
            
        returns = [r['total_return'] for r in results]
        max_drawdowns = [r['max_drawdown'] for r in results]
        win_rates = [r['win_rate'] for r in results]
        profit_factors = [r['profit_factor'] for r in results if r['profit_factor'] != float('inf')]
        sharpe_ratios = [r['sharpe_ratio'] for r in results if r['sharpe_ratio'] is not None]
        
        return {
            'avg_return': np.mean(returns),
            'std_return': np.std(returns),
            'min_return': np.min(returns),
            'max_return': np.max(returns),
            'avg_max_drawdown': np.mean(max_drawdowns),
            'max_max_drawdown': np.max(max_drawdowns),
            'avg_win_rate': np.mean(win_rates),
            'avg_profit_factor': np.mean(profit_factors) if profit_factors else 0,
            'avg_sharpe_ratio': np.mean(sharpe_ratios) if sharpe_ratios else 0,
            'profitable_splits': sum(1 for r in returns if r > 0),
            'total_splits': len(results)
        }
