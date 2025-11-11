"""
Remote Monitoring Server
Provides web-based monitoring interface with real-time alerts and remote control.
"""

import json
import asyncio
import os
from typing import Dict, List, Optional, Callable
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from threading import Thread
import logging
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv(override=False)


class RemoteMonitorServer:
    """Web-based remote monitoring server."""
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, 
                 api_key: Optional[str] = None):
        """
        Initialize remote monitor server.
        
        Args:
            host: Server host address (defaults to REMOTE_MONITOR_HOST env var or 127.0.0.1)
            port: Server port (defaults to REMOTE_MONITOR_PORT env var or 8080)
            api_key: API key for authentication (defaults to API_KEY env var)
        """
        self.host = host or os.getenv('REMOTE_MONITOR_HOST', '127.0.0.1')
        self.port = port or int(os.getenv('REMOTE_MONITOR_PORT', '8080'))
        self.api_key = api_key or os.getenv('API_KEY', '')
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for web interface
        
        self.trading_data = {
            'balance': 0.0,
            'equity': 0.0,
            'positions': [],
            'trades': [],
            'status': 'disconnected',
            'last_update': None
        }
        
        self.alert_callbacks: List[Callable] = []
        self.control_callbacks: Dict[str, Callable] = {}
        
        self.setup_routes()
        self.server_thread = None
        self.running = False
        
    def setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Serve monitoring dashboard."""
            return render_template_string(self._get_dashboard_html())
            
        @self.app.route('/api/v1/status', methods=['GET'])
        def get_status():
            """Get trading status."""
            if not self._check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            return jsonify(self.trading_data)
            
        @self.app.route('/api/v1/positions', methods=['GET'])
        def get_positions():
            """Get open positions."""
            if not self._check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            return jsonify({'positions': self.trading_data['positions']})
            
        @self.app.route('/api/v1/trades', methods=['GET'])
        def get_trades():
            """Get trade history."""
            if not self._check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            return jsonify({'trades': self.trading_data['trades']})
            
        @self.app.route('/api/v1/control/start', methods=['POST'])
        def control_start():
            """Start trading remotely."""
            if not self._check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            if 'start_trading' in self.control_callbacks:
                result = self.control_callbacks['start_trading']()
                return jsonify({'success': result})
            return jsonify({'error': 'Control not available'}), 400
            
        @self.app.route('/api/v1/control/stop', methods=['POST'])
        def control_stop():
            """Stop trading remotely."""
            if not self._check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            if 'stop_trading' in self.control_callbacks:
                result = self.control_callbacks['stop_trading']()
                return jsonify({'success': result})
            return jsonify({'error': 'Control not available'}), 400
            
        @self.app.route('/api/v1/alerts', methods=['GET'])
        def get_alerts():
            """Get recent alerts."""
            if not self._check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            return jsonify({'alerts': self._get_recent_alerts()})
            
    def _check_auth(self) -> bool:
        """Check API key authentication."""
        if not self.api_key:
            return True  # No auth required if no key set
            
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return token == self.api_key
        return False
        
    def _get_recent_alerts(self) -> List[Dict]:
        """Get recent alerts (placeholder)."""
        return []
        
    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML template."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>ForexSmartBot Remote Monitor</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1e1e1e; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; }
        .status-card { background: #2d2d2d; padding: 20px; margin: 10px 0; border-radius: 8px; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-connected { background: #4CAF50; }
        .status-disconnected { background: #f44336; }
        .data-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
        .data-item { background: #3d3d3d; padding: 15px; border-radius: 5px; }
        .data-label { font-size: 12px; color: #aaa; }
        .data-value { font-size: 24px; font-weight: bold; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
        .btn-start { background: #4CAF50; color: white; }
        .btn-stop { background: #f44336; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ForexSmartBot Remote Monitor</h1>
        
        <div class="status-card">
            <h2>Status</h2>
            <div id="status-indicator" class="status-indicator status-disconnected"></div>
            <span id="status-text">Disconnected</span>
        </div>
        
        <div class="data-grid">
            <div class="data-item">
                <div class="data-label">Balance</div>
                <div class="data-value" id="balance">$0.00</div>
            </div>
            <div class="data-item">
                <div class="data-label">Equity</div>
                <div class="data-value" id="equity">$0.00</div>
            </div>
            <div class="data-item">
                <div class="data-label">Open Positions</div>
                <div class="data-value" id="positions-count">0</div>
            </div>
            <div class="data-item">
                <div class="data-label">Total Trades</div>
                <div class="data-value" id="trades-count">0</div>
            </div>
        </div>
        
        <div class="status-card">
            <h2>Remote Control</h2>
            <button class="btn btn-start" onclick="startTrading()">Start Trading</button>
            <button class="btn btn-stop" onclick="stopTrading()">Stop Trading</button>
        </div>
        
        <div class="status-card">
            <h2>Open Positions</h2>
            <table id="positions-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Entry Price</th>
                        <th>Current Price</th>
                        <th>PnL</th>
                    </tr>
                </thead>
                <tbody id="positions-body"></tbody>
            </table>
        </div>
    </div>
    
    <script>
        function updateStatus() {
            fetch('/api/v1/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('balance').textContent = '$' + data.balance.toFixed(2);
                    document.getElementById('equity').textContent = '$' + data.equity.toFixed(2);
                    document.getElementById('positions-count').textContent = data.positions.length;
                    document.getElementById('trades-count').textContent = data.trades.length;
                    
                    const indicator = document.getElementById('status-indicator');
                    const statusText = document.getElementById('status-text');
                    if (data.status === 'connected') {
                        indicator.className = 'status-indicator status-connected';
                        statusText.textContent = 'Connected';
                    } else {
                        indicator.className = 'status-indicator status-disconnected';
                        statusText.textContent = 'Disconnected';
                    }
                    
                    // Update positions table
                    const tbody = document.getElementById('positions-body');
                    tbody.innerHTML = data.positions.map(pos => `
                        <tr>
                            <td>${pos.symbol}</td>
                            <td>${pos.side}</td>
                            <td>${pos.entry_price.toFixed(4)}</td>
                            <td>${pos.current_price.toFixed(4)}</td>
                            <td>$${pos.pnl.toFixed(2)}</td>
                        </tr>
                    `).join('');
                })
                .catch(err => console.error('Error:', err));
        }
        
        function startTrading() {
            fetch('/api/v1/control/start', {method: 'POST'})
                .then(r => r.json())
                .then(data => alert(data.success ? 'Trading started' : 'Failed to start'));
        }
        
        function stopTrading() {
            fetch('/api/v1/control/stop', {method: 'POST'})
                .then(r => r.json())
                .then(data => alert(data.success ? 'Trading stopped' : 'Failed to stop'));
        }
        
        // Update every 3 seconds
        setInterval(updateStatus, 3000);
        updateStatus();
    </script>
</body>
</html>
        """
        
    def update_trading_data(self, data: Dict):
        """
        Update trading data for monitoring.
        
        Args:
            data: Trading data dictionary
        """
        self.trading_data.update(data)
        self.trading_data['last_update'] = datetime.now().isoformat()
        
    def register_control_callback(self, action: str, callback: Callable):
        """
        Register callback for remote control actions.
        
        Args:
            action: Action name ('start_trading', 'stop_trading', etc.)
            callback: Callback function
        """
        self.control_callbacks[action] = callback
        
    def register_alert_callback(self, callback: Callable):
        """
        Register callback for alerts.
        
        Args:
            callback: Callback function
        """
        self.alert_callbacks.append(callback)
        
    def start(self):
        """Start the monitoring server."""
        if self.running:
            return
            
        self.running = True
        self.server_thread = Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        print(f"Remote monitor server started on http://{self.host}:{self.port}")
        
    def stop(self):
        """Stop the monitoring server."""
        self.running = False
        # Flask doesn't have a clean way to stop, so we'll just mark as stopped
        print("Remote monitor server stopped")
        
    def _run_server(self):
        """Run Flask server in thread."""
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

