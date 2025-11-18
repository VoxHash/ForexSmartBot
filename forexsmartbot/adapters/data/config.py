"""Configuration for data providers."""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Ensure .env is loaded before reading environment variables
# This is safe to call multiple times - it only loads if not already loaded
load_dotenv(override=False)


class DataProviderConfig:
    """Configuration manager for data providers."""
    
    def __init__(self):
        # Reload env vars to ensure they're available (in case module imported before load_dotenv)
        # This ensures env vars are always available when DataProviderConfig is instantiated
        self.config = {
            'alpha_vantage': {
                'api_key': os.getenv('ALPHA_VANTAGE_API_KEY', 'demo'),
                'enabled': True
            },
            'oanda': {
                'api_key': os.getenv('OANDA_API_KEY', 'demo'),
                'account_id': os.getenv('OANDA_ACCOUNT_ID', '101-001-123456-001'),
                'enabled': True
            },
            'yfinance': {
                'enabled': True
            }
        }
    
    def get_alpha_vantage_key(self) -> str:
        """Get Alpha Vantage API key."""
        return self.config['alpha_vantage']['api_key']
    
    def get_oanda_key(self) -> str:
        """Get OANDA API key."""
        return self.config['oanda']['api_key']
    
    def get_oanda_account_id(self) -> str:
        """Get OANDA account ID."""
        return self.config['oanda']['account_id']
    
    def is_provider_enabled(self, provider_name: str) -> bool:
        """Check if a provider is enabled."""
        return self.config.get(provider_name, {}).get('enabled', False)
    
    def set_api_key(self, provider: str, api_key: str):
        """Set API key for a provider."""
        if provider in self.config:
            self.config[provider]['api_key'] = api_key
    
    def get_setup_instructions(self) -> Dict[str, str]:
        """Get setup instructions for each provider."""
        return {
            'alpha_vantage': """
            Alpha Vantage Setup:
            1. Go to https://www.alphavantage.co/support/#api-key
            2. Get a free API key (500 calls per day)
            3. Set environment variable: ALPHA_VANTAGE_API_KEY=your_key
            4. Or set in code: config.set_api_key('alpha_vantage', 'your_key')
            """,
            'oanda': """
            OANDA Setup:
            1. Go to https://www.oanda.com/account/tapi/personal_token
            2. Create a free practice account
            3. Generate an API token
            4. Set environment variables:
               - OANDA_API_KEY=your_token
               - OANDA_ACCOUNT_ID=your_account_id
            """,
            'yfinance': """
            Yahoo Finance:
            - No setup required (free)
            - Limited forex data availability
            - Used as fallback
            """
        }
