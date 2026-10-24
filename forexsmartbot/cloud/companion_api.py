"""
Read-only companion API for mobile / web monitoring clients.

Designed for GrapheneOS-friendly clients: Bearer / X-API-Key auth, local-first
polling, optional HTTP webhook alerts (no Google Play Services / FCM required).
Broker keys and order routing stay on the desktop host.
"""

from __future__ import annotations

import json
import logging
import secrets
import threading
import uuid
from datetime import datetime, timedelta
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
HistoryProvider = Callable[[Optional[str], int], Dict[str, Any]]

PAIRING_SCHEME = "fsb-companion"
PAIRING_TTL_SECONDS = 300
ALLOWED_ACTIONS = frozenset({"start_trading", "stop_trading", "pause_trading"})


def normalize_cert_pin(pin: Optional[str]) -> str:
    """Normalize SPKI pin to ``sha256/...`` form (empty string if unset)."""
    value = (pin or "").strip()
    if not value:
        return ""
    if value.startswith("sha256/"):
        return value
    return f"sha256/{value}"


def resolve_companion_cert_pin(explicit: Optional[str] = None) -> str:
    """
    Production cert-pin default for pairing QR payloads.

    Order: explicit arg → ``FSB_COMPANION_CERT_PIN`` → ``COMPANION_CERT_PIN``.
    """
    import os

    if explicit and str(explicit).strip():
        return normalize_cert_pin(str(explicit))
    return normalize_cert_pin(
        os.getenv("FSB_COMPANION_CERT_PIN") or os.getenv("COMPANION_CERT_PIN") or ""
    )



