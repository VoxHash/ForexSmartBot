"""
Example: Mobile App Integration
Demonstrates how to integrate with mobile app using push notifications.
"""

from forexsmartbot.cloud.mobile_api import MobileAppAPI, PushNotificationService
from flask import Flask
import os

def main():
    # Initialize Flask app
    app = Flask(__name__)
    
    # Initialize mobile API
    mobile_api = MobileAppAPI(app=app)
    
    # Initialize push notification service
    fcm_key = os.getenv('FCM_SERVER_KEY', '')
    push_service = PushNotificationService(fcm_server_key=fcm_key)
    mobile_api.push_notification_service = push_service
    
    # Register a device token (in real app, this would come from mobile app)
    device_token = "DEVICE_FCM_TOKEN"
    push_service.register_device(device_token)
    
    # Example: Send trade alert
    push_service.send_trade_alert(
        trade_type="Open",
        symbol="EURUSD",
        price=1.1050,
        pnl=50.0
    )
    
    # Example: Send general alert
    push_service.send_alert(
        alert_type="Risk Warning",
        message="Maximum drawdown threshold reached"
    )
    
    # Start Flask app
    print("Mobile API server starting on http://127.0.0.1:5000")
    print("Mobile app endpoints available at /api/v1/mobile/*")
    app.run(host='127.0.0.1', port=5000, debug=True)

if __name__ == '__main__':
    main()

