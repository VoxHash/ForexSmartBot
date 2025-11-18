"""OANDA data provider implementation."""

import requests
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta
import time
from ...core.interfaces import IDataProvider


class OANDAProvider(IDataProvider):
    """OANDA data provider for forex data."""
    
    def __init__(self, api_key: str = None, account_id: str = None):
        self.api_key = api_key or "demo"  # Use demo if none provided
        self.account_id = account_id or "101-001-123456-001"  # Demo account
        self.base_url = "https://api-fxpractice.oanda.com"  # Demo environment
        self._available = True
        
    def get_data(self, symbol: str, start: str, end: str, 
                interval: str = "1h") -> pd.DataFrame:
        """Get historical data from OANDA."""
        try:
            # Convert forex symbol to OANDA format
            if symbol.endswith('=X'):
                symbol = symbol.replace('=X', '')
            
            # OANDA uses different format (e.g., EUR_USD instead of EURUSD)
            oanda_symbol = f"{symbol[:3]}_{symbol[3:]}"
            
            # Map interval to OANDA granularity
            granularity = self._map_interval(interval)
            
            # Convert dates to OANDA format
            start_date = pd.to_datetime(start).strftime('%Y-%m-%dT%H:%M:%S.000000000Z')
            end_date = pd.to_datetime(end).strftime('%Y-%m-%dT%H:%M:%S.000000000Z')
            
            url = f"{self.base_url}/v3/instruments/{oanda_symbol}/candles"
            params = {
                'from': start_date,
                'to': end_date,
                'granularity': granularity,
                'price': 'M'  # Mid prices
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            data = response.json()
            
            if 'candles' not in data:
                print(f"No candles data for {symbol}: {data.get('errorMessage', 'Unknown error')}")
                return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            
            candles = data['candles']
            if not candles:
                print(f"No candles available for {symbol}")
                return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            
            # Convert to DataFrame
            df_data = []
            for candle in candles:
                if candle['complete']:  # Only use complete candles
                    df_data.append({
                        'Open': float(candle['mid']['o']),
                        'High': float(candle['mid']['h']),
                        'Low': float(candle['mid']['l']),
                        'Close': float(candle['mid']['c']),
                        'Volume': int(candle['volume'])
                    })
            
            if not df_data:
                print(f"No complete candles for {symbol}")
                return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            
            df = pd.DataFrame(df_data)
            df.index = pd.to_datetime([candle['time'] for candle in candles if candle['complete']])
            
            return df.sort_index()
            
        except Exception as e:
            print(f"Error getting OANDA data for {symbol}: {e}")
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price from OANDA."""
        try:
            # Convert forex symbol to OANDA format
            if symbol.endswith('=X'):
                symbol = symbol.replace('=X', '')
            
            oanda_symbol = f"{symbol[:3]}_{symbol[3:]}"
            
            url = f"{self.base_url}/v3/accounts/{self.account_id}/pricing"
            params = {
                'instruments': oanda_symbol
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            data = response.json()
            
            if 'prices' in data and data['prices']:
                price_data = data['prices'][0]
                if 'bids' in price_data and 'asks' in price_data:
                    bid = float(price_data['bids'][0]['price'])
                    ask = float(price_data['asks'][0]['price'])
                    return (bid + ask) / 2  # Return mid price
            
            return None
            
        except Exception as e:
            print(f"Error getting OANDA latest price for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = '1d', interval: str = '1h') -> pd.DataFrame:
        """Get historical data for a symbol with specified period and interval."""
        try:
            # Convert period to start/end dates
            now = datetime.now()
            
            if period == '1d':
                end_date = now
                start_date = now - timedelta(days=1)
            elif period == '5d':
                end_date = now
                start_date = now - timedelta(days=5)
            elif period == '1mo':
                end_date = now
                start_date = now - timedelta(days=30)
            elif period == '3mo':
                end_date = now
                start_date = now - timedelta(days=90)
            elif period == '6mo':
                end_date = now
                start_date = now - timedelta(days=180)
            elif period == '1y':
                end_date = now
                start_date = now - timedelta(days=365)
            else:
                # Default to 1 day
                end_date = now
                start_date = now - timedelta(days=1)
            
            return self.get_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), interval)
            
        except Exception as e:
            print(f"Error getting OANDA historical data for {symbol}: {e}")
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    
    def _map_interval(self, interval: str) -> str:
        """Map interval to OANDA granularity."""
        mapping = {
            '1m': 'M1',
            '5m': 'M5',
            '15m': 'M15',
            '30m': 'M30',
            '1h': 'H1',
            '4h': 'H4',
            '1d': 'D'
        }
        return mapping.get(interval, 'H1')
    
    def is_available(self) -> bool:
        """Check if OANDA is available."""
        return self._available
