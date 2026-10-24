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
from typing import Any, Callable, Deque, Dict, List, Optional

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
from .companion_api import CompanionAPI

load_dotenv(override=False)

logger = logging.getLogger(__name__)


class RemoteMonitorServer:
    """Web-based remote monitoring server with strategy health + companion API."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        *,
        max_alerts: int = 100,
        require_api_key: Optional[bool] = None,
        strategy_monitor: Optional[Any] = None,
        enable_companion: bool = True,
    ):
        """
        Initialize remote monitor server.

        Args:
            host: Server host address (defaults to REMOTE_MONITOR_HOST env var or 127.0.0.1)
            port: Server port (defaults to REMOTE_MONITOR_PORT env var or 8080)
            api_key: API key for authentication (defaults to API_KEY env var)
            max_alerts: Ring-buffer size for recent alerts
            require_api_key: Force auth even on localhost when True
            strategy_monitor: Optional StrategyMonitor for health dashboard
            enable_companion: Mount read-only /api/v1/companion/* routes
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
        self.strategy_monitor = strategy_monitor
        self.companion: Optional[CompanionAPI] = None

        self.setup_routes()
        if enable_companion:
            self._mount_companion()
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

        @self.app.route("/api/v1/strategies", methods=["GET"])
        def get_strategies():
            """Strategy health dashboard payload (authenticated)."""
            denied = self._auth_response()
            if denied:
                return denied
            return jsonify(self._strategies_payload())

        @self.app.route("/api/v1/strategies/history", methods=["GET"])
        def get_strategies_history():
            """All strategy metrics history for charts (authenticated)."""
            denied = self._auth_response()
            if denied:
                return denied
            return jsonify(self._history_payload(None))

        @self.app.route("/api/v1/strategies/<strategy_name>/history", methods=["GET"])
        def get_strategy_history(strategy_name: str):
            """Single strategy metrics history (authenticated)."""
            denied = self._auth_response()
            if denied:
                return denied
            return jsonify(self._history_payload(strategy_name))

        @self.app.route("/api/v1/strategies/<strategy_name>", methods=["GET"])
        def get_strategy(strategy_name: str):
            """Single strategy health (authenticated)."""
            denied = self._auth_response()
            if denied:
                return denied
            payload = self._strategies_payload()
            strategies = payload.get("strategies") or {}
            if strategy_name not in strategies:
                return jsonify({"error": "strategy not found"}), 404
            return jsonify({"strategy": strategies[strategy_name], "timestamp": payload.get("timestamp")})

    def _mount_companion(self) -> None:
        """Mount companion API on the same Flask app."""
        from .companion_api import resolve_companion_cert_pin

        public = (
            os.getenv("FSB_PUBLIC_BASE_URL")
            or os.getenv("COMPANION_PUBLIC_BASE_URL")
            or f"http://{self.host}:{self.port}"
        ).rstrip("/")
        self.companion = CompanionAPI(
            app=self.app,
            api_key=self.api_key,
            require_api_key=self.require_api_key,
            portfolio_provider=lambda: self.trading_data,
            alerts_provider=self._get_recent_alerts,
            strategies_provider=self._strategies_payload,
            history_provider=lambda name, limit: self._history_payload(name, limit),
            allow_control=False,
            public_base_url=public,
            pin_sha256=resolve_companion_cert_pin(),
        )

    def set_strategy_monitor(self, monitor: Any) -> None:
        """Attach a StrategyMonitor for /api/v1/strategies and companion clients."""
        self.strategy_monitor = monitor
        if self.companion is not None:
            self.companion.set_history_provider(
                lambda name, limit: self._history_payload(name, limit)
            )

    def register_control_callback(self, action: str, callback: Callable):
        """
        Register callback for remote control actions.

        Args:
            action: Action name ('start_trading', 'stop_trading', etc.)
            callback: Callback function
        """
        self.control_callbacks[action] = callback
        if self.companion is not None:
            self.companion.register_control_callback(action, callback)

    def _strategies_payload(self) -> Dict:
        """Build strategy health JSON for dashboard / companion."""
        if self.strategy_monitor is not None and hasattr(
            self.strategy_monitor, "get_dashboard_payload"
        ):
            payload = self.strategy_monitor.get_dashboard_payload()
        elif self.strategy_monitor is not None and hasattr(
            self.strategy_monitor, "get_strategy_statuses"
        ):
            strategies = self.strategy_monitor.get_strategy_statuses()
            payload = {
                "strategies": strategies,
                "summary": {"total": len(strategies), "by_status": {}},
            }
        else:
            payload = {"strategies": {}, "summary": {"total": 0, "by_status": {}}}
        payload["timestamp"] = datetime.now().isoformat()
        return payload

    def _history_payload(
        self, strategy_name: Optional[str] = None, limit: int = 100
    ) -> Dict:
        """Build strategy history JSON for charts."""
        try:
            from flask import has_request_context

            if has_request_context() and request.args.get("limit") is not None:
                limit = int(request.args.get("limit"))
        except (TypeError, ValueError):
            pass
        if self.strategy_monitor is not None and hasattr(
            self.strategy_monitor, "get_history_payload"
        ):
            return self.strategy_monitor.get_history_payload(strategy_name, limit=limit)
        if strategy_name:
            return {
                "strategy": strategy_name,
                "history": [],
                "count": 0,
                "timestamp": datetime.now().isoformat(),
            }
        return {
            "histories": {},
            "count": 0,
            "timestamp": datetime.now().isoformat(),
        }

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
        .health-healthy { color: #4CAF50; }
        .health-warning { color: #FFC107; }
        .health-critical { color: #f44336; }
        .health-unknown { color: #9e9e9e; }
        .badge { display:inline-block; padding:2px 8px; border-radius:4px; background:#444; font-size:12px; }
        .chart-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px; margin-top:12px; }
        .chart-card { background:#3d3d3d; padding:12px; border-radius:6px; }
        .chart-card h3 { margin:0 0 8px; font-size:14px; color:#ccc; }
        canvas.spark { width:100%; height:80px; background:#2a2a2a; border-radius:4px; }
        #pairing-qr { background:#fff; padding:12px; display:inline-block; border-radius:8px; }
        #pairing-text { width:100%; min-height:72px; font-family:monospace; font-size:12px; }
        .action-row button { margin-right:6px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ForexSmartBot Remote Monitor</h1>
        <p style="color:#aaa;">Strategy health + history charts + companion pairing / approve-reject at <code>/api/v1/companion/*</code> · multi-host health poll</p>

        <div class="status-card">
            <h2>API Key</h2>
            <input id="api-key" type="password" placeholder="Bearer / X-API-Key token" />
            <button class="btn" onclick="saveKey()">Save</button>
            <span id="auth-hint" style="color:#aaa;margin-left:8px;"></span>
        </div>

        <div class="status-card">
            <h2>Multi-Host Monitors</h2>
            <p style="color:#aaa;">Poll additional remote-monitor hosts (browser-side). Keys stay in this browser session only.</p>
            <input id="remote-host-url" type="text" placeholder="https://host:8080" style="width:360px;" />
            <input id="remote-host-key" type="password" placeholder="API key (optional)" style="width:200px;" />
            <button class="btn" onclick="addRemoteHost()">Add host</button>
            <button class="btn" onclick="refreshRemoteHosts()">Refresh</button>
            <table id="remote-hosts-table" style="margin-top:12px;">
                <thead>
                    <tr>
                        <th>Host</th>
                        <th>Health</th>
                        <th>Version</th>
                        <th>Strategies</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody id="remote-hosts-body"></tbody>
            </table>
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
            <div class="data-item">
                <div class="data-label">Strategies</div>
                <div class="data-value" id="strategies-count">0</div>
            </div>
        </div>

        <div class="status-card">
            <h2>Strategy Health</h2>
            <div id="strategy-summary" style="color:#aaa;margin-bottom:10px;"></div>
            <table id="strategies-table">
                <thead>
                    <tr>
                        <th>Strategy</th>
                        <th>Status</th>
                        <th>Signals</th>
                        <th>Errors</th>
                        <th>Avg ms</th>
                        <th>Last signal</th>
                    </tr>
                </thead>
                <tbody id="strategies-body"></tbody>
            </table>
            <h2 style="margin-top:20px;">History Charts</h2>
            <div id="history-charts" class="chart-grid"></div>
        </div>

        <div class="status-card">
            <h2>Companion Pairing (QR)</h2>
            <p style="color:#aaa;">Create a short-lived session; scan or paste on the Android companion.</p>
            <button class="btn btn-start" onclick="createPairing()">Create pairing QR</button>
            <div id="pairing-meta" style="color:#aaa;margin:8px 0;"></div>
            <div id="pairing-qr"></div>
            <textarea id="pairing-text" readonly placeholder="QR JSON payload appears here"></textarea>
        </div>

        <div class="status-card">
            <h2>Pending Companion Actions</h2>
            <p style="color:#aaa;">Phone-requested start/stop/pause — approve or reject on this host.</p>
            <div id="actions-list" style="color:#aaa;">No pending actions</div>
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

    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
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

        function loadRemoteHosts() {
            try {
                return JSON.parse(localStorage.getItem('fsb_remote_hosts') || '[]');
            } catch (e) {
                return [];
            }
        }

        function saveRemoteHosts(hosts) {
            localStorage.setItem('fsb_remote_hosts', JSON.stringify(hosts || []));
        }

        function addRemoteHost() {
            const url = document.getElementById('remote-host-url').value.trim().replace(/\\/$/, '');
            const key = document.getElementById('remote-host-key').value.trim();
            if (!url) return alert('Enter a host base URL');
            const hosts = loadRemoteHosts().filter(h => h.url !== url);
            hosts.push({url: url, key: key});
            saveRemoteHosts(hosts);
            document.getElementById('remote-host-url').value = '';
            document.getElementById('remote-host-key').value = '';
            refreshRemoteHosts();
        }

        function removeRemoteHost(url) {
            saveRemoteHosts(loadRemoteHosts().filter(h => h.url !== url));
            refreshRemoteHosts();
        }

        function refreshRemoteHosts() {
            const hosts = loadRemoteHosts();
            const tbody = document.getElementById('remote-hosts-body');
            if (!hosts.length) {
                tbody.innerHTML = '<tr><td colspan="5" style="color:#888;">No remote hosts — add a monitor URL</td></tr>';
                return;
            }
            tbody.innerHTML = hosts.map(h =>
                '<tr data-url="' + h.url + '">' +
                '<td>' + h.url + '</td>' +
                '<td class="host-health">…</td>' +
                '<td class="host-version">…</td>' +
                '<td class="host-strats">…</td>' +
                '<td><button class="btn btn-stop" onclick="removeRemoteHost(\\'' + h.url.replace(/'/g, '') + '\\')">Remove</button></td>' +
                '</tr>'
            ).join('');
            hosts.forEach(h => {
                const headers = {'Content-Type': 'application/json'};
                if (h.key) {
                    headers['Authorization'] = 'Bearer ' + h.key;
                    headers['X-API-Key'] = h.key;
                }
                const row = tbody.querySelector('tr[data-url="' + h.url + '"]');
                if (!row) return;
                fetch(h.url + '/api/v1/health').then(r => r.json()).then(health => {
                    row.querySelector('.host-health').textContent = health.status || 'ok';
                    row.querySelector('.host-health').className = 'host-health ' +
                        (health.status === 'healthy' ? 'health-healthy' : 'health-warning');
                    row.querySelector('.host-version').textContent = health.version || '—';
                }).catch(() => {
                    row.querySelector('.host-health').textContent = 'unreachable';
                    row.querySelector('.host-health').className = 'host-health health-critical';
                    row.querySelector('.host-version').textContent = '—';
                    row.querySelector('.host-strats').textContent = '—';
                });
                fetch(h.url + '/api/v1/strategies', {headers: headers}).then(async r => {
                    if (!r.ok) throw new Error('auth');
                    return r.json();
                }).then(data => {
                    const total = (data.summary && data.summary.total) ||
                        Object.keys(data.strategies || {}).length;
                    row.querySelector('.host-strats').textContent = String(total);
                }).catch(() => {
                    row.querySelector('.host-strats').textContent = 'n/a';
                });
            });
        }

        function statusClass(status) {
            const s = (status || 'unknown').toLowerCase();
            if (s === 'healthy') return 'health-healthy';
            if (s === 'warning') return 'health-warning';
            if (s === 'critical') return 'health-critical';
            return 'health-unknown';
        }

        function drawSpark(canvas, series, key, color) {
            const ctx = canvas.getContext('2d');
            const w = canvas.width = canvas.clientWidth * (window.devicePixelRatio || 1);
            const h = canvas.height = 80 * (window.devicePixelRatio || 1);
            ctx.clearRect(0, 0, w, h);
            const vals = (series || []).map(p => Number(p[key] || 0));
            if (vals.length < 2) {
                ctx.fillStyle = '#666';
                ctx.font = '12px sans-serif';
                ctx.fillText('Not enough samples', 8, h/2);
                return;
            }
            const min = Math.min(...vals), max = Math.max(...vals);
            const span = (max - min) || 1;
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            vals.forEach((v, i) => {
                const x = (i / (vals.length - 1)) * (w - 4) + 2;
                const y = h - 4 - ((v - min) / span) * (h - 8);
                if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            });
            ctx.stroke();
        }

        function updateHistoryCharts() {
            fetch('/api/v1/strategies/history?limit=80', {headers: authHeaders()})
                .then(async r => {
                    if (r.status === 401) throw new Error('unauthorized');
                    return r.json();
                })
                .then(data => {
                    const histories = data.histories || {};
                    const root = document.getElementById('history-charts');
                    const names = Object.keys(histories);
                    if (!names.length) {
                        root.innerHTML = '<div style="color:#888;">No history yet — signals populate charts</div>';
                        return;
                    }
                    root.innerHTML = names.map(name => {
                        const id = 'spark-' + name.replace(/[^a-zA-Z0-9_-]/g, '_');
                        return '<div class="chart-card"><h3>' + name + ' · signals</h3>' +
                            '<canvas class="spark" id="' + id + '"></canvas></div>';
                    }).join('');
                    names.forEach(name => {
                        const id = 'spark-' + name.replace(/[^a-zA-Z0-9_-]/g, '_');
                        const el = document.getElementById(id);
                        if (el) drawSpark(el, histories[name], 'signal_count', '#4CAF50');
                    });
                })
                .catch(() => {});
        }

        function updateStrategies() {
            fetch('/api/v1/strategies', {headers: authHeaders()})
                .then(async r => {
                    if (r.status === 401) throw new Error('unauthorized');
                    return r.json();
                })
                .then(data => {
                    const strategies = data.strategies || {};
                    const names = Object.keys(strategies);
                    document.getElementById('strategies-count').textContent = names.length;
                    const by = (data.summary && data.summary.by_status) || {};
                    document.getElementById('strategy-summary').textContent =
                        'Total ' + names.length + ' | ' +
                        Object.keys(by).map(k => k + '=' + by[k]).join(' · ');
                    const tbody = document.getElementById('strategies-body');
                    if (!names.length) {
                        tbody.innerHTML = '<tr><td colspan="6" style="color:#888;">No strategies registered — attach StrategyMonitor</td></tr>';
                        return;
                    }
                    tbody.innerHTML = names.map(name => {
                        const s = strategies[name] || {};
                        const st = s.status || 'unknown';
                        return '<tr>' +
                            '<td>' + (s.strategy_name || name) + '</td>' +
                            '<td class="' + statusClass(st) + '"><span class="badge">' + st + '</span></td>' +
                            '<td>' + (s.signal_count || 0) + '</td>' +
                            '<td>' + (s.error_count || 0) + '</td>' +
                            '<td>' + Number(s.execution_time_avg || 0).toFixed(2) + '</td>' +
                            '<td>' + (s.last_signal_time || '—') + '</td>' +
                            '</tr>';
                    }).join('');
                })
                .catch(() => {});
            updateHistoryCharts();
            updateActions();
        }

        function createPairing() {
            fetch('/api/v1/companion/pairing/session', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({}),
            })
            .then(async r => {
                if (r.status === 401) throw new Error('unauthorized');
                return r.json();
            })
            .then(data => {
                const text = data.qr_text || JSON.stringify(data.qr_payload || {});
                document.getElementById('pairing-text').value = text;
                document.getElementById('pairing-meta').textContent =
                    'Code ' + data.pairing_code + ' · expires ' + data.expires_at +
                    ' · TTL ' + data.ttl_seconds + 's';
                const box = document.getElementById('pairing-qr');
                box.innerHTML = '';
                if (window.QRCode) {
                    new QRCode(box, { text: text, width: 192, height: 192 });
                } else {
                    box.textContent = 'QR library unavailable — copy JSON below';
                }
            })
            .catch(err => alert('Pairing failed: ' + err));
        }

        function updateActions() {
            fetch('/api/v1/companion/actions', {headers: authHeaders()})
                .then(async r => {
                    if (r.status === 401) throw new Error('unauthorized');
                    return r.json();
                })
                .then(data => {
                    const pending = data.pending || [];
                    const root = document.getElementById('actions-list');
                    if (!pending.length) {
                        root.innerHTML = 'No pending actions';
                        return;
                    }
                    root.innerHTML = pending.map(a =>
                        '<div class="action-row" style="margin:8px 0;">' +
                        '<span class="badge">' + a.action + '</span> ' +
                        '<span style="color:#aaa;">' + a.id.slice(0,8) + ' · ' + a.requested_by + ' · ' + a.created_at + '</span> ' +
                        '<button class="btn btn-start" onclick="resolveAction(\\'' + a.id + '\\', true)">Approve</button>' +
                        '<button class="btn btn-stop" onclick="resolveAction(\\'' + a.id + '\\', false)">Reject</button>' +
                        '</div>'
                    ).join('');
                })
                .catch(() => {});
        }

        function resolveAction(id, approve) {
            const path = approve ? 'approve' : 'reject';
            fetch('/api/v1/companion/actions/' + id + '/' + path, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify(approve ? {} : {reason: 'rejected from dashboard'}),
            })
            .then(r => r.json())
            .then(() => updateActions())
            .catch(err => alert(err));
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

            updateStrategies();
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
        setInterval(refreshRemoteHosts, 15000);
        updateStatus();
        refreshRemoteHosts();
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
