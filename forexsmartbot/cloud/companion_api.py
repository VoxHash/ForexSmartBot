"""
Read-only companion API for mobile / web monitoring clients.

Designed for GrapheneOS-friendly clients: Bearer / X-API-Key auth, local-first
polling, optional HTTP webhook alerts (no Google Play Services / FCM required).
Broker keys and order routing stay on the desktop host.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request

from .auth_utils import (
    constant_time_equals,
    extract_bearer_or_api_key,
    is_insecure_secret,
    package_version,
    resolve_api_key,
)

logger = logging.getLogger(__name__)

PortfolioProvider = Callable[[], Dict[str, Any]]
AlertsProvider = Callable[[], List[Dict[str, Any]]]
StrategiesProvider = Callable[[], Dict[str, Any]]


def _normalize_portfolio(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize host trading snapshot for companion clients."""
    positions = raw.get("positions") or []
    if isinstance(positions, dict):
        positions = list(positions.values())
    trades = raw.get("trades") or []
    return {
        "balance": float(raw.get("balance") or 0.0),
        "equity": float(raw.get("equity") or raw.get("balance") or 0.0),
        "status": str(raw.get("status") or "disconnected"),
        "positions_count": len(positions),
        "trades_count": len(trades),
        "positions": positions,
        "last_update": raw.get("last_update"),
        "timestamp": datetime.now().isoformat(),
        "read_only": True,
    }


