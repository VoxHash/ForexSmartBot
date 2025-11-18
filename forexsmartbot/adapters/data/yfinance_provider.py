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
            # Convert dates to timezone-naive datetime objects
            start_date = pd.to_datetime(start).tz_localize(None) if pd.to_datetime(start).tz is not None else pd.to_datetime(start)
            end_date = pd.to_datetime(end).tz_localize(None) if pd.to_datetime(end).tz is not None else pd.to_datetime(end)
            
            # Convert forex symbol to yfinance format if needed
            if not symbol.endswith('=X'):
                symbol = symbol.upper() + "=X"
                
            ticker = yf.Ticker(symbol)
            date_range_days = (end_date - start_date).days
            
            # Try different approaches to get data
            df = pd.DataFrame()
            
            # First try: Get data with the requested interval
            try:
                if date_range_days > 365:
                    # For long ranges, use daily data and resample
                    df = ticker.history(start=start_date, end=end_date, interval="1d", auto_adjust=True, progress=False)
                else:
                    # For shorter ranges, use the requested interval
                    df = ticker.history(start=start_date, end=end_date, interval=interval, auto_adjust=True, progress=False)
                
                # Convert index to timezone-naive if needed
                if not df.empty and df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
            except Exception:
                pass
            
            # Second try: Get maximum available data if first attempt failed
            if df.empty:
                try:
                    df = ticker.history(period="max", interval="1d", auto_adjust=True, progress=False)
                    if not df.empty:
                        # Convert index to timezone-naive for comparison
                        df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index
                        # Filter to requested date range
                        df = df[(df.index >= start_date) & (df.index <= end_date)]
                except Exception:
                    pass
            
            # Third try: Get recent data if all else fails
            if df.empty:
                try:
                    df = ticker.history(period="5d", interval="1d", auto_adjust=True, progress=False)
                    # Convert index to timezone-naive if needed
                    if not df.empty and df.index.tz is not None:
                        df.index = df.index.tz_localize(None)
                except Exception:
                    pass
            
            if df.empty:
                print(f"Warning: No data available for {symbol}")
                return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
                
            # Resample if needed and interval is not daily
            if not df.empty and interval != "1d" and len(df) > 1:
                try:
                    # Convert interval to pandas frequency format
                    freq_map = {'1h': '1h', '4h': '4h', '1m': '1T'}
                    freq = freq_map.get(interval, interval)
                    df = df.resample(freq).interpolate(method='linear')
                except Exception:
                    pass
                
            # Ensure proper column names
            df = df.rename(columns={
                'Open': 'Open',
                'High': 'High', 
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })
            
            # Fill missing volume data
            if 'Volume' not in df.columns or df['Volume'].isna().all():
                df['Volume'] = 1000000  # Default volume for forex
            
            # Ensure all required columns exist
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'Volume':
                        df[col] = 1000000
                    else:
                        df[col] = df['Close']  # Use Close price as fallback
            
            return df.dropna()
            
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    
    def _generate_synthetic_data(self, start_date, end_date, interval):
        """Generate synthetic forex data for testing purposes."""
        import numpy as np
        
        # Create date range
        if interval == "1h":
            freq = '1h'
        elif interval == "4h":
            freq = '4h'
        elif interval == "1m":
            freq = '1T'
        else:
            freq = '1d'
            
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        if len(date_range) == 0:
            # Fallback to daily if no data points
            date_range = pd.date_range(start=start_date, end=end_date, freq='1d')
        
        # Generate synthetic price data (starting around 1.1000 for EURUSD-like pair)
        base_price = 1.1000
        n_points = len(date_range)
        
        # Generate random walk
        returns = np.random.normal(0, 0.001, n_points)  # 0.1% daily volatility
        prices = [base_price]
        
        for i in range(1, n_points):
            new_price = prices[-1] * (1 + returns[i])
            prices.append(new_price)
        
        # Create OHLC data
        data = []
        for i, (date, price) in enumerate(zip(date_range, prices)):
            # Add some intraday variation
            high = price * (1 + abs(np.random.normal(0, 0.0005)))
            low = price * (1 - abs(np.random.normal(0, 0.0005)))
            open_price = price * (1 + np.random.normal(0, 0.0002))
            close_price = price
            
            data.append({
                'Open': open_price,
                'High': max(open_price, high, close_price),
                'Low': min(open_price, low, close_price),
                'Close': close_price,
                'Volume': 1000000
            })
        
        df = pd.DataFrame(data, index=date_range)
        return df
            
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price from Yahoo Finance."""
        try:
            # Convert forex symbol to yfinance format if needed
            if not symbol.endswith('=X'):
                symbol = symbol.upper() + "=X"
                
            ticker = yf.Ticker(symbol)
            
            # Try to get price from info first
            try:
                info = ticker.info
                if 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
                    return float(info['regularMarketPrice'])
                elif 'currentPrice' in info and info['currentPrice'] is not None:
                    return float(info['currentPrice'])
            except Exception:
                pass
            
            # Fallback to recent data
            try:
                df = ticker.history(period="1d", interval="1m", progress=False)
                if not df.empty and 'Close' in df.columns:
                    return float(df['Close'].iloc[-1])
            except Exception:
                pass
            
            # Second fallback: try daily data
            try:
                df = ticker.history(period="5d", interval="1d", progress=False)
                if not df.empty and 'Close' in df.columns:
                    return float(df['Close'].iloc[-1])
            except Exception:
                pass
                
        except Exception as e:
            print(f"Error getting latest price for {symbol}: {e}")
            
        # Return None if all attempts fail
        return None
    
    def get_historical_data(self, symbol: str, period: str = '1d', interval: str = '1h') -> pd.DataFrame:
        """Get historical data for a symbol with specified period and interval."""
        try:
            # Convert period to start/end dates
            from datetime import datetime, timedelta
            
            # Use timezone-naive datetime objects
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
            
            # Use the existing get_data method
            return self.get_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), interval)
            
        except Exception as e:
            print(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        
    def is_available(self) -> bool:
        """Check if Yahoo Finance is available."""
        return self._available
