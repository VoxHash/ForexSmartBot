"""
Remote Monitoring Server
Provides web-based monitoring interface with real-time alerts and remote control.
"""

from __future__ import annotations

import logging
import os
from collections import deque
from datetime import datetime
from threading import Thread
from typing import Callable, Deque, Dict, List, Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

from .auth_utils import (
    constant_time_equals,
    extract_bearer_or_api_key,
    is_insecure_secret,
    package_version,
    resolve_api_key,
    validate_server_credentials,
)

load_dotenv(override=False)

logger = logging.getLogger(__name__)


class RemoteMonitorServer:
    """Web-based remote monitoring server."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        *,
        max_alerts: int = 100,
        require_api_key: Optional[bool] = None,
    ):
        """
        Initialize remote monitor server.

        Args:
            host: Server host address (defaults to REMOTE_MONITOR_HOST env var or 127.0.0.1)
            port: Server port (defaults to REMOTE_MONITOR_PORT env var or 8080)
            api_key: API key for authentication (defaults to API_KEY env var)
            max_alerts: Ring-buffer size for recent alerts
            require_api_key: Force auth even on localhost when True
        """
        self.host = host or os.getenv("REMOTE_MONITOR_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("REMOTE_MONITOR_PORT", "8080"))
        self.api_key = resolve_api_key(api_key, env_names=("API_KEY", "REMOTE_MONITOR_API_KEY"))
        if require_api_key is None:
            require_api_key = not is_insecure_secret(self.api_key)
        self.require_api_key = require_api_key

        self.app = Flask(__name__)
        CORS(self.app)

        self.trading_data = {
            "balance": 0.0,
            "equity": 0.0,
            "positions": [],
            "trades": [],
            "status": "disconnected",
            "last_update": None,
        }

        self.alert_callbacks: List[Callable] = []
        self.control_callbacks: Dict[str, Callable] = {}
        self._alerts: Deque[Dict] = deque(maxlen=max_alerts)

        self.setup_routes()
        self.server_thread = None
        self.running = False
        self.started_at: Optional[datetime] = None

    def setup_routes(self):
        """Setup Flask routes."""

        @self.app.route("/")
        def index():
            """Serve monitoring dashboard."""
            return render_template_string(self._get_dashboard_html())

        @self.app.route("/healthz", methods=["GET"])
        @self.app.route("/api/v1/health", methods=["GET"])
        def health():
            """Public health endpoint (no trading secrets)."""
            return jsonify(
                {
                    "status": "healthy" if self.running else "starting",
                    "service": "remote_monitor",
                    "version": package_version(),
                    "auth_required": self.require_api_key,
                    "trading_status": self.trading_data.get("status"),
                    "last_update": self.trading_data.get("last_update"),
                    "started_at": self.started_at.isoformat() if self.started_at else None,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        @self.app.route("/api/v1/status", methods=["GET"])
        def get_status():
            """Get trading status."""
            denied = self._auth_response()
            if denied:
                return denied
            return jsonify(self.trading_data)

        @self.app.route("/api/v1/positions", methods=["GET"])
        def get_positions():
            """Get open positions."""
            denied = self._auth_response()
            if denied:
                return denied
            return jsonify({"positions": self.trading_data["positions"]})

        @self.app.route("/api/v1/trades", methods=["GET"])
        def get_trades():
            """Get trade history."""
            denied = self._auth_response()
            if denied:
                return denied
            return jsonify({"trades": self.trading_data["trades"]})

        @self.app.route("/api/v1/control/start", methods=["POST"])
        def control_start():
            """Start trading remotely."""
            denied = self._auth_response()
            if denied:
                return denied
            if "start_trading" in self.control_callbacks:
                result = self.control_callbacks["start_trading"]()
                self.push_alert("info", "Remote start requested", {"result": bool(result)})
                return jsonify({"success": result})
            return jsonify({"error": "Control not available"}), 400

        @self.app.route("/api/v1/control/stop", methods=["POST"])
        def control_stop():
            """Stop trading remotely."""
            denied = self._auth_response()
            if denied:
                return denied
            if "stop_trading" in self.control_callbacks:
                result = self.control_callbacks["stop_trading"]()
                self.push_alert("warning", "Remote stop requested", {"result": bool(result)})
                return jsonify({"success": result})
            return jsonify({"error": "Control not available"}), 400

        @self.app.route("/api/v1/alerts", methods=["GET"])
        def get_alerts():
            """Get recent alerts."""
            denied = self._auth_response()
            if denied:
                return denied
            return jsonify({"alerts": self._get_recent_alerts()})

        @self.app.route("/api/v1/alerts", methods=["POST"])
        def post_alert():
            """Push an alert into the ring buffer (authenticated)."""
            denied = self._auth_response()
            if denied:
                return denied
            data = request.get_json(silent=True) or {}
            level = str(data.get("level", "info"))
            message = str(data.get("message", "")).strip()
            if not message:
                return jsonify({"error": "message required"}), 400
            alert = self.push_alert(level, message, data.get("details") or {})
            return jsonify({"alert": alert}), 201

    def _auth_response(self):
        """Return 401 response tuple when auth fails, else None."""
        if not self._check_auth():
            return jsonify({"error": "Unauthorized"}), 401
        return None

    def _check_auth(self) -> bool:
        """Check API key authentication (Bearer or X-API-Key)."""
        if not self.require_api_key:
            return True
        if is_insecure_secret(self.api_key):
            return False

        token = extract_bearer_or_api_key(
            request.headers.get("Authorization", ""),
            request.headers.get("X-API-Key", ""),
        )
        return constant_time_equals(token, self.api_key)

    def push_alert(
        self, level: str, message: str, details: Optional[Dict] = None
    ) -> Dict:
        """Store an alert and notify registered callbacks."""
        alert = {
            "level": level,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }
        self._alerts.appendleft(alert)
        for callback in list(self.alert_callbacks):
            try:
                callback(alert)
            except Exception as e:
                logger.warning("Alert callback failed: %s", e)
        return alert

    def _get_recent_alerts(self) -> List[Dict]:
        """Get recent alerts (newest first)."""
        return list(self._alerts)

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
        input { padding: 8px; margin: 5px 0; width: 280px; background: #3d3d3d; color: #fff; border: 1px solid #555; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ForexSmartBot Remote Monitor</h1>

        <div class="status-card">
            <h2>API Key</h2>
            <input id="api-key" type="password" placeholder="Bearer / X-API-Key token" />
            <button class="btn" onclick="saveKey()">Save</button>
            <span id="auth-hint" style="color:#aaa;margin-left:8px;"></span>
        </div>

        <div class="status-card">
            <h2>Status</h2>
            <div id="status-indicator" class="status-indicator status-disconnected"></div>
            <span id="status-text">Disconnected</span>
            <div id="health-text" style="color:#aaa;margin-top:8px;"></div>
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
        function authHeaders() {
            const key = sessionStorage.getItem('fsb_api_key') || '';
            const headers = {'Content-Type': 'application/json'};
            if (key) {
                headers['Authorization'] = 'Bearer ' + key;
                headers['X-API-Key'] = key;
            }
            return headers;
        }

        function saveKey() {
            const key = document.getElementById('api-key').value.trim();
            sessionStorage.setItem('fsb_api_key', key);
            document.getElementById('auth-hint').textContent = key ? 'Key saved for this session' : 'Key cleared';
            updateStatus();
        }

        function updateStatus() {
            fetch('/api/v1/health').then(r => r.json()).then(h => {
                document.getElementById('health-text').textContent =
                    'Health: ' + h.status + ' | auth_required=' + h.auth_required + ' | v' + h.version;
            }).catch(() => {});

            fetch('/api/v1/status', {headers: authHeaders()})
                .then(async r => {
                    if (r.status === 401) {
                        document.getElementById('auth-hint').textContent = 'Unauthorized — enter API key';
                        throw new Error('unauthorized');
                    }
                    return r.json();
                })
                .then(data => {
                    document.getElementById('balance').textContent = '$' + Number(data.balance || 0).toFixed(2);
                    document.getElementById('equity').textContent = '$' + Number(data.equity || 0).toFixed(2);
                    document.getElementById('positions-count').textContent = (data.positions || []).length;
                    document.getElementById('trades-count').textContent = (data.trades || []).length;

                    const indicator = document.getElementById('status-indicator');
                    const statusText = document.getElementById('status-text');
                    if (data.status === 'connected') {
                        indicator.className = 'status-indicator status-connected';
                        statusText.textContent = 'Connected';
                    } else {
                        indicator.className = 'status-indicator status-disconnected';
                        statusText.textContent = 'Disconnected';
                    }

                    const tbody = document.getElementById('positions-body');
                    tbody.innerHTML = (data.positions || []).map(pos => `
                        <tr>
                            <td>${pos.symbol}</td>
                            <td>${pos.side}</td>
                            <td>${Number(pos.entry_price).toFixed(4)}</td>
                            <td>${Number(pos.current_price).toFixed(4)}</td>
                            <td>$${Number(pos.pnl || 0).toFixed(2)}</td>
                        </tr>
                    `).join('');
                })
                .catch(err => console.error('Error:', err));
        }

        function startTrading() {
            fetch('/api/v1/control/start', {method: 'POST', headers: authHeaders()})
                .then(r => r.json())
                .then(data => alert(data.success ? 'Trading started' : (data.error || 'Failed to start')));
        }

        function stopTrading() {
            fetch('/api/v1/control/stop', {method: 'POST', headers: authHeaders()})
                .then(r => r.json())
                .then(data => alert(data.success ? 'Trading stopped' : (data.error || 'Failed to stop')));
        }

        const existing = sessionStorage.getItem('fsb_api_key');
        if (existing) document.getElementById('api-key').value = existing;
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
        self.trading_data["last_update"] = datetime.now().isoformat()

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

        validate_server_credentials(
            self.api_key,
            host=self.host,
            service_name="RemoteMonitorServer",
        )

        self.running = True
        self.started_at = datetime.now()
        self.server_thread = Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        logger.info("Remote monitor server started on http://%s:%s", self.host, self.port)
        print(f"Remote monitor server started on http://{self.host}:{self.port}")

    def stop(self):
        """Stop the monitoring server."""
        self.running = False
        print("Remote monitor server stopped")

    def _run_server(self):
        """Run Flask server in thread."""
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
