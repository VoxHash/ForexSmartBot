# Extending Brokers

ForexSmartBot supports multiple broker types through a plugin architecture. This document explains how to add support for new brokers or extend existing ones.

## Broker Architecture

### IBroker Interface

All brokers must implement the `IBroker` interface:

```python
from forexsmartbot.core.interfaces import IBroker, Position, Order
from typing import Dict, Optional

class IBroker(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the broker. Returns True if successful."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the broker."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        pass
    
    @abstractmethod
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        pass
    
    @abstractmethod
    def submit_order(self, symbol: str, side: int, quantity: float, 
                    stop_loss: Optional[float] = None, 
                    take_profit: Optional[float] = None) -> Optional[str]:
        """Submit an order. Returns order ID or None if failed."""
        pass
    
    @abstractmethod
    def close_all(self, symbol: str) -> bool:
        """Close all positions for symbol. Returns True if successful."""
        pass
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    def get_balance(self) -> float:
        """Get account balance."""
        pass
    
    @abstractmethod
    def get_equity(self) -> float:
        """Get account equity (balance + unrealized PnL)."""
        pass
```

## Built-in Brokers

### Paper Broker

The paper broker simulates trading without real money:

```python
from forexsmartbot.adapters.brokers.paper_broker import PaperBroker

broker = PaperBroker(initial_balance=10000.0)
```

**Features:**
- Simulates real trading
- Tracks positions and PnL
- No real money at risk
- Perfect for backtesting

### MT4 Broker

The MT4 broker connects to MetaTrader 4 via ZeroMQ:

```python
from forexsmartbot.adapters.brokers.mt4_broker import MT4Broker

broker = MT4Broker(host="127.0.0.1", port=5555)
```

**Requirements:**
- MetaTrader 4 installed
- ZeroMQ bridge EA loaded
- Network connection to MT4

### REST Broker (Placeholder)

The REST broker provides a template for REST API brokers:

```python
from forexsmartbot.adapters.brokers.rest_broker import RestBroker

broker = RestBroker(
    api_key="your_api_key",
    api_secret="your_api_secret",
    base_url="https://api.broker.com"
)
```

## Creating a Custom Broker

### Step 1: Create Broker Class

Create a new broker class implementing `IBroker`:

```python
from forexsmartbot.core.interfaces import IBroker, Position, Order
from typing import Dict, Optional
import requests
import json

class MyCustomBroker(IBroker):
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session = requests.Session()
        self._connected = False
        
    def connect(self) -> bool:
        """Connect to the broker API."""
        try:
            # Authenticate with broker
            auth_data = {
                'api_key': self.api_key,
                'api_secret': self.api_secret
            }
            response = self.session.post(f"{self.base_url}/auth", json=auth_data)
            
            if response.status_code == 200:
                self._connected = True
                return True
            else:
                return False
                
        except Exception:
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the broker."""
        self.session.close()
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price."""
        try:
            response = self.session.get(f"{self.base_url}/price/{symbol}")
            if response.status_code == 200:
                data = response.json()
                return float(data['price'])
            return None
        except Exception:
            return None
    
    def submit_order(self, symbol: str, side: int, quantity: float, 
                    stop_loss: Optional[float] = None, 
                    take_profit: Optional[float] = None) -> Optional[str]:
        """Submit an order."""
        try:
            order_data = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
            
            response = self.session.post(f"{self.base_url}/orders", json=order_data)
            if response.status_code == 200:
                data = response.json()
                return data['order_id']
            return None
            
        except Exception:
            return None
    
    def close_all(self, symbol: str) -> bool:
        """Close all positions for symbol."""
        try:
            response = self.session.delete(f"{self.base_url}/positions/{symbol}")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        try:
            response = self.session.get(f"{self.base_url}/positions")
            if response.status_code == 200:
                data = response.json()
                positions = {}
                
                for pos_data in data['positions']:
                    position = Position(
                        symbol=pos_data['symbol'],
                        side=pos_data['side'],
                        quantity=pos_data['quantity'],
                        entry_price=pos_data['entry_price'],
                        current_price=pos_data['current_price'],
                        unrealized_pnl=pos_data['unrealized_pnl'],
                        stop_loss=pos_data.get('stop_loss'),
                        take_profit=pos_data.get('take_profit')
                    )
                    positions[pos_data['symbol']] = position
                
                return positions
            return {}
            
        except Exception:
            return {}
    
    def get_balance(self) -> float:
        """Get account balance."""
        try:
            response = self.session.get(f"{self.base_url}/balance")
            if response.status_code == 200:
                data = response.json()
                return float(data['balance'])
            return 0.0
        except Exception:
            return 0.0
    
    def get_equity(self) -> float:
        """Get account equity."""
        try:
            response = self.session.get(f"{self.base_url}/equity")
            if response.status_code == 200:
                data = response.json()
                return float(data['equity'])
            return 0.0
        except Exception:
            return 0.0
```

