"""Yahoo Finance data provider implementation."""

import yfinance as yf
import pandas as pd
from typing import Optional
from ...core.interfaces import IDataProvider


class YFinanceProvider(IDataProvider):
    """Yahoo Finance data provider."""
    
    def __init__(self):
        self._available = True
        
    def get_data(self, symbol: str, start: str, end: str, 
                interval: str = "1h") -> pd.DataFrame:
        """Get historical data from Yahoo Finance."""
        try:
            # Convert forex symbol to yfinance format
            if not symbol.endswith('=X'):
                symbol = symbol.upper() + "=X"
                
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end, interval=interval, auto_adjust=True)
            
            if df.empty:
                return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
                
            # Ensure proper column names
            df = df.rename(columns={
                'Open': 'Open',
                'High': 'High', 
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })
            
            return df.dropna()
            
        except Exception:
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price from Yahoo Finance."""
        try:
            if not symbol.endswith('=X'):
                symbol = symbol.upper() + "=X"
                
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if 'regularMarketPrice' in info:
                return float(info['regularMarketPrice'])
            elif 'currentPrice' in info:
                return float(info['currentPrice'])
            else:
                # Fallback to recent data
                df = ticker.history(period="1d", interval="1m")
                if not df.empty:
                    return float(df['Close'].iloc[-1])
                    
        except Exception:
            pass
            
        return None
        
    def is_available(self) -> bool:
        """Check if Yahoo Finance is available."""
        return self._available
