# Configuration Guide

This guide covers all configuration options available in ForexSmartBot.

## Configuration Methods

### 1. Settings Dialog (Recommended)
Access via the "Settings" button in the main window.

### 2. Environment Variables
Create a `.env` file in the project root.

### 3. Settings File
Modify `~/.forexsmartbot/settings.json` directly.

## General Settings

### Strategy Configuration
- **Default Strategy**: Choose the default trading strategy
- **Data Provider**: Select data source (yfinance, csv)
- **Data Interval**: Timeframe for data (1m, 5m, 15m, 1h, 4h, 1d)
- **Portfolio Mode**: Enable multi-symbol trading
- **Live Trade Confirmation**: Require confirmation for live trades

### Example Configuration
```json
{
  "strategy": "SMA_Crossover",
  "data_provider": "yfinance",
  "data_interval": "1h",
  "portfolio_mode": false,
  "confirm_live_trades": true
}
```

## Broker Settings

### Paper Trading
- **Mode**: PAPER
- **Initial Balance**: Starting capital (default: $10,000)

### MetaTrader 4
- **Mode**: MT4
- **Host**: ZeroMQ server host (default: 127.0.0.1)
- **Port**: ZeroMQ server port (default: 5555)

### REST API
- **Mode**: REST
- **API Key**: Your broker's API key
- **API Secret**: Your broker's API secret
- **Base URL**: Broker's API endpoint

### Example Configuration
```json
{
  "broker_mode": "PAPER",
  "mt4_host": "127.0.0.1",
  "mt4_port": 5555,
  "rest_api_key": "",
  "rest_api_secret": "",
  "rest_base_url": "https://api.broker.com"
}
```

## Risk Management Settings

### Position Sizing
- **Base Risk %**: Risk per trade as percentage of balance (default: 2%)
- **Max Risk %**: Maximum risk per trade (default: 5%)
- **Min Trade Amount**: Minimum position size in dollars (default: $10)
- **Max Trade Amount**: Maximum position size in dollars (default: $100)

### Drawdown Control
- **Max Drawdown %**: Maximum allowed drawdown (default: 25%)
- **Daily Risk Cap %**: Daily loss limit (default: 5%)

### Example Configuration
```json
{
  "risk_pct": 0.02,
  "max_risk_pct": 0.05,
  "trade_amount_min": 10.0,
  "trade_amount_max": 100.0,
  "max_drawdown_pct": 0.25,
  "daily_risk_cap": 0.05
}
```

## UI Settings

### Theme
- **Auto**: Follow system theme
- **Light**: Light theme
- **Dark**: Dark theme

### Symbols
- **Default Symbols**: Comma-separated list of default symbols
- **Selected Symbols**: Currently active symbols

### Example Configuration
```json
{
  "theme": "auto",
  "default_symbols": ["EURUSD", "USDJPY", "GBPUSD"],
  "selected_symbols": ["EURUSD"]
}
```

## Environment Variables

### Creating .env File
Create a `.env` file in the project root:

```env
# Broker settings
BROKER_MODE=PAPER
MT4_ZMQ_HOST=127.0.0.1
MT4_ZMQ_PORT=5555

# Risk settings
RISK_PCT=0.02
MAX_DRAWDOWN_PCT=0.25
TRADE_AMOUNT_MIN=10
TRADE_AMOUNT_MAX=100

# UI settings
THEME=auto
DEFAULT_SYMBOLS=EURUSD,USDJPY,GBPUSD
```

### Environment Variable Override
Environment variables override settings file values:
1. `.env` file
2. System environment variables
3. Settings file defaults

## Advanced Configuration

### Symbol-Specific Risk
Configure different risk levels for different symbols:

```json
{
  "symbol_risk_multipliers": {
    "EURUSD": 1.0,
    "GBPUSD": 1.2,
    "USDJPY": 0.8
  }
}
```

### Strategy-Specific Risk
Configure different risk levels for different strategies:

```json
{
  "strategy_risk_multipliers": {
    "SMA_Crossover": 1.0,
    "BreakoutATR": 1.5,
    "RSI_Reversion": 0.7
  }
}
```

### Data Provider Settings

#### Yahoo Finance
```json
{
  "data_provider": "yfinance",
  "data_interval": "1h",
  "data_retries": 3,
  "data_timeout": 30
}
```

#### CSV Provider
```json
{
  "data_provider": "csv",
  "csv_directory": "data/csv",
  "csv_format": "standard"
}
```

## Configuration Validation

### Settings Validation
ForexSmartBot validates all settings on startup:
- Required fields are present
- Values are within valid ranges
- Dependencies are satisfied

### Common Validation Errors
- **Invalid Risk %**: Must be between 0.001 and 0.1
- **Invalid Symbol**: Must be valid forex pair format
- **Invalid Broker**: Must be PAPER, MT4, or REST
- **Missing API Keys**: Required for REST broker

## Configuration Files

### Settings File Location
- **Windows**: `%USERPROFILE%\.forexsmartbot\settings.json`
- **macOS**: `~/.forexsmartbot/settings.json`
- **Linux**: `~/.forexsmartbot/settings.json`

### Log Files Location
- **Windows**: `%USERPROFILE%\.forexsmartbot\logs\`
- **macOS**: `~/.forexsmartbot/logs/`
- **Linux**: `~/.forexsmartbot/logs/`

### Database Location
- **Windows**: `%USERPROFILE%\.forexsmartbot\trades.db`
- **macOS**: `~/.forexsmartbot/trades.db`
- **Linux**: `~/.forexsmartbot/trades.db`

## Configuration Examples

### Conservative Trading
```json
{
  "risk_pct": 0.01,
  "max_risk_pct": 0.02,
  "max_drawdown_pct": 0.15,
  "daily_risk_cap": 0.03,
  "strategy": "SMA_Crossover"
}
```

### Aggressive Trading
```json
{
  "risk_pct": 0.05,
  "max_risk_pct": 0.10,
  "max_drawdown_pct": 0.30,
  "daily_risk_cap": 0.08,
  "strategy": "BreakoutATR"
}
```

### Portfolio Mode
```json
{
  "portfolio_mode": true,
  "selected_symbols": ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD"],
  "symbol_risk_multipliers": {
    "EURUSD": 1.0,
    "USDJPY": 0.8,
    "GBPUSD": 1.2,
    "AUDUSD": 1.1
  }
}
```

## Troubleshooting Configuration

### Settings Not Saving
- Check file permissions
- Ensure directory exists
- Verify JSON syntax

### Invalid Configuration
- Check validation errors in log
- Verify all required fields
- Ensure values are within ranges

### Environment Variables Not Working
- Check `.env` file location
- Verify variable names
- Restart application after changes

## Best Practices

### Security
- Never commit `.env` files to version control
- Use strong API keys and secrets
- Regularly rotate credentials

### Performance
- Use appropriate data intervals
- Limit number of symbols in portfolio mode
- Monitor memory usage

### Reliability
- Test configurations with paper trading
- Keep backups of working configurations
- Document custom settings

## Configuration Migration

### Upgrading Versions
- Settings are automatically migrated
- Old settings are backed up
- Check release notes for breaking changes

### Backup and Restore
```bash
# Backup settings
cp ~/.forexsmartbot/settings.json settings_backup.json

# Restore settings
cp settings_backup.json ~/.forexsmartbot/settings.json
```

---

*For more detailed information, see the [Installation Guide](Installation-Guide) and [Troubleshooting](Troubleshooting) pages.*
