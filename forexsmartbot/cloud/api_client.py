"""
Python SDK for ForexSmartBot API
Provides easy-to-use client for REST API and WebSocket API.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import requests
import websockets
from dotenv import load_dotenv

from .auth_utils import resolve_api_key
from .error_handler import retry_call

load_dotenv(override=False)


class APIClient:
    """Python client for ForexSmartBot REST API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        *,
        max_retries: int = 3,
        timeout: float = 10.0,
    ):
        """
        Initialize API client.

        Args:
            api_key: API key for authentication (defaults to API_KEY env var)
            base_url: Base URL of the API server (defaults to API_BASE_URL env var or http://localhost:5000)
            max_retries: Transient failure retries
            timeout: Request timeout seconds
        """
        self.api_key = resolve_api_key(api_key, env_names=("API_KEY",))
        default_base = os.getenv("API_BASE_URL", "http://localhost:5000")
        self.base_url = (base_url or default_base).rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
            self.session.headers["X-API-Key"] = self.api_key

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)

        def _do() -> requests.Response:
            response = self.session.request(method, url, **kwargs)
            if response.status_code >= 500:
                response.raise_for_status()
            response.raise_for_status()
            return response

        return retry_call(_do, max_retries=self.max_retries, base_delay=1.0)

    def health(self) -> Dict:
        """Call public health endpoint."""
        for path in ("/healthz", "/api/v1/health"):
            try:
                response = self.session.get(
                    f"{self.base_url}{path}", timeout=min(5.0, self.timeout)
                )
                if response.status_code == 200:
                    return response.json()
            except Exception:
                continue
        raise requests.exceptions.ConnectionError(
            f"Health endpoint unreachable at {self.base_url}"
        )

    def get_balance(self) -> float:
        """Get account balance."""
        response = self._request("GET", "/api/v1/account/balance")
        return response.json()["balance"]

    def get_positions(self) -> List[Dict]:
        """Get open positions."""
        response = self._request("GET", "/api/v1/account/positions")
        return response.json()["positions"]

    def get_trades(self) -> List[Dict]:
        """Get trade history."""
        response = self._request("GET", "/api/v1/trades")
        return response.json()["trades"]

    def create_order(
        self,
        symbol: str,
        side: int,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Dict:
        """
        Create a new order.

        Args:
            symbol: Trading symbol
            side: 1 for buy, -1 for sell
            quantity: Order quantity
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)

        Returns:
            Order response dictionary
        """
        payload = {"symbol": symbol, "side": side, "quantity": quantity}
        if stop_loss:
            payload["stop_loss"] = stop_loss
        if take_profit:
            payload["take_profit"] = take_profit

        response = self._request("POST", "/api/v1/orders", json=payload)
        return response.json()

    def close_positions(self, symbol: str) -> Dict:
        """
        Close all positions for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Response dictionary
        """
        response = self._request("DELETE", f"/api/v1/orders/{symbol}")
        return response.json()

    def get_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Current price
        """
        response = self._request("GET", f"/api/v1/market/price/{symbol}")
        return response.json()["price"]


class WebSocketClient:
    """Python client for ForexSmartBot WebSocket API."""

    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize WebSocket client.

        Args:
            url: WebSocket server URL (defaults to WS_URL env var or ws://localhost:8765)
            api_key: API key for authentication (defaults to API_KEY env var)
        """
        default_url = os.getenv("WS_URL", "ws://localhost:8765")
        self.url = url or default_url
        self.api_key = resolve_api_key(api_key, env_names=("API_KEY", "WS_API_KEY"))
        self.websocket = None

    async def connect(self):
        """Connect to WebSocket server and authenticate when a key is set."""
        self.websocket = await websockets.connect(self.url)
        if self.api_key:
            await self.websocket.send(
                json.dumps({"command": "auth", "token": self.api_key})
            )
            raw = await self.websocket.recv()
            data = json.loads(raw)
            if not data.get("ok"):
                await self.disconnect()
                raise PermissionError("WebSocket authentication failed")

    async def disconnect(self):
        """Disconnect from WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def subscribe(self, symbol: str):
        """Subscribe to price updates for a symbol."""
        if not self.websocket:
            await self.connect()

        message = {"command": "subscribe", "symbol": symbol}
        await self.websocket.send(json.dumps(message))

    async def get_balance(self) -> float:
        """Get balance via WebSocket."""
        if not self.websocket:
            await self.connect()

        message = {"command": "get_balance"}
        await self.websocket.send(json.dumps(message))

        response = await self.websocket.recv()
        data = json.loads(response)
        return data.get("value", 0.0)

    async def get_positions(self) -> List[Dict]:
        """Get positions via WebSocket."""
        if not self.websocket:
            await self.connect()

        message = {"command": "get_positions"}
        await self.websocket.send(json.dumps(message))

        response = await self.websocket.recv()
        data = json.loads(response)
        return data.get("data", [])

    async def listen(self, callback):
        """Listen for real-time updates."""
        if not self.websocket:
            await self.connect()

        while True:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                callback(data)
            except websockets.exceptions.ConnectionClosed:
                break
