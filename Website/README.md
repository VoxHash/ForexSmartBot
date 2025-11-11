# Remote Monitoring Website

This folder contains the web-based remote monitoring interface for ForexSmartBot.

## Features

- Real-time dashboard
- Strategy monitoring
- Performance tracking
- Trade history
- Alerts and notifications

## Setup

1. Install dependencies:
```bash
pip install flask flask-cors flask-limiter websockets
```

2. Configure the API server in `forexsmartbot/cloud/api_server.py`

3. Start the web server:
```bash
python -m forexsmartbot.cloud.api_server
```

4. Access the dashboard at: `http://localhost:8080`

## Structure

- `index.html` - Main dashboard page
- `static/` - CSS, JavaScript, and assets
- `templates/` - HTML templates

## Integration

The remote monitoring is integrated with:
- `forexsmartbot/cloud/remote_monitor.py` - Remote monitoring server
- `forexsmartbot/cloud/api_server.py` - REST and WebSocket API

