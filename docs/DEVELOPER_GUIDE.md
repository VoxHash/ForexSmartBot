# Developer Guide - Extending ForexSmartBot v3.1.0

This guide helps developers extend and customize ForexSmartBot.

## Architecture Overview

### Core Components

```
forexsmartbot/
├── core/           # Core interfaces and base classes
├── strategies/     # Trading strategies
├── optimization/   # Optimization tools
├── monitoring/     # Monitoring and analytics
├── builder/        # Strategy builder
├── marketplace/    # Strategy marketplace
├── adapters/       # Data and broker adapters
├── services/       # Business logic services
└── ui/            # User interface
```

## Creating a New Strategy

### Step 1: Implement IStrategy Interface

```python
from forexsmartbot.core.interfaces import IStrategy
import pandas as pd
from typing import Dict, Any, Optional

class MyCustomStrategy(IStrategy):
    """My custom trading strategy."""
    
    def __init__(self, param1: int = 20, param2: float = 0.5):
        self._param1 = param1
        self._param2 = param2
        self._name = "My Custom Strategy"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'param1': self._param1,
            'param2': self._param2
        }
    
    def set_params(self, **kwargs) -> None:
        if 'param1' in kwargs:
            self._param1 = int(kwargs['param1'])
        if 'param2' in kwargs:
            self._param2 = float(kwargs['param2'])
    
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators."""
        out = df.copy()
        # Your indicator calculations
        out['MyIndicator'] = calculate_my_indicator(out, self._param1)
        return out
    
    def signal(self, df: pd.DataFrame) -> int:
        """Generate signal: +1 (buy), -1 (sell), 0 (hold)."""
        if len(df) < self._param1:
            return 0
        
        # Your signal logic
        indicator = df['MyIndicator'].iloc[-1]
        if indicator > self._param2:
            return 1  # Buy
        elif indicator < -self._param2:
            return -1  # Sell
        else:
            return 0  # Hold
    
    def volatility(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate volatility for position sizing."""
        if 'ATR' in df.columns and len(df) > 0:
            atr = float(df['ATR'].iloc[-1])
            price = float(df['Close'].iloc[-1])
            if price > 0:
                return atr / price
        return None
    
    def stop_loss(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate stop loss."""
        if 'ATR' in df.columns and len(df) > 0:
            atr = float(df['ATR'].iloc[-1])
            if side > 0:  # Long
                return entry_price - (2 * atr)
            else:  # Short
                return entry_price + (2 * atr)
        return None
    
    def take_profit(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate take profit."""
        if 'ATR' in df.columns and len(df) > 0:
            atr = float(df['ATR'].iloc[-1])
            if side > 0:  # Long
                return entry_price + (4 * atr)
            else:  # Short
                return entry_price - (4 * atr)
        return None
```

### Step 2: Register Strategy

Add to `forexsmartbot/strategies/__init__.py`:

```python
from .my_custom_strategy import MyCustomStrategy

STRATEGIES = {
    # ... existing strategies ...
    'My_Custom_Strategy': MyCustomStrategy,
}
```

### Step 3: Test Strategy

```python
from forexsmartbot.strategies import get_strategy
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.adapters.data import YFinanceProvider

strategy = get_strategy('My_Custom_Strategy', param1=20, param2=0.5)
service = BacktestService(YFinanceProvider())
results = service.run_backtest(strategy, 'EURUSD=X', '2023-01-01', '2023-12-31')
```

## Creating a New Optimization Tool

### Example: Custom Optimizer

```python
from typing import Dict, Any, Callable, Tuple
import numpy as np

class MyCustomOptimizer:
    """Custom optimization algorithm."""
    
    def __init__(self, param_bounds: Dict[str, Tuple[float, float]]):
        self.param_bounds = param_bounds
    
    def optimize(self, fitness_function: Callable[[Dict[str, float]], float]) -> Tuple[Dict[str, float], float]:
        """Run optimization."""
        # Your optimization algorithm
        best_params = {}
        best_fitness = -float('inf')
        
        # Example: Grid search
        for param_name, (min_val, max_val) in self.param_bounds.items():
            # Test values
            for val in np.linspace(min_val, max_val, 10):
                params = {param_name: val}
                fitness = fitness_function(params)
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_params = params
        
        return best_params, best_fitness
```

## Creating a New Data Provider

### Implement IDataProvider

```python
from forexsmartbot.core.interfaces import IDataProvider
import pandas as pd
from typing import Optional

class MyDataProvider(IDataProvider):
    """Custom data provider."""
    
    def get_data(self, symbol: str, start_date: str, end_date: str, 
                 interval: str = "1h") -> pd.DataFrame:
        """Fetch market data."""
        # Your data fetching logic
        # Return DataFrame with columns: Open, High, Low, Close, Volume
        df = fetch_from_your_source(symbol, start_date, end_date, interval)
        return df
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price."""
        # Your implementation
        return get_latest_from_source(symbol)
```

