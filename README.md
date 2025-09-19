# 🚀 ForexSmartBot v2.0.0

> **ForexSmartBot** - A professional, modular forex trading bot with advanced risk management, multiple strategies, portfolio mode, and comprehensive backtesting capabilities.

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/voxhash/ForexSmartBot)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org/)
[![PyQt6](https://img.shields.io/badge/pyqt6-6.7+-blue.svg)](https://pypi.org/project/PyQt6/)

## ✨ Features

### 🎯 **Core Trading Features**
- **Multiple Trading Strategies**: SMA Crossover, Breakout ATR, RSI Reversion
- **Advanced Risk Management**: Kelly Criterion, volatility targeting, drawdown protection
- **Portfolio Mode**: Multi-symbol trading with concurrent pipelines
- **Real-time Trading**: Live trading with MetaTrader 4 integration
- **Paper Trading**: Risk-free simulation and testing

### 📊 **Advanced Analytics**
- **Comprehensive Backtesting**: Historical strategy performance analysis
- **Walk-Forward Analysis**: K-fold time series validation
- **Performance Metrics**: Sharpe ratio, drawdown, win rate, profit factor
- **Real-time Charts**: Matplotlib-based charts with technical indicators
- **Export Capabilities**: CSV and JSON export for external analysis

### 🛡️ **Risk Management**
- **Kelly Criterion**: Optimal position sizing based on win rate
- **Volatility Targeting**: Position sizing based on market volatility
- **Drawdown Protection**: Automatic drawdown limits and throttling
- **Daily Risk Limits**: Per-day risk exposure caps
- **Risk Multipliers**: Per-symbol and per-strategy adjustments

### 🎨 **Professional UI**
- **Modern PyQt6 Interface**: Professional dark/light theme support
- **Settings Management**: Comprehensive configuration options
- **Real-time Monitoring**: Live status updates and performance tracking
- **Log Viewer**: Integrated logging display
- **Export Tools**: Trade and data export functionality

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- 4 GB RAM (8 GB recommended)
- 1 GB free disk space
- Windows 10/11, macOS 10.15+, or Linux

### Installation

#### Method 1: Clone Repository (Recommended)
```bash
# Clone the repository
git clone https://github.com/voxhash/ForexSmartBot.git
cd ForexSmartBot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

#### Method 2: Development Installation
```bash
# Install in development mode
pip install -e .

# Run the application
python -m forexsmartbot
```

### First Run
1. **Launch the application**: `python app.py`
2. **Select a strategy** from the dropdown (SMA Crossover, Breakout ATR, RSI Reversion)
3. **Choose a symbol** (e.g., EURUSD, GBPUSD, USDJPY)
4. **Configure risk parameters** in the settings
5. **Start paper trading** to test your setup
6. **Monitor performance** in real-time

## 🎯 Usage

### Basic Trading
```python
from forexsmartbot.adapters.brokers import PaperBroker
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.strategies import SMACrossoverStrategy
from forexsmartbot.core.risk_engine import RiskEngine, RiskConfig

# Initialize components
broker = PaperBroker(initial_balance=10000.0)
data_provider = YFinanceProvider()
strategy = SMACrossoverStrategy()
risk_config = RiskConfig()
risk_engine = RiskEngine(risk_config)

# Get data and generate signals
df = data_provider.get_data("EURUSD", "2024-01-01", "2024-01-31")
df = strategy.calculate_indicators(df)
signal = strategy.signal(df)

# Execute trade if signal
if signal != 0:
    balance = 10000.0
    volatility = strategy.volatility(df)
    size = risk_engine.calculate_position_size("EURUSD", "SMA", balance, volatility)
    order_id = broker.place_order("EURUSD", signal, size, df['Close'].iloc[-1])
```

### Backtesting
```bash
# Run backtest from command line
python scripts/run_backtest.py --strategy SMA_Crossover --symbol EURUSD --start 2024-01-01 --end 2024-01-31 --plot

# Run walk-forward analysis
python scripts/walk_forward.py --strategy SMA_Crossover --symbol EURUSD --start 2024-01-01 --end 2024-12-31 --train 30 --test 7
```

### Configuration
Access settings via **Settings** button or `Ctrl+,`:
- **Risk Management**: Base risk %, max trade amount, drawdown limits
- **Broker Settings**: MT4 connection, paper trading options
- **Data Source**: Yahoo Finance, CSV files, custom providers
- **UI Preferences**: Theme, default symbols, display options

## 📊 Trading Strategies

### SMA Crossover Strategy
- **Description**: Moving average crossover with ATR-based stops
- **Parameters**: Fast SMA (10), Slow SMA (20), ATR Period (14)
- **Best For**: Trending markets
- **Risk Level**: Medium

### Breakout ATR Strategy
- **Description**: Donchian channel breakouts with ATR filter
- **Parameters**: Lookback (20), ATR Period (14), ATR Multiplier (2.0)
- **Best For**: Volatile markets
- **Risk Level**: High

### RSI Reversion Strategy
- **Description**: RSI mean reversion with trend filter
- **Parameters**: RSI Period (14), Oversold (30), Overbought (70), SMA Period (50)
- **Best For**: Ranging markets
- **Risk Level**: Low

## 🛡️ Risk Management

### Position Sizing
- **Kelly Criterion**: Optimal sizing based on win rate and average win/loss
- **Volatility Targeting**: Adjust size based on market volatility
- **Risk Multipliers**: Per-symbol and per-strategy adjustments
- **Daily Limits**: Maximum daily risk exposure

### Safety Features
- **Drawdown Protection**: Automatic position size reduction during drawdowns
- **Daily Risk Caps**: Prevent excessive daily losses
- **Live Trade Confirmations**: Modal confirmations for live orders
- **Risk Warnings**: Built-in risk notifications

## 📈 Backtesting & Analysis

### Performance Metrics
- **Total Return**: Overall strategy performance
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss

### Walk-Forward Analysis
- **Purpose**: Validate strategy robustness across different time periods
- **Method**: Rolling training and testing periods
- **Output**: Performance statistics and equity curves
- **Use Case**: Strategy optimization and validation

## 🔧 Development

### Project Structure
```
ForexSmartBot/
├── forexsmartbot/          # Main package
│   ├── core/              # Core business logic
│   ├── adapters/          # External integrations
│   ├── strategies/        # Trading strategies
│   ├── services/          # Application services
│   └── ui/               # User interface
├── tests/                 # Test suite
├── scripts/              # Command-line tools
├── docs/                 # Documentation
└── data/                 # Data storage
```

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=forexsmartbot

# Run specific test
python -m pytest tests/test_risk.py::TestRiskEngine::test_position_sizing
```

### Code Quality
```bash
# Run linting
ruff check .

# Run type checking
mypy forexsmartbot/

# Format code
black forexsmartbot/
```

## 📚 Documentation

- **[Installation Guide](docs/Installation-Guide.md)** - Detailed setup instructions
- **[Quick Start Tutorial](docs/Quick-Start-Tutorial.md)** - Getting started guide
- **[Configuration Guide](docs/Configuration-Guide.md)** - Configuration options
- **[API Reference](docs/API-REFERENCE.md)** - Complete API documentation
- **[Strategy Development](docs/STRATEGIES.md)** - Creating custom strategies
- **[Risk Management](docs/RISK.md)** - Advanced risk management
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[FAQ](docs/FAQ.md)** - Frequently asked questions

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and upcoming features.

## 🎯 Roadmap

See [ROADMAP.md](ROADMAP.md) for future development plans and feature roadmap.

## ⚠️ Disclaimer

**IMPORTANT**: This software is for educational and research purposes only. Trading forex involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results.

- **No Financial Advice**: This software does not provide financial advice
- **Risk of Loss**: You could lose some or all of your invested capital
- **Test First**: Always test thoroughly with paper trading
- **Seek Professional Advice**: Consult qualified financial advisors

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Acknowledgments

- **PyQt6** - Modern GUI framework
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **Matplotlib** - Charting and visualization
- **Yahoo Finance** - Free market data
- **Community** - Feedback and contributions

---

**Made with ❤️ by VoxHash**

*ForexSmartBot - Professional forex trading made simple!* 🚀💰