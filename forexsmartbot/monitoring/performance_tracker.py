"""Strategy performance metrics tracking."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Performance metrics for a strategy."""
    strategy_name: str
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    avg_trade_duration: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float


class PerformanceTracker:
    """Track and analyze strategy performance."""
    
    def __init__(self):
        self.trades: Dict[str, List[Dict[str, Any]]] = {}
        self.equity_curves: Dict[str, List[float]] = {}
        self.timestamps: Dict[str, List[datetime]] = {}
        
    def record_trade(self, strategy_name: str, trade_data: Dict[str, Any]) -> None:
        """Record a trade."""
        if strategy_name not in self.trades:
            self.trades[strategy_name] = []
            self.equity_curves[strategy_name] = []
            self.timestamps[strategy_name] = []
            
        self.trades[strategy_name].append({
            **trade_data,
            'timestamp': datetime.now()
        })
        
    def record_equity(self, strategy_name: str, equity: float) -> None:
        """Record equity value."""
        if strategy_name not in self.equity_curves:
            self.equity_curves[strategy_name] = []
            self.timestamps[strategy_name] = []
            
        self.equity_curves[strategy_name].append(equity)
        self.timestamps[strategy_name].append(datetime.now())
        
    def calculate_metrics(self, strategy_name: str, 
                          risk_free_rate: float = 0.02) -> Optional[PerformanceMetrics]:
        """Calculate performance metrics for a strategy."""
        if strategy_name not in self.trades or len(self.trades[strategy_name]) == 0:
            return None
            
        trades = self.trades[strategy_name]
        
        # Calculate returns
        returns = [t.get('profit', 0) / t.get('entry_price', 1) for t in trades]
        returns = [r for r in returns if not np.isnan(r)]
        
        if len(returns) == 0:
            return None
            
        total_return = sum(returns)
        winning_trades = [r for r in returns if r > 0]
        losing_trades = [r for r in returns if r < 0]
        
        # Calculate metrics
        sharpe_ratio = self._calculate_sharpe(returns, risk_free_rate)
        sortino_ratio = self._calculate_sortino(returns, risk_free_rate)
        max_drawdown = self._calculate_max_drawdown(strategy_name)
        win_rate = len(winning_trades) / len(returns) if returns else 0
        
        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = abs(np.mean(losing_trades)) if losing_trades else 0
        profit_factor = (sum(winning_trades) / abs(sum(losing_trades))) if losing_trades else float('inf')
        
        # Calculate average trade duration
        durations = []
        for trade in trades:
            if 'entry_time' in trade and 'exit_time' in trade:
                duration = (trade['exit_time'] - trade['entry_time']).total_seconds()
                durations.append(duration)
        avg_duration = np.mean(durations) if durations else 0
        
        return PerformanceMetrics(
            strategy_name=strategy_name,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_trade_duration=avg_duration,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=avg_win,
            avg_loss=avg_loss
        )
        
    def _calculate_sharpe(self, returns: List[float], risk_free_rate: float) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
            
        excess_returns = [r - risk_free_rate / 252 for r in returns]
        return np.sqrt(252) * np.mean(excess_returns) / np.std(returns)
        
    def _calculate_sortino(self, returns: List[float], risk_free_rate: float) -> float:
        """Calculate Sortino ratio."""
        if len(returns) == 0:
            return 0.0
            
        excess_returns = [r - risk_free_rate / 252 for r in returns]
        downside_returns = [r for r in excess_returns if r < 0]
        
        if len(downside_returns) == 0 or np.std(downside_returns) == 0:
            return 0.0
            
        return np.sqrt(252) * np.mean(excess_returns) / np.std(downside_returns)
        
    def _calculate_max_drawdown(self, strategy_name: str) -> float:
        """Calculate maximum drawdown from equity curve."""
        if strategy_name not in self.equity_curves or len(self.equity_curves[strategy_name]) < 2:
            return 0.0
            
        equity = np.array(self.equity_curves[strategy_name])
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max
        return abs(np.min(drawdown))
        
    def get_trades(self, strategy_name: str) -> List[Dict[str, Any]]:
        """Get all trades for a strategy."""
        return self.trades.get(strategy_name, [])
        
    def get_equity_curve(self, strategy_name: str) -> List[float]:
        """Get equity curve for a strategy."""
        return self.equity_curves.get(strategy_name, [])
    
    def get_summary(self, strategy_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance summary.
        
        Args:
            strategy_name: Optional strategy name. If None, aggregates all strategies.
            
        Returns:
            Dictionary with summary metrics
        """
        if strategy_name:
            metrics = self.calculate_metrics(strategy_name)
            if metrics:
                return {
                    'total_return': metrics.total_return,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'sortino_ratio': metrics.sortino_ratio,
                    'max_drawdown': metrics.max_drawdown,
                    'win_rate': metrics.win_rate,
                    'profit_factor': metrics.profit_factor,
                    'total_trades': metrics.total_trades,
                    'winning_trades': metrics.winning_trades,
                    'losing_trades': metrics.losing_trades,
                    'avg_win': metrics.avg_win,
                    'avg_loss': metrics.avg_loss
                }
        else:
            # Aggregate across all strategies
            all_metrics = {}
            for strat_name in self.trades.keys():
                metrics = self.calculate_metrics(strat_name)
                if metrics:
                    all_metrics[strat_name] = {
                        'total_return': metrics.total_return,
                        'sharpe_ratio': metrics.sharpe_ratio,
                        'max_drawdown': metrics.max_drawdown,
                        'win_rate': metrics.win_rate,
                        'total_trades': metrics.total_trades
                    }
            
            if all_metrics:
                # Aggregate summary
                total_trades = sum(m['total_trades'] for m in all_metrics.values())
                avg_return = sum(m['total_return'] for m in all_metrics.values()) / len(all_metrics)
                avg_sharpe = sum(m['sharpe_ratio'] for m in all_metrics.values()) / len(all_metrics)
                avg_win_rate = sum(m['win_rate'] for m in all_metrics.values()) / len(all_metrics)
                
                return {
                    'total_strategies': len(all_metrics),
                    'total_trades': total_trades,
                    'avg_return': avg_return,
                    'avg_sharpe_ratio': avg_sharpe,
                    'avg_win_rate': avg_win_rate,
                    'strategies': all_metrics
                }
        
        # Return empty summary if no data
        return {
            'total_trades': 0,
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0
        }

