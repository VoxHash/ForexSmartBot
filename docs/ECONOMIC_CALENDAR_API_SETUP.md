# Economic Calendar API Setup Guide

The Economic Calendar feature uses real-time data from trusted economic news providers. This guide explains how to set up API keys for the best experience.

## Supported APIs

The Economic Calendar supports multiple API sources with automatic fallback:

1. **TradingEconomics API** (Recommended - Most Comprehensive)
   - Coverage: 196+ countries, real-time economic calendar
   - Cost: Paid subscription required
   - Get API Key: https://tradingeconomics.com/api
   - Environment Variable: `TRADING_ECONOMICS_API_KEY`

2. **Alpha Vantage API** (Free Tier Available)
   - Coverage: Economic indicators, limited calendar
   - Cost: Free tier (5 API calls/minute, 500 calls/day)
   - Get API Key: https://www.alphavantage.co/support/#api-key
   - Environment Variable: `ALPHA_VANTAGE_API_KEY`

3. **FRED API** (Free - US Data Only)
   - Coverage: US economic indicators from Federal Reserve
   - Cost: Free (requires registration)
   - Get API Key: https://fred.stlouisfed.org/docs/api/api_key.html
   - Environment Variable: `FRED_API_KEY`

4. **NewsAPI** (Free Tier Available)
   - Coverage: Economic news articles
   - Cost: Free tier (100 requests/day)
   - Get API Key: https://newsapi.org/register
   - Environment Variable: `NEWS_API_KEY`

## Setup Instructions

### Step 1: Get API Keys

1. **TradingEconomics** (Best for comprehensive calendar):
   - Visit https://tradingeconomics.com/api
   - Sign up for an account
   - Subscribe to a plan
   - Copy your API key

2. **Alpha Vantage** (Free option):
   - Visit https://www.alphavantage.co/support/#api-key
   - Fill out the form
   - Copy your free API key

3. **FRED** (Free US data):
   - Visit https://fred.stlouisfed.org/docs/api/api_key.html
   - Create a free account
   - Copy your API key

4. **NewsAPI** (Free news):
   - Visit https://newsapi.org/register
   - Sign up for free account
   - Copy your API key

### Step 2: Configure Environment Variables

Add your API keys to the `.env` file in the project root:

```env
# Economic Calendar API Keys
TRADING_ECONOMICS_API_KEY=your_trading_economics_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
FRED_API_KEY=your_fred_key_here
NEWS_API_KEY=your_newsapi_key_here
```

### Step 3: Restart Application

After adding API keys, restart the ForexSmartBot application for the changes to take effect.

## API Priority

The system tries APIs in this order:

1. TradingEconomics (if key provided)
2. Alpha Vantage (if key provided)
3. FRED (if key provided)
4. NewsAPI (if key provided)

If no API keys are configured, the calendar will show a message prompting you to set up API keys.

## Free Options

For users who want to use free APIs:

1. **Alpha Vantage** - Free tier with 500 calls/day
2. **FRED** - Completely free, US data only
3. **NewsAPI** - Free tier with 100 requests/day

**Recommended Free Setup:**
- Get Alpha Vantage API key (free)
- Get FRED API key (free)
- Get NewsAPI key (free)

This combination provides good coverage without any cost.

## Troubleshooting

### No Events Showing

If no events are showing:

1. Check that API keys are correctly set in `.env` file
2. Verify API keys are valid and not expired
3. Check console for error messages
4. Ensure you have internet connection
5. Try refreshing the calendar

### API Rate Limits

If you hit rate limits:

- Alpha Vantage: 5 calls/minute, 500/day (free tier)
- NewsAPI: 100 requests/day (free tier)
- Consider upgrading to paid plans for higher limits

### Error Messages

Common errors:

- **"No economic events found"**: No API keys configured or all APIs failed
- **"API rate limit exceeded"**: Too many requests, wait or upgrade plan
- **"Invalid API key"**: Check that your API key is correct

## Support

For API-specific issues:

- TradingEconomics: support@tradingeconomics.com
- Alpha Vantage: support@alphavantage.co
- FRED: https://fred.stlouisfed.org/support
- NewsAPI: support@newsapi.org

