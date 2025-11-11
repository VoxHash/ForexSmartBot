"""Strategy sandbox environment for safe testing."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import warnings

from ..core.interfaces import IStrategy
from ..adapters.brokers.paper_broker import PaperBroker
from ..core.portfolio import Portfolio
from ..core.risk_engine import RiskEngine, RiskConfig


class StrategySandbox:
    """Sandbox environment for safe strategy testing."""
    
    def __init__(self, initial_balance: float = 10000.0,
                 risk_config: Optional[RiskConfig] = None,
                 max_drawdown_limit: float = 0.5,
                 max_loss_per_trade: float = 0.1):
        """
        Initialize strategy sandbox.
        
        Args:
            initial_balance: Initial balance for testing
            risk_config: Risk management configuration
            max_drawdown_limit: Maximum allowed drawdown (0.5 = 50%)
            max_loss_per_trade: Maximum loss per trade (0.1 = 10%)
        """
        self.initial_balance = initial_balance
        self.risk_config = risk_config or RiskConfig()
        self.max_drawdown_limit = max_drawdown_limit
        self.max_loss_per_trade = max_loss_per_trade
        self.broker = PaperBroker(initial_balance)
        self.portfolio = Portfolio(initial_balance)
        self.risk_engine = RiskEngine(self.risk_config)
        self.safety_checks_enabled = True
        
    def test_strategy(self, strategy: IStrategy, df: pd.DataFrame, 
                     symbol: str = "TEST") -> Dict[str, Any]:
        """
        Test strategy in sandbox environment.
        
        Args:
            strategy: Strategy to test
            df: Historical data
            symbol: Trading symbol
            
        Returns:
            Test results with safety checks
        """
        # Reset sandbox
        self.broker = PaperBroker(self.initial_balance)
        self.portfolio = Portfolio(self.initial_balance)
        
        positions = {}
        trades = []
        equity_history = []
        safety_violations = []
        
        for i in range(len(df)):
            try:
                current_data = df.iloc[:i+1]
                
                if len(current_data) < 20:
                    continue
                
                # Calculate indicators
                current_data = strategy.indicators(current_data)
                
                # Get current price
                current_price = float(current_data['Close'].iloc[-1])
                
                # Generate signal
                signal = strategy.signal(current_data)
                volatility = strategy.volatility(current_data)
                
                # Safety check: Validate signal
                if signal not in [-1, 0, 1]:
                    safety_violations.append({
                        'step': i,
                        'type': 'invalid_signal',
                        'message': f'Invalid signal value: {signal}'
                    })
                    signal = 0
                
                # Process trading logic
                if signal != 0:
                    # Safety check: Position size
                    size = self.risk_engine.calculate_position_size(
                        self.portfolio.get_total_balance(), volatility or 0.01, signal
                    )
                    
                    # Check max loss per trade
                    potential_loss = abs(size * current_price * self.max_loss_per_trade)
                    if potential_loss > self.portfolio.get_total_balance() * self.max_loss_per_trade:
                        safety_violations.append({
                            'step': i,
                            'type': 'max_loss_exceeded',
                            'message': f'Potential loss {potential_loss:.2f} exceeds limit'
                        })
                        size = self.portfolio.get_total_balance() * self.max_loss_per_trade / current_price
                    
                    if size > 0:
                        sl = strategy.stop_loss(current_data, current_price, signal)
                        tp = strategy.take_profit(current_data, current_price, signal)
                        
                        # Safety check: SL/TP validation
                        if sl and tp:
                            if signal > 0:  # Long
                                if sl >= current_price:
                                    safety_violations.append({
                                        'step': i,
                                        'type': 'invalid_sl',
                                        'message': 'Stop loss above entry for long'
                                    })
                                    sl = current_price * 0.98  # Default 2% SL
                                if tp <= current_price:
                                    safety_violations.append({
                                        'step': i,
                                        'type': 'invalid_tp',
                                        'message': 'Take profit below entry for long'
                                    })
                                    tp = current_price * 1.04  # Default 4% TP
                        
                        # Open position
                        self.broker.open_position(symbol, signal, size, current_price, sl, tp)
                        positions[symbol] = {
                            'side': signal,
                            'entry_price': current_price,
                            'size': size,
                            'entry_time': datetime.now()
                        }
                
                # Check exit conditions
                if symbol in positions:
                    pos = positions[symbol]
                    
                    # Check stop loss
                    if pos.get('stop_loss') and (
                        (pos['side'] > 0 and current_price <= pos['stop_loss']) or
                        (pos['side'] < 0 and current_price >= pos['stop_loss'])
                    ):
                        self.broker.close_position(symbol, current_price)
                        profit = (current_price - pos['entry_price']) * pos['side'] * pos['size']
                        trades.append({
                            'profit': profit,
                            'entry_price': pos['entry_price'],
                            'exit_price': current_price,
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
                        trades.append({
                            'profit': profit,
                            'entry_price': pos['entry_price'],
                            'exit_price': current_price,
                            'exit_reason': 'take_profit'
                        })
                        del positions[symbol]
                
                # Update portfolio
                self.portfolio.update_equity(self.broker.get_balance())
                equity_history.append(self.portfolio.get_total_equity())
                
                # Safety check: Max drawdown
                if equity_history:
                    equity_series = pd.Series(equity_history)
                    running_max = equity_series.expanding().max()
                    drawdown = (equity_series - running_max) / running_max
                    current_drawdown = abs(drawdown.iloc[-1])
                    
                    if current_drawdown > self.max_drawdown_limit:
                        safety_violations.append({
                            'step': i,
                            'type': 'max_drawdown_exceeded',
                            'message': f'Drawdown {current_drawdown:.2%} exceeds limit {self.max_drawdown_limit:.2%}'
                        })
                        
                        # Auto-stop if drawdown too high
                        if self.safety_checks_enabled:
                            break
                
            except Exception as e:
                safety_violations.append({
                    'step': i,
                    'type': 'exception',
                    'message': str(e)
                })
                continue
        
        # Calculate final metrics
        total_return = (self.portfolio.get_total_equity() / self.initial_balance) - 1
        
        # Calculate max drawdown
        if equity_history:
            equity_series = pd.Series(equity_history)
            running_max = equity_series.expanding().max()
            drawdown = (equity_series - running_max) / running_max
            max_drawdown = abs(drawdown.min())
        else:
            max_drawdown = 0.0
        
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        # Safety assessment
        is_safe = len(safety_violations) == 0 and max_drawdown <= self.max_drawdown_limit
        
        return {
            'strategy_name': strategy.name,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'win_rate': win_rate,
            'final_balance': self.portfolio.get_total_equity(),
            'safety_violations': safety_violations,
            'is_safe': is_safe,
            'trades': trades,
            'equity_history': equity_history
        }
        
    def validate_strategy(self, strategy: IStrategy, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate strategy safety without full backtest.
        
        Args:
            strategy: Strategy to validate
            df: Sample data
            
        Returns:
            Validation results
        """
        validation_results = {
            'strategy_name': strategy.name,
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check strategy interface
        required_methods = ['indicators', 'signal', 'volatility', 'stop_loss', 'take_profit']
        for method in required_methods:
            if not hasattr(strategy, method):
                validation_results['errors'].append(f'Missing method: {method}')
                validation_results['is_valid'] = False
        
        # Test indicator calculation
        try:
            df_with_indicators = strategy.indicators(df)
            if df_with_indicators.empty:
                validation_results['warnings'].append('Indicators return empty DataFrame')
        except Exception as e:
            validation_results['errors'].append(f'Indicator calculation error: {e}')
            validation_results['is_valid'] = False
        
        # Test signal generation
        try:
            signal = strategy.signal(df_with_indicators if 'df_with_indicators' in locals() else df)
            if signal not in [-1, 0, 1]:
                validation_results['warnings'].append(f'Signal value {signal} not in [-1, 0, 1]')
        except Exception as e:
            validation_results['errors'].append(f'Signal generation error: {e}')
            validation_results['is_valid'] = False
        
        # Test volatility calculation
        try:
            volatility = strategy.volatility(df_with_indicators if 'df_with_indicators' in locals() else df)
            if volatility is not None and (volatility < 0 or volatility > 1):
                validation_results['warnings'].append(f'Volatility value {volatility} outside [0, 1]')
        except Exception as e:
            validation_results['warnings'].append(f'Volatility calculation error: {e}')
        
        return validation_results

