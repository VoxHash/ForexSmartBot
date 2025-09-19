# Installation Guide

This guide will walk you through installing ForexSmartBot on your system.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Ubuntu 18.04+
- **Python**: 3.10 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 1GB free space
- **Internet**: Required for data downloads and live trading

### Recommended Requirements
- **Operating System**: Windows 11, macOS 12+, or Ubuntu 20.04+
- **Python**: 3.11 or 3.12
- **RAM**: 8GB or more
- **Storage**: 5GB free space
- **Internet**: Stable broadband connection

## Installation Methods

### Method 1: From Source (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/voxhash/forexsmartbot.git
   cd forexsmartbot
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python app.py --version
   ```

### Method 2: Using pip (Future)

```bash
pip install forexsmartbot
```

### Method 3: Using Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/voxhash/forexsmartbot.git
   cd forexsmartbot
   ```

2. **Build the Docker image**
   ```bash
   docker build -t forexsmartbot .
   ```

3. **Run the container**
   ```bash
   docker run -it --rm -p 8080:8080 forexsmartbot
   ```

## Platform-Specific Instructions

### Windows

1. **Install Python 3.10+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Install Git** (if not already installed)
   - Download from [git-scm.com](https://git-scm.com/download/win)

3. **Follow the general installation steps above**

### macOS

1. **Install Python using Homebrew**
   ```bash
   brew install python@3.11
   ```

2. **Install Git** (if not already installed)
   ```bash
   brew install git
   ```

3. **Follow the general installation steps above**

### Ubuntu/Debian

1. **Update package list**
   ```bash
   sudo apt update
   ```

2. **Install Python and pip**
   ```bash
   sudo apt install python3.11 python3.11-venv python3-pip git
   ```

3. **Follow the general installation steps above**

## Dependencies

### Core Dependencies
- **PyQt6**: GUI framework
- **pandas**: Data manipulation
- **numpy**: Numerical computing
- **yfinance**: Market data
- **pyzmq**: ZeroMQ for MT4 integration
- **matplotlib**: Charting
- **pydantic**: Data validation
- **python-dotenv**: Environment variables

### Optional Dependencies
- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking

## Configuration

### Environment Variables

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

### Settings File

ForexSmartBot creates a settings file at `~/.forexsmartbot/settings.json` on first run. You can modify this file or use the Settings dialog in the application.

## Verification

### Test Installation

1. **Run the application**
   ```bash
   python app.py
   ```

2. **Test backtesting**
   ```bash
   python scripts/run_backtest.py --strategy SMA_Crossover --symbol EURUSD --start 2024-01-01 --end 2024-01-31
   ```

3. **Test walk-forward analysis**
   ```bash
   python scripts/walk_forward.py --strategy SMA_Crossover --symbol EURUSD --start 2024-01-01 --end 2024-12-31
   ```

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=forexsmartbot --cov-report=html
```

## Troubleshooting

### Common Issues

#### Python Not Found
- **Windows**: Add Python to PATH or reinstall with "Add to PATH" checked
- **macOS**: Use `python3` instead of `python`
- **Linux**: Install python3-pip package

#### Permission Denied
- **Windows**: Run Command Prompt as Administrator
- **macOS/Linux**: Use `sudo` for system-wide installation or fix permissions

#### Module Not Found
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`
- Check Python version: `python --version`

#### GUI Issues
- **Linux**: Install GUI dependencies: `sudo apt install python3-pyqt6`
- **macOS**: Install XQuartz if needed
- **Windows**: Ensure Windows 10+ with proper display drivers

### Getting Help

1. Check the [Troubleshooting](Troubleshooting) wiki page
2. Search [GitHub Issues](https://github.com/voxhash/forexsmartbot/issues)
3. Create a new issue with the bug report template
4. Join community discussions

## Quick Start Tutorial

This tutorial will get you up and running with ForexSmartBot in just a few minutes.

### Step 1: Launch the Application

```bash
python app.py
```

You should see the ForexSmartBot main window with:
- Trading controls at the top
- Log and metrics tabs on the left
- Chart area on the right

### Step 2: Configure Basic Settings

#### Select Broker
1. In the "Broker" dropdown, select **"PAPER"** for safe testing
2. Click **"Connect"** - you should see "Connected to PAPER broker" in the log

#### Choose Strategy
1. In the "Strategy" dropdown, select **"SMA_Crossover"**
2. This is a beginner-friendly trend-following strategy

#### Set Trading Symbol
1. In the "Symbols" field, enter **"EURUSD"**
2. You can add multiple symbols separated by commas: `EURUSD,USDJPY,GBPUSD`

#### Configure Risk
1. Set "Risk %" to **2.0** (2% risk per trade)
2. This is a conservative starting point

### Step 3: Start Paper Trading

1. Click **"Start Bot"**
2. You should see "Trading bot started" in the log
3. The bot will begin analyzing the market and generating signals

#### What's Happening
- The bot downloads recent price data for EURUSD
- It calculates technical indicators (SMA, ATR)
- It generates buy/sell signals based on the strategy
- It simulates trades in paper mode (no real money)

### Step 4: Monitor Performance

#### View Logs
- Check the "Log" tab for real-time activity
- Look for signal generation and trade execution messages

#### Check Metrics
- Switch to the "Metrics" tab to see performance statistics
- Monitor equity, drawdown, win rate, and other key metrics

#### View Positions
- The "Positions" tab shows any open trades
- You'll see entry price, current price, and unrealized PnL

### Step 5: Understand the Strategy

#### SMA Crossover Strategy
- **Buy Signal**: Fast SMA crosses above slow SMA
- **Sell Signal**: Fast SMA crosses below slow SMA
- **Stop Loss**: 2x ATR below/above entry price
- **Take Profit**: 3x ATR above/below entry price

#### Risk Management
- Position size is calculated based on your risk percentage
- Stop losses protect against large losses
- Take profits lock in gains

### Step 6: Try Different Strategies

#### Breakout ATR Strategy
1. Stop the bot (click "Stop Bot")
2. Change strategy to **"BreakoutATR"**
3. Start the bot again
4. This strategy looks for price breakouts with volatility filters

#### RSI Reversion Strategy
1. Stop the bot
2. Change strategy to **"RSI_Reversion"**
3. Start the bot again
4. This strategy looks for oversold/overbought conditions

### Step 7: Run a Backtest

#### Basic Backtest
```bash
python scripts/run_backtest.py --strategy SMA_Crossover --symbol EURUSD --start 2024-01-01 --end 2024-12-31
```

#### With Charts
```bash
python scripts/run_backtest.py --strategy SMA_Crossover --symbol EURUSD --start 2024-01-01 --end 2024-12-31 --plot
```

#### Walk-Forward Analysis
```bash
python scripts/walk_forward.py --strategy SMA_Crossover --symbol EURUSD --start 2024-01-01 --end 2024-12-31 --training 252 --testing 63
```

### Step 8: Explore Settings

1. Click **"Settings"** button
2. Explore different tabs:
   - **General**: Strategy and data settings
   - **Broker**: MT4 and API configuration
   - **Risk**: Position sizing and limits
   - **UI**: Theme and display options

### Step 9: Portfolio Mode

#### Enable Portfolio Mode
1. Go to Settings → General
2. Check "Enable Portfolio Mode"
3. Add multiple symbols: `EURUSD,USDJPY,GBPUSD`
4. Start the bot

#### Benefits
- Trade multiple symbols simultaneously
- Diversified risk across currency pairs
- Portfolio-level risk management

### Step 10: Advanced Features

#### Charts
- The chart area shows price data and indicators
- Switch between symbols using the dropdown
- View different time periods

#### Export Data
- Click "Export Trades" to save trade history
- Backtest results are automatically saved
- Logs are saved to `~/.forexsmartbot/logs/`

## Common First-Time Issues

### No Data Available
- Check your internet connection
- Verify the symbol is correct (e.g., "EURUSD" not "EUR/USD")
- Try a different symbol

### No Signals Generated
- The strategy might need more data
- Check if the market is in a suitable condition
- Try a different strategy

### Application Crashes
- Check the log for error messages
- Ensure all dependencies are installed
- Try restarting the application

## Next Steps

After successful installation and quick start:

1. Configure your [Settings](Configuration-Guide)
2. Learn about [Trading Strategies](Trading-Strategies)
3. Set up [Risk Management](Risk-Management)
4. Try [Backtesting](Backtesting-Guide)

## Uninstallation

### Remove from Virtual Environment
```bash
deactivate
rm -rf .venv
```

### Remove from System
```bash
pip uninstall forexsmartbot
```

### Remove Configuration
```bash
# Remove settings directory
rm -rf ~/.forexsmartbot
```

---

*For more detailed information, see the [Configuration Guide](Configuration-Guide) and [Troubleshooting](Troubleshooting) pages.*
