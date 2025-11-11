# Performance Tuning Guide - v3.1.0

Optimize ForexSmartBot performance for your use case.

## 🎯 Performance Targets

### Recommended Performance
- **Startup Time**: < 2 seconds
- **Backtest Speed**: < 30 seconds per year of data
- **Memory Usage**: < 500 MB (without ML strategies)
- **Signal Generation**: < 100ms per signal
- **UI Response**: < 50ms

## ⚡ Quick Wins

### 1. Use Simpler Strategies for Real-Time Trading

**Problem**: ML strategies are slow for real-time use  
**Solution**: Use traditional strategies for live trading

```python
# Fast: Traditional strategy
strategy = get_strategy('SMA_Crossover', fast_period=20, slow_period=50)

# Slow: ML strategy (use for analysis only)
ml_strategy = get_strategy('LSTM_Strategy')  # Use for backtesting
```

### 2. Reduce Dataset Size

**Problem**: Large datasets slow down backtests  
**Solution**: Use recent data only

```python
# Instead of full history
df = data_provider.get_data('EURUSD=X', '2020-01-01', '2024-12-31', '1h')

# Use recent data
df = data_provider.get_data('EURUSD=X', '2023-01-01', '2024-12-31', '1h')
```

### 3. Use Parallel Processing

**Problem**: Sequential backtests are slow  
**Solution**: Enable parallel processing

```python
from forexsmartbot.services.enhanced_backtest import EnhancedBacktestService

service = EnhancedBacktestService(
    data_provider,
    use_parallel=True,
    max_workers=4  # Adjust based on CPU cores
)
```

### 4. Cache Indicator Calculations

**Problem**: Recalculating indicators repeatedly  
**Solution**: Cache results

```python
# Cache indicators
indicator_cache = {}

def get_indicators(df, strategy):
    cache_key = (len(df), df.index[-1])
    if cache_key not in indicator_cache:
        indicator_cache[cache_key] = strategy.indicators(df)
    return indicator_cache[cache_key]
```

## 🔧 Strategy-Specific Tuning

### Traditional Strategies

**Optimization**:
- Use shorter lookback periods
- Disable unnecessary indicators
- Use vectorized operations

```python
# Optimized SMA Crossover
strategy = get_strategy('SMA_Crossover', 
    fast_period=10,  # Shorter = faster
    slow_period=20
)
```

### ML Strategies

**Optimization**:
- Reduce training frequency
- Use smaller models
- Limit training data

```python
# Optimized LSTM
strategy = get_strategy('LSTM_Strategy',
    lookback_period=30,  # Shorter lookback
    sequence_length=10,  # Shorter sequences
    lstm_units=25,       # Smaller model
    epochs=10            # Fewer epochs
)
```

### Ensemble Strategies

**Optimization**:
- Reduce number of estimators
- Shallow trees
- Limit features

```python
# Optimized Ensemble
strategy = get_strategy('Ensemble_ML_Strategy',
    n_estimators=50,  # Fewer estimators
    max_depth=5       # Shallow trees
)
```

## 🚀 Optimization Tools Performance

### Genetic Algorithm

**Tuning**:
```python
# Faster optimization
optimizer = GeneticOptimizer(
    param_bounds,
    population_size=20,  # Smaller population
    generations=10       # Fewer generations
)
```

### Hyperparameter Optimization

**Tuning**:
```python
# Faster optimization
optimizer = HyperparameterOptimizer(
    param_space,
    n_trials=50  # Fewer trials
)
```

### Walk-Forward Analysis

**Tuning**:
```python
# Faster analysis
analyzer = WalkForwardAnalyzer(
    train_period=120,  # Shorter periods
    test_period=30,
    step_size=15       # Larger steps
)
```

### Monte Carlo Simulation

**Tuning**:
```python
# Faster simulation
simulator = MonteCarloSimulator(
    n_simulations=100  # Fewer simulations
)
```

## 💾 Memory Optimization

### 1. Process Data in Chunks

```python
# Process large datasets in chunks
chunk_size = 1000
for i in range(0, len(df), chunk_size):
    chunk = df.iloc[i:i+chunk_size]
    process_chunk(chunk)
```

### 2. Clear Cache Regularly

```python
import gc

# After large operations
gc.collect()
```

### 3. Use Generators

```python
# Instead of loading all data
def data_generator(symbol, start, end):
    for date_range in split_date_range(start, end):
        yield data_provider.get_data(symbol, *date_range)
```

### 4. Limit ML Model Size

```python
# Smaller models use less memory
strategy = get_strategy('LSTM_Strategy',
    lstm_units=25,  # Smaller = less memory
    batch_size=16   # Smaller batches
)
```

## ⏱️ Execution Time Optimization

### 1. Pre-calculate Indicators

```python
# Calculate once, reuse
df_with_indicators = strategy.indicators(df)

# Reuse for multiple signals
for i in range(len(df_with_indicators)):
    signal = strategy.signal(df_with_indicators.iloc[:i+1])
```

### 2. Use Vectorized Operations

```python
# Fast: Vectorized
df['SMA'] = df['Close'].rolling(20).mean()

# Slow: Loop
for i in range(len(df)):
    df.loc[i, 'SMA'] = df['Close'].iloc[max(0, i-19):i+1].mean()
```

