"""
Example: Cloud Sync Usage
Demonstrates how to use cloud sync for settings and data synchronization.
"""

from forexsmartbot.cloud.cloud_sync import CloudSyncManager
from forexsmartbot.services.persistence import SettingsManager
import os

def main():
    # Initialize cloud sync manager
    api_endpoint = os.getenv('CLOUD_API_ENDPOINT', 'https://api.forexsmartbot.cloud')
    api_key = os.getenv('CLOUD_API_KEY', '')
    
    cloud_sync = CloudSyncManager(api_endpoint=api_endpoint, api_key=api_key)
    
    # Get sync status
    status = cloud_sync.get_sync_status()
    print(f"Cloud Sync Status: {status}")
    
    # Sync settings
    settings_manager = SettingsManager()
    settings = {
        'broker_mode': settings_manager.get('broker_mode', 'PAPER'),
        'risk_pct': settings_manager.get('risk_pct', 0.02),
        'selected_symbols': settings_manager.get('selected_symbols', ['EURUSD'])
    }
    
    if cloud_sync.sync_settings(settings):
        print("Settings synced successfully")
    else:
        print("Failed to sync settings")
    
    # Get settings from cloud
    cloud_settings = cloud_sync.get_settings()
    if cloud_settings:
        print(f"Retrieved settings from cloud: {cloud_settings}")
    
    # Sync trade data
    trades = [
        {
            'symbol': 'EURUSD',
            'side': 'Long',
            'entry_price': 1.1000,
            'exit_price': 1.1050,
            'pnl': 50.0,
            'timestamp': '2026-01-15T10:00:00'
        }
    ]
    
    if cloud_sync.sync_trade_data(trades):
        print("Trade data synced successfully")
    
    # Get trade data from cloud
    from datetime import datetime, timedelta
    start_date = datetime.now() - timedelta(days=7)
    cloud_trades = cloud_sync.get_trade_data(start_date=start_date)
    print(f"Retrieved {len(cloud_trades)} trades from cloud")

if __name__ == '__main__':
    main()

