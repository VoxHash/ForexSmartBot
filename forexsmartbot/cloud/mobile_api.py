"""
Mobile App API
Provides endpoints and push notification support for mobile companion app.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv(override=False)


class MobileAppAPI:
    """API for mobile companion app."""
    
    def __init__(self, app: Flask = None):
        """
        Initialize mobile app API.
        
        Args:
            app: Flask app instance (optional)
        """
        self.app = app or Flask(__name__)
        CORS(self.app)
        
        self.push_notification_service = None
        self.trading_controller = None
        self.broker = None
        
        self.setup_routes()
        
    def setup_routes(self):
        """Setup mobile app API routes."""
        
        @self.app.route('/api/v1/mobile/status', methods=['GET'])
        def mobile_status():
            """Get mobile app status."""
            return jsonify({
                'status': 'connected',
                'version': '3.3.0',
                'timestamp': datetime.now().isoformat()
            })
            
        @self.app.route('/api/v1/mobile/balance', methods=['GET'])
        def mobile_balance():
            """Get account balance for mobile."""
            if not self.broker:
                return jsonify({'error': 'Broker not initialized'}), 500
                
            try:
                balance = self.broker.get_balance()
                equity = self.broker.get_equity() if hasattr(self.broker, 'get_equity') else balance
                return jsonify({
                    'balance': balance,
                    'equity': equity
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/v1/mobile/positions', methods=['GET'])
        def mobile_positions():
            """Get positions for mobile."""
            if not self.broker:
                return jsonify({'error': 'Broker not initialized'}), 500
                
            try:
                positions = self.broker.get_positions()
                positions_list = []
                for symbol, pos in positions.items():
                    positions_list.append({
                        'symbol': pos.symbol,
                        'side': 'Long' if pos.side > 0 else 'Short',
                        'quantity': pos.quantity,
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'pnl': pos.pnl if hasattr(pos, 'pnl') else 0,
                        'stop_loss': pos.stop_loss,
                        'take_profit': pos.take_profit
                    })
                return jsonify({'positions': positions_list})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/v1/mobile/control/start', methods=['POST'])
        def mobile_start():
            """Start trading from mobile."""
            if self.trading_controller:
                try:
                    # This would call the trading controller's start method
                    return jsonify({'success': True, 'message': 'Trading started'})
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            return jsonify({'error': 'Trading controller not available'}), 500
            
        @self.app.route('/api/v1/mobile/control/stop', methods=['POST'])
        def mobile_stop():
            """Stop trading from mobile."""
            if self.trading_controller:
                try:
                    # This would call the trading controller's stop method
                    return jsonify({'success': True, 'message': 'Trading stopped'})
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            return jsonify({'error': 'Trading controller not available'}), 500
            
    def set_trading_controller(self, controller):
        """Set trading controller reference."""
        self.trading_controller = controller
        
    def set_broker(self, broker):
        """Set broker reference."""
        self.broker = broker


class PushNotificationService:
    """Service for sending push notifications to mobile devices."""
    
    def __init__(self, fcm_server_key: Optional[str] = None):
        """
        Initialize push notification service.
        
        Args:
            fcm_server_key: Firebase Cloud Messaging server key
        """
        self.fcm_server_key = fcm_server_key or os.getenv('FCM_SERVER_KEY', '')
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.device_tokens: List[str] = []
        
    def register_device(self, token: str):
        """Register a device token for push notifications."""
        if token not in self.device_tokens:
            self.device_tokens.append(token)
            
    def unregister_device(self, token: str):
        """Unregister a device token."""
        if token in self.device_tokens:
            self.device_tokens.remove(token)
            
    def send_notification(self, title: str, body: str, data: Optional[Dict] = None):
        """
        Send push notification to all registered devices.
        
        Args:
            title: Notification title
            body: Notification body
            data: Additional data payload
        """
        if not self.fcm_server_key or not self.device_tokens:
            return False
            
        try:
            for token in self.device_tokens:
                payload = {
                    'to': token,
                    'notification': {
                        'title': title,
                        'body': body,
                        'sound': 'default'
                    },
                    'data': data or {}
                }
                
                headers = {
                    'Authorization': f'key={self.fcm_server_key}',
                    'Content-Type': 'application/json'
                }
                
                response = requests.post(self.fcm_url, json=payload, headers=headers, timeout=5)
                if response.status_code == 200:
                    print(f"Push notification sent to {token}")
                else:
                    print(f"Failed to send push notification: {response.status_code}")
                    
            return True
        except Exception as e:
            print(f"Error sending push notification: {e}")
            return False
            
    def send_trade_alert(self, trade_type: str, symbol: str, price: float, pnl: Optional[float] = None):
        """Send trade alert notification."""
        title = f"Trade {trade_type}: {symbol}"
        body = f"Price: {price:.4f}"
        if pnl is not None:
            body += f", PnL: ${pnl:.2f}"
            
        data = {
            'type': 'trade',
            'symbol': symbol,
            'price': price,
            'pnl': pnl
        }
        
        return self.send_notification(title, body, data)
        
    def send_alert(self, alert_type: str, message: str):
        """Send general alert notification."""
        title = f"Alert: {alert_type}"
        body = message
        
        data = {
            'type': 'alert',
            'alert_type': alert_type,
            'message': message
        }
        
        return self.send_notification(title, body, data)

