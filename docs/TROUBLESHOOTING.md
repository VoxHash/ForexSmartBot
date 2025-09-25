# Troubleshooting Guide

Common issues and solutions for ForexSmartBot.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Runtime Errors](#runtime-errors)
- [Trading Issues](#trading-issues)
- [Performance Issues](#performance-issues)
- [UI Issues](#ui-issues)
- [Data Issues](#data-issues)
- [Broker Issues](#broker-issues)
- [Backtesting Issues](#backtesting-issues)
- [Debugging Tips](#debugging-tips)

## Installation Issues

### Python Version Compatibility

**Problem**: `ModuleNotFoundError` or version conflicts during installation.

**Solution**:
```bash
# Check Python version
python --version

# Should be 3.11 or higher
# If not, install Python 3.11+ from python.org

# Create fresh virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### PyQt6 Installation Issues

**Problem**: PyQt6 installation fails on some systems.

**Solution**:
```bash
# Try installing system dependencies first
# Ubuntu/Debian:
sudo apt-get install python3-pyqt6

# macOS with Homebrew:
brew install pyqt6

# Windows: Use pre-compiled wheels
pip install --only-binary=all PyQt6

# If still failing, try:
pip install --upgrade setuptools wheel
pip install PyQt6
```

### Pandas Compatibility Issues

**Problem**: `stdalign.h` header file missing or pandas installation fails.

**Solution**:
```bash
# Update pip and setuptools
python -m pip install --upgrade pip setuptools wheel

# Install pandas with specific version
pip install "pandas>=2.2.0"

# If still failing, try:
pip install --no-cache-dir pandas
```

## Runtime Errors

### Module Import Errors

**Problem**: `ModuleNotFoundError: No module named 'forexsmartbot'`

**Solution**:
```bash
# Ensure you're in the project root directory
cd /path/to/ForexSmartBot

# Install in development mode
pip install -e .

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Permission Errors

**Problem**: Permission denied when creating directories or files.

**Solution**:
```bash
# Create data directory with proper permissions
mkdir -p ~/.forexsmartbot
chmod 755 ~/.forexsmartbot

# On Windows, run as administrator if needed
# Or change directory permissions in Properties
```

### Memory Issues

**Problem**: `MemoryError` during backtesting or data processing.

**Solution**:
```python
# Reduce data size
df = df.tail(1000)  # Use only last 1000 rows

# Process data in chunks
chunk_size = 100
for i in range(0, len(df), chunk_size):
    chunk = df.iloc[i:i+chunk_size]
    # Process chunk

# Clear unused variables
del large_dataframe
import gc
gc.collect()
```

## Trading Issues

### No Trading Signals

**Problem**: Strategy not generating any signals.

**Debugging Steps**:
1. Check if data is being loaded correctly
2. Verify strategy parameters
3. Check indicator calculations
4. Review signal generation logic

**Solution**:
```python
# Debug strategy signals
strategy = SMACrossoverStrategy(fast=5, slow=10)  # Use shorter periods
df = data_provider.get_data("EURUSD", "2024-01-01", "2024-01-31")
df = strategy.calculate_indicators(df)

# Check indicators
print(df[['Close', 'SMA_fast', 'SMA_slow']].tail())

# Check signals
for i in range(len(df)):
    signal = strategy.signal(df.iloc[:i+1])
    if signal != 0:
        print(f"Signal at {i}: {signal}")
```

### Position Sizing Issues

**Problem**: Position sizes are too small or too large.

**Solution**:
```python
# Check risk configuration
config = RiskConfig(
    base_risk_pct=0.02,      # 2% base risk
    max_trade_amount=1000.0,  # Increase max trade size
    min_trade_amount=10.0     # Decrease min trade size
)

# Check volatility calculation
volatility = strategy.volatility(df)
print(f"Volatility: {volatility}")

# Check position size calculation
balance = portfolio.get_total_balance()
size = risk_engine.calculate_position_size("EURUSD", "SMA", balance, volatility)
print(f"Position size: {size}")
```

### Risk Management Errors

**Problem**: Risk limits preventing trades.

**Solution**:
```python
# Check daily risk limit
daily_risk = risk_engine.get_daily_risk_used()
print(f"Daily risk used: {daily_risk}")

# Check drawdown
current_equity = portfolio.get_total_equity()
peak_equity = risk_engine.get_peak_equity()
drawdown = (peak_equity - current_equity) / peak_equity
print(f"Current drawdown: {drawdown:.2%}")

# Reset risk limits if needed
risk_engine.reset_daily_risk()
```

## Performance Issues

### Slow Backtesting

**Problem**: Backtesting takes too long.

**Solution**:
```python
# Use smaller date ranges
start_date = "2024-01-01"
end_date = "2024-01-31"  # Instead of full year

# Reduce data frequency
df = data_provider.get_data(symbol, start_date, end_date, interval="1h")

# Optimize strategy calculations
# Cache indicator calculations
# Use vectorized operations instead of loops
```

### High Memory Usage

**Problem**: Application uses too much memory.

**Solution**:
```python
# Monitor memory usage
import psutil
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")

# Clear unused data
del old_dataframe
import gc
gc.collect()

# Use data types that use less memory
df['Close'] = df['Close'].astype('float32')
```

### UI Freezing

**Problem**: UI becomes unresponsive during long operations.

**Solution**:
```python
# Use threading for long operations
from PyQt6.QtCore import QThread, pyqtSignal

class DataThread(QThread):
    data_ready = pyqtSignal(pd.DataFrame)
    
    def run(self):
        data = data_provider.get_data(symbol, start, end)
        self.data_ready.emit(data)

# In main thread
thread = DataThread()
thread.data_ready.connect(self.on_data_ready)
thread.start()
```

## UI Issues

### Theme Not Applying

**Problem**: Dark/light theme not working correctly.

**Solution**:
```python
# Check theme detection
from darkdetect import isDark
print(f"System is dark: {isDark()}")

# Manually set theme
theme_manager = ThemeManager()
theme_manager.set_theme("dark")  # or "light"
theme_manager.apply_theme(app)
```

### Charts Not Displaying

**Problem**: Matplotlib charts not showing in UI.

**Solution**:
```python
# Check matplotlib backend
import matplotlib
print(f"Backend: {matplotlib.get_backend()}")

# Set Qt5Agg backend for PyQt6
matplotlib.use('Qt5Agg')

# Check if chart widget is properly embedded
chart_widget = ChartWidget()
layout.addWidget(chart_widget)
```

### Settings Not Saving

**Problem**: Settings dialog changes not persisting.

**Solution**:
```python
# Check settings file permissions
import os
settings_file = os.path.expanduser("~/.forexsmartbot/settings.json")
print(f"Settings file exists: {os.path.exists(settings_file)}")
print(f"Settings file writable: {os.access(os.path.dirname(settings_file), os.W_OK)}")

# Check persistence service
persistence = PersistenceService()
settings = persistence.load_settings()
print(f"Loaded settings: {settings}")
```

## Data Issues

### No Data Available

**Problem**: Data provider returns empty DataFrame.

**Solution**:
```python
# Check data provider availability
if not data_provider.is_available():
    print("Data provider not available")

# Check symbol format
symbol = "EURUSD=X"  # Yahoo Finance format
# or
symbol = "EURUSD"    # Some providers use this format

# Check date format
start_date = "2024-01-01"  # YYYY-MM-DD format
end_date = "2024-01-31"

# Try different intervals
data = data_provider.get_data(symbol, start_date, end_date, "1d")
```

### Data Quality Issues

**Problem**: Missing or incorrect data.

**Solution**:
```python
# Check for missing values
print(f"Missing values: {df.isnull().sum()}")

# Fill missing values
df = df.fillna(method='ffill')  # Forward fill
df = df.dropna()  # Drop rows with any missing values

# Check data types
print(df.dtypes)

# Convert to proper types
df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
```

### Slow Data Loading

**Problem**: Data loading takes too long.

**Solution**:
```python
# Use caching
import pickle

cache_file = f"data/cache/{symbol}_{start_date}_{end_date}.pkl"
if os.path.exists(cache_file):
    with open(cache_file, 'rb') as f:
        df = pickle.load(f)
else:
    df = data_provider.get_data(symbol, start_date, end_date)
    with open(cache_file, 'wb') as f:
        pickle.dump(df, f)

# Use smaller date ranges
# Load data in chunks
```

## Broker Issues

### MT4 Connection Failed

**Problem**: Cannot connect to MetaTrader 4.

**Solution**:
```python
# Check ZeroMQ installation
import zmq
print(f"ZMQ version: {zmq.zmq_version()}")

# Check MT4 bridge
# Ensure MT4 bridge EA is running
# Check host and port settings
broker = MT4Broker(host="localhost", port=5555)
if not broker.connect():
    print("Failed to connect to MT4")
    print("Check if MT4 bridge EA is running")
    print("Verify host and port settings")
```

### Paper Trading Issues

**Problem**: Paper broker not working correctly.

**Solution**:
```python
# Check paper broker state
broker = PaperBroker(initial_balance=10000.0)
print(f"Connected: {broker.connect()}")
print(f"Balance: {broker.get_balance()}")

# Check order placement
order_id = broker.place_order("EURUSD", 1, 100.0, 1.1000)
print(f"Order ID: {order_id}")

# Check positions
positions = broker.get_positions()
print(f"Positions: {positions}")
```

## Backtesting Issues

### Backtest Results Seem Wrong

**Problem**: Backtest results don't match expectations.

**Solution**:
```python
# Check data quality
print(f"Data shape: {df.shape}")
print(f"Date range: {df.index[0]} to {df.index[-1]}")
print(f"Missing values: {df.isnull().sum().sum()}")

# Check strategy signals
signals = []
for i in range(len(df)):
    signal = strategy.signal(df.iloc[:i+1])
    signals.append(signal)

print(f"Total signals: {sum(1 for s in signals if s != 0)}")
print(f"Buy signals: {sum(1 for s in signals if s > 0)}")
print(f"Sell signals: {sum(1 for s in signals if s < 0)}")

# Check position sizing
for i, signal in enumerate(signals):
    if signal != 0:
        price = df.iloc[i]['Close']
        size = risk_engine.calculate_position_size("EURUSD", "SMA", 10000, 0.02)
        print(f"Signal {i}: {signal}, Price: {price}, Size: {size}")
```

### Walk-Forward Analysis Issues

**Problem**: Walk-forward analysis fails or gives unexpected results.

**Solution**:
```python
# Check date ranges
print(f"Start date: {start_date}")
print(f"End date: {end_date}")
print(f"Train period: {train_period} days")
print(f"Test period: {test_period} days")

# Check data availability for each period
for i in range(0, len(df), step_size):
    train_start = df.index[i]
    train_end = df.index[min(i + train_period, len(df) - 1)]
    test_start = train_end
    test_end = df.index[min(i + train_period + test_period, len(df) - 1)]
    
    print(f"Period {i//step_size + 1}:")
    print(f"  Train: {train_start} to {train_end}")
    print(f"  Test: {test_start} to {test_end}")
```

## Debugging Tips

### Enable Debug Logging

```python
import logging

# Set up debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# Enable debug for specific modules
logging.getLogger('forexsmartbot').setLevel(logging.DEBUG)
```

### Use Print Statements

```python
# Add debug prints
print(f"Data shape: {df.shape}")
print(f"Strategy parameters: {strategy.parameters}")
print(f"Signal: {signal}")
print(f"Position size: {position_size}")
```

### Check Data at Each Step

```python
# Verify data at each step
def debug_strategy(df, strategy):
    print("=== Strategy Debug ===")
    print(f"Input data shape: {df.shape}")
    
    # Calculate indicators
    df_with_indicators = strategy.calculate_indicators(df)
    print(f"After indicators: {df_with_indicators.shape}")
    print(f"Indicators: {df_with_indicators.columns.tolist()}")
    
    # Generate signal
    signal = strategy.signal(df_with_indicators)
    print(f"Signal: {signal}")
    
    # Calculate stop/take
    price = df_with_indicators['Close'].iloc[-1]
    stop_loss = strategy.stop_loss(df_with_indicators, price, signal)
    take_profit = strategy.take_profit(df_with_indicators, price, signal)
    print(f"Stop loss: {stop_loss}")
    print(f"Take profit: {take_profit}")
    
    return df_with_indicators
```

### Use Python Debugger

```python
import pdb

# Set breakpoint
pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

### Profile Performance

```python
import cProfile
import pstats

# Profile function
def profile_function():
    # Your code here
    pass

# Run profiler
cProfile.run('profile_function()', 'profile_output.prof')

# Analyze results
stats = pstats.Stats('profile_output.prof')
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 functions
```

## Getting Help

### Check Logs

```bash
# Check application logs
tail -f ~/.forexsmartbot/logs/$(date +%Y-%m-%d).log

# Check system logs (Linux/macOS)
journalctl -u forexsmartbot

# Check Windows Event Viewer for errors
```

### Create Minimal Example

```python
# Create minimal example to reproduce issue
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.strategies import SMACrossoverStrategy

# Minimal setup
data_provider = YFinanceProvider()
strategy = SMACrossoverStrategy()

# Minimal data
df = data_provider.get_data("EURUSD", "2024-01-01", "2024-01-31")
print(df.head())

# Test strategy
df = strategy.calculate_indicators(df)
signal = strategy.signal(df)
print(f"Signal: {signal}")
```

### Report Issues

When reporting issues, include:

1. **Environment**:
   - Operating system
   - Python version
   - Package versions

2. **Error Details**:
   - Full error message
   - Stack trace
   - Steps to reproduce

3. **Code**:
   - Minimal example
   - Configuration used
   - Data being processed

4. **Logs**:
   - Relevant log entries
   - Debug output

### Community Support

- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share ideas
- Wiki: Check documentation and examples
