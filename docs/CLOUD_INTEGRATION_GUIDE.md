# Cloud Integration Guide - ForexSmartBot v3.3.0

## Quick Start

Install optional remote extras when needed:

```bash
pip install 'forexsmartbot[remote]'
```

### 1. Enable Cloud Sync

```python
import os
from forexsmartbot.cloud.cloud_sync import CloudSyncManager
from forexsmartbot.services.persistence import SettingsManager

# Initialize (retries + pending queue built in)
cloud_sync = CloudSyncManager(
    api_endpoint=os.getenv('CLOUD_API_ENDPOINT', 'https://api.forexsmartbot.cloud'),
    api_key=os.getenv('CLOUD_API_KEY'),
    max_retries=3,
)

# Sync settings
settings_manager = SettingsManager()
settings = {
    'broker_mode': settings_manager.get('broker_mode'),
    'risk_pct': settings_manager.get('risk_pct')
}
cloud_sync.sync_settings(settings)
cloud_sync.enable_auto_sync(interval_seconds=300)  # background flush + re-sync
print(cloud_sync.get_sync_status())
print(cloud_sync.check_endpoint_health())
```

### 2. Start Remote Monitor

```python
import os
from forexsmartbot.cloud.remote_monitor import RemoteMonitorServer
from forexsmartbot.cloud.auth_utils import generate_api_token

api_key = os.getenv('API_KEY') or generate_api_token()
from forexsmartbot.monitoring.strategy_monitor import StrategyMonitor

sm = StrategyMonitor()
monitor = RemoteMonitorServer(
    host='127.0.0.1',
    port=8080,
    api_key=api_key,  # required for authenticated status/control
    strategy_monitor=sm,
)
monitor.start()

# Public health (no auth): http://127.0.0.1:8080/healthz
# Dashboard: http://127.0.0.1:8080  (paste API key; Strategy Health table)
# Authenticated status / strategies / companion:
#   curl -H "Authorization: Bearer $API_KEY" http://127.0.0.1:8080/api/v1/status
#   curl -H "X-API-Key: $API_KEY" http://127.0.0.1:8080/api/v1/strategies
#   curl -H "X-API-Key: $API_KEY" http://127.0.0.1:8080/api/v1/companion/portfolio
```

Non-loopback binds require a strong `API_KEY` (16+ chars) unless
`FSB_ALLOW_INSECURE_MONITOR=1` is set (local/dev only).

### 3. Start API Server

```python
from forexsmartbot.cloud.api_server import APIServer

api_server = APIServer(
    host='127.0.0.1',
    port=5000,
    api_key='YOUR_API_KEY'  # min 16 chars; Bearer or X-API-Key
)
api_server.set_broker(broker)
api_server.start()
# GET /healthz and /api/v1/health are public
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

## Mobile Companion Integration

Read-only companion endpoints are mounted on the remote monitor (`/api/v1/companion/*`).
Android scaffold: `mobile/android-companion/`. Prefer HTTPS webhooks on GrapheneOS; FCM is optional.

```python
from forexsmartbot.cloud.mobile_api import PushNotificationService
from forexsmartbot.cloud.companion_api import CompanionAPI

push_service = PushNotificationService()
push_service.register_webhook('https://notify.example/fsb')  # no Google required
push_service.send_alert('Risk Warning', 'Max drawdown threshold reached')

# Standalone companion (also available via RemoteMonitorServer):
# companion = CompanionAPI(api_key='...', portfolio_provider=...)
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

1. **Always set `API_KEY` / `CLOUD_API_KEY`** (16+ random chars); prefer `generate_api_token()`
2. **Bind monitors to `127.0.0.1`** unless TLS termination and a strong key are in place
3. **Use Bearer or `X-API-Key`** on every non-health endpoint
4. **Rely on sync retries** (`max_retries`) and call `flush_pending()` after outages
5. **Probe `/healthz`** from uptime monitors; keep status/control authenticated
6. **Set `API_SECRET_KEY`** for stable JWT signing across process restarts
7. **Rotate keys** and never commit `.env` secrets

---

**Version**: 3.3.0  
**Last Updated**: October 2026