### 3. Disable Unnecessary Features

```python
# Disable monitoring in backtests
# (monitoring adds overhead)
# Only enable for production
```

### 4. Optimize Data Loading

```python
# Load only needed columns
df = df[['Open', 'High', 'Low', 'Close']]

# Use appropriate data types
df['Close'] = df['Close'].astype('float32')
```

## 📊 Monitoring Performance

### Enable Performance Tracking

```python
import time
from forexsmartbot.monitoring import StrategyMonitor

monitor = StrategyMonitor()
monitor.register_strategy("MyStrategy")

# Track execution time
start = time.time()
signal = strategy.signal(df)
execution_time = time.time() - start

monitor.record_signal("MyStrategy", execution_time=execution_time)
```

### Identify Bottlenecks

```python
import cProfile
import pstats

# Profile strategy execution
profiler = cProfile.Profile()
profiler.enable()

# Your code
strategy.signal(df)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 slowest functions
```

## 🎛️ Configuration Tuning

### Optimization Config

Edit `config/optimization_config.json`:

```json
{
  "genetic_algorithm": {
    "population_size": 30,  // Reduce for speed
    "generations": 20        // Reduce for speed
  },
  "hyperparameter_optimization": {
    "n_trials": 50           // Reduce for speed
  }
}
```

### Strategy Config

Edit `config/strategy_configs.json`:

```json
{
  "LSTM_Strategy": {
    "lstm_units": 25,        // Smaller = faster
    "epochs": 10             // Fewer = faster
  }
}
```

## 🔍 Profiling Tools

### Python Profiler

```python
python -m cProfile -o profile.stats your_script.py
python -m pstats profile.stats
```

### Memory Profiler

```python
pip install memory-profiler

@profile
def my_function():
    # Your code
    pass
```

### Line Profiler

```python
pip install line-profiler

kernprof -l -v your_script.py
```

## 📈 Performance Benchmarks

### Benchmark Your Strategies

```bash
python scripts/benchmark_strategies.py \
    --symbol EURUSD=X \
    --start 2023-01-01 \
    --end 2023-12-31 \
    --strategies SMA_Crossover RSI_Reversion
```

### Compare Performance

```python
from forexsmartbot.services.enhanced_backtest import EnhancedBacktestService
import time

strategies = ['SMA_Crossover', 'RSI_Reversion', 'BreakoutATR']
results = {}

for strategy_name in strategies:
    start = time.time()
    # Run backtest
    execution_time = time.time() - start
    results[strategy_name] = execution_time

# Compare
for name, time_taken in sorted(results.items(), key=lambda x: x[1]):
    print(f"{name}: {time_taken:.2f}s")
```

## 🎯 Best Practices

### 1. Development vs Production

**Development**:
- Use full datasets
- Enable all features
- Detailed logging

**Production**:
- Use optimized strategies
- Minimal logging
- Cached calculations

### 2. Strategy Selection

**Real-Time Trading**:
- Use traditional strategies
- Simple indicators
- Fast execution

**Analysis/Backtesting**:
- Use ML strategies
- Complex models
- Detailed metrics

### 3. Resource Management

```python
# Close resources
data_provider.close()

# Clear caches
cache.clear()

# Force garbage collection
import gc
gc.collect()
```

## ⚠️ Common Performance Issues

### Issue: Slow Backtests

**Causes**:
- Large datasets
- ML strategies training
- Complex calculations

**Solutions**:
- Reduce dataset size
- Use simpler strategies
- Enable parallel processing
- Cache calculations

### Issue: High Memory Usage

**Causes**:
- Large datasets in memory
- ML models
- Multiple strategies

**Solutions**:
- Process in chunks
- Use smaller models
- Clear cache regularly
- Limit concurrent strategies

### Issue: Slow Optimization

**Causes**:
- Large parameter space
- Many generations/trials
- Slow fitness function

**Solutions**:
- Reduce parameter bounds
- Fewer generations/trials
- Optimize fitness function
- Use smaller datasets

## 📊 Performance Metrics

Track these metrics:

- **Execution Time**: Time per operation
- **Memory Usage**: Peak memory consumption
- **CPU Usage**: CPU utilization
- **Throughput**: Operations per second
- **Latency**: Time to first result

## 🔧 Advanced Tuning

### Multi-Processing

```python
from multiprocessing import Pool

def process_strategy(strategy_name):
    # Process strategy
    pass

with Pool(processes=4) as pool:
    results = pool.map(process_strategy, strategy_names)
```

### Async Processing

```python
import asyncio

async def process_strategy_async(strategy):
    # Async processing
    pass

# Run multiple strategies concurrently
await asyncio.gather(*[process_strategy_async(s) for s in strategies])
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_indicator(price_data_hash, period):
    # Expensive calculation
    return result
```

## 📝 Performance Checklist

- [ ] Use appropriate strategies for use case
- [ ] Optimize dataset size
- [ ] Enable parallel processing
- [ ] Cache calculations
- [ ] Monitor execution times
- [ ] Profile bottlenecks
- [ ] Optimize configuration
- [ ] Clear cache regularly
- [ ] Use vectorized operations
- [ ] Limit ML model complexity

---

**For more help**: See [Troubleshooting Guide](TROUBLESHOOTING.md) or [FAQ](FAQ.md)

