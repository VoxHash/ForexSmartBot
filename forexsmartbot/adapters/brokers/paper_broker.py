"""Paper trading broker implementation."""

from typing import Dict, Optional
from datetime import datetime
from ...core.interfaces import IBroker, Position, Order


class PaperBroker(IBroker):
    """Paper trading broker for backtesting and simulation."""
    
    def __init__(self, initial_balance: float = 10000.0):
        self._balance = initial_balance
        self._positions: Dict[str, Position] = {}
        self._orders: Dict[str, Order] = {}
        self._connected = False
        self._order_counter = 0
        
    def connect(self) -> bool:
        """Connect to paper broker (always successful)."""
        self._connected = True
        return True
        
    def disconnect(self) -> None:
        """Disconnect from paper broker."""
        self._connected = False
        
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected
        
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price (placeholder - would need data provider)."""
        # In real implementation, this would get price from data provider
        return None
        
    def submit_order(self, symbol: str, side: int, quantity: float, 
                    stop_loss: Optional[float] = None, 
                    take_profit: Optional[float] = None) -> Optional[str]:
        """Submit a paper order."""
        if not self._connected:
            return None
            
        order_id = f"PAPER_{self._order_counter}"
        self._order_counter += 1
        
        # Create order
        order = Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=0.0,  # Will be filled with current price
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self._orders[order_id] = order
        return order_id
        
    def close_all(self, symbol: str) -> bool:
        """Close all positions for symbol."""
        if symbol in self._positions:
            del self._positions[symbol]
            return True
        return False
        
    def get_positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        return self._positions.copy()
        
    def get_balance(self) -> float:
        """Get account balance."""
        return self._balance
        
    def get_equity(self) -> float:
        """Get account equity."""
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self._positions.values())
        return self._balance + unrealized_pnl
        
    def update_position(self, symbol: str, side: int, quantity: float, 
                       entry_price: float, current_price: float) -> None:
        """Update or create a position."""
        unrealized_pnl = side * quantity * (current_price - entry_price)
        
        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl
        )
        
        self._positions[symbol] = position
        
    def close_position(self, symbol: str, exit_price: float) -> Optional[float]:
        """Close a position and return realized PnL."""
        if symbol not in self._positions:
            return None
            
        position = self._positions.pop(symbol)
        realized_pnl = position.side * position.quantity * (exit_price - position.entry_price)
        self._balance += realized_pnl
        
        return realized_pnl
        
    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update position prices and calculate unrealized PnL."""
        for symbol, position in self._positions.items():
            if symbol in prices:
                position.current_price = prices[symbol]
                position.unrealized_pnl = position.side * position.quantity * (
                    position.current_price - position.entry_price
                )
