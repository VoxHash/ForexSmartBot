# Performance Optimization Guide

This guide covers performance optimization techniques for ForexSmartBot to ensure optimal performance in production environments.

## Table of Contents

- [Performance Overview](#performance-overview)
- [Code Optimization](#code-optimization)
- [Data Processing](#data-processing)
- [Memory Management](#memory-management)
- [Database Optimization](#database-optimization)
- [UI Performance](#ui-performance)
- [Backtesting Performance](#backtesting-performance)
- [Monitoring & Profiling](#monitoring--profiling)
- [Best Practices](#best-practices)

## Performance Overview

### Key Performance Metrics

- **Startup Time**: < 3 seconds
- **Memory Usage**: < 200MB typical
- **Response Time**: < 100ms for most operations
- **Backtesting Speed**: 1000+ bars per second
- **Chart Rendering**: < 500ms for typical charts
- **Data Loading**: < 1 second for 1 year of daily data

### Performance Bottlenecks

1. **Data Processing**: Large datasets and complex calculations
2. **Memory Usage**: Inefficient data structures and memory leaks
3. **UI Responsiveness**: Blocking operations on main thread
4. **Database Operations**: Slow queries and inefficient storage
5. **Network I/O**: Slow data provider responses

## Code Optimization

### Algorithm Optimization

1. **Use vectorized operations**:
   ```python
   # Slow - loop-based
   def calculate_sma_slow(prices, period):
       sma = []
       for i in range(period-1, len(prices)):
           sma.append(sum(prices[i-period+1:i+1]) / period)
       return sma
   
   # Fast - vectorized
   def calculate_sma_fast(prices, period):
       return prices.rolling(window=period).mean()
   ```

2. **Avoid unnecessary calculations**:
   ```python
   # Slow - recalculates every time
   def get_volatility(df):
       return df['Close'].pct_change().std()
   
   # Fast - caches result
   @lru_cache(maxsize=128)
   def get_volatility_cached(df_hash, period):
       return df['Close'].pct_change().std()
   ```

3. **Use appropriate data structures**:
   ```python
   # Slow - list for frequent lookups
   positions = []
   for pos in positions:
       if pos.symbol == symbol:
           return pos
   
   # Fast - dictionary for O(1) lookups
   positions = {}
   if symbol in positions:
       return positions[symbol]
   ```

### Function Optimization

1. **Minimize function calls**:
   ```python
   # Slow - multiple function calls
   def process_data(df):
       df = df.dropna()
       df = df.reset_index()
       df = df.sort_values('Date')
       return df
   
   # Fast - chained operations
   def process_data(df):
       return (df.dropna()
               .reset_index()
               .sort_values('Date'))
   ```

2. **Use generators for large datasets**:
   ```python
   # Slow - loads all data into memory
   def process_large_dataset(data):
       results = []
       for item in data:
           results.append(process_item(item))
       return results
   
   # Fast - generator for memory efficiency
   def process_large_dataset(data):
       for item in data:
           yield process_item(item)
   ```

3. **Optimize hot paths**:
   ```python
   # Profile to identify hot paths
   import cProfile
   
   def profile_function():
       # Your code here
       pass
   
   cProfile.run('profile_function()')
   ```

## Data Processing

### Pandas Optimization

1. **Use appropriate data types**:
   ```python
   # Slow - default float64
   df['Close'] = df['Close'].astype('float64')
   
   # Fast - use float32 for price data
   df['Close'] = df['Close'].astype('float32')
   ```

2. **Optimize DataFrame operations**:
   ```python
   # Slow - multiple operations
   df['SMA_10'] = df['Close'].rolling(10).mean()
   df['SMA_20'] = df['Close'].rolling(20).mean()
   df['SMA_50'] = df['Close'].rolling(50).mean()
   
   # Fast - single operation
   df[['SMA_10', 'SMA_20', 'SMA_50']] = df['Close'].rolling([10, 20, 50]).mean()
   ```

3. **Use categorical data for strings**:
   ```python
   # Slow - string objects
   df['Symbol'] = df['Symbol'].astype('object')
   
   # Fast - categorical data
   df['Symbol'] = df['Symbol'].astype('category')
   ```

4. **Optimize groupby operations**:
   ```python
   # Slow - multiple groupby operations
   result1 = df.groupby('Symbol')['Close'].mean()
   result2 = df.groupby('Symbol')['Volume'].sum()
   
   # Fast - single groupby operation
   result = df.groupby('Symbol').agg({
       'Close': 'mean',
       'Volume': 'sum'
   })
   ```

### Data Loading Optimization

1. **Use chunking for large files**:
   ```python
   def load_large_csv(filename, chunk_size=10000):
       chunks = []
       for chunk in pd.read_csv(filename, chunksize=chunk_size):
           # Process chunk
           processed_chunk = process_chunk(chunk)
           chunks.append(processed_chunk)
       return pd.concat(chunks, ignore_index=True)
   ```

2. **Use parallel processing**:
   ```python
   from multiprocessing import Pool
   
   def process_data_parallel(data_chunks):
       with Pool() as pool:
           results = pool.map(process_chunk, data_chunks)
       return results
   ```

3. **Cache frequently used data**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def get_cached_data(symbol, start_date, end_date):
       return data_provider.get_data(symbol, start_date, end_date)
   ```

## Memory Management

### Memory Optimization

1. **Use memory-efficient data types**:
   ```python
   # Memory usage comparison
   import sys
   
   # float64 - 8 bytes per value
   df_float64 = pd.DataFrame({'Close': [1.0] * 1000000})
   print(f"float64: {sys.getsizeof(df_float64)} bytes")
   
   # float32 - 4 bytes per value
   df_float32 = pd.DataFrame({'Close': [1.0] * 1000000}, dtype='float32')
   print(f"float32: {sys.getsizeof(df_float32)} bytes")
   ```

2. **Clear unused variables**:
   ```python
   def process_data(df):
       # Process data
       result = df.groupby('Symbol').mean()
       
       # Clear large variables
       del df
       import gc
       gc.collect()
       
       return result
   ```

3. **Use generators for large datasets**:
   ```python
   def process_large_dataset(data):
       for chunk in data:
           yield process_chunk(chunk)
   ```

### Memory Monitoring

1. **Monitor memory usage**:
   ```python
   import psutil
   import os
   
   def monitor_memory():
       process = psutil.Process(os.getpid())
       memory_info = process.memory_info()
       print(f"Memory usage: {memory_info.rss / 1024 / 1024:.1f} MB")
   ```

2. **Set memory limits**:
   ```python
   import resource
   
   def set_memory_limit(mb):
       resource.setrlimit(resource.RLIMIT_AS, (mb * 1024 * 1024, -1))
   ```

3. **Use memory profiling**:
   ```python
   from memory_profiler import profile
   
   @profile
   def memory_intensive_function():
       # Your code here
       pass
   ```

## Database Optimization

### SQLite Optimization

1. **Use appropriate data types**:
   ```sql
   CREATE TABLE trades (
       id INTEGER PRIMARY KEY,
       symbol TEXT,
       side INTEGER,
       quantity REAL,
       entry_price REAL,
       exit_price REAL,
       pnl REAL,
       entry_time TIMESTAMP,
       exit_time TIMESTAMP
   );
   ```

2. **Create indexes**:
   ```sql
   CREATE INDEX idx_trades_symbol ON trades(symbol);
   CREATE INDEX idx_trades_entry_time ON trades(entry_time);
   CREATE INDEX idx_trades_symbol_time ON trades(symbol, entry_time);
   ```

3. **Use prepared statements**:
   ```python
   def insert_trade(trade):
       cursor.execute("""
           INSERT INTO trades (symbol, side, quantity, entry_price, exit_price, pnl, entry_time, exit_time)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
       """, (trade.symbol, trade.side, trade.quantity, trade.entry_price, 
             trade.exit_price, trade.pnl, trade.entry_time, trade.exit_time))
   ```

4. **Batch operations**:
   ```python
   def insert_trades_batch(trades):
       cursor.executemany("""
           INSERT INTO trades (symbol, side, quantity, entry_price, exit_price, pnl, entry_time, exit_time)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
       """, trades)
   ```

### Connection Pooling

1. **Use connection pooling**:
   ```python
   from sqlite3 import connect
   from threading import Lock
   
   class ConnectionPool:
       def __init__(self, db_path, max_connections=10):
           self.db_path = db_path
           self.max_connections = max_connections
           self.connections = []
           self.lock = Lock()
       
       def get_connection(self):
           with self.lock:
               if self.connections:
                   return self.connections.pop()
               else:
                   return connect(self.db_path)
       
       def return_connection(self, conn):
           with self.lock:
               if len(self.connections) < self.max_connections:
                   self.connections.append(conn)
               else:
                   conn.close()
   ```

## UI Performance

### PyQt6 Optimization

1. **Use threading for long operations**:
   ```python
   from PyQt6.QtCore import QThread, pyqtSignal
   
   class DataThread(QThread):
       data_ready = pyqtSignal(pd.DataFrame)
       
       def run(self):
           # Long-running operation
           data = self.load_data()
           self.data_ready.emit(data)
   ```

2. **Optimize chart rendering**:
   ```python
   def update_chart(self, df):
       # Limit data points for performance
       if len(df) > 1000:
           df = df.tail(1000)
       
       # Use efficient plotting
       self.axes.clear()
       self.axes.plot(df.index, df['Close'], linewidth=1)
       self.canvas.draw()
   ```

3. **Use lazy loading**:
   ```python
   def load_data_lazy(self, symbol):
       if symbol not in self._data_cache:
           self._data_cache[symbol] = self.load_data(symbol)
       return self._data_cache[symbol]
   ```

### UI Responsiveness

1. **Use QTimer for periodic updates**:
   ```python
   from PyQt6.QtCore import QTimer
   
   class MainWindow(QMainWindow):
       def __init__(self):
           super().__init__()
           self.timer = QTimer()
           self.timer.timeout.connect(self.update_data)
           self.timer.start(1000)  # Update every second
   ```

2. **Implement progress bars**:
   ```python
   from PyQt6.QtWidgets import QProgressBar
   
   def long_operation(self):
       progress = QProgressBar()
       progress.setRange(0, 100)
       
       for i in range(100):
           # Do work
           progress.setValue(i)
           QApplication.processEvents()
   ```

## Backtesting Performance

### Backtesting Optimization

1. **Vectorize calculations**:
   ```python
   def vectorized_backtest(self, df, strategy):
       # Calculate all indicators at once
       df = strategy.calculate_indicators(df)
       
       # Vectorize signal generation
       signals = strategy.signal_vectorized(df)
       
       # Vectorize position sizing
       sizes = self.calculate_position_sizes_vectorized(df, signals)
       
       return self.simulate_trades_vectorized(df, signals, sizes)
   ```

2. **Use NumPy for calculations**:
   ```python
   import numpy as np
   
   def calculate_returns(prices):
       return np.diff(prices) / prices[:-1]
   
   def calculate_sharpe_ratio(returns):
       return np.mean(returns) / np.std(returns) * np.sqrt(252)
   ```

3. **Optimize data structures**:
   ```python
   def optimized_backtest(self, df):
       # Use NumPy arrays for calculations
       prices = df['Close'].values
       signals = np.zeros(len(prices))
       
       # Vectorized signal generation
       for i in range(1, len(prices)):
           signals[i] = self.generate_signal(prices[:i+1])
       
       return self.simulate_trades(prices, signals)
   ```

### Memory-Efficient Backtesting

1. **Process data in chunks**:
   ```python
   def chunked_backtest(self, df, chunk_size=1000):
       results = []
       for i in range(0, len(df), chunk_size):
           chunk = df.iloc[i:i+chunk_size]
           result = self.backtest_chunk(chunk)
           results.append(result)
       return self.combine_results(results)
   ```

2. **Use generators for large datasets**:
   ```python
   def generator_backtest(self, data_generator):
       for chunk in data_generator:
           yield self.backtest_chunk(chunk)
   ```

## Monitoring & Profiling

### Performance Monitoring

1. **Use cProfile for profiling**:
   ```python
   import cProfile
   import pstats
   
   def profile_function():
       # Your code here
       pass
   
   # Profile function
   cProfile.run('profile_function()', 'profile_output.prof')
   
   # Analyze results
   stats = pstats.Stats('profile_output.prof')
   stats.sort_stats('cumulative')
   stats.print_stats(10)
   ```

2. **Use line_profiler for line-by-line profiling**:
   ```python
   from line_profiler import LineProfiler
   
   def profile_lines():
       profiler = LineProfiler()
       profiler.add_function(your_function)
       profiler.run('your_function()')
       profiler.print_stats()
   ```

3. **Monitor system resources**:
   ```python
   import psutil
   import time
   
   def monitor_resources():
       while True:
           cpu_percent = psutil.cpu_percent()
           memory = psutil.virtual_memory()
           disk = psutil.disk_usage('/')
           
           print(f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")
           time.sleep(1)
   ```

### Performance Metrics

1. **Track key metrics**:
   ```python
   class PerformanceMetrics:
       def __init__(self):
           self.start_time = time.time()
           self.operation_times = {}
       
       def start_operation(self, name):
           self.operation_times[name] = time.time()
       
       def end_operation(self, name):
           if name in self.operation_times:
               duration = time.time() - self.operation_times[name]
               print(f"{name}: {duration:.3f}s")
   ```

2. **Log performance data**:
   ```python
   import logging
   
   def log_performance(operation, duration):
       logger = logging.getLogger('performance')
       logger.info(f"{operation}: {duration:.3f}s")
   ```

## Best Practices

### General Optimization

1. **Profile before optimizing**:
   - Identify actual bottlenecks
   - Measure before and after
   - Focus on hot paths

2. **Use appropriate data structures**:
   - Lists for ordered data
   - Sets for membership testing
   - Dictionaries for key-value lookups
   - NumPy arrays for numerical data

3. **Avoid premature optimization**:
   - Write clear, readable code first
   - Profile to identify bottlenecks
   - Optimize only what needs optimization

### Code Organization

1. **Separate concerns**:
   - Data processing
   - Business logic
   - UI updates
   - I/O operations

2. **Use caching strategically**:
   - Cache expensive calculations
   - Cache frequently accessed data
   - Use appropriate cache sizes

3. **Optimize imports**:
   ```python
   # Slow - imports at function level
   def process_data():
       import pandas as pd
       import numpy as np
       # Process data
   
   # Fast - imports at module level
   import pandas as pd
   import numpy as np
   
   def process_data():
       # Process data
   ```

### Memory Management

1. **Use context managers**:
   ```python
   with open('data.csv') as f:
       data = pd.read_csv(f)
   # File automatically closed
   ```

2. **Clear large variables**:
   ```python
   def process_large_data():
       large_data = load_large_dataset()
       result = process_data(large_data)
       del large_data  # Clear from memory
       return result
   ```

3. **Use generators for large datasets**:
   ```python
   def process_large_file(filename):
       with open(filename) as f:
           for line in f:
               yield process_line(line)
   ```

### Database Optimization

1. **Use transactions**:
   ```python
   def batch_insert_trades(trades):
       conn = sqlite3.connect('trades.db')
       try:
           conn.execute('BEGIN TRANSACTION')
           for trade in trades:
               insert_trade(conn, trade)
           conn.commit()
       except Exception as e:
           conn.rollback()
           raise e
       finally:
           conn.close()
   ```

2. **Use prepared statements**:
   ```python
   def insert_trade_prepared(conn, trade):
       cursor = conn.cursor()
       cursor.execute("""
           INSERT INTO trades (symbol, side, quantity, entry_price, exit_price, pnl, entry_time, exit_time)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
       """, (trade.symbol, trade.side, trade.quantity, trade.entry_price, 
             trade.exit_price, trade.pnl, trade.entry_time, trade.exit_time))
   ```

### UI Optimization

1. **Use QTimer for updates**:
   ```python
   from PyQt6.QtCore import QTimer
   
   class MainWindow(QMainWindow):
       def __init__(self):
           super().__init__()
           self.timer = QTimer()
           self.timer.timeout.connect(self.update_ui)
           self.timer.start(100)  # Update every 100ms
   ```

2. **Implement lazy loading**:
   ```python
   def load_data_lazy(self, symbol):
       if symbol not in self._data_cache:
           self._data_cache[symbol] = self.load_data(symbol)
       return self._data_cache[symbol]
   ```

3. **Use threading for long operations**:
   ```python
   from PyQt6.QtCore import QThread, pyqtSignal
   
   class DataThread(QThread):
       data_ready = pyqtSignal(pd.DataFrame)
       
       def run(self):
           data = self.load_data()
           self.data_ready.emit(data)
   ```

## Performance Testing

### Benchmarking

1. **Create benchmarks**:
   ```python
   import time
   
   def benchmark_function(func, *args, **kwargs):
       start_time = time.time()
       result = func(*args, **kwargs)
       end_time = time.time()
       print(f"{func.__name__}: {end_time - start_time:.3f}s")
       return result
   ```

2. **Compare implementations**:
   ```python
   def compare_implementations():
       data = generate_test_data()
       
       # Test implementation 1
       result1 = benchmark_function(implementation1, data)
       
       # Test implementation 2
       result2 = benchmark_function(implementation2, data)
       
       # Compare results
       assert np.allclose(result1, result2)
   ```

### Load Testing

1. **Test with large datasets**:
   ```python
   def test_large_dataset():
       # Generate large dataset
       data = generate_large_dataset(1000000)
       
       # Test performance
       start_time = time.time()
       result = process_data(data)
       end_time = time.time()
       
       print(f"Processed {len(data)} records in {end_time - start_time:.3f}s")
   ```

2. **Test memory usage**:
   ```python
   def test_memory_usage():
       import psutil
       import os
       
       process = psutil.Process(os.getpid())
       initial_memory = process.memory_info().rss
       
       # Process data
       result = process_large_dataset()
       
       final_memory = process.memory_info().rss
       memory_used = (final_memory - initial_memory) / 1024 / 1024
       
       print(f"Memory used: {memory_used:.1f} MB")
   ```

## Conclusion

Performance optimization is an ongoing process that requires:

1. **Measurement**: Always measure before optimizing
2. **Profiling**: Identify actual bottlenecks
3. **Iteration**: Optimize, measure, repeat
4. **Monitoring**: Continuously monitor performance
5. **Testing**: Test with realistic data and loads

Remember that premature optimization can lead to complex, hard-to-maintain code. Focus on clear, readable code first, then optimize only what needs optimization based on actual performance measurements.

---

**Note**: This guide provides general optimization techniques. Always profile your specific use case to identify the most effective optimizations for your particular application.