### Step 2: Add to Broker Registry

Add your broker to the registry in `forexsmartbot/adapters/brokers/__init__.py`:

```python
from .paper_broker import PaperBroker
from .mt4_broker import MT4Broker
from .rest_broker import RestBroker
from .my_custom_broker import MyCustomBroker

__all__ = ['PaperBroker', 'MT4Broker', 'RestBroker', 'MyCustomBroker']
```

### Step 3: Add to UI

Update the main window to include your broker:

```python
# In forexsmartbot/ui/main_window.py
self.broker_combo.addItems(["PAPER", "MT4", "REST", "MY_CUSTOM"])

# In the on_connect method
elif broker_type == "MY_CUSTOM":
    api_key = self.settings_manager.get('my_custom_api_key', '')
    api_secret = self.settings_manager.get('my_custom_api_secret', '')
    base_url = self.settings_manager.get('my_custom_base_url', '')
    self.broker = MyCustomBroker(api_key, api_secret, base_url)
```

### Step 4: Add Settings

Add broker-specific settings to the settings dialog:

```python
# In forexsmartbot/ui/settings_dialog.py
def create_broker_tab(self) -> QWidget:
    # ... existing code ...
    
    # My Custom Broker settings group
    my_custom_group = QGroupBox("My Custom Broker Settings")
    my_custom_layout = QFormLayout(my_custom_group)
    
    self.my_custom_api_key_edit = QLineEdit()
    self.my_custom_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    my_custom_layout.addRow("API Key:", self.my_custom_api_key_edit)
    
    self.my_custom_api_secret_edit = QLineEdit()
    self.my_custom_api_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
    my_custom_layout.addRow("API Secret:", self.my_custom_api_secret_edit)
    
    self.my_custom_base_url_edit = QLineEdit()
    self.my_custom_base_url_edit.setPlaceholderText("https://api.mybroker.com")
    my_custom_layout.addRow("Base URL:", self.my_custom_base_url_edit)
    
    layout.addWidget(my_custom_group)
```

## Broker-Specific Features

### Authentication

Different brokers may require different authentication methods:

```python
class OAuthBroker(IBroker):
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
    
    def connect(self) -> bool:
        # OAuth 2.0 authentication
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        response = requests.post(f"{self.base_url}/oauth/token", data=auth_data)
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            self.session.headers.update({
                'Authorization': f"Bearer {self.access_token}"
            })
            return True
        return False
```

### Rate Limiting

Implement rate limiting for API calls:

```python
import time
from collections import deque

class RateLimitedBroker(IBroker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rate_limit = 100  # requests per minute
        self.request_times = deque()
    
    def _check_rate_limit(self):
        """Check and enforce rate limit."""
        now = time.time()
        
        # Remove requests older than 1 minute
        while self.request_times and self.request_times[0] < now - 60:
            self.request_times.popleft()
        
        # Check if we're at the limit
        if len(self.request_times) >= self.rate_limit:
            sleep_time = 60 - (now - self.request_times[0])
            time.sleep(sleep_time)
        
        self.request_times.append(now)
    
    def get_price(self, symbol: str) -> Optional[float]:
        self._check_rate_limit()
        return super().get_price(symbol)
```

### Error Handling

Implement robust error handling:

```python
class RobustBroker(IBroker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = 3
        self.retry_delay = 1
    
    def _make_request(self, method: str, url: str, **kwargs):
        """Make HTTP request with retries."""
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    return None
            except Exception:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    return None
        return None
```

### WebSocket Support

For real-time data, implement WebSocket support:

```python
import websocket
import threading
import json

class WebSocketBroker(IBroker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws = None
        self.price_cache = {}
        self.positions_cache = {}
        self.balance_cache = 0.0
        self.equity_cache = 0.0
    
    def connect(self) -> bool:
        """Connect to WebSocket."""
        try:
            self.ws = websocket.WebSocketApp(
                f"{self.base_url}/ws",
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start WebSocket in separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            self._connected = True
            return True
            
        except Exception:
            return False
    
    def _on_message(self, ws, message):
        """Handle WebSocket messages."""
        try:
            data = json.loads(message)
            
            if data['type'] == 'price':
                self.price_cache[data['symbol']] = data['price']
            elif data['type'] == 'position':
                # Update position cache
                pass
            elif data['type'] == 'balance':
                self.balance_cache = data['balance']
            elif data['type'] == 'equity':
                self.equity_cache = data['equity']
                
        except Exception:
            pass
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get cached price."""
        return self.price_cache.get(symbol)
```

## Testing Brokers

### Unit Tests

Create comprehensive tests for your broker:

