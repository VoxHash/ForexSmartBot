"""Dummy data provider that returns empty data."""

import pandas as pd
from typing import Optional, Dict
from ...core.interfaces import IDataProvider


class DummyProvider(IDataProvider):
    """Dummy data provider that returns empty data."""
    
    def __init__(self):
        super().__init__()
        self._available = True
        
    def get_historical_data(self, symbol: str, period: str = '1d', 
                          interval: str = '1h') -> pd.DataFrame:
        """Return empty DataFrame."""
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Return None for latest price."""
        return None
    
    def get_data(self, symbol: str, start: str, end: str, 
                interval: str = "1h") -> pd.DataFrame:
        """Return empty DataFrame."""
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    
    def is_available(self) -> bool:
        """Always return True."""
        return True
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Return None for symbol info."""
        return None
