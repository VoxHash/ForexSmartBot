# Frequently Asked Questions (FAQ)

Common questions and answers about ForexSmartBot.

## Table of Contents

- [General Questions](#general-questions)
- [Installation & Setup](#installation--setup)
- [Trading & Strategies](#trading--strategies)
- [Risk Management](#risk-management)
- [Data & Brokers](#data--brokers)
- [Backtesting](#backtesting)
- [UI & Configuration](#ui--configuration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## General Questions

### What is ForexSmartBot?

ForexSmartBot is a professional, modular forex trading bot with advanced risk management, multiple trading strategies, portfolio mode, and comprehensive backtesting capabilities. It's designed for both paper trading and live trading with MetaTrader 4.

### Is ForexSmartBot free to use?

Yes, ForexSmartBot is open-source and free to use. It's released under the MIT License, which allows you to use, modify, and distribute the software freely.

### What programming language is ForexSmartBot written in?

ForexSmartBot is written in Python 3.11+ and uses PyQt6 for the graphical user interface.

### Can I use ForexSmartBot for live trading?

Yes, ForexSmartBot supports live trading through MetaTrader 4 integration. However, always test thoroughly with paper trading first and understand the risks involved in live trading.

### Is ForexSmartBot suitable for beginners?

ForexSmartBot is designed to be user-friendly, but forex trading involves significant risk. Beginners should:
- Start with paper trading
- Learn about risk management
- Understand the strategies being used
- Never risk more than you can afford to lose

## Installation & Setup

### What are the system requirements?

**Minimum Requirements**:
- Python 3.11 or higher
- 4 GB RAM
- 1 GB free disk space
- Windows 10/11, macOS 10.15+, or Linux

**Recommended Requirements**:
- Python 3.12
- 8 GB RAM
- 5 GB free disk space
- SSD storage

### How do I install ForexSmartBot?

1. **Clone the repository**:
   ```bash
   git clone https://github.com/voxhash/ForexSmartBot.git
   cd ForexSmartBot
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

### Do I need to install MetaTrader 4?

MetaTrader 4 is only required if you want to use live trading. For paper trading and backtesting, MT4 is not needed.

### How do I set up MetaTrader 4 integration?

1. Install MetaTrader 4
2. Download the ZeroMQ bridge EA from the project repository
3. Install the EA in MT4's `Experts` folder
4. Configure the EA with the correct host and port
5. Start the EA in MT4
6. Configure ForexSmartBot to connect to the same host/port

### Can I install ForexSmartBot on a VPS?

Yes, ForexSmartBot can run on a VPS. You'll need:
- A VPS with Python 3.11+
- X11 forwarding for GUI (or use headless mode)
- Stable internet connection
- Sufficient resources for your trading needs

## Trading & Strategies

### What trading strategies are available?

ForexSmartBot includes three built-in strategies:

1. **SMA Crossover**: Uses Simple Moving Average crossovers with ATR-based stops
2. **Breakout ATR**: Donchian channel breakouts with ATR filter
3. **RSI Reversion**: RSI mean reversion with trend filter

### Can I create my own trading strategies?

Yes! ForexSmartBot has a plugin architecture for strategies. Create a new strategy by:

1. Inheriting from `IStrategy`
2. Implementing required methods
3. Registering the strategy
4. Using it in the application

See [Strategy Development Guide](STRATEGIES.md) for details.

### How do I choose the right strategy?

Strategy selection depends on:
- Market conditions (trending vs. ranging)
- Your risk tolerance
- Time frame
- Backtesting results

Test different strategies with backtesting to see which works best for your chosen symbols and time periods.

### Can I use multiple strategies simultaneously?

Yes, ForexSmartBot supports portfolio mode where you can run different strategies on different symbols simultaneously.

### How often does the bot check for signals?

The bot checks for signals based on the data interval you've configured. For example:
- 1-minute data: Checks every minute
- 1-hour data: Checks every hour
- 1-day data: Checks once per day

### Can I modify strategy parameters?

Yes, strategy parameters can be modified through the UI or by editing the strategy code. The UI provides a settings dialog for easy parameter adjustment.

## Risk Management

### How does risk management work?

ForexSmartBot uses multiple risk management techniques:

1. **Position Sizing**: Kelly Criterion and volatility targeting
2. **Drawdown Protection**: Limits maximum drawdown
3. **Daily Risk Limits**: Caps daily risk exposure
4. **Stop Losses**: Automatic stop loss placement
5. **Risk Multipliers**: Per-symbol and per-strategy adjustments

### What is the Kelly Criterion?

The Kelly Criterion is a mathematical formula for optimal position sizing based on win rate and average win/loss ratio. ForexSmartBot uses a modified version that's more conservative.

### How do I set appropriate risk levels?

Risk levels depend on your:
- Account size
- Risk tolerance
- Trading experience
- Market conditions

Start with conservative settings (1-2% risk per trade) and adjust based on your results.

### Can I set different risk levels for different symbols?

Yes, ForexSmartBot supports per-symbol risk multipliers. You can set higher risk for more liquid symbols and lower risk for volatile ones.

### What happens if I hit the drawdown limit?

When the drawdown limit is reached:
- New trades are blocked
- Existing positions may be closed
- Risk engine enters "throttle mode"
- You'll need to manually reset the limit

### How do I calculate position sizes?

Position sizes are calculated using:
1. Base risk percentage of account balance
2. Volatility targeting (higher volatility = smaller positions)
3. Kelly Criterion adjustment
4. Symbol and strategy risk multipliers
5. Daily and drawdown limits

## Data & Brokers

### What data sources are supported?

Currently supported:
- **Yahoo Finance**: Free, delayed data
- **CSV Files**: Your own historical data
- **MetaTrader 4**: Live data via ZeroMQ

### How do I get real-time data?

For real-time data, you need:
1. MetaTrader 4 with a broker account
2. ZeroMQ bridge EA installed
3. ForexSmartBot configured to connect to MT4

### Can I use my own data?

Yes, you can use CSV files with your own data. The CSV should have columns: Date, Open, High, Low, Close, Volume.

### What brokers are supported?

Currently supported:
- **Paper Trading**: Built-in simulation
- **MetaTrader 4**: Via ZeroMQ bridge
- **REST API**: Placeholder for future implementation

### How do I connect to my broker?

1. **Paper Trading**: No setup required
2. **MT4**: Install bridge EA, configure host/port
3. **REST API**: Configure API credentials (when available)

### Is my data secure?

ForexSmartBot stores data locally in `~/.forexsmartbot/`. No data is sent to external servers except for:
- Yahoo Finance data requests
- MetaTrader 4 communication (if enabled)

## Backtesting

### How accurate is backtesting?

Backtesting accuracy depends on:
- Data quality
- Strategy implementation
- Market conditions
- Slippage and commission assumptions

Past performance doesn't guarantee future results.

### What metrics are provided?

Backtesting provides:
- Total return and annualized return
- Maximum drawdown
- Sharpe ratio
- Win rate and profit factor
- Average win/loss
- Total trades

### Can I backtest multiple strategies?

Yes, you can:
- Backtest individual strategies
- Compare multiple strategies
- Run walk-forward analysis
- Test portfolio combinations

### How do I interpret backtest results?

Key metrics to consider:
- **Total Return**: Overall performance
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss

### What is walk-forward analysis?

Walk-forward analysis tests strategies on rolling time periods to:
- Validate strategy robustness
- Avoid overfitting
- Test different market conditions
- Provide more realistic performance estimates

### Can I export backtest results?

Yes, backtest results can be exported as:
- CSV files (equity curves, trades)
- JSON files (detailed results)
- PNG images (charts)

## UI & Configuration

### How do I change the theme?

Use the theme selector in the main window or settings dialog. Available themes:
- **Auto**: Follows system theme
- **Light**: Light theme
- **Dark**: Dark theme

### Where are settings stored?

Settings are stored in `~/.forexsmartbot/settings.json` and include:
- Theme preferences
- Default symbols
- Risk parameters
- Broker settings
- UI preferences

### Can I customize the UI?

The UI is built with PyQt6 and can be customized by:
- Modifying the theme files
- Editing the UI code
- Creating custom widgets

### How do I view my trading history?

Trading history is available in:
- **Trades tab**: Recent trades
- **Export CSV**: Download all trades
- **Database**: SQLite database in `~/.forexsmartbot/trades.db`

### Can I run ForexSmartBot headless?

Yes, you can run ForexSmartBot without the GUI by using the command-line interface for backtesting and automated trading.

## Troubleshooting

### The application won't start

Common solutions:
1. Check Python version (3.11+ required)
2. Verify all dependencies are installed
3. Check for permission issues
4. Review error logs

### No trading signals are generated

Check:
1. Data is loading correctly
2. Strategy parameters are appropriate
3. Market conditions match strategy
4. Indicators are calculating properly

### Connection to MT4 fails

Verify:
1. MT4 is running
2. Bridge EA is installed and running
3. Host and port settings are correct
4. Firewall isn't blocking the connection

### Backtesting is slow

Optimize by:
1. Using smaller date ranges
2. Reducing data frequency
3. Optimizing strategy code
4. Using more efficient data types

### Memory usage is high

Reduce memory usage by:
1. Processing data in chunks
2. Clearing unused variables
3. Using appropriate data types
4. Limiting historical data

## Development

### How do I contribute to ForexSmartBot?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### What coding standards are used?

ForexSmartBot follows:
- PEP 8 style guidelines
- Type hints for all functions
- Google-style docstrings
- 100-character line limit

### How do I run the tests?

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=forexsmartbot

# Run specific test
python -m pytest tests/test_risk.py
```

### Can I add new brokers?

Yes, add new brokers by:
1. Implementing the `IBroker` interface
2. Adding broker-specific logic
3. Registering the broker
4. Updating the UI

### How do I add new data providers?

Add new data providers by:
1. Implementing the `IDataProvider` interface
2. Adding data fetching logic
3. Registering the provider
4. Updating the UI

### Is there a plugin system?

Yes, ForexSmartBot supports plugins for:
- Trading strategies
- Data providers
- Brokers
- Risk managers
- UI components

### How do I report bugs?

Report bugs by:
1. Creating a GitHub issue
2. Providing detailed information
3. Including steps to reproduce
4. Attaching relevant logs

### How do I request features?

Request features by:
1. Creating a GitHub issue
2. Describing the feature
3. Explaining the use case
4. Providing implementation ideas

## Additional Resources

### Documentation
- [Installation Guide](Installation-Guide.md)
- [Quick Start Tutorial](Quick-Start-Tutorial.md)
- [Configuration Guide](Configuration-Guide.md)
- [Strategy Development](STRATEGIES.md)
- [Risk Management](RISK.md)
- [API Reference](API-REFERENCE.md)

### Community
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and ideas
- Wiki: Additional documentation and examples

### Support
- Check the troubleshooting guide
- Search existing issues
- Create a new issue with detailed information
- Join the community discussions
