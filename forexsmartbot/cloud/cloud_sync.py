"""
Cloud Sync Manager
Handles cloud-based settings and data synchronization with multi-device support.
"""

import json
import os
import hashlib
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path
import requests
from threading import Lock
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv(override=False)


class CloudSyncManager:
    """Manages cloud synchronization of settings and data."""
    
    def __init__(self, api_endpoint: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize cloud sync manager.
        
        Args:
            api_endpoint: Cloud API endpoint URL
            api_key: API key for authentication
        """
        self.api_endpoint = api_endpoint or os.getenv('CLOUD_API_ENDPOINT', 'https://api.forexsmartbot.cloud')
        self.api_key = api_key or os.getenv('CLOUD_API_KEY', '')
        self.device_id = self._get_device_id()
        self.sync_lock = Lock()
        self.last_sync_time = None
        
    def _get_device_id(self) -> str:
        """Get unique device ID."""
        import platform
        import uuid
        
        # Generate device ID from machine characteristics
        machine_id = platform.node()
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                       for elements in range(0, 2*6, 2)][::-1])
        device_string = f"{machine_id}_{mac}"
        return hashlib.md5(device_string.encode()).hexdigest()
        
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
            
        try:
            with self.sync_lock:
                payload = {
                    'device_id': self.device_id,
                    'settings': settings,
                    'timestamp': datetime.now().isoformat(),
                    'version': '3.3.0'
                }
                
                response = requests.post(
                    f"{self.api_endpoint}/api/v1/settings/sync",
                    json=payload,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.last_sync_time = datetime.now()
                    return True
                else:
                    print(f"Cloud sync failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"Error syncing settings to cloud: {e}")
            return False
            
    def get_settings(self) -> Optional[Dict]:
        """
        Get settings from cloud.
        
        Returns:
            Settings dictionary or None if failed
        """
        if not self.api_key:
            return None
            
        try:
            response = requests.get(
                f"{self.api_endpoint}/api/v1/settings/get",
                params={'device_id': self.device_id},
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('settings')
            else:
                return None
                
        except Exception as e:
            print(f"Error getting settings from cloud: {e}")
            return None
            
    def sync_trade_data(self, trades: List[Dict]) -> bool:
        """
        Sync trade data to cloud.
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            True if sync successful
        """
        if not self.api_key:
            return False
            
        try:
            with self.sync_lock:
                payload = {
                    'device_id': self.device_id,
                    'trades': trades,
                    'timestamp': datetime.now().isoformat(),
                    'version': '3.3.0'
                }
                
                response = requests.post(
                    f"{self.api_endpoint}/api/v1/data/trades/sync",
                    json=payload,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.last_sync_time = datetime.now()
                    return True
                else:
                    print(f"Trade data sync failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"Error syncing trade data to cloud: {e}")
            return False
            
    def get_trade_data(self, start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get trade data from cloud.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of trade dictionaries
        """
        if not self.api_key:
            return []
            
        try:
            params = {'device_id': self.device_id}
            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()
                
            response = requests.get(
                f"{self.api_endpoint}/api/v1/data/trades/get",
                params=params,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('trades', [])
            else:
                return []
                
        except Exception as e:
            print(f"Error getting trade data from cloud: {e}")
            return []
            
    def sync_portfolio(self, portfolio_data: Dict) -> bool:
        """
        Sync portfolio data to cloud.
        
        Args:
            portfolio_data: Portfolio data dictionary
            
        Returns:
            True if sync successful
        """
        if not self.api_key:
            return False
            
        try:
            with self.sync_lock:
                payload = {
                    'device_id': self.device_id,
                    'portfolio': portfolio_data,
                    'timestamp': datetime.now().isoformat(),
                    'version': '3.3.0'
                }
                
                response = requests.post(
                    f"{self.api_endpoint}/api/v1/data/portfolio/sync",
                    json=payload,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.last_sync_time = datetime.now()
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Error syncing portfolio to cloud: {e}")
            return False
            
    def get_sync_status(self) -> Dict:
        """
        Get synchronization status.
        
        Returns:
            Dictionary with sync status information
        """
        return {
            'device_id': self.device_id,
            'api_endpoint': self.api_endpoint,
            'api_key_configured': bool(self.api_key),
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_enabled': bool(self.api_key)
        }
        
    def enable_auto_sync(self, interval_seconds: int = 300):
        """
        Enable automatic synchronization.
        
        Args:
            interval_seconds: Sync interval in seconds (default 5 minutes)
        """
        # This would be implemented with a background thread
        # For now, it's a placeholder
        pass
        
    def disable_auto_sync(self):
        """Disable automatic synchronization."""
        pass

