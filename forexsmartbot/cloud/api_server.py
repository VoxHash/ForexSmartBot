"""
API Server for ForexSmartBot v3.3.0
Provides REST API and WebSocket API for external integrations.
"""

import json
import asyncio
import logging
import os
from typing import Dict, Optional, List, Callable
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
from functools import wraps
from threading import Thread
import websockets
from websockets.server import serve
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv(override=False)


class APIServer:
    """REST API server for external integrations."""
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None,
                 api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Initialize API server.
        
        Args:
            host: Server host address (defaults to API_HOST env var or 127.0.0.1)
            port: Server port (defaults to API_PORT env var or 5000)
            api_key: API key for authentication (defaults to API_KEY env var)
            secret_key: Secret key for JWT tokens (defaults to API_SECRET_KEY env var)
        """
        self.host = host or os.getenv('API_HOST', '127.0.0.1')
        self.port = port or int(os.getenv('API_PORT', '5000'))
        self.api_key = api_key or os.getenv('API_KEY', '')
        self.secret_key = secret_key or os.getenv('API_SECRET_KEY', 'default-secret-key-change-in-production')
        
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Rate limiting
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["100 per hour", "10 per minute"]
        )
        
        self.trading_controller = None
        self.broker = None
        self.data_provider = None
        
        self.setup_routes()
        self.server_thread = None
        self.running = False
        
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.route('/api/v1/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'version': '3.3.0',
                'timestamp': datetime.now().isoformat()
            })
            
        @self.app.route('/api/v1/account/balance', methods=['GET'])
        @self.require_auth
        def get_balance():
            """Get account balance."""
            if not self.broker:
                return jsonify({'error': 'Broker not initialized'}), 500
                
            try:
                balance = self.broker.get_balance()
                return jsonify({'balance': balance})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/v1/account/positions', methods=['GET'])
        @self.require_auth
        def get_positions():
            """Get open positions."""
            if not self.broker:
                return jsonify({'error': 'Broker not initialized'}), 500
                
            try:
                positions = self.broker.get_positions()
                positions_list = []
                for symbol, pos in positions.items():
                    positions_list.append({
                        'symbol': pos.symbol,
                        'side': pos.side,
                        'quantity': pos.quantity,
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'stop_loss': pos.stop_loss,
                        'take_profit': pos.take_profit,
                        'pnl': pos.pnl if hasattr(pos, 'pnl') else 0
                    })
                return jsonify({'positions': positions_list})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/v1/trades', methods=['GET'])
        @self.require_auth
        def get_trades():
            """Get trade history."""
            # This would query from database or trading controller
            return jsonify({'trades': []})
            
        @self.app.route('/api/v1/orders', methods=['POST'])
        @self.require_auth
        @self.limiter.limit("5 per minute")
        def create_order():
            """Create a new order."""
            if not self.broker or not self.broker.is_connected():
                return jsonify({'error': 'Broker not connected'}), 400
                
            try:
                data = request.json
                symbol = data.get('symbol')
                side = data.get('side')  # 1 for buy, -1 for sell
                quantity = data.get('quantity')
                stop_loss = data.get('stop_loss')
                take_profit = data.get('take_profit')
                
                if not symbol or not side or not quantity:
                    return jsonify({'error': 'Missing required parameters'}), 400
                    
                order_id = self.broker.submit_order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                if order_id:
                    return jsonify({
                        'order_id': order_id,
                        'status': 'success',
                        'symbol': symbol,
                        'side': side,
                        'quantity': quantity
                    })
                else:
                    return jsonify({'error': 'Order submission failed'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/v1/orders/<symbol>', methods=['DELETE'])
        @self.require_auth
        @self.limiter.limit("10 per minute")
        def close_positions(symbol):
            """Close all positions for a symbol."""
            if not self.broker or not self.broker.is_connected():
                return jsonify({'error': 'Broker not connected'}), 400
                
            try:
                success = self.broker.close_all(symbol)
                if success:
                    return jsonify({'status': 'success', 'message': f'Closed positions for {symbol}'})
                else:
                    return jsonify({'error': 'Failed to close positions'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/v1/market/price/<symbol>', methods=['GET'])
        @self.require_auth
        def get_price(symbol):
            """Get current price for a symbol."""
            if not self.broker:
                return jsonify({'error': 'Broker not initialized'}), 500
                
            try:
                price = self.broker.get_price(symbol)
                if price:
                    return jsonify({'symbol': symbol, 'price': price})
                else:
                    return jsonify({'error': 'Price not available'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
    def require_auth(self, f):
        """Decorator for API authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.api_key:
                return jsonify({'error': 'API key not configured'}), 500
                
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid authorization header'}), 401
                
            token = auth_header[7:]
            if token != self.api_key:
                return jsonify({'error': 'Invalid API key'}), 401
                
            return f(*args, **kwargs)
        return decorated_function
        
    def set_trading_controller(self, controller):
        """Set trading controller reference."""
        self.trading_controller = controller
        
    def set_broker(self, broker):
        """Set broker reference."""
        self.broker = broker
        
    def set_data_provider(self, data_provider):
        """Set data provider reference."""
        self.data_provider = data_provider
        
    def start(self):
        """Start the API server."""
        if self.running:
            return
            
        self.running = True
        self.server_thread = Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        print(f"API server started on http://{self.host}:{self.port}")
        
    def stop(self):
        """Stop the API server."""
        self.running = False
        print("API server stopped")
        
    def _run_server(self):
        """Run Flask server in thread."""
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)