class CompanionActionQueue:
    """Pending high-level companion actions awaiting host approve/reject."""

    def __init__(self, *, max_pending: int = 64):
        self.max_pending = max_pending
        self._lock = threading.Lock()
        self._items: Dict[str, Dict[str, Any]] = {}

    def request(self, action: str, *, requested_by: str = "companion") -> Optional[Dict[str, Any]]:
        action = (action or "").strip()
        if action not in ALLOWED_ACTIONS:
            return None
        with self._lock:
            pending = [i for i in self._items.values() if i["status"] == "pending"]
            if len(pending) >= self.max_pending:
                return None
            item_id = uuid.uuid4().hex
            item = {
                "id": item_id,
                "action": action,
                "status": "pending",
                "requested_by": requested_by,
                "created_at": datetime.now().isoformat(),
                "resolved_at": None,
                "reason": None,
            }
            self._items[item_id] = item
            return dict(item)

    def list_pending(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(i) for i in self._items.values() if i["status"] == "pending"]

    def get(self, action_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            item = self._items.get(action_id)
            return dict(item) if item else None

    def resolve(
        self, action_id: str, *, approve: bool, reason: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            item = self._items.get(action_id)
            if not item or item["status"] != "pending":
                return None
            item["status"] = "approved" if approve else "rejected"
            item["resolved_at"] = datetime.now().isoformat()
            item["reason"] = reason
            return dict(item)


class CompanionPairingStore:
    """Short-lived pairing sessions for QR onboarding (phone redeems without prior key)."""

    def __init__(self, *, ttl_seconds: int = PAIRING_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create(
        self,
        *,
        base_url: str,
        api_key: str,
        pin_sha256: Optional[str] = None,
    ) -> Dict[str, Any]:
        code = secrets.token_urlsafe(12)
        expires = datetime.now() + timedelta(seconds=self.ttl_seconds)
        payload = {
            "v": 1,
            "scheme": PAIRING_SCHEME,
            "base_url": base_url.rstrip("/"),
            "pairing_code": code,
            "expires_at": expires.isoformat(),
            "pin_sha256": pin_sha256 or "",
        }
        with self._lock:
            self._sessions[code] = {
                "api_key": api_key,
                "base_url": base_url.rstrip("/"),
                "pin_sha256": pin_sha256 or "",
                "expires_at": expires,
                "redeemed": False,
            }
            # Drop expired
            now = datetime.now()
            dead = [k for k, v in self._sessions.items() if v["expires_at"] < now]
            for k in dead:
                del self._sessions[k]
        return {
            "pairing_code": code,
            "expires_at": expires.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "qr_payload": payload,
            "qr_text": json.dumps(payload, separators=(",", ":")),
        }

    def redeem(self, pairing_code: str) -> Optional[Dict[str, Any]]:
        code = (pairing_code or "").strip()
        with self._lock:
            session = self._sessions.get(code)
            if not session:
                return None
            if session["expires_at"] < datetime.now() or session["redeemed"]:
                self._sessions.pop(code, None)
                return None
            session["redeemed"] = True
            return {
                "scheme": PAIRING_SCHEME,
                "base_url": session["base_url"],
                "api_key": session["api_key"],
                "pin_sha256": session["pin_sha256"],
                "redeemed_at": datetime.now().isoformat(),
            }


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
        history_provider: Optional[HistoryProvider] = None,
        allow_control: bool = False,
        public_base_url: Optional[str] = None,
        pin_sha256: Optional[str] = None,
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
        self.public_base_url = (public_base_url or "").rstrip("/")
        self.pin_sha256 = resolve_companion_cert_pin(pin_sha256)
        self.url_prefix = url_prefix.rstrip("/") or "/api/v1/companion"

        self._portfolio_provider = portfolio_provider or (lambda: {})
        self._alerts_provider = alerts_provider or (lambda: [])
        self._strategies_provider = strategies_provider or (lambda: {"strategies": {}})
        self._history_provider = history_provider
        self.webhook_notifier = WebhookNotifier()
        self.control_callbacks: Dict[str, Callable[[], bool]] = {}
        self.action_queue = CompanionActionQueue()
        self.pairing_store = CompanionPairingStore()

        self.setup_routes()

    def set_portfolio_provider(self, provider: PortfolioProvider) -> None:
        self._portfolio_provider = provider

    def set_alerts_provider(self, provider: AlertsProvider) -> None:
        self._alerts_provider = provider

    def set_strategies_provider(self, provider: StrategiesProvider) -> None:
        self._strategies_provider = provider

    def set_history_provider(self, provider: HistoryProvider) -> None:
        self._history_provider = provider

    def set_public_base_url(self, base_url: str) -> None:
        self.public_base_url = (base_url or "").rstrip("/")

    def register_control_callback(self, action: str, callback: Callable[[], bool]) -> None:
        """Register optional start/stop callbacks (used on approve or allow_control)."""
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
                        "history": self._history_provider is not None,
                        "webhooks": True,
                        "pairing": True,
                        "actions": True,
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

        @self.app.route(f"{prefix}/strategies/history", methods=["GET"])
        def companion_strategies_history():
            denied = self._auth_response()
            if denied:
                return denied
            if not self._history_provider:
                return jsonify({"error": "History not available"}), 404
            try:
                limit = int(request.args.get("limit", 100))
                return jsonify(self._history_provider(None, limit))
            except Exception as exc:
                return jsonify({"error": str(exc)}), 500

        @self.app.route(f"{prefix}/strategies/<strategy_name>/history", methods=["GET"])
        def companion_strategy_history(strategy_name: str):
            denied = self._auth_response()
            if denied:
                return denied
            if not self._history_provider:
                return jsonify({"error": "History not available"}), 404
            try:
                limit = int(request.args.get("limit", 100))
                return jsonify(self._history_provider(strategy_name, limit))
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

        @self.app.route(f"{prefix}/pairing/session", methods=["POST"])
        def pairing_session():
            """Create QR pairing payload (authenticated host)."""
            denied = self._auth_response()
            if denied:
                return denied
            data = request.get_json(silent=True) or {}
            base = str(
                data.get("base_url")
                or self.public_base_url
                or request.host_url.rstrip("/")
            ).rstrip("/")
            pin = resolve_companion_cert_pin(
                str(data.get("pin_sha256") or self.pin_sha256 or "").strip() or None
            )
            session = self.pairing_store.create(
                base_url=base, api_key=self.api_key, pin_sha256=pin or None
            )
            return jsonify(session), 201

        @self.app.route(f"{prefix}/pairing/redeem", methods=["POST"])
        def pairing_redeem():
            """Phone redeems short-lived pairing code (no prior API key)."""
            data = request.get_json(silent=True) or {}
            code = str(data.get("pairing_code") or data.get("code") or "").strip()
            result = self.pairing_store.redeem(code)
            if not result:
                return jsonify({"error": "Invalid or expired pairing code"}), 400
            return jsonify(result)

        @self.app.route(f"{prefix}/actions", methods=["GET"])
        def list_actions():
            denied = self._auth_response()
            if denied:
                return denied
            pending = self.action_queue.list_pending()
            return jsonify({"pending": pending, "count": len(pending)})

        @self.app.route(f"{prefix}/actions", methods=["POST"])
        def request_action():
            """Phone requests a high-level action (queued until host approves)."""
            denied = self._auth_response()
            if denied:
                return denied
            data = request.get_json(silent=True) or {}
            action = str(data.get("action") or "").strip()
            requested_by = str(data.get("requested_by") or "companion").strip() or "companion"
            item = self.action_queue.request(action, requested_by=requested_by)
            if not item:
                return jsonify(
                    {
                        "error": "Invalid action or queue full",
                        "allowed": sorted(ALLOWED_ACTIONS),
                    }
                ), 400
            return jsonify({"action": item}), 201

        @self.app.route(f"{prefix}/actions/<action_id>/approve", methods=["POST"])
        def approve_action(action_id: str):
            denied = self._auth_response()
            if denied:
                return denied
            item = self.action_queue.resolve(action_id, approve=True)
            if not item:
                return jsonify({"error": "Action not found or already resolved"}), 404
            cb = self.control_callbacks.get(item["action"])
            executed = False
            if cb:
                try:
                    executed = bool(cb())
                except Exception as exc:
                    logger.exception("Action callback failed")
                    return jsonify(
                        {"action": item, "executed": False, "error": str(exc)}
                    ), 500
            return jsonify({"action": item, "executed": executed})

        @self.app.route(f"{prefix}/actions/<action_id>/reject", methods=["POST"])
        def reject_action(action_id: str):
            denied = self._auth_response()
            if denied:
                return denied
            data = request.get_json(silent=True) or {}
            reason = str(data.get("reason") or "").strip() or None
            item = self.action_queue.resolve(action_id, approve=False, reason=reason)
            if not item:
                return jsonify({"error": "Action not found or already resolved"}), 404
            return jsonify({"action": item})

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
