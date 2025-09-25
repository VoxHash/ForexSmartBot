"""MetaTrader 4 broker implementation via ZeroMQ."""

import json
import zmq
from typing import Dict, Optional
from datetime import datetime
from ...core.interfaces import IBroker, Position, Order


class MT4Broker(IBroker):
    """MT4 broker implementation using ZeroMQ bridge."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5555):
        self._host = host
        self._port = port
        self._context = None
        self._socket = None
        self._connected = False
        
    def connect(self) -> bool:
        """Connect to MT4 via ZeroMQ."""
        try:
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.REQ)
            self._socket.connect(f"tcp://{self._host}:{self._port}")
            self._socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False
            
    def disconnect(self) -> None:
        """Disconnect from MT4."""
        if self._socket:
            self._socket.close()
        if self._context:
            self._context.term()
        self._connected = False
        
    def is_connected(self) -> bool:
        """Check if connected to MT4."""
        return self._connected
        
    def _send_command(self, cmd: str, **kwargs) -> Optional[dict]:
        """Send command to MT4 and return response."""
        if not self._connected:
            return None
            
        try:
            payload = {'cmd': cmd, **kwargs}
            self._socket.send_string(json.dumps(payload))
            response = self._socket.recv_string()
            return json.loads(response)
        except Exception:
            return None
            
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price from MT4."""
        response = self._send_command('price', symbol=symbol)
        if response and 'price' in response:
            return float(response['price'])
        return None
        
    def submit_order(self, symbol: str, side: int, quantity: float, 
                    stop_loss: Optional[float] = None, 
                    take_profit: Optional[float] = None) -> Optional[str]:
        """Submit order to MT4."""
        response = self._send_command(
            'order', 
            symbol=symbol, 
            side=side, 
            volume=quantity,
            sl=stop_loss,
            tp=take_profit
        )
        if response and 'order_id' in response:
            return str(response['order_id'])
        return None
        
    def close_all(self, symbol: str) -> bool:
        """Close all positions for symbol."""
        response = self._send_command('close_all', symbol=symbol)
        return response and response.get('success', False)
        
    def get_positions(self) -> Dict[str, Position]:
        """Get positions from MT4."""
        response = self._send_command('positions')
        positions = {}
        
        if response and 'positions' in response:
            for pos_data in response['positions']:
                symbol = pos_data['symbol']
                position = Position(
                    symbol=symbol,
                    side=pos_data['side'],
                    quantity=pos_data['volume'],
                    entry_price=pos_data['entry_price'],
                    current_price=pos_data['current_price'],
                    unrealized_pnl=pos_data['unrealized_pnl'],
                    stop_loss=pos_data.get('stop_loss'),
                    take_profit=pos_data.get('take_profit'),
                    timestamp=datetime.fromisoformat(pos_data['timestamp'])
                )
                positions[symbol] = position
                
        return positions
        
    def get_balance(self) -> float:
        """Get account balance from MT4."""
        response = self._send_command('balance')
        if response and 'balance' in response:
            return float(response['balance'])
        return 0.0
        
    def get_equity(self) -> float:
        """Get account equity from MT4."""
        response = self._send_command('equity')
        if response and 'equity' in response:
            return float(response['equity'])
        return 0.0
