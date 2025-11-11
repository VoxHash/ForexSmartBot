"""
Performance Attribution Module
Analyzes performance by strategy, symbol, and time period.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from ..core.interfaces import Trade


class PerformanceAttribution:
    """Performance attribution analysis by various dimensions."""
    
    def __init__(self):
        self.trades: List[Trade] = []
        
    def add_trade(self, trade: Trade):
        """Add a trade to the attribution analysis."""
        self.trades.append(trade)
        
    def analyze_by_strategy(self) -> Dict[str, Dict]:
        """
        Analyze performance by strategy.
        
        Returns:
            Dictionary with performance metrics for each strategy
        """
        if not self.trades:
            return {}
            
        strategy_performance = defaultdict(lambda: {
            'trades': [],
            'total_pnl': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_volume': 0.0
        })
        
        for trade in self.trades:
            strategy = trade.strategy if hasattr(trade, 'strategy') else 'Unknown'
            strategy_performance[strategy]['trades'].append(trade)
            strategy_performance[strategy]['total_pnl'] += trade.pnl
            strategy_performance[strategy]['total_volume'] += trade.quantity * trade.entry_price
            
            if trade.pnl > 0:
                strategy_performance[strategy]['winning_trades'] += 1
            else:
                strategy_performance[strategy]['losing_trades'] += 1
                
        # Calculate additional metrics
        results = {}
        for strategy, data in strategy_performance.items():
            total_trades = len(data['trades'])
            win_rate = (data['winning_trades'] / total_trades * 100) if total_trades > 0 else 0.0
            
            winning_pnl = sum(t.pnl for t in data['trades'] if t.pnl > 0)
            losing_pnl = abs(sum(t.pnl for t in data['trades'] if t.pnl < 0))
            profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else float('inf')
            
            avg_pnl = data['total_pnl'] / total_trades if total_trades > 0 else 0.0
            
            results[strategy] = {
                'total_trades': total_trades,
                'total_pnl': data['total_pnl'],
                'average_pnl': avg_pnl,
                'win_rate': win_rate,
                'winning_trades': data['winning_trades'],
                'losing_trades': data['losing_trades'],
                'profit_factor': profit_factor,
                'total_volume': data['total_volume'],
                'return_pct': (data['total_pnl'] / data['total_volume'] * 100) if data['total_volume'] > 0 else 0.0
            }
            
        return results
        
    def analyze_by_symbol(self) -> Dict[str, Dict]:
        """
        Analyze performance by symbol.
        
        Returns:
            Dictionary with performance metrics for each symbol
        """
        if not self.trades:
            return {}
            
        symbol_performance = defaultdict(lambda: {
            'trades': [],
            'total_pnl': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_volume': 0.0
        })
        
        for trade in self.trades:
            symbol = trade.symbol
            symbol_performance[symbol]['trades'].append(trade)
            symbol_performance[symbol]['total_pnl'] += trade.pnl
            symbol_performance[symbol]['total_volume'] += trade.quantity * trade.entry_price
            
            if trade.pnl > 0:
                symbol_performance[symbol]['winning_trades'] += 1
            else:
                symbol_performance[symbol]['losing_trades'] += 1
                
        # Calculate additional metrics
        results = {}
        for symbol, data in symbol_performance.items():
            total_trades = len(data['trades'])
            win_rate = (data['winning_trades'] / total_trades * 100) if total_trades > 0 else 0.0
            
            winning_pnl = sum(t.pnl for t in data['trades'] if t.pnl > 0)
            losing_pnl = abs(sum(t.pnl for t in data['trades'] if t.pnl < 0))
            profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else float('inf')
            
            avg_pnl = data['total_pnl'] / total_trades if total_trades > 0 else 0.0
            
            results[symbol] = {
                'total_trades': total_trades,
                'total_pnl': data['total_pnl'],
                'average_pnl': avg_pnl,
                'win_rate': win_rate,
                'winning_trades': data['winning_trades'],
                'losing_trades': data['losing_trades'],
                'profit_factor': profit_factor,
                'total_volume': data['total_volume'],
                'return_pct': (data['total_pnl'] / data['total_volume'] * 100) if data['total_volume'] > 0 else 0.0
            }
            
        return results
        
    def analyze_by_time_period(self, period: str = 'daily') -> Dict[str, Dict]:
        """
        Analyze performance by time period.
        
        Args:
            period: 'daily', 'weekly', 'monthly', 'yearly'
            
        Returns:
            Dictionary with performance metrics for each period
        """
        if not self.trades:
            return {}
            
        period_performance = defaultdict(lambda: {
            'trades': [],
            'total_pnl': 0.0,
            'winning_trades': 0,
            'losing_trades': 0
        })
        
        for trade in self.trades:
            # Get period key
            if period == 'daily':
                period_key = trade.exit_time.date() if trade.exit_time else trade.entry_time.date()
            elif period == 'weekly':
                period_key = trade.exit_time.isocalendar()[:2] if trade.exit_time else trade.entry_time.isocalendar()[:2]
                period_key = f"{period_key[0]}-W{period_key[1]}"
            elif period == 'monthly':
                period_key = trade.exit_time.strftime('%Y-%m') if trade.exit_time else trade.entry_time.strftime('%Y-%m')
            elif period == 'yearly':
                period_key = trade.exit_time.year if trade.exit_time else trade.entry_time.year
            else:
                period_key = trade.exit_time.date() if trade.exit_time else trade.entry_time.date()
                
            period_performance[period_key]['trades'].append(trade)
            period_performance[period_key]['total_pnl'] += trade.pnl
            
            if trade.pnl > 0:
                period_performance[period_key]['winning_trades'] += 1
            else:
                period_performance[period_key]['losing_trades'] += 1
                
        # Calculate additional metrics
        results = {}
        for period_key, data in period_performance.items():
            total_trades = len(data['trades'])
            win_rate = (data['winning_trades'] / total_trades * 100) if total_trades > 0 else 0.0
            
            avg_pnl = data['total_pnl'] / total_trades if total_trades > 0 else 0.0
            
            results[str(period_key)] = {
                'total_trades': total_trades,
                'total_pnl': data['total_pnl'],
                'average_pnl': avg_pnl,
                'win_rate': win_rate,
                'winning_trades': data['winning_trades'],
                'losing_trades': data['losing_trades']
            }
            
        return results
        
    def get_attribution_summary(self) -> Dict:
        """
        Get comprehensive attribution summary.
        
        Returns:
            Dictionary with all attribution analyses
        """
        return {
            'by_strategy': self.analyze_by_strategy(),
            'by_symbol': self.analyze_by_symbol(),
            'by_daily': self.analyze_by_time_period('daily'),
            'by_weekly': self.analyze_by_time_period('weekly'),
            'by_monthly': self.analyze_by_time_period('monthly'),
            'by_yearly': self.analyze_by_time_period('yearly')
        }