class WebhookNotifier:
    """
    Deliver alert payloads to registered HTTPS (or localhost HTTP) webhook URLs.

    Prefer this over FCM on hardened Android / GrapheneOS builds.
    """

    def __init__(self, *, timeout: float = 5.0, max_endpoints: int = 32):
        self.timeout = timeout
        self.max_endpoints = max_endpoints
        self._endpoints: List[str] = []
        self._lock = threading.Lock()

    @staticmethod
    def _validate_url(url: str) -> Optional[str]:
        cleaned = (url or "").strip()
        if not cleaned or len(cleaned) > 2048:
            return None
        parsed = urlparse(cleaned)
        if parsed.scheme not in {"https", "http"}:
            return None
        if parsed.scheme == "http":
            host = (parsed.hostname or "").lower()
            if host not in {"127.0.0.1", "localhost", "::1"}:
                return None
        if not parsed.netloc:
            return None
        return cleaned

    def register(self, url: str) -> bool:
        """Register a webhook endpoint. Returns False if invalid or at capacity."""
        cleaned = self._validate_url(url)
        if not cleaned:
            return False
        with self._lock:
            if cleaned in self._endpoints:
                return True
            if len(self._endpoints) >= self.max_endpoints:
                return False
            self._endpoints.append(cleaned)
            return True

    def unregister(self, url: str) -> bool:
        cleaned = (url or "").strip()
        with self._lock:
            if cleaned in self._endpoints:
                self._endpoints.remove(cleaned)
                return True
        return False

    def list_endpoints(self) -> List[str]:
        with self._lock:
            return list(self._endpoints)

    def notify(self, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> int:
        """POST JSON alert to all endpoints. Returns success count."""
        payload = {
            "title": title,
            "body": body,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "source": "forexsmartbot.companion",
        }
        ok = 0
        for url in self.list_endpoints():
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                if 200 <= resp.status_code < 300:
                    ok += 1
                else:
                    logger.warning("Webhook %s returned %s", url, resp.status_code)
            except Exception as exc:
                logger.warning("Webhook notify failed for %s: %s", url, exc)
        return ok


class CompanionAPI:
    """
    Read-only companion REST surface for phones and external dashboards.

    Mounts under ``/api/v1/companion/*`` on an existing or new Flask app.
    """

    def __init__(
        self,
        app: Optional[Flask] = None,
        *,
        api_key: Optional[str] = None,
        require_api_key: Optional[bool] = None,
        portfolio_provider: Optional[PortfolioProvider] = None,
        alerts_provider: Optional[AlertsProvider] = None,
        strategies_provider: Optional[StrategiesProvider] = None,
        allow_control: bool = False,
        url_prefix: str = "/api/v1/companion",
    ):
        self.app = app or Flask(__name__)
        self.api_key = resolve_api_key(
            api_key, env_names=("API_KEY", "REMOTE_MONITOR_API_KEY", "COMPANION_API_KEY")
        )
        if require_api_key is None:
            require_api_key = not is_insecure_secret(self.api_key)
        self.require_api_key = require_api_key
        self.allow_control = allow_control
        self.url_prefix = url_prefix.rstrip("/") or "/api/v1/companion"

        self._portfolio_provider = portfolio_provider or (lambda: {})
        self._alerts_provider = alerts_provider or (lambda: [])
        self._strategies_provider = strategies_provider or (lambda: {"strategies": {}})
        self.webhook_notifier = WebhookNotifier()
        self.control_callbacks: Dict[str, Callable[[], bool]] = {}

        self.setup_routes()

    def set_portfolio_provider(self, provider: PortfolioProvider) -> None:
        self._portfolio_provider = provider

    def set_alerts_provider(self, provider: AlertsProvider) -> None:
        self._alerts_provider = provider

    def set_strategies_provider(self, provider: StrategiesProvider) -> None:
        self._strategies_provider = provider

    def register_control_callback(self, action: str, callback: Callable[[], bool]) -> None:
        """Register optional start/stop callbacks (disabled unless allow_control)."""
        self.control_callbacks[action] = callback

    def _auth_response(self):
        if not self._check_auth():
            return jsonify({"error": "Unauthorized"}), 401
        return None

    def _check_auth(self) -> bool:
        if not self.require_api_key:
            return True
        if is_insecure_secret(self.api_key):
            return False
        token = extract_bearer_or_api_key(
            request.headers.get("Authorization", ""),
            request.headers.get("X-API-Key", ""),
        )
        return constant_time_equals(token, self.api_key)

    def setup_routes(self) -> None:
        prefix = self.url_prefix

        @self.app.route(f"{prefix}/health", methods=["GET"])
        def companion_health():
            """Public companion health (no trading secrets)."""
            return jsonify(
                {
                    "status": "healthy",
                    "service": "companion",
                    "version": package_version(),
                    "auth_required": self.require_api_key,
                    "read_only": not self.allow_control,
                    "features": {
                        "portfolio": True,
                        "alerts": True,
                        "strategies": True,
                        "webhooks": True,
                        "control": self.allow_control,
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

        @self.app.route(f"{prefix}/portfolio", methods=["GET"])
        def companion_portfolio():
            denied = self._auth_response()
            if denied:
                return denied
            try:
                return jsonify(_normalize_portfolio(self._portfolio_provider() or {}))
            except Exception as exc:
                logger.exception("Companion portfolio failed")
                return jsonify({"error": str(exc)}), 500

        @self.app.route(f"{prefix}/positions", methods=["GET"])
        def companion_positions():
            denied = self._auth_response()
            if denied:
                return denied
            try:
                snapshot = _normalize_portfolio(self._portfolio_provider() or {})
                return jsonify(
                    {
                        "positions": snapshot["positions"],
                        "count": snapshot["positions_count"],
                        "timestamp": snapshot["timestamp"],
                        "read_only": True,
                    }
                )
            except Exception as exc:
                return jsonify({"error": str(exc)}), 500

        @self.app.route(f"{prefix}/alerts", methods=["GET"])
        def companion_alerts():
            denied = self._auth_response()
            if denied:
                return denied
            try:
                alerts = self._alerts_provider() or []
                return jsonify({"alerts": list(alerts), "count": len(alerts)})
            except Exception as exc:
                return jsonify({"error": str(exc)}), 500

        @self.app.route(f"{prefix}/strategies", methods=["GET"])
        def companion_strategies():
            denied = self._auth_response()
            if denied:
                return denied
            try:
                payload = self._strategies_provider() or {}
                if "strategies" not in payload:
                    payload = {"strategies": payload}
                payload["timestamp"] = datetime.now().isoformat()
                return jsonify(payload)
            except Exception as exc:
                return jsonify({"error": str(exc)}), 500

        @self.app.route(f"{prefix}/devices/webhook", methods=["POST"])
        def register_webhook():
            denied = self._auth_response()
            if denied:
                return denied
            data = request.get_json(silent=True) or {}
            url = str(data.get("url") or data.get("webhook_url") or "").strip()
            if not self.webhook_notifier.register(url):
                return jsonify(
                    {
                        "error": "Invalid webhook URL. Use https://… or http://127.0.0.1/…",
                    }
                ), 400
            return jsonify(
                {
                    "success": True,
                    "endpoints": self.webhook_notifier.list_endpoints(),
                }
            ), 201

        @self.app.route(f"{prefix}/devices/webhook", methods=["DELETE"])
        def unregister_webhook():
            denied = self._auth_response()
            if denied:
                return denied
            data = request.get_json(silent=True) or {}
            url = str(data.get("url") or data.get("webhook_url") or "").strip()
            removed = self.webhook_notifier.unregister(url)
            return jsonify({"success": removed})

        if self.allow_control:

            @self.app.route(f"{prefix}/control/start", methods=["POST"])
            def companion_start():
                denied = self._auth_response()
                if denied:
                    return denied
                cb = self.control_callbacks.get("start_trading")
                if not cb:
                    return jsonify({"error": "Control not available"}), 400
                return jsonify({"success": bool(cb())})

            @self.app.route(f"{prefix}/control/stop", methods=["POST"])
            def companion_stop():
                denied = self._auth_response()
                if denied:
                    return denied
                cb = self.control_callbacks.get("stop_trading")
                if not cb:
                    return jsonify({"error": "Control not available"}), 400
                return jsonify({"success": bool(cb())})
