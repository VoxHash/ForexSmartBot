# Cloud Integration Guide - ForexSmartBot v3.3.0

## Quick Start

### 1. Enable Cloud Sync

```python
from forexsmartbot.cloud.cloud_sync import CloudSyncManager
from forexsmartbot.services.persistence import SettingsManager

# Initialize
cloud_sync = CloudSyncManager(
    api_endpoint='https://api.forexsmartbot.cloud',
    api_key=os.getenv('CLOUD_API_KEY')
)

# Sync settings
settings_manager = SettingsManager()
settings = {
    'broker_mode': settings_manager.get('broker_mode'),
    'risk_pct': settings_manager.get('risk_pct')
}
cloud_sync.sync_settings(settings)
```

### 2. Start Remote Monitor

```python
from forexsmartbot.cloud.remote_monitor import RemoteMonitorServer

monitor = RemoteMonitorServer(host='127.0.0.1', port=8080)
monitor.start()

# Access at http://127.0.0.1:8080
```

### 3. Start API Server

```python
from forexsmartbot.cloud.api_server import APIServer

api_server = APIServer(
    host='127.0.0.1',
    port=5000,
    api_key='YOUR_API_KEY'
)
api_server.set_broker(broker)
api_server.start()
```

## Integration with Main Application

### Enhanced Main Window Integration

```python
from forexsmartbot.cloud import CloudSyncManager, RemoteMonitorServer, APIServer

class EnhancedMainWindow:
    def __init__(self):
        # ... existing initialization ...
        
        # Initialize cloud services
        self.cloud_sync = CloudSyncManager()
        self.remote_monitor = RemoteMonitorServer()
        self.api_server = APIServer()
        
        # Register callbacks
        self.remote_monitor.register_control_callback(
            'start_trading', 
            self.start_trading
        )
        self.remote_monitor.register_control_callback(
            'stop_trading',
            self.stop_trading
        )
        
        # Start services
        if self.settings_manager.get('cloud_sync_enabled', False):
            self.cloud_sync.enable_auto_sync()
            
        if self.settings_manager.get('remote_monitor_enabled', False):
            self.remote_monitor.start()
            
        if self.settings_manager.get('api_server_enabled', False):
            self.api_server.set_broker(self.broker)
            self.api_server.set_trading_controller(self.trading_controller)
            self.api_server.start()
```

### Auto-Sync on Settings Change

```python
def save_settings(self):
    """Save settings and sync to cloud."""
    # Save to local file
    self.settings_manager.save()
    
    # Sync to cloud
    if self.cloud_sync:
        settings_dict = self.settings_manager.get_all()
        self.cloud_sync.sync_settings(settings_dict)
```

### Real-Time Data Updates

```python
def update_real_time_data(self):
    """Update real-time data and sync to cloud."""
    # Update local data
    # ... existing code ...
    
    # Update remote monitor
    if self.remote_monitor:
        self.remote_monitor.update_trading_data({
            'balance': balance,
            'equity': equity,
            'positions': positions_list,
            'status': 'connected'
        })
    
    # Sync to cloud
    if self.cloud_sync:
        portfolio_data = {
            'balance': balance,
            'equity': equity,
            'positions_count': len(positions)
        }
        self.cloud_sync.sync_portfolio(portfolio_data)
```

## Mobile App Integration

### Push Notifications

```python
from forexsmartbot.cloud.mobile_api import PushNotificationService

push_service = PushNotificationService(fcm_server_key='YOUR_FCM_KEY')

# Send trade alert
def on_trade_opened(symbol, price, pnl):
    push_service.send_trade_alert('Open', symbol, price, pnl)

# Send risk alert
def on_risk_warning(message):
    push_service.send_alert('Risk Warning', message)
```

## API Client Usage

### Python Client

```python
from forexsmartbot.cloud.api_client import APIClient

client = APIClient(
    api_key='YOUR_API_KEY',
    base_url='http://localhost:5000'
)

# Get balance
balance = client.get_balance()

# Create order
order = client.create_order(
    symbol='EURUSD',
    side=1,
    quantity=1000,
    stop_loss=1.0980,
    take_profit=1.1100
)
```

### WebSocket Client

```python
from forexsmartbot.cloud.api_client import WebSocketClient
import asyncio

async def main():
    client = WebSocketClient(url='ws://localhost:8765')
    await client.connect()
    
    # Subscribe to updates
    await client.subscribe('EURUSD')
    
    # Listen for updates
    def handle_update(data):
        print(f"Update: {data}")
    
    await client.listen(handle_update)

asyncio.run(main())
```

## Security Configuration

### API Key Management

```python
from forexsmartbot.cloud.security import SecurityManager

security = SecurityManager(secret_key='YOUR_SECRET_KEY')

# Generate JWT token
token = security.generate_token(
    user_id='user123',
    permissions=['read', 'write']
)

# Verify token
payload = security.verify_token(token)
```

### Rate Limiting

```python
from forexsmartbot.cloud.security import RateLimiter

rate_limiter = RateLimiter()

# Check rate limit
if rate_limiter.check_rate_limit('user123', max_requests=100, time_window=3600):
    # Process request
    pass
else:
    # Rate limit exceeded
    pass
```

## Error Handling

```python
from forexsmartbot.cloud.error_handler import CloudErrorHandler

error_handler = CloudErrorHandler(max_retries=3, retry_delay=1.0)

@error_handler.handle_api_error
def sync_to_cloud(data):
    # API call with automatic retries
    response = requests.post(url, json=data)
    return response.json()
```

## Health Monitoring

```python
from forexsmartbot.cloud.error_handler import CloudHealthMonitor

health_monitor = CloudHealthMonitor()

def check_cloud_api():
    try:
        response = requests.get('https://api.forexsmartbot.cloud/health', timeout=5)
        return response.status_code == 200
    except:
        return False

# Check health
status = health_monitor.check_service_health('cloud_api', check_cloud_api)
print(f"Cloud API Status: {status['status']}")
```

## Best Practices

1. **Enable cloud sync for multi-device usage**
2. **Use remote monitor for monitoring from anywhere**
3. **Implement proper authentication for API access**
4. **Monitor API usage and set rate limits**
5. **Use error handling for all cloud operations**
6. **Regularly check service health**
7. **Keep API keys secure and rotate regularly**

---

**Version**: 3.3.0  
**Last Updated**: January 2026

