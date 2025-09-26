"""Advanced Trade Management System for ForexSmartBot."""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from .interfaces import Position, Trade, IStrategy

logger = logging.getLogger(__name__)


class TradeManager:
    """Advanced trade management system with stop loss, take profit, and position management."""
    
    def __init__(self, risk_reward_ratio: float = 2.0, breakeven_ratio: float = 1.0):
        self.risk_reward_ratio = risk_reward_ratio
        self.breakeven_ratio = breakeven_ratio
        self.positions: Dict[str, Position] = {}
        self.completed_trades: List[Trade] = []
        
    def create_position(self, symbol: str, side: int, quantity: float, 
                       entry_price: float, strategy: IStrategy, 
                       current_data: dict) -> Position:
        """Create a new position with stop loss and take profit."""
        try:
            # Calculate stop loss and take profit from strategy
            stop_loss = strategy.stop_loss(current_data)
            take_profit = strategy.take_profit(current_data)
            
            # Calculate additional take profit levels
            take_profit_2 = self._calculate_take_profit_2(entry_price, stop_loss, take_profit, side)
            take_profit_3 = self._calculate_take_profit_3(entry_price, stop_loss, take_profit, side)
            
            position = Position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                current_price=entry_price,
                unrealized_pnl=0.0,
                stop_loss=stop_loss,
                take_profit=take_profit,
                take_profit_2=take_profit_2,
                take_profit_3=take_profit_3,
                strategy=strategy.name,
                timestamp=datetime.now()
            )
            
            self.positions[symbol] = position
            logger.info(f"Created position: {symbol} {side} {quantity} @ {entry_price}, SL: {stop_loss}, TP: {take_profit}")
            
            return position
            
        except Exception as e:
            logger.error(f"Error creating position: {e}")
            return None
    
    def update_position(self, symbol: str, current_price: float) -> Optional[Position]:
        """Update position with current price and check for management triggers."""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        position.current_price = current_price
        
        # Update unrealized PnL
        position.unrealized_pnl = position.side * position.get_remaining_quantity() * (current_price - position.entry_price)
        
        # Check for breakeven trigger
        if self._check_breakeven_trigger(position, current_price):
            self._move_to_breakeven(position)
        
        # Check for trailing stop
        if self._check_trailing_stop(position, current_price):
            self._update_trailing_stop(position, current_price)
        
        # Check for take profit levels
        self._check_take_profit_levels(position, current_price)
        
        return position
    
    def _calculate_take_profit_2(self, entry_price: float, stop_loss: float, 
                                take_profit: float, side: int) -> Optional[float]:
        """Calculate second take profit level."""
        if not stop_loss or not take_profit:
            return None
        
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if side > 0:  # Long position
            return entry_price + (reward * 1.5)  # 1.5x the initial reward
        else:  # Short position
            return entry_price - (reward * 1.5)
    
    def _calculate_take_profit_3(self, entry_price: float, stop_loss: float, 
                                take_profit: float, side: int) -> Optional[float]:
        """Calculate third take profit level."""
        if not stop_loss or not take_profit:
            return None
        
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if side > 0:  # Long position
            return entry_price + (reward * 2.0)  # 2x the initial reward
        else:  # Short position
            return entry_price - (reward * 2.0)
    
    def _check_breakeven_trigger(self, position: Position, current_price: float) -> bool:
        """Check if position should move to breakeven."""
        if position.breakeven_triggered:
            return False
        
        return position.is_breakeven_eligible(current_price)
    
    def _move_to_breakeven(self, position: Position) -> None:
        """Move stop loss to breakeven."""
        position.stop_loss = position.entry_price
        position.breakeven_triggered = True
        logger.info(f"Moved {position.symbol} to breakeven at {position.entry_price}")
    
    def _check_trailing_stop(self, position: Position, current_price: float) -> bool:
        """Check if stop loss should be trailed."""
        return position.should_trail_stop(current_price)
    
    def _update_trailing_stop(self, position: Position, current_price: float) -> None:
        """Update trailing stop loss."""
        if not position.stop_loss:
            return
        
        # Calculate new trailing stop
        if position.side > 0:  # Long position
            new_stop = current_price - (position.entry_price - position.stop_loss)
            if new_stop > position.stop_loss:
                position.stop_loss = new_stop
        else:  # Short position
            new_stop = current_price + (position.stop_loss - position.entry_price)
            if new_stop < position.stop_loss:
                position.stop_loss = new_stop
        
        logger.info(f"Updated trailing stop for {position.symbol} to {position.stop_loss}")
    
    def _check_take_profit_levels(self, position: Position, current_price: float) -> None:
        """Check for take profit level hits and execute partial closes."""
        if position.side > 0:  # Long position
            # Check TP1
            if position.take_profit and current_price >= position.take_profit and len(position.partial_closes) == 0:
                self._execute_partial_close(position, 0.3, "TP1 Hit")
            
            # Check TP2
            if position.take_profit_2 and current_price >= position.take_profit_2 and len(position.partial_closes) == 1:
                self._execute_partial_close(position, 0.4, "TP2 Hit")
            
            # Check TP3
            if position.take_profit_3 and current_price >= position.take_profit_3 and len(position.partial_closes) == 2:
                self._execute_partial_close(position, 0.3, "TP3 Hit")
        
        else:  # Short position
            # Check TP1
            if position.take_profit and current_price <= position.take_profit and len(position.partial_closes) == 0:
                self._execute_partial_close(position, 0.3, "TP1 Hit")
            
            # Check TP2
            if position.take_profit_2 and current_price <= position.take_profit_2 and len(position.partial_closes) == 1:
                self._execute_partial_close(position, 0.4, "TP2 Hit")
            
            # Check TP3
            if position.take_profit_3 and current_price <= position.take_profit_3 and len(position.partial_closes) == 2:
                self._execute_partial_close(position, 0.3, "TP3 Hit")
    
    def _execute_partial_close(self, position: Position, percentage: float, reason: str) -> None:
        """Execute a partial close of the position."""
        close_quantity = position.get_remaining_quantity() * percentage
        position.add_partial_close(close_quantity)
        
        # Calculate PnL for this partial close
        pnl = position.side * close_quantity * (position.current_price - position.entry_price)
        
        logger.info(f"Partial close {position.symbol}: {close_quantity} units, PnL: {pnl:.2f}, Reason: {reason}")
    
    def check_stop_loss_hit(self, position: Position, current_price: float) -> bool:
        """Check if stop loss was hit."""
        if not position.stop_loss:
            return False
        
        if position.side > 0:  # Long position
            return current_price <= position.stop_loss
        else:  # Short position
            return current_price >= position.stop_loss
    
    def close_position(self, symbol: str, exit_price: float, reason: str = "Manual Close") -> Optional[Trade]:
        """Close a position and create a completed trade."""
        if symbol not in self.positions:
            return None
        
        position = self.positions.pop(symbol)
        remaining_quantity = position.get_remaining_quantity()
        
        # Calculate total PnL including partial closes
        total_pnl = position.side * remaining_quantity * (exit_price - position.entry_price)
        
        # Add PnL from partial closes
        for partial_quantity in position.partial_closes:
            partial_pnl = position.side * partial_quantity * (position.current_price - position.entry_price)
            total_pnl += partial_pnl
        
        trade = Trade(
            symbol=symbol,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=exit_price,
            pnl=total_pnl,
            strategy=position.strategy,
            entry_time=position.timestamp,
            exit_time=datetime.now(),
            stop_loss=position.stop_loss,
            take_profit=position.take_profit,
            breakeven_triggered=position.breakeven_triggered,
            partial_closes=position.partial_closes.copy(),
            management_notes=reason
        )
        
        self.completed_trades.append(trade)
        logger.info(f"Closed position {symbol}: PnL {total_pnl:.2f}, Reason: {reason}")
        
        return trade
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get a position by symbol."""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        return self.positions.copy()
    
    def get_completed_trades(self) -> List[Trade]:
        """Get all completed trades."""
        return self.completed_trades.copy()
    
    def get_position_summary(self) -> dict:
        """Get summary of all positions and trades."""
        total_positions = len(self.positions)
        total_trades = len(self.completed_trades)
        
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_realized_pnl = sum(trade.pnl for trade in self.completed_trades)
        
        winning_trades = sum(1 for trade in self.completed_trades if trade.pnl > 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'open_positions': total_positions,
            'completed_trades': total_trades,
            'unrealized_pnl': total_unrealized_pnl,
            'realized_pnl': total_realized_pnl,
            'total_pnl': total_unrealized_pnl + total_realized_pnl,
            'win_rate': win_rate,
            'winning_trades': winning_trades
        }
