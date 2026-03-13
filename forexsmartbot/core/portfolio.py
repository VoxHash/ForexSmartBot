"""Portfolio management and aggregation with memory optimization."""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
from collections import deque
from .interfaces import Position, Trade


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""
    total_balance: float
    total_equity: float
    unrealized_pnl: float
    realized_pnl: float
    daily_pnl: float
    max_drawdown: float
    current_drawdown: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: Optional[float] = None
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0


class Portfolio:
    """Portfolio management with memory optimization for fast trading."""
    
    # Memory limits to prevent unbounded growth
    MAX_HISTORY_SIZE = 10000  # Keep last 10k equity points
    MAX_TRADES_HISTORY = 10000  # Keep last 10k trades
    
    def __init__(self, initial_balance: float = 10000.0, max_history_size: int = None):
        self.initial_balance = initial_balance
        self.positions: Dict[str, Position] = {}
        
        # Use deque for O(1) append/popleft and automatic size limiting
        max_hist = max_history_size or self.MAX_HISTORY_SIZE
        self.trades: deque = deque(maxlen=self.MAX_TRADES_HISTORY)
        self.equity_history: deque = deque([initial_balance], maxlen=max_hist)
        self.balance_history: deque = deque([initial_balance], maxlen=max_hist)
        self.timestamps: deque = deque([datetime.now()], maxlen=max_hist)
        
        self.peak_equity = initial_balance
        self.max_drawdown = 0.0
        
        # Cache for fast access
        self._cached_balance = initial_balance
        self._cached_equity = initial_balance
        self._cache_valid = True
        
    def add_position(self, position: Position) -> None:
        """Add or update a position."""
        self.positions[position.symbol] = position
        self._cache_valid = False
        
    def remove_position(self, symbol: str) -> Optional[Position]:
        """Remove a position and return it."""
        pos = self.positions.pop(symbol, None)
        if pos:
            self._cache_valid = False
        return pos
        
    def add_trade(self, trade: Trade) -> None:
        """Add a completed trade (automatically limits size)."""
        self.trades.append(trade)
        self._cache_valid = False
        
    def update_equity(self, current_balance: float) -> None:
        """Update equity with current balance and unrealized PnL."""
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        current_equity = current_balance + unrealized_pnl
        
        # Use deque for automatic size limiting
        self.equity_history.append(current_equity)
        self.balance_history.append(current_balance)
        self.timestamps.append(datetime.now())
        
        # Update cached values
        self._cached_balance = current_balance
        self._cached_equity = current_equity
        
        # Update peak equity and drawdown
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            
        current_drawdown = (self.peak_equity - current_equity) / self.peak_equity if self.peak_equity > 0 else 0.0
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
            
    def get_total_equity(self) -> float:
        """Get total portfolio equity (cached for performance)."""
        if self._cache_valid and self._cached_equity is not None:
            return self._cached_equity
        if not self.equity_history:
            return self.initial_balance
        return self.equity_history[-1]
        
    def get_total_balance(self) -> float:
        """Get total portfolio balance (cached for performance)."""
        if self._cache_valid and self._cached_balance is not None:
            return self._cached_balance
        if not self.balance_history:
            return self.initial_balance
        return self.balance_history[-1]
        
    def get_unrealized_pnl(self) -> float:
        """Get total unrealized PnL."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
        
    def get_realized_pnl(self) -> float:
        """Get total realized PnL from completed trades."""
        return sum(trade.pnl for trade in self.trades)
        
    def get_daily_pnl(self) -> float:
        """Get today's PnL (optimized with early exit)."""
        today = datetime.now().date()
        daily_pnl = 0.0
        # Iterate backwards for better performance (most recent trades first)
        for trade in reversed(self.trades):
            if trade.exit_time.date() < today:
                break  # Early exit since trades are chronological
            if trade.exit_time.date() == today:
                daily_pnl += trade.pnl
        return daily_pnl
        
    def get_current_drawdown(self) -> float:
        """Get current drawdown percentage."""
        current_equity = self.get_total_equity()
        if self.peak_equity == 0:
            return 0.0
        return (self.peak_equity - current_equity) / self.peak_equity
        
    def get_metrics(self) -> PortfolioMetrics:
        """Get comprehensive portfolio metrics."""
        total_balance = self.get_total_balance()
        total_equity = self.get_total_equity()
        unrealized_pnl = self.get_unrealized_pnl()
        realized_pnl = self.get_realized_pnl()
        daily_pnl = self.get_daily_pnl()
        
        # Calculate trade statistics efficiently
        if not self.trades:
            return PortfolioMetrics(
                total_balance=total_balance,
                total_equity=total_equity,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                daily_pnl=daily_pnl,
                max_drawdown=self.max_drawdown,
                current_drawdown=self.get_current_drawdown(),
                win_rate=0.0,
                profit_factor=0.0
            )
        
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        total_trades = len(self.trades)
        wins = len(winning_trades)
        losses = len(losing_trades)
        
        win_rate = wins / total_trades if total_trades > 0 else 0.0
        
        avg_win = sum(t.pnl for t in winning_trades) / wins if wins > 0 else 0.0
        avg_loss = abs(sum(t.pnl for t in losing_trades) / losses) if losses > 0 else 0.0
        
        profit_factor = (avg_win * wins) / (avg_loss * losses) if losses > 0 and avg_loss > 0 else 0.0
        
        largest_win = max((t.pnl for t in winning_trades), default=0.0)
        largest_loss = min((t.pnl for t in losing_trades), default=0.0)
        
        return PortfolioMetrics(
            total_balance=total_balance,
            total_equity=total_equity,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            daily_pnl=daily_pnl,
            max_drawdown=self.max_drawdown,
            current_drawdown=self.get_current_drawdown(),
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=wins,
            losing_trades=losses,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss
        )
        
    def clear_old_history(self, keep_last_n: int = 1000) -> None:
        """Clear old history while keeping recent data."""
        if len(self.equity_history) > keep_last_n:
            # Convert to list, trim, convert back
            equity_list = list(self.equity_history)
            balance_list = list(self.balance_history)
            time_list = list(self.timestamps)
            
            self.equity_history = deque(equity_list[-keep_last_n:], maxlen=self.MAX_HISTORY_SIZE)
            self.balance_history = deque(balance_list[-keep_last_n:], maxlen=self.MAX_HISTORY_SIZE)
            self.timestamps = deque(time_list[-keep_last_n:], maxlen=self.MAX_HISTORY_SIZE)
            
    def get_memory_usage(self) -> dict:
        """Get memory usage statistics."""
        import sys
        return {
            'positions_count': len(self.positions),
            'trades_count': len(self.trades),
            'equity_history_size': len(self.equity_history),
            'balance_history_size': len(self.balance_history),
            'timestamps_size': len(self.timestamps),
            'estimated_memory_mb': (
                sys.getsizeof(self.positions) +
                sys.getsizeof(self.trades) +
                sys.getsizeof(self.equity_history) +
                sys.getsizeof(self.balance_history) +
                sys.getsizeof(self.timestamps)
            ) / 1024 / 1024
        }