## Extending Strategy Builder

### Add Custom Component Type

```python
from forexsmartbot.builder.strategy_builder import ComponentType, StrategyComponent

# Add new component type
class CustomComponentType(Enum):
    MY_CUSTOM_TYPE = "my_custom_type"

# Extend builder
class ExtendedStrategyBuilder(StrategyBuilder):
    def add_custom_component(self, name: str, params: dict):
        return self.add_component(CustomComponentType.MY_CUSTOM_TYPE, name, params)
```

## Creating Custom Monitoring

### Extend Performance Tracker

```python
from forexsmartbot.monitoring import PerformanceTracker

class CustomPerformanceTracker(PerformanceTracker):
    """Extended performance tracker."""
    
    def calculate_custom_metric(self, strategy_name: str) -> float:
        """Calculate custom metric."""
        trades = self.get_trades(strategy_name)
        # Your custom calculation
        return custom_calculation(trades)
```

## Best Practices

### 1. Follow Interfaces

Always implement required interface methods:

```python
# Good: Implements all IStrategy methods
class MyStrategy(IStrategy):
    def indicators(self, df): ...
    def signal(self, df): ...
    def volatility(self, df): ...
    # ... all methods ...

# Bad: Missing methods
class MyStrategy(IStrategy):
    def signal(self, df): ...
    # Missing other methods
```

### 2. Error Handling

Always handle errors gracefully:

```python
def signal(self, df: pd.DataFrame) -> int:
    try:
        # Your logic
        return calculated_signal
    except Exception as e:
        logger.error(f"Error in signal: {e}")
        return 0  # Safe default
```

### 3. Type Hints

Use type hints for better code clarity:

```python
def calculate_indicator(
    df: pd.DataFrame, 
    period: int, 
    multiplier: float = 2.0
) -> pd.Series:
    """Calculate indicator with type hints."""
    # Implementation
    return indicator_series
```

### 4. Documentation

Document your code:

```python
def my_function(param1: int, param2: float) -> float:
    """
    Calculate something important.
    
    Args:
        param1: First parameter description
        param2: Second parameter description
    
    Returns:
        Calculated result
    
    Raises:
        ValueError: If parameters are invalid
    """
    # Implementation
    pass
```

### 5. Testing

Write tests for your code:

```python
import unittest

class TestMyStrategy(unittest.TestCase):
    def test_signal_generation(self):
        strategy = MyCustomStrategy()
        df = create_test_data()
        signal = strategy.signal(df)
        self.assertIn(signal, [-1, 0, 1])
```

## Integration Points

### Adding to UI

```python
# In ui/enhanced_main_window.py
from forexsmartbot.strategies import get_strategy

# Add your strategy to the UI
strategy = get_strategy('My_Custom_Strategy')
```

### Adding to CLI Tools

```python
# In scripts/optimize_strategy.py
# Your strategy will automatically work with optimization tools
```

### Adding to Marketplace

```python
from forexsmartbot.marketplace import StrategyMarketplace, StrategyListing

marketplace = StrategyMarketplace()
listing = StrategyListing(
    strategy_id="my_strategy_001",
    name="My Custom Strategy",
    # ... other fields ...
)
marketplace.add_listing(listing)
```

## Code Organization

### File Structure

```
my_extension/
├── __init__.py
├── my_strategy.py
├── my_optimizer.py
├── my_provider.py
└── tests/
    └── test_my_extension.py
```

### Import Pattern

```python
# In your extension
from forexsmartbot.core.interfaces import IStrategy
from forexsmartbot.optimization import GeneticOptimizer

# Your code uses ForexSmartBot interfaces
```

## Debugging

### Enable Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your code will show debug messages
```

### Use Validation Script

```python
# Test your strategy
from forexsmartbot.strategies import get_strategy

try:
    strategy = get_strategy('My_Custom_Strategy')
    print("✓ Strategy loads successfully")
except Exception as e:
    print(f"✗ Error: {e}")
```

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Add comments for complex logic

### Testing

- Write unit tests
- Test edge cases
- Test error handling
- Run validation script

### Documentation

- Document public APIs
- Add usage examples
- Update README if needed
- Document breaking changes

## Examples

See `examples/` directory for:
- Strategy implementations
- Optimization usage
- Builder examples
- Integration patterns

## Support

- Review existing code for patterns
- Check documentation
- Look at examples
- Ask questions in issues

---

**Happy Coding!** 🚀