class WebSocketServer:
    """WebSocket server for real-time data streaming."""
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None,
                 api_key: Optional[str] = None):
        """
        Initialize WebSocket server.
        
        Args:
            host: Server host address (defaults to WS_HOST env var or 127.0.0.1)
            port: Server port (defaults to WS_PORT env var or 8765)
            api_key: API key for authentication (defaults to API_KEY env var)
        """
        self.host = host or os.getenv('WS_HOST', '127.0.0.1')
        self.port = port or int(os.getenv('WS_PORT', '8765'))
        self.api_key = api_key or os.getenv('API_KEY', '')
        self.clients = set()
        self.running = False
        self.broker = None
        
    async def register_client(self, websocket, path):
        """Register a new WebSocket client."""
        # Simple authentication check
        if self.api_key:
            # In production, implement proper authentication
            pass
            
        self.clients.add(websocket)
        print(f"WebSocket client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                # Handle incoming messages
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            print(f"WebSocket client disconnected: {websocket.remote_address}")
            
    async def handle_message(self, websocket, message):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'subscribe':
                symbol = data.get('symbol')
                # Subscribe to price updates for symbol
                await websocket.send(json.dumps({
                    'type': 'subscribed',
                    'symbol': symbol
                }))
            elif command == 'get_balance':
                if self.broker:
                    balance = self.broker.get_balance()
                    await websocket.send(json.dumps({
                        'type': 'balance',
                        'value': balance
                    }))
            elif command == 'get_positions':
                if self.broker:
                    positions = self.broker.get_positions()
                    positions_list = []
                    for symbol, pos in positions.items():
                        positions_list.append({
                            'symbol': pos.symbol,
                            'side': pos.side,
                            'quantity': pos.quantity,
                            'entry_price': pos.entry_price,
                            'current_price': pos.current_price,
                            'pnl': pos.pnl if hasattr(pos, 'pnl') else 0
                        })
                    await websocket.send(json.dumps({
                        'type': 'positions',
                        'data': positions_list
                    }))
        except Exception as e:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))
            
    async def broadcast(self, message_type: str, data: Dict):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return
            
        message = json.dumps({
            'type': message_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except:
                disconnected.add(client)
                
        self.clients -= disconnected
        
    def set_broker(self, broker):
        """Set broker reference."""
        self.broker = broker
        
    async def start(self):
        """Start the WebSocket server."""
        self.running = True
        async with serve(self.register_client, self.host, self.port):
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
            
    def start_sync(self):
        """Start WebSocket server in synchronous way."""
        asyncio.run(self.start())
        
    def stop(self):
        """Stop the WebSocket server."""
        self.running = False

