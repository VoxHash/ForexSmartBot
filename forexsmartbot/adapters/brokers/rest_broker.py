"""REST API broker implementation for live trading."""

import requests
import hashlib
import hmac
import time
import json
from typing import Dict, Optional, List
from datetime import datetime
from ...core.interfaces import IBroker, Position, Order


class RestBroker(IBroker):
    """REST API broker for live trading with real brokers."""
    
    def __init__(self, api_key: str = "", api_secret: str = "", 
                 base_url: str = "https://api.example.com", account_id: str = None, 
                 sandbox: bool = True):
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip('/')
        self._account_id = account_id
        self._sandbox = sandbox
        self._connected = False
        self._session = requests.Session()
        self._session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ForexSmartBot/2.0'
        })
        
    def connect(self) -> bool:
        """Connect to the REST API broker."""
        try:
            if not self._api_key or not self._api_secret:
                print("REST broker: API key or secret not provided")
                return False
                
            # Test connection with account info
            response = self._make_request('GET', '/v1/accounts')
            if response and response.get('status') == 'success':
                self._connected = True
                print("REST broker: Connected successfully")
                return True
            else:
                # Fallback: try to get balance as connection test
                balance = self.get_balance()
                if balance is not None:
                    self._connected = True
                    print("REST broker: Connected successfully (fallback)")
                    return True
        except Exception as e:
            print(f"REST broker connection failed: {e}")
            
        return False
        
    def disconnect(self) -> None:
        """Disconnect from the REST API broker."""
        self._connected = False
        if hasattr(self, '_session'):
            self._session.close()
        print("REST broker: Disconnected")
        
    def is_connected(self) -> bool:
        """Check if connected to the broker."""
        return self._connected
        
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        try:
            response = self._make_request('GET', f'/v1/prices/{symbol}')
            if response and 'price' in response:
                return float(response['price'])
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
        return None
        
    def submit_order(self, symbol: str, side: int, quantity: float, 
                    stop_loss: Optional[float] = None, 
                    take_profit: Optional[float] = None) -> Optional[str]:
        """Submit an order to the broker."""
        try:
            order_data = {
                'symbol': symbol,
                'side': 'buy' if side > 0 else 'sell',
                'quantity': quantity,
                'type': 'market'
            }
            
            if stop_loss:
                order_data['stop_loss'] = stop_loss
            if take_profit:
                order_data['take_profit'] = take_profit
                
            response = self._make_request('POST', '/v1/orders', data=order_data)
            if response and 'order_id' in response:
                print(f"REST broker: Order submitted for {symbol}")
                return response['order_id']
        except Exception as e:
            print(f"Error submitting order: {e}")
        return None
        
    def close_all(self, symbol: str) -> bool:
        """Close all positions for a symbol."""
        try:
            response = self._make_request('DELETE', f'/v1/positions/{symbol}')
            success = response and response.get('status') == 'success'
            if success:
                print(f"REST broker: Closed all positions for {symbol}")
            return success
        except Exception as e:
            print(f"Error closing positions for {symbol}: {e}")
        return False
        
    def get_positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        try:
            response = self._make_request('GET', '/v1/positions')
            positions = {}
            
            if response and 'positions' in response:
                for pos_data in response['positions']:
                    position = Position(
                        symbol=pos_data['symbol'],
                        side=1 if pos_data['side'] == 'long' else -1,
                        quantity=pos_data['quantity'],
                        entry_price=pos_data['entry_price'],
                        current_price=pos_data['current_price'],
                        unrealized_pnl=pos_data.get('unrealized_pnl', 0.0)
                    )
                    positions[position.symbol] = position
                    
            return positions
        except Exception as e:
            print(f"Error getting positions: {e}")
        return {}
        
    def get_balance(self) -> float:
        """Get account balance."""
        try:
            response = self._make_request('GET', '/v1/accounts/balance')
            if response and 'balance' in response:
                return float(response['balance'])
        except Exception as e:
            print(f"Error getting balance: {e}")
        return 0.0
        
    def get_equity(self) -> float:
        """Get account equity."""
        try:
            response = self._make_request('GET', '/v1/accounts/equity')
            if response and 'equity' in response:
                return float(response['equity'])
        except Exception as e:
            print(f"Error getting equity: {e}")
        return 0.0
        
    def get_orders(self) -> List[Dict]:
        """Get all orders."""
        try:
            response = self._make_request('GET', '/v1/orders')
            if response and 'orders' in response:
                return response['orders']
        except Exception as e:
            print(f"Error getting orders: {e}")
        return []
        
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            response = self._make_request('DELETE', f'/v1/orders/{order_id}')
            success = response and response.get('status') == 'success'
            if success:
                print(f"REST broker: Canceled order {order_id}")
            return success
        except Exception as e:
            print(f"Error canceling order {order_id}: {e}")
        return False
        
    def get_account_info(self) -> Dict:
        """Get account information."""
        try:
            response = self._make_request('GET', '/v1/accounts/info')
            return response or {}
        except Exception as e:
            print(f"Error getting account info: {e}")
        return {}
        
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make an authenticated HTTP request to the broker API."""
        try:
            url = f"{self._base_url}{endpoint}"
            
            # Add authentication headers
            timestamp = str(int(time.time() * 1000))
            signature = self._create_signature(method, endpoint, data, timestamp)
            
            headers = {
                'X-API-Key': self._api_key,
                'X-Timestamp': timestamp,
                'X-Signature': signature
            }
            
            if method == 'GET':
                response = self._session.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = self._session.post(url, headers=headers, json=data, timeout=10)
            elif method == 'PUT':
                response = self._session.put(url, headers=headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = self._session.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"HTTP request failed: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
        except Exception as e:
            print(f"Request error: {e}")
            
        return None
        
    def _create_signature(self, method: str, endpoint: str, data: Dict, timestamp: str) -> str:
        """Create HMAC signature for API authentication."""
        try:
            # Create message to sign
            message = f"{method}{endpoint}{timestamp}"
            if data:
                message += json.dumps(data, sort_keys=True)
                
            # Create HMAC signature
            signature = hmac.new(
                self._api_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
        except Exception as e:
            print(f"Error creating signature: {e}")
            return ""
            
    def get_market_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """Get historical market data."""
        try:
            params = {
                'symbol': symbol,
                'timeframe': timeframe,
                'limit': limit
            }
            response = self._make_request('GET', '/v1/market_data', params)
            if response and 'data' in response:
                return response['data']
        except Exception as e:
            print(f"Error getting market data: {e}")
        return []
        
    def get_trading_hours(self, symbol: str) -> Dict:
        """Get trading hours for a symbol."""
        try:
            response = self._make_request('GET', f'/v1/trading_hours/{symbol}')
            return response or {}
        except Exception as e:
            print(f"Error getting trading hours: {e}")
        return {}
        
    def get_margin_requirements(self, symbol: str) -> Dict:
        """Get margin requirements for a symbol."""
        try:
            response = self._make_request('GET', f'/v1/margin/{symbol}')
            return response or {}
        except Exception as e:
            print(f"Error getting margin requirements: {e}")
        return {}
        
    def get_instruments(self) -> List[Dict]:
        """Get available trading instruments."""
        try:
            response = self._make_request('GET', '/v1/instruments')
            if response and 'instruments' in response:
                return response['instruments']
        except Exception as e:
            print(f"Error getting instruments: {e}")
        return []
        
    def get_historical_prices(self, symbol: str, start_date: str, end_date: str, 
                             timeframe: str = '1h') -> List[Dict]:
        """Get historical price data."""
        try:
            params = {
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'timeframe': timeframe
            }
            response = self._make_request('GET', '/v1/historical_prices', params)
            if response and 'prices' in response:
                return response['prices']
        except Exception as e:
            print(f"Error getting historical prices: {e}")
        return []