"""
Python SDK for ForexSmartBot API
Provides easy-to-use client for REST API and WebSocket API.
"""

import requests
import websockets
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv(override=False)


class APIClient:
    """Python client for ForexSmartBot REST API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            api_key: API key for authentication (defaults to API_KEY env var)
            base_url: Base URL of the API server (defaults to API_BASE_URL env var or http://localhost:5000)
        """
        self.api_key = api_key or os.getenv('API_KEY', '')
        default_base = os.getenv('API_BASE_URL', 'http://localhost:5000')
        self.base_url = (base_url or default_base).rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
    def get_balance(self) -> float:
        """Get account balance."""
        response = self.session.get(f"{self.base_url}/api/v1/account/balance")
        response.raise_for_status()
        return response.json()['balance']
        
    def get_positions(self) -> List[Dict]:
        """Get open positions."""
        response = self.session.get(f"{self.base_url}/api/v1/account/positions")
        response.raise_for_status()
        return response.json()['positions']
        
    def get_trades(self) -> List[Dict]:
        """Get trade history."""
        response = self.session.get(f"{self.base_url}/api/v1/trades")
        response.raise_for_status()
        return response.json()['trades']
        
    def create_order(self, symbol: str, side: int, quantity: float,
                    stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None) -> Dict:
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
        payload = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity
        }
        
        if stop_loss:
            payload['stop_loss'] = stop_loss
        if take_profit:
            payload['take_profit'] = take_profit
            
        response = self.session.post(f"{self.base_url}/api/v1/orders", json=payload)
        response.raise_for_status()
        return response.json()
        
    def close_positions(self, symbol: str) -> Dict:
        """
        Close all positions for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Response dictionary
        """
        response = self.session.delete(f"{self.base_url}/api/v1/orders/{symbol}")
        response.raise_for_status()
        return response.json()
        
    def get_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Current price
        """
        response = self.session.get(f"{self.base_url}/api/v1/market/price/{symbol}")
        response.raise_for_status()
        return response.json()['price']


class WebSocketClient:
    """Python client for ForexSmartBot WebSocket API."""
    
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize WebSocket client.
        
        Args:
            url: WebSocket server URL (defaults to WS_URL env var or ws://localhost:8765)
            api_key: API key for authentication (defaults to API_KEY env var)
        """
        default_url = os.getenv('WS_URL', 'ws://localhost:8765')
        self.url = url or default_url
        self.api_key = api_key or os.getenv('API_KEY', '')
        self.websocket = None
        
    async def connect(self):
        """Connect to WebSocket server."""
        self.websocket = await websockets.connect(self.url)
        
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            
    async def subscribe(self, symbol: str):
        """Subscribe to price updates for a symbol."""
        if not self.websocket:
            await self.connect()
            
        message = {
            'command': 'subscribe',
            'symbol': symbol
        }
        await self.websocket.send(json.dumps(message))
        
    async def get_balance(self) -> float:
        """Get balance via WebSocket."""
        if not self.websocket:
            await self.connect()
            
        message = {'command': 'get_balance'}
        await self.websocket.send(json.dumps(message))
        
        response = await self.websocket.recv()
        data = json.loads(response)
        return data.get('value', 0.0)
        
    async def get_positions(self) -> List[Dict]:
        """Get positions via WebSocket."""
        if not self.websocket:
            await self.connect()
            
        message = {'command': 'get_positions'}
        await self.websocket.send(json.dumps(message))
        
        response = await self.websocket.recv()
        data = json.loads(response)
        return data.get('data', [])
        
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

