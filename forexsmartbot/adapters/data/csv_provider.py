"""CSV data provider implementation."""

import pandas as pd
import os
from typing import Optional, Dict
from ...core.interfaces import IDataProvider


class CSVProvider(IDataProvider):
    """CSV file data provider."""
    
    def __init__(self, data_directory: str = "data/csv"):
        self._data_directory = data_directory
        self._cache: Dict[str, pd.DataFrame] = {}
        self._available = os.path.exists(data_directory)
        
    def get_data(self, symbol: str, start: str, end: str, 
                interval: str = "1h") -> pd.DataFrame:
        """Get historical data from CSV file."""
        try:
            # Look for CSV file matching symbol
            csv_file = os.path.join(self._data_directory, f"{symbol.upper()}.csv")
            
            if not os.path.exists(csv_file):
                return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
                
            # Load from cache if available
            cache_key = f"{symbol}_{start}_{end}_{interval}"
            if cache_key in self._cache:
                return self._cache[cache_key]
                
            # Read CSV file
            df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
            
            # Ensure proper column names
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'Volume' and 'Volume' not in df.columns:
                        df['Volume'] = 0  # Default volume if not present
                    else:
                        return pd.DataFrame(columns=required_columns)
                        
            # Filter by date range
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
            
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            # Cache the result
            self._cache[cache_key] = df
            
            return df.dropna()
            
        except Exception:
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price from CSV file."""
        try:
            csv_file = os.path.join(self._data_directory, f"{symbol.upper()}.csv")
            
            if not os.path.exists(csv_file):
                return None
                
            # Read just the last few rows for efficiency
            df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
            
            if df.empty or 'Close' not in df.columns:
                return None
                
            return float(df['Close'].iloc[-1])
            
        except Exception:
            return None
            
    def is_available(self) -> bool:
        """Check if CSV data directory is available."""
        return self._available
        
    def add_data_file(self, symbol: str, file_path: str) -> bool:
        """Add a CSV data file for a symbol."""
        try:
            if not os.path.exists(self._data_directory):
                os.makedirs(self._data_directory)
                
            target_file = os.path.join(self._data_directory, f"{symbol.upper()}.csv")
            
            # Copy or move the file
            import shutil
            shutil.copy2(file_path, target_file)
            
            # Clear cache for this symbol
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(symbol)]
            for key in keys_to_remove:
                del self._cache[key]
                
            return True
            
        except Exception:
            return False
    
    def get_historical_data(self, symbol: str, period: str = '1d', interval: str = '1h') -> pd.DataFrame:
        """Get historical data for a symbol with specified period and interval."""
        try:
            # Convert period to start/end dates
            from datetime import datetime, timedelta
            
            if period == '1d':
                end_date = datetime.now()
                start_date = end_date - timedelta(days=1)
            elif period == '5d':
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5)
            elif period == '1mo':
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
            elif period == '3mo':
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)
            elif period == '6mo':
                end_date = datetime.now()
                start_date = end_date - timedelta(days=180)
            elif period == '1y':
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
            else:
                # Default to 1 day
                end_date = datetime.now()
                start_date = end_date - timedelta(days=1)
            
            # Use the existing get_data method
            return self.get_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), interval)
            
        except Exception as e:
            print(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])