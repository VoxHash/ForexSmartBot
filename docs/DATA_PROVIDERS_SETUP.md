# Data Providers Setup Guide

ForexSmartBot supports multiple real market data providers through `MultiProvider` fallback.

## Supported Providers

1. **MT4 Provider** (local terminal feed)
2. **OANDA Provider** (official API)
3. **Twelve Data Provider** (official API)
4. **Alpha Vantage Provider** (official API)
5. **Stooq Provider** (public market data endpoint)
6. **Yahoo Finance Provider** (public market data endpoint)

## Provider Fallback Order

`MultiProvider` attempts providers in this order (when configured):

1. MT4 (if enabled)
2. OANDA (if credentials available)
3. Twelve Data (if API key available)
4. Alpha Vantage (if API key available)
5. Stooq
6. Yahoo Finance

If one provider fails, the next provider is tried automatically.

## Environment Variables

Set provider credentials before launching the app:

```bash
# OANDA
export OANDA_API_KEY=your_oanda_api_token
export OANDA_ACCOUNT_ID=your_oanda_account_id

# Twelve Data
export TWELVE_DATA_API_KEY=your_twelve_data_api_key

# Alpha Vantage
export ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
```

Windows (PowerShell):

```powershell
$env:OANDA_API_KEY="your_oanda_api_token"
$env:OANDA_ACCOUNT_ID="your_oanda_account_id"
$env:TWELVE_DATA_API_KEY="your_twelve_data_api_key"
$env:ALPHA_VANTAGE_API_KEY="your_alpha_vantage_api_key"
```

## Notes

- For latency-critical live execution, use MT4/OANDA/Twelve Data as primary sources.
- Public endpoints (Stooq/Yahoo Finance) are useful fallback sources.
- Always test broker/data connectivity in Settings before live sessions.
