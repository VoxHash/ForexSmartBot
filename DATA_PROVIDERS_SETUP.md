# Data Providers Setup Guide

The ForexSmartBot now supports multiple data providers to ensure reliable forex data access. Here's how to set them up:

## Available Providers

### 1. Yahoo Finance (Default - No Setup Required)
- **Status**: Free, no API key needed
- **Limitations**: Limited forex data, some pairs may not be available
- **Usage**: Works out of the box as fallback

### 2. Alpha Vantage (Recommended)
- **Status**: Free tier available (500 calls/day)
- **Setup Required**: Yes
- **Coverage**: Excellent forex data coverage

#### Setup Steps:
1. Go to https://www.alphavantage.co/support/#api-key
2. Sign up for a free account
3. Get your API key
4. Set environment variable:
   ```bash
   set ALPHA_VANTAGE_API_KEY=your_api_key_here
   ```
5. Or set in code (see below)

### 3. OANDA (Best for Forex)
- **Status**: Free practice account
- **Setup Required**: Yes
- **Coverage**: Professional forex data

#### Setup Steps:
1. Go to https://www.oanda.com/account/tapi/personal_token
2. Create a free practice account
3. Generate an API token
4. Get your account ID
5. Set environment variables:
   ```bash
   set OANDA_API_KEY=your_token_here
   set OANDA_ACCOUNT_ID=your_account_id_here
   ```

## How It Works

The bot uses a **MultiProvider** that tries providers in this order:
1. Yahoo Finance (if available)
2. Alpha Vantage (if API key provided)
3. OANDA (if API key provided)

If one provider fails, it automatically tries the next one.

## Setting Up API Keys

### Method 1: Environment Variables (Recommended)
```bash
# Windows
set ALPHA_VANTAGE_API_KEY=your_key_here
set OANDA_API_KEY=your_token_here
set OANDA_ACCOUNT_ID=your_account_id_here

# Linux/Mac
export ALPHA_VANTAGE_API_KEY=your_key_here
export OANDA_API_KEY=your_token_here
export OANDA_ACCOUNT_ID=your_account_id_here
```

### Method 2: Code Configuration
```python
from forexsmartbot.adapters.data import MultiProvider, DataProviderConfig

# Create configuration
config = DataProviderConfig()
config.set_api_key('alpha_vantage', 'your_key_here')
config.set_api_key('oanda', 'your_token_here')

# Use with multi-provider
provider = MultiProvider()
```

## Testing Your Setup

Run the bot and check the console output. You should see messages like:
```
Trying provider 1/3 for GBPJPY
Successfully got data from provider 2 for GBPJPY
```

## Troubleshooting

### "No data available" warnings
- This means all providers failed for that symbol
- Check your API keys are correct
- Verify internet connection
- Some exotic currency pairs may not be available

### Rate limit errors
- Alpha Vantage free tier: 5 calls per minute
- OANDA: 1000 calls per day
- The bot handles rate limits automatically

### API key errors
- Double-check your API keys
- Ensure environment variables are set correctly
- Restart the application after setting environment variables

## Recommended Setup

For best results, set up both Alpha Vantage and OANDA:
1. Get Alpha Vantage API key (free)
2. Get OANDA practice account (free)
3. Set both environment variables
4. The bot will use the most reliable source for each symbol

This gives you maximum coverage and reliability for forex data!
