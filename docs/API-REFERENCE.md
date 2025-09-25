# API Reference

Complete API reference for ForexSmartBot components.

## Table of Contents

- [Core Interfaces](#core-interfaces)
- [Risk Engine](#risk-engine)
- [Portfolio Management](#portfolio-management)
- [Strategies](#strategies)
- [Brokers](#brokers)
- [Data Providers](#data-providers)
- [Services](#services)
- [UI Components](#ui-components)

## Core Interfaces

### IBroker

Abstract base class for broker implementations.

```python
class IBroker(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Connect to broker."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from broker."""
        pass
    
    @abstractmethod
    def get_balance(self) -> float:
        """Get account balance."""
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, side: int, quantity: float, 
                   price: float, stop_loss: float = None, 
                   take_profit: float = None) -> str:
        """Place a trading order."""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get open positions."""
        pass
    
    @abstractmethod
    def get_orders(self) -> List[Order]:
        """Get pending orders."""
        pass
```

### IStrategy

Abstract base class for trading strategies.

```python
class IStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Strategy parameters."""
        pass
    
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        pass
    
    @abstractmethod
    def signal(self, df: pd.DataFrame) -> int:
        """Generate trading signal (-1, 0, 1)."""
        pass
    
    @abstractmethod
    def stop_loss(self, df: pd.DataFrame, price: float, signal: int) -> float:
        """Calculate stop loss price."""
        pass
    
    @abstractmethod
    def take_profit(self, df: pd.DataFrame, price: float, signal: int) -> float:
        """Calculate take profit price."""
        pass
```

### IDataProvider

Abstract base class for data providers.

```python
class IDataProvider(ABC):
    @abstractmethod
    def get_data(self, symbol: str, start_date: str, end_date: str, 
                interval: str = '1d') -> pd.DataFrame:
        """Get historical data."""
        pass
    
    @abstractmethod
    def get_latest_price(self, symbol: str) -> float:
        """Get latest price."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if data provider is available."""
        pass
```

## Risk Engine

### RiskConfig

Configuration for risk management.

```python
class RiskConfig(BaseModel):
    # Base risk settings
    base_risk_pct: float = 0.02
    max_risk_pct: float = 0.05
    min_trade_amount: float = 10.0
    max_trade_amount: float = 1000.0
    
    # Volatility targeting
    volatility_target: float = 0.02
    
    # Kelly Criterion
    kelly_fraction: float = 0.25
    
    # Drawdown protection
    max_drawdown_pct: float = 0.10
    drawdown_throttle_pct: float = 0.05
    
    # Daily risk limits
    daily_risk_cap: float = 0.20
    
    # Risk multipliers
    symbol_risk_multipliers: Dict[str, float] = {}
    strategy_risk_multipliers: Dict[str, float] = {}
    
    # Trade tracking
    recent_trades_count: int = 20
```

### RiskEngine

Main risk management engine.

```python
class RiskEngine:
    def __init__(self, config: RiskConfig):
        """Initialize risk engine."""
        pass
    
    def calculate_position_size(self, symbol: str, strategy: str, 
                              balance: float, volatility: Optional[float],
                              win_rate: Optional[float] = None) -> float:
        """Calculate position size using risk management rules."""
        pass
    
    def check_daily_risk_limit(self, symbol: str, amount: float) -> bool:
        """Check if daily risk limit would be exceeded."""
        pass
    
    def check_drawdown_limit(self, current_equity: float, 
                           peak_equity: float) -> bool:
        """Check if drawdown limit would be exceeded."""
        pass
    
    def record_trade_result(self, symbol: str, strategy: str, pnl: float) -> None:
        """Record trade result for analysis."""
        pass
    
    def get_recent_win_rate(self, symbol: str, strategy: str) -> Optional[float]:
        """Get recent win rate for symbol/strategy."""
        pass
    
    def get_recent_volatility(self, symbol: str = None) -> Optional[float]:
        """Get recent PnL volatility."""
        pass
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary."""
        pass
```

## Portfolio Management

### Position

Represents an open trading position.

```python
class Position(BaseModel):
    symbol: str
    side: int  # 1 for long, -1 for short
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
```

### Trade

Represents a completed trade.

```python
class Trade(BaseModel):
    symbol: str
    side: int
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    strategy: str
    entry_time: datetime
    exit_time: datetime
    notes: Optional[str] = None
```

### Portfolio

Manages portfolio state and positions.

```python
class Portfolio:
    def __init__(self, initial_balance: float = 10000.0):
        """Initialize portfolio."""
        pass
    
    def get_total_balance(self) -> float:
        """Get total account balance."""
        pass
    
    def get_total_equity(self) -> float:
        """Get total portfolio equity."""
        pass
    
    def add_position(self, position: Position) -> None:
        """Add new position."""
        pass
    
    def remove_position(self, symbol: str) -> None:
        """Remove position by symbol."""
        pass
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol."""
        pass
    
    def get_all_positions(self) -> List[Position]:
        """Get all open positions."""
        pass
    
    def add_trade(self, trade: Trade) -> None:
        """Add completed trade."""
        pass
    
    def get_trades(self, symbol: str = None) -> List[Trade]:
        """Get trades, optionally filtered by symbol."""
        pass
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get portfolio performance metrics."""
        pass
```

## Strategies

### SMACrossoverStrategy

Simple Moving Average crossover strategy.

```python
class SMACrossoverStrategy(IStrategy):
    def __init__(self, fast: int = 10, slow: int = 20, atr_period: int = 14):
        """Initialize SMA crossover strategy."""
        pass
    
    @property
    def name(self) -> str:
        return "SMA_Crossover"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "fast": self.fast,
            "slow": self.slow,
            "atr_period": self.atr_period
        }
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate SMA and ATR indicators."""
        pass
    
    def signal(self, df: pd.DataFrame) -> int:
        """Generate crossover signal."""
        pass
    
    def stop_loss(self, df: pd.DataFrame, price: float, signal: int) -> float:
        """Calculate ATR-based stop loss."""
        pass
    
    def take_profit(self, df: pd.DataFrame, price: float, signal: int) -> float:
        """Calculate ATR-based take profit."""
        pass
```

### BreakoutATRStrategy

Breakout strategy with ATR filter.

```python
class BreakoutATRStrategy(IStrategy):
    def __init__(self, lookback: int = 20, atr_period: int = 14, 
                 atr_multiplier: float = 2.0):
        """Initialize breakout strategy."""
        pass
    
    @property
    def name(self) -> str:
        return "BreakoutATR"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "lookback": self.lookback,
            "atr_period": self.atr_period,
            "atr_multiplier": self.atr_multiplier
        }
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Donchian channels and ATR."""
        pass
    
    def signal(self, df: pd.DataFrame) -> int:
        """Generate breakout signal."""
        pass
    
    def stop_loss(self, df: pd.DataFrame, price: float, signal: int) -> float:
        """Calculate stop loss."""
        pass
    
    def take_profit(self, df: pd.DataFrame, price: float, signal: int) -> float:
        """Calculate take profit."""
        pass
```

### RSIReversionStrategy

RSI mean reversion strategy.

```python
class RSIReversionStrategy(IStrategy):
    def __init__(self, rsi_period: int = 14, oversold: float = 30.0, 
                 overbought: float = 70.0, sma_period: int = 50):
        """Initialize RSI reversion strategy."""
        pass
    
    @property
    def name(self) -> str:
        return "RSI_Reversion"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "rsi_period": self.rsi_period,
            "oversold": self.oversold,
            "overbought": self.overbought,
            "sma_period": self.sma_period
        }
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI and SMA indicators."""
        pass
    
    def signal(self, df: pd.DataFrame) -> int:
        """Generate RSI reversion signal."""
        pass
    
    def stop_loss(self, df: pd.DataFrame, price: float, signal: int) -> float:
        """Calculate stop loss."""
        pass
    
    def take_profit(self, df: pd.DataFrame, price: float, signal: int) -> float:
        """Calculate take profit."""
        pass
```

## Brokers

### PaperBroker

Paper trading broker implementation.

```python
class PaperBroker(IBroker):
    def __init__(self, initial_balance: float = 10000.0):
        """Initialize paper broker."""
        pass
    
    def connect(self) -> bool:
        """Connect to paper broker (always succeeds)."""
        pass
    
    def disconnect(self) -> None:
        """Disconnect from paper broker."""
        pass
    
    def get_balance(self) -> float:
        """Get paper account balance."""
        pass
    
    def place_order(self, symbol: str, side: int, quantity: float, 
                   price: float, stop_loss: float = None, 
                   take_profit: float = None) -> str:
        """Place paper order."""
        pass
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel paper order."""
        pass
    
    def get_positions(self) -> List[Position]:
        """Get paper positions."""
        pass
    
    def get_orders(self) -> List[Order]:
        """Get paper orders."""
        pass
    
    def update_position(self, symbol: str, side: int, quantity: float, 
                       entry_price: float, current_price: float) -> None:
        """Update position (for backtesting)."""
        pass
```

### MT4Broker

MetaTrader 4 broker implementation.

```python
class MT4Broker(IBroker):
    def __init__(self, host: str = "localhost", port: int = 5555):
        """Initialize MT4 broker."""
        pass
    
    def connect(self) -> bool:
        """Connect to MT4 via ZeroMQ."""
        pass
    
    def disconnect(self) -> None:
        """Disconnect from MT4."""
        pass
    
    def get_balance(self) -> float:
        """Get MT4 account balance."""
        pass
    
    def place_order(self, symbol: str, side: int, quantity: float, 
                   price: float, stop_loss: float = None, 
                   take_profit: float = None) -> str:
        """Place MT4 order."""
        pass
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel MT4 order."""
        pass
    
    def get_positions(self) -> List[Position]:
        """Get MT4 positions."""
        pass
    
    def get_orders(self) -> List[Order]:
        """Get MT4 orders."""
        pass
```

## Data Providers

### YFinanceProvider

Yahoo Finance data provider.

```python
class YFinanceProvider(IDataProvider):
    def __init__(self):
        """Initialize YFinance provider."""
        pass
    
    def get_data(self, symbol: str, start_date: str, end_date: str, 
                interval: str = '1d') -> pd.DataFrame:
        """Get data from Yahoo Finance."""
        pass
    
    def get_latest_price(self, symbol: str) -> float:
        """Get latest price from Yahoo Finance."""
        pass
    
    def is_available(self) -> bool:
        """Check if Yahoo Finance is available."""
        pass
```

### CSVProvider

CSV file data provider.

```python
class CSVProvider(IDataProvider):
    def __init__(self, data_dir: str = "data"):
        """Initialize CSV provider."""
        pass
    
    def get_data(self, symbol: str, start_date: str, end_date: str, 
                interval: str = '1d') -> pd.DataFrame:
        """Get data from CSV files."""
        pass
    
    def get_latest_price(self, symbol: str) -> float:
        """Get latest price from CSV."""
        pass
    
    def is_available(self) -> bool:
        """Check if CSV files are available."""
        pass
```

## Services

### BacktestService

Backtesting engine.

```python
class BacktestService:
    def __init__(self, data_provider: IDataProvider):
        """Initialize backtest service."""
        pass
    
    def run_backtest(self, strategy: IStrategy, symbol: str, 
                    start_date: str, end_date: str, 
                    initial_balance: float = 10000.0,
                    risk_config: RiskConfig = None) -> Dict[str, Any]:
        """Run backtest for strategy."""
        pass
    
    def run_walk_forward(self, strategy: IStrategy, symbol: str,
                        start_date: str, end_date: str, 
                        train_period: int, test_period: int,
                        step_size: int = 1) -> Dict[str, Any]:
        """Run walk-forward analysis."""
        pass
```

### TradingController

Main trading controller.

```python
class TradingController:
    def __init__(self, broker: IBroker, data_provider: IDataProvider,
                 risk_engine: RiskEngine, portfolio: Portfolio):
        """Initialize trading controller."""
        pass
    
    def start_trading(self, strategy: IStrategy, symbol: str) -> None:
        """Start trading with strategy."""
        pass
    
    def stop_trading(self, symbol: str) -> None:
        """Stop trading symbol."""
        pass
    
    def update_positions(self) -> None:
        """Update all positions."""
        pass
    
    def process_signals(self) -> None:
        """Process trading signals."""
        pass
```

### PersistenceService

Data persistence service.

```python
class PersistenceService:
    def __init__(self, data_dir: str = "~/.forexsmartbot"):
        """Initialize persistence service."""
        pass
    
    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Save application settings."""
        pass
    
    def load_settings(self) -> Dict[str, Any]:
        """Load application settings."""
        pass
    
    def save_trade(self, trade: Trade) -> None:
        """Save trade to database."""
        pass
    
    def get_trades(self, symbol: str = None, 
                  start_date: datetime = None,
                  end_date: datetime = None) -> List[Trade]:
        """Get trades from database."""
        pass
    
    def export_trades_csv(self, filename: str, 
                         symbol: str = None) -> None:
        """Export trades to CSV."""
        pass
```

## UI Components

### MainWindow

Main application window.

```python
class MainWindow(QMainWindow):
    def __init__(self):
        """Initialize main window."""
        pass
    
    def setup_ui(self) -> None:
        """Setup user interface."""
        pass
    
    def connect_signals(self) -> None:
        """Connect UI signals."""
        pass
    
    def on_connect_clicked(self) -> None:
        """Handle connect button click."""
        pass
    
    def on_start_clicked(self) -> None:
        """Handle start button click."""
        pass
    
    def on_stop_clicked(self) -> None:
        """Handle stop button click."""
        pass
    
    def on_settings_clicked(self) -> None:
        """Handle settings button click."""
        pass
    
    def update_status(self, message: str) -> None:
        """Update status bar."""
        pass
    
    def append_log(self, message: str) -> None:
        """Append message to log."""
        pass
```

### SettingsDialog

Settings configuration dialog.

```python
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        """Initialize settings dialog."""
        pass
    
    def setup_ui(self) -> None:
        """Setup dialog UI."""
        pass
    
    def load_settings(self) -> None:
        """Load current settings."""
        pass
    
    def save_settings(self) -> None:
        """Save settings."""
        pass
    
    def on_ok_clicked(self) -> None:
        """Handle OK button click."""
        pass
    
    def on_cancel_clicked(self) -> None:
        """Handle Cancel button click."""
        pass
```

### ChartWidget

Matplotlib chart widget.

```python
class ChartWidget(QWidget):
    def __init__(self, parent=None):
        """Initialize chart widget."""
        pass
    
    def plot_data(self, df: pd.DataFrame, symbol: str) -> None:
        """Plot price data and indicators."""
        pass
    
    def add_trade_markers(self, trades: List[Trade]) -> None:
        """Add trade markers to chart."""
        pass
    
    def clear_chart(self) -> None:
        """Clear chart."""
        pass
    
    def save_chart(self, filename: str) -> None:
        """Save chart to file."""
        pass
```

### ThemeManager

Theme management.

```python
class ThemeManager:
    def __init__(self):
        """Initialize theme manager."""
        pass
    
    def get_available_themes(self) -> List[str]:
        """Get list of available themes."""
        pass
    
    def get_current_theme(self) -> str:
        """Get current theme."""
        pass
    
    def set_theme(self, theme: str) -> None:
        """Set application theme."""
        pass
    
    def apply_theme(self, app: QApplication) -> None:
        """Apply theme to application."""
        pass
```

## Error Handling

### Custom Exceptions

```python
class ForexSmartBotError(Exception):
    """Base exception for ForexSmartBot."""
    pass

class BrokerError(ForexSmartBotError):
    """Broker-related errors."""
    pass

class DataProviderError(ForexSmartBotError):
    """Data provider errors."""
    pass

class RiskManagementError(ForexSmartBotError):
    """Risk management errors."""
    pass

class StrategyError(ForexSmartBotError):
    """Strategy errors."""
    pass
```

## Configuration

### Environment Variables

- `FOREXSMARTBOT_DATA_DIR`: Data directory path
- `FOREXSMARTBOT_LOG_LEVEL`: Logging level
- `FOREXSMARTBOT_MT4_HOST`: MT4 ZeroMQ host
- `FOREXSMARTBOT_MT4_PORT`: MT4 ZeroMQ port
- `FOREXSMARTBOT_API_KEY`: API key for REST broker

### Configuration Files

- `~/.forexsmartbot/settings.json`: Application settings
- `~/.forexsmartbot/trades.db`: SQLite trades database
- `~/.forexsmartbot/logs/`: Log files directory
