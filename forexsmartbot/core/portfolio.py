"""Portfolio management and aggregation."""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
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
    """Portfolio management and aggregation."""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_history: List[float] = [initial_balance]
        self.balance_history: List[float] = [initial_balance]
        self.timestamps: List[datetime] = [datetime.now()]
        self.peak_equity = initial_balance
        self.max_drawdown = 0.0
        
    def add_position(self, position: Position) -> None:
        """Add or update a position."""
        self.positions[position.symbol] = position
        
    def remove_position(self, symbol: str) -> Optional[Position]:
        """Remove a position and return it."""
        return self.positions.pop(symbol, None)
        
    def add_trade(self, trade: Trade) -> None:
        """Add a completed trade."""
        self.trades.append(trade)
        
    def update_equity(self, current_balance: float) -> None:
        """Update equity with current balance and unrealized PnL."""
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        current_equity = current_balance + unrealized_pnl
        
        self.equity_history.append(current_equity)
        self.balance_history.append(current_balance)
        self.timestamps.append(datetime.now())
        
        # Update peak equity and drawdown
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            
        current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
            
    def get_total_equity(self) -> float:
        """Get total portfolio equity."""
        if not self.equity_history:
            return self.initial_balance
        return self.equity_history[-1]
        
    def get_total_balance(self) -> float:
        """Get total portfolio balance."""
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
        """Get today's PnL."""
        today = datetime.now().date()
        today_trades = [t for t in self.trades if t.exit_time.date() == today]
        return sum(trade.pnl for trade in today_trades)
        
    def get_current_drawdown(self) -> float:
        """Get current drawdown percentage."""
        current_equity = self.get_total_equity()
        if self.peak_equity == 0:
            return 0.0
        return (self.peak_equity - current_equity) / self.peak_equity
        
    def calculate_metrics(self) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics."""
        total_balance = self.get_total_balance()
        total_equity = self.get_total_equity()
        unrealized_pnl = self.get_unrealized_pnl()
        realized_pnl = self.get_realized_pnl()
        daily_pnl = self.get_daily_pnl()
        
        # Trade statistics
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0.0
        
        largest_win = max((t.pnl for t in winning_trades), default=0.0)
        largest_loss = min((t.pnl for t in losing_trades), default=0.0)
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        sharpe_ratio = None
        if len(self.equity_history) > 1:
            returns = pd.Series(self.equity_history).pct_change().dropna()
            if len(returns) > 0 and returns.std() > 0:
                sharpe_ratio = returns.mean() / returns.std() * (252 ** 0.5)  # Annualized
        
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
            sharpe_ratio=sharpe_ratio,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss
        )
        
    def get_equity_series(self) -> pd.Series:
        """Get equity as pandas Series with timestamps."""
        if not self.equity_history:
            return pd.Series([self.initial_balance], index=[datetime.now()])
        return pd.Series(self.equity_history, index=self.timestamps)
        
    def get_balance_series(self) -> pd.Series:
        """Get balance as pandas Series with timestamps."""
        if not self.balance_history:
            return pd.Series([self.initial_balance], index=[datetime.now()])
        return pd.Series(self.balance_history, index=self.timestamps)
        
    def get_positions_by_symbol(self) -> Dict[str, List[Position]]:
        """Get positions grouped by symbol."""
        result = {}
        for pos in self.positions.values():
            if pos.symbol not in result:
                result[pos.symbol] = []
            result[pos.symbol].append(pos)
        return result
        
    def get_trades_by_symbol(self) -> Dict[str, List[Trade]]:
        """Get trades grouped by symbol."""
        result = {}
        for trade in self.trades:
            if trade.symbol not in result:
                result[trade.symbol] = []
            result[trade.symbol].append(trade)
        return result