```python
import pytest
from unittest.mock import Mock, patch
from forexsmartbot.adapters.brokers.my_custom_broker import MyCustomBroker

class TestMyCustomBroker:
    def test_connect_success(self):
        broker = MyCustomBroker("key", "secret", "https://api.test.com")
        
        with patch('requests.Session.post') as mock_post:
            mock_post.return_value.status_code = 200
            assert broker.connect() == True
            assert broker.is_connected() == True
    
    def test_connect_failure(self):
        broker = MyCustomBroker("key", "secret", "https://api.test.com")
        
        with patch('requests.Session.post') as mock_post:
            mock_post.return_value.status_code = 401
            assert broker.connect() == False
            assert broker.is_connected() == False
    
    def test_get_price(self):
        broker = MyCustomBroker("key", "secret", "https://api.test.com")
        broker._connected = True
        
        with patch('requests.Session.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'price': 1.2345}
            
            price = broker.get_price('EURUSD')
            assert price == 1.2345
    
    def test_submit_order(self):
        broker = MyCustomBroker("key", "secret", "https://api.test.com")
        broker._connected = True
        
        with patch('requests.Session.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'order_id': '12345'}
            
            order_id = broker.submit_order('EURUSD', 1, 0.1)
            assert order_id == '12345'
```

### Integration Tests

Test with real broker APIs (in test environment):

```python
@pytest.mark.integration
def test_real_broker_connection():
    broker = MyCustomBroker(
        api_key=os.getenv('TEST_API_KEY'),
        api_secret=os.getenv('TEST_API_SECRET'),
        base_url=os.getenv('TEST_BASE_URL')
    )
    
    assert broker.connect() == True
    assert broker.is_connected() == True
    
    # Test getting price
    price = broker.get_price('EURUSD')
    assert price is not None
    assert price > 0
    
    # Test getting balance
    balance = broker.get_balance()
    assert balance >= 0
    
    broker.disconnect()
    assert broker.is_connected() == False
```

## Broker Configuration

### Settings Management

Add broker-specific settings to the settings manager:

```python
# In forexsmartbot/services/persistence.py
class SettingsManager:
    def _load_settings(self) -> Dict[str, Any]:
        default_settings = {
            # ... existing settings ...
            
            # My Custom Broker settings
            'my_custom_api_key': '',
            'my_custom_api_secret': '',
            'my_custom_base_url': 'https://api.mybroker.com',
            'my_custom_sandbox': True,
        }
        # ... rest of method ...
```

### Environment Variables

Support environment variables for sensitive data:

```python
class MyCustomBroker(IBroker):
    def __init__(self, api_key: str = None, api_secret: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv('MY_CUSTOM_API_KEY')
        self.api_secret = api_secret or os.getenv('MY_CUSTOM_API_SECRET')
        self.base_url = base_url or os.getenv('MY_CUSTOM_BASE_URL', 'https://api.mybroker.com')
```

## Best Practices

### 1. Error Handling

- Always handle network errors gracefully
- Implement retry logic for transient failures
- Log errors for debugging
- Provide meaningful error messages

### 2. Rate Limiting

- Respect broker API rate limits
- Implement exponential backoff
- Cache data when appropriate
- Use WebSockets for real-time data

### 3. Security

- Never log sensitive data (API keys, secrets)
- Use secure connections (HTTPS/WSS)
- Validate all input data
- Implement proper authentication

### 4. Performance

- Use connection pooling
- Implement caching where appropriate
- Minimize API calls
- Use asynchronous operations when possible

### 5. Testing

- Write comprehensive unit tests
- Test error conditions
- Use mock objects for external dependencies
- Test with real APIs in test environment

## Common Broker Types

### REST API Brokers

Most modern brokers provide REST APIs:

```python
class RESTBroker(IBroker):
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
```

### FIX Protocol Brokers

For institutional brokers using FIX protocol:

```python
import quickfix as fix

class FIXBroker(IBroker):
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.settings = fix.SessionSettings(config_file)
        self.store_factory = fix.FileStoreFactory(self.settings)
        self.log_factory = fix.FileLogFactory(self.settings)
        self.initiator = fix.SocketInitiator(
            self, self.store_factory, self.settings, self.log_factory
        )
```

### WebSocket Brokers

For real-time data and trading:

```python
import websocket
import threading

class WebSocketBroker(IBroker):
    def __init__(self, ws_url: str, api_key: str):
        self.ws_url = ws_url
        self.api_key = api_key
        self.ws = None
        self.data_cache = {}
```

## Conclusion

Creating custom brokers for ForexSmartBot is straightforward with the `IBroker` interface. Follow the patterns established by the built-in brokers and implement robust error handling, testing, and security measures. The plugin architecture makes it easy to add new brokers without modifying the core system.
