"""Multi-provider data source that tries multiple providers in order."""

import pandas as pd
from typing import Optional, List
from ...core.interfaces import IDataProvider
from .yfinance_provider import YFinanceProvider
from .alpha_vantage_provider import AlphaVantageProvider
from .oanda_provider import OANDAProvider
from .mt4_provider import MT4Provider
from .config import DataProviderConfig


class MultiProvider(IDataProvider):
    """Multi-provider that tries multiple data sources in order."""
    
    def __init__(self, providers: List[IDataProvider] = None, settings_manager=None):
        self.settings_manager = settings_manager
        self.config = DataProviderConfig()
        
        if providers is None:
            # Default providers in order of preference
            self.providers = []
            
            # Add providers based on settings manager or configuration
            if self.settings_manager:
                # Use settings from settings manager
                # Add MT4 provider first if enabled
                if self.settings_manager.get('mt4_data_enabled', False):
                    mt4_host = self.settings_manager.get('mt4_host', '127.0.0.1')
                    mt4_port = self.settings_manager.get('mt4_port', 5555)
                    mt4_provider = MT4Provider(mt4_host, mt4_port)
                    self.providers.append(mt4_provider)
                    print("Added MT4Provider as primary provider")
                
                
                
                
                # Always ensure we have at least one provider as fallback
                if not self.providers:
                    # If no providers available, create a dummy provider that returns empty data
                    from forexsmartbot.adapters.data.dummy_provider import DummyProvider
                    self.providers.append(DummyProvider())
                    print("Added DummyProvider as fallback")
            else:
                # Fallback to configuration
                if self.config.is_provider_enabled('yfinance'):
                    self.providers.append(YFinanceProvider())
                
                if self.config.is_provider_enabled('alpha_vantage'):
                    api_key = self.config.get_alpha_vantage_key()
                    self.providers.append(AlphaVantageProvider(api_key))
                
                if self.config.is_provider_enabled('oanda'):
                    api_key = self.config.get_oanda_key()
                    account_id = self.config.get_oanda_account_id()
                    self.providers.append(OANDAProvider(api_key, account_id))
        else:
            self.providers = providers
        
        # Don't check availability during initialization to prevent hanging
        # Availability will be checked on first use
        self._available = True  # Assume available, will be checked on first use
        self._current_provider = 0  # Start with first provider
        
    def get_data(self, symbol: str, start: str, end: str, 
                interval: str = "1h") -> pd.DataFrame:
        """Get historical data from the first available provider."""
        print(f"MultiProvider: Trying to get data for {symbol} from {len(self.providers)} providers")
        for i, provider in enumerate(self.providers):
            try:
                provider_name = type(provider).__name__
                print(f"Provider {i+1}: {provider_name}, Available: {provider.is_available()}")
                
                if not provider.is_available():
                    print(f"Provider {i+1} ({provider_name}) not available, skipping")
                    continue
                    
                print(f"Trying provider {i+1}/{len(self.providers)} ({provider_name}) for {symbol}")
                df = provider.get_data(symbol, start, end, interval)
                
                if not df.empty:
                    print(f"Successfully got data from provider {i+1} ({provider_name}) for {symbol}")
                    self._current_provider = i
                    return df
                else:
                    print(f"Provider {i+1} ({provider_name}) returned empty data for {symbol}")
                    
            except Exception as e:
                print(f"Provider {i+1} ({provider_name}) failed for {symbol}: {e}")
                continue
        
        print(f"All providers failed for {symbol}")
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price from the first available provider."""
        for i, provider in enumerate(self.providers):
            try:
                if not provider.is_available():
                    continue
                    
                price = provider.get_latest_price(symbol)
                if price is not None:
                    print(f"Got latest price from provider {i+1} for {symbol}")
                    self._current_provider = i
                    return price
                    
            except Exception as e:
                print(f"Provider {i+1} failed for latest price {symbol}: {e}")
                continue
        
        print(f"All providers failed for latest price {symbol}")
        return None
    
    def get_historical_data(self, symbol: str, period: str = '1d', interval: str = '1h') -> pd.DataFrame:
        """Get historical data from the first available provider."""
        print(f"MultiProvider: Trying to get historical data for {symbol} from {len(self.providers)} providers")
        for i, provider in enumerate(self.providers):
            try:
                provider_name = type(provider).__name__
                print(f"Provider {i+1}: {provider_name}, Available: {provider.is_available()}")
                
                if not provider.is_available():
                    print(f"Provider {i+1} ({provider_name}) not available, skipping")
                    continue
                    
                print(f"Trying provider {i+1}/{len(self.providers)} ({provider_name}) for historical data {symbol}")
                df = provider.get_historical_data(symbol, period, interval)
                
                if not df.empty:
                    print(f"Successfully got historical data from provider {i+1} ({provider_name}) for {symbol}")
                    self._current_provider = i
                    return df
                else:
                    print(f"Provider {i+1} ({provider_name}) returned empty historical data for {symbol}")
                    
            except Exception as e:
                print(f"Provider {i+1} ({provider_name}) failed for historical data {symbol}: {e}")
                continue
        
        print(f"All providers failed for historical data {symbol}")
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    
    def is_available(self) -> bool:
        """Check if any provider is available."""
        return self._available
    
    def get_current_provider_name(self) -> str:
        """Get the name of the currently used provider."""
        if self._current_provider < len(self.providers):
            return type(self.providers[self._current_provider]).__name__
        return "Unknown"
    
    def add_provider(self, provider: IDataProvider):
        """Add a new provider to the list."""
        self.providers.append(provider)
        # Don't check availability to prevent hanging
        self._available = True
    
    def remove_provider(self, provider_class):
        """Remove a provider by class."""
        self.providers = [p for p in self.providers if not isinstance(p, provider_class)]
        # Don't check availability to prevent hanging
        self._available = True
