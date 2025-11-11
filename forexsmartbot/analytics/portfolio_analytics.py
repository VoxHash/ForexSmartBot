"""
Portfolio Analytics Module
Calculates Sharpe ratio, Sortino ratio, maximum drawdown, and performance attribution.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from ..core.interfaces import Trade, Position


class PortfolioAnalytics:
    """Portfolio analytics and performance metrics."""
    
    def __init__(self):
        self.trades: List[Trade] = []
        self.positions: List[Position] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        
    def add_trade(self, trade: Trade):
        """Add a trade to the analytics."""
        self.trades.append(trade)
        
    def add_position(self, position: Position):
        """Add a position to the analytics."""
        self.positions.append(position)
        
    def update_equity(self, timestamp: datetime, equity: float):
        """Update equity curve."""
        self.equity_curve.append((timestamp, equity))
        
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02, 
                              period: Optional[str] = None) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
            period: Period to analyze ('daily', 'weekly', 'monthly', None for all)
            
        Returns:
            Sharpe ratio
        """
        if not self.trades:
            return 0.0
            
        # Get returns
        returns = self._get_returns(period)
        if len(returns) < 2:
            return 0.0
            
        # Calculate excess returns
        if period == 'daily':
            excess_returns = returns - (risk_free_rate / 252)
        elif period == 'weekly':
            excess_returns = returns - (risk_free_rate / 52)
        elif period == 'monthly':
            excess_returns = returns - (risk_free_rate / 12)
        else:
            # Annualize based on total period
            days = (self.trades[-1].exit_time - self.trades[0].entry_time).days
            if days > 0:
                excess_returns = returns - (risk_free_rate * (len(returns) / days))
            else:
                excess_returns = returns - risk_free_rate
        
        # Calculate Sharpe ratio
        if np.std(returns) == 0:
            return 0.0
            
        sharpe = np.mean(excess_returns) / np.std(returns)
        
        # Annualize if needed
        if period == 'daily':
            sharpe *= np.sqrt(252)
        elif period == 'weekly':
            sharpe *= np.sqrt(52)
        elif period == 'monthly':
            sharpe *= np.sqrt(12)
            
        return float(sharpe)
        
    def calculate_sortino_ratio(self, risk_free_rate: float = 0.02,
                               period: Optional[str] = None) -> float:
        """
        Calculate Sortino ratio (downside deviation only).
        
        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
            period: Period to analyze
            
        Returns:
            Sortino ratio
        """
        if not self.trades:
            return 0.0
            
        returns = self._get_returns(period)
        if len(returns) < 2:
            return 0.0
            
        # Calculate excess returns
        if period == 'daily':
            excess_returns = returns - (risk_free_rate / 252)
        elif period == 'weekly':
            excess_returns = returns - (risk_free_rate / 52)
        elif period == 'monthly':
            excess_returns = returns - (risk_free_rate / 12)
        else:
            days = (self.trades[-1].exit_time - self.trades[0].entry_time).days
            if days > 0:
                excess_returns = returns - (risk_free_rate * (len(returns) / days))
            else:
                excess_returns = returns - risk_free_rate
        
        # Calculate downside deviation (only negative returns)
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf') if np.mean(excess_returns) > 0 else 0.0
            
        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return 0.0
            
        sortino = np.mean(excess_returns) / downside_std
        
        # Annualize if needed
        if period == 'daily':
            sortino *= np.sqrt(252)
        elif period == 'weekly':
            sortino *= np.sqrt(52)
        elif period == 'monthly':
            sortino *= np.sqrt(12)
            
        return float(sortino)
        
    def calculate_max_drawdown(self) -> Dict[str, float]:
        """
        Calculate maximum drawdown.
        
        Returns:
            Dictionary with 'max_drawdown', 'max_drawdown_pct', 'peak', 'trough', 'recovery_date'
        """
        if not self.equity_curve and not self.trades:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
                'peak': 0.0,
                'trough': 0.0,
                'recovery_date': None
            }
            
        # Build equity curve from trades if not available
        if not self.equity_curve:
            equity_curve = self._build_equity_curve_from_trades()
        else:
            equity_curve = sorted(self.equity_curve, key=lambda x: x[0])
            
        if len(equity_curve) < 2:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
                'peak': equity_curve[0][1] if equity_curve else 0.0,
                'trough': equity_curve[0][1] if equity_curve else 0.0,
                'recovery_date': None
            }
            
        equity_values = [e[1] for e in equity_curve]
        timestamps = [e[0] for e in equity_curve]
        
        # Calculate running maximum (peak)
        running_max = np.maximum.accumulate(equity_values)
        
        # Calculate drawdown
        drawdown = running_max - equity_values
        drawdown_pct = (drawdown / running_max) * 100
        
        # Find maximum drawdown
        max_dd_idx = np.argmax(drawdown)
        max_drawdown = float(drawdown[max_dd_idx])
        max_drawdown_pct = float(drawdown_pct[max_dd_idx])
        peak = float(running_max[max_dd_idx])
        trough = float(equity_values[max_dd_idx])
        trough_date = timestamps[max_dd_idx]
        
        # Find recovery date (when equity returns to peak level)
        recovery_date = None
        if max_dd_idx < len(equity_curve) - 1:
            for i in range(max_dd_idx + 1, len(equity_curve)):
                if equity_values[i] >= peak:
                    recovery_date = timestamps[i]
                    break
                    
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'peak': peak,
            'trough': trough,
            'trough_date': trough_date,
            'recovery_date': recovery_date
        }
        
    def _get_returns(self, period: Optional[str] = None) -> np.ndarray:
        """Get returns array from trades."""
        if not self.trades:
            return np.array([])
            
        # Sort trades by exit time
        sorted_trades = sorted(self.trades, key=lambda t: t.exit_time if t.exit_time else t.entry_time)
        
        # Calculate returns
        returns = []
        for trade in sorted_trades:
            if trade.entry_price > 0:
                return_pct = (trade.pnl / (trade.entry_price * trade.quantity)) * 100
                returns.append(return_pct)
                
        return np.array(returns)
        
    def _build_equity_curve_from_trades(self) -> List[Tuple[datetime, float]]:
        """Build equity curve from trades."""
        if not self.trades:
            return []
            
        sorted_trades = sorted(self.trades, key=lambda t: t.exit_time if t.exit_time else t.entry_time)
        
        equity_curve = []
        cumulative_pnl = 0.0
        initial_balance = 10000.0  # Default initial balance
        
        for trade in sorted_trades:
            cumulative_pnl += trade.pnl
            equity = initial_balance + cumulative_pnl
            timestamp = trade.exit_time if trade.exit_time else trade.entry_time
            equity_curve.append((timestamp, equity))
            
        return equity_curve
        
    def get_performance_summary(self) -> Dict[str, float]:
        """Get comprehensive performance summary."""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0
            }
            
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        total_pnl = sum(t.pnl for t in self.trades)
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        
        max_dd = self.calculate_max_drawdown()
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(self.trades)) * 100 if self.trades else 0.0,
            'total_pnl': total_pnl,
            'average_win': total_wins / len(winning_trades) if winning_trades else 0.0,
            'average_loss': total_losses / len(losing_trades) if losing_trades else 0.0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else float('inf'),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            'max_drawdown': max_dd['max_drawdown'],
            'max_drawdown_pct': max_dd['max_drawdown_pct']
        }
    
    def calculate_metrics(self, portfolio=None) -> Dict[str, float]:
        """
        Calculate portfolio metrics (alias for get_performance_summary for compatibility).
        
        Args:
            portfolio: Optional portfolio object (currently unused, kept for compatibility)
            
        Returns:
            Dictionary of performance metrics
        """
        # If portfolio is provided and has trades, use them
        if portfolio and hasattr(portfolio, 'trades') and portfolio.trades:
            # Temporarily use portfolio's trades
            original_trades = self.trades
            self.trades = portfolio.trades
            metrics = self.get_performance_summary()
            self.trades = original_trades
            return metrics
        
        # Otherwise use internal trades
        return self.get_performance_summary()

