"""
Cloud Sync Manager
Handles cloud-based settings and data synchronization with multi-device support.
"""

from __future__ import annotations

import hashlib
import logging
import os
import platform
import threading
import uuid
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Optional

import requests
from dotenv import load_dotenv

from .auth_utils import package_version, resolve_api_key
from .error_handler import retry_call

load_dotenv(override=False)

logger = logging.getLogger(__name__)


class CloudSyncManager:
    """Manages cloud synchronization of settings and data."""

    def __init__(
        self,
        api_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        max_retries: int = 3,
        timeout: float = 10.0,
        max_pending: int = 50,
    ):
        """
        Initialize cloud sync manager.

        Args:
            api_endpoint: Cloud API endpoint URL
            api_key: API key for authentication
            max_retries: Retry attempts for transient failures
            timeout: Per-request timeout in seconds
            max_pending: Max failed payloads retained for flush
        """
        self.api_endpoint = (
            api_endpoint or os.getenv("CLOUD_API_ENDPOINT", "https://api.forexsmartbot.cloud")
        ).rstrip("/")
        self.api_key = resolve_api_key(api_key, env_names=("CLOUD_API_KEY", "API_KEY"))
        self.device_id = self._get_device_id()
        self.sync_lock = threading.Lock()
        self.last_sync_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.consecutive_failures = 0
        self.max_retries = max_retries
        self.timeout = timeout
        self._pending: Deque[Dict] = deque(maxlen=max_pending)
        self._auto_sync_thread: Optional[threading.Thread] = None
        self._auto_sync_stop = threading.Event()
        self._auto_sync_interval = 300
        self._last_settings: Optional[Dict] = None
        self._last_portfolio: Optional[Dict] = None

    def _get_device_id(self) -> str:
        """Get unique device ID."""
        machine_id = platform.node()
        mac = ":".join(
            [
                "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
                for elements in range(0, 2 * 6, 2)
            ][::-1]
        )
        device_string = f"{machine_id}_{mac}"
        return hashlib.md5(device_string.encode()).hexdigest()

    def _auth_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> requests.Response:
        url = f"{self.api_endpoint}{path}"

        def _do() -> requests.Response:
            response = requests.request(
                method,
                url,
                json=json_body,
                params=params,
                headers=self._auth_headers(),
                timeout=self.timeout,
            )
            if response.status_code >= 500:
                response.raise_for_status()
            return response

        return retry_call(
            _do,
            max_retries=self.max_retries,
            base_delay=1.0,
            logger=logger,
        )

    def _record_success(self) -> None:
        self.last_sync_time = datetime.now()
        self.last_error = None
        self.consecutive_failures = 0

    def _record_failure(self, exc: BaseException, pending: Optional[Dict] = None) -> None:
        self.consecutive_failures += 1
        self.last_error = str(exc)
        logger.warning("Cloud sync failure (%s): %s", self.consecutive_failures, exc)
        if pending is not None:
            self._pending.append(pending)

    def sync_settings(self, settings: Dict) -> bool:
        """
        Sync settings to cloud.

        Args:
            settings: Settings dictionary to sync

        Returns:
            True if sync successful
        """
        if not self.api_key:
            return False

        self._last_settings = dict(settings)
        payload = {
            "device_id": self.device_id,
            "settings": settings,
            "timestamp": datetime.now().isoformat(),
            "version": package_version(),
        }

        try:
            with self.sync_lock:
                response = self._request(
                    "POST", "/api/v1/settings/sync", json_body=payload
                )
                if response.status_code == 200:
                    self._record_success()
                    return True
                self._record_failure(
                    RuntimeError(f"{response.status_code}: {response.text}"),
                    {"type": "settings", "payload": payload},
                )
                return False
        except Exception as e:
            self._record_failure(e, {"type": "settings", "payload": payload})
            return False

    def get_settings(self) -> Optional[Dict]:
        """Get settings from cloud."""
        if not self.api_key:
            return None

        try:
            response = self._request(
                "GET",
                "/api/v1/settings/get",
                params={"device_id": self.device_id},
            )
            if response.status_code == 200:
                return response.json().get("settings")
            return None
        except Exception as e:
            self._record_failure(e)
            return None

    def sync_trade_data(self, trades: List[Dict]) -> bool:
        """Sync trade data to cloud."""
        if not self.api_key:
            return False

        payload = {
            "device_id": self.device_id,
            "trades": trades,
            "timestamp": datetime.now().isoformat(),
            "version": package_version(),
        }

        try:
            with self.sync_lock:
                response = self._request(
                    "POST", "/api/v1/data/trades/sync", json_body=payload
                )
                if response.status_code == 200:
                    self._record_success()
                    return True
                self._record_failure(
                    RuntimeError(f"{response.status_code}"),
                    {"type": "trades", "payload": payload},
                )
                return False
        except Exception as e:
            self._record_failure(e, {"type": "trades", "payload": payload})
            return False

    def get_trade_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get trade data from cloud."""
        if not self.api_key:
            return []

        try:
            params: Dict[str, str] = {"device_id": self.device_id}
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()

            response = self._request("GET", "/api/v1/data/trades/get", params=params)
            if response.status_code == 200:
                return response.json().get("trades", [])
            return []
        except Exception as e:
            self._record_failure(e)
            return []

    def sync_portfolio(self, portfolio_data: Dict) -> bool:
        """Sync portfolio data to cloud."""
        if not self.api_key:
            return False

        self._last_portfolio = dict(portfolio_data)
        payload = {
            "device_id": self.device_id,
            "portfolio": portfolio_data,
            "timestamp": datetime.now().isoformat(),
            "version": package_version(),
        }

        try:
            with self.sync_lock:
                response = self._request(
                    "POST", "/api/v1/data/portfolio/sync", json_body=payload
                )
                if response.status_code == 200:
                    self._record_success()
                    return True
                self._record_failure(
                    RuntimeError(f"{response.status_code}"),
                    {"type": "portfolio", "payload": payload},
                )
                return False
        except Exception as e:
            self._record_failure(e, {"type": "portfolio", "payload": payload})
            return False

    def flush_pending(self) -> int:
        """Retry queued failed sync payloads. Returns number of successes."""
        if not self.api_key or not self._pending:
            return 0

        successes = 0
        remaining: Deque[Dict] = deque()
        while self._pending:
            item = self._pending.popleft()
            kind = item.get("type")
            payload = item.get("payload") or {}
            path_map = {
                "settings": "/api/v1/settings/sync",
                "trades": "/api/v1/data/trades/sync",
                "portfolio": "/api/v1/data/portfolio/sync",
            }
            path = path_map.get(kind)
            if not path:
                continue
            try:
                with self.sync_lock:
                    response = self._request("POST", path, json_body=payload)
                if response.status_code == 200:
                    successes += 1
                    self._record_success()
                else:
                    remaining.append(item)
            except Exception as e:
                self._record_failure(e)
                remaining.append(item)
        self._pending.extend(remaining)
        return successes

    def check_endpoint_health(self) -> Dict:
        """Probe remote health endpoint (``/healthz`` then ``/api/v1/health``)."""
        for path in ("/healthz", "/api/v1/health", "/api/v1/health/"):
            try:
                response = requests.get(
                    f"{self.api_endpoint}{path}",
                    headers=self._auth_headers(),
                    timeout=min(5.0, self.timeout),
                )
                if response.status_code == 200:
                    body = {}
                    try:
                        body = response.json()
                    except Exception:
                        body = {"raw": response.text[:200]}
                    return {
                        "available": True,
                        "path": path,
                        "status_code": response.status_code,
                        "body": body,
                        "checked_at": datetime.now().isoformat(),
                    }
            except Exception as e:
                last = str(e)
                continue
        return {
            "available": False,
            "error": locals().get("last", "unreachable"),
            "checked_at": datetime.now().isoformat(),
        }

    def get_sync_status(self) -> Dict:
        """Get synchronization status."""
        return {
            "device_id": self.device_id,
            "api_endpoint": self.api_endpoint,
            "api_key_configured": bool(self.api_key),
            "last_sync_time": self.last_sync_time.isoformat()
            if self.last_sync_time
            else None,
            "last_error": self.last_error,
            "consecutive_failures": self.consecutive_failures,
            "pending_count": len(self._pending),
            "auto_sync_enabled": self._auto_sync_thread is not None
            and self._auto_sync_thread.is_alive(),
            "auto_sync_interval_seconds": self._auto_sync_interval,
            "sync_enabled": bool(self.api_key),
            "version": package_version(),
        }

    def _auto_sync_loop(self) -> None:
        while not self._auto_sync_stop.wait(self._auto_sync_interval):
            try:
                self.flush_pending()
                if self._last_settings is not None:
                    self.sync_settings(self._last_settings)
                if self._last_portfolio is not None:
                    self.sync_portfolio(self._last_portfolio)
            except Exception as e:
                logger.warning("Auto-sync iteration failed: %s", e)

    def enable_auto_sync(self, interval_seconds: int = 300):
        """
        Enable automatic synchronization in a background daemon thread.

        Args:
            interval_seconds: Sync interval in seconds (default 5 minutes)
        """
        if interval_seconds < 30:
            raise ValueError("interval_seconds must be >= 30")
        self.disable_auto_sync()
        self._auto_sync_interval = interval_seconds
        self._auto_sync_stop.clear()
        self._auto_sync_thread = threading.Thread(
            target=self._auto_sync_loop,
            name="CloudSyncAuto",
            daemon=True,
        )
        self._auto_sync_thread.start()
        logger.info("Cloud auto-sync enabled every %ss", interval_seconds)

    def disable_auto_sync(self):
        """Disable automatic synchronization."""
        self._auto_sync_stop.set()
        thread = self._auto_sync_thread
        if thread and thread.is_alive():
            thread.join(timeout=2.0)
        self._auto_sync_thread = None
