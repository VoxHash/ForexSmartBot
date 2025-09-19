"""Core interfaces for ForexSmartBot."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class Order:
    """Represents a trading order."""
    symbol: str
    side: int  # +1 for long, -1 for short
    quantity: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Position:
    """Represents an open position."""
    symbol: str
    side: int
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Trade:
    """Represents a completed trade."""
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


class IBroker(ABC):
    """Broker interface for trading operations."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the broker. Returns True if successful."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the broker."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        pass
    
    @abstractmethod
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        pass
    
    @abstractmethod
    def submit_order(self, symbol: str, side: int, quantity: float, 
                    stop_loss: Optional[float] = None, 
                    take_profit: Optional[float] = None) -> Optional[str]:
        """Submit an order. Returns order ID or None if failed."""
        pass
    
    @abstractmethod
    def close_all(self, symbol: str) -> bool:
        """Close all positions for symbol. Returns True if successful."""
        pass
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    def get_balance(self) -> float:
        """Get account balance."""
        pass
    
    @abstractmethod
    def get_equity(self) -> float:
        """Get account equity (balance + unrealized PnL)."""
        pass


class IStrategy(ABC):
    """Strategy interface for trading algorithms."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name."""
        pass
    
    @property
    @abstractmethod
    def params(self) -> Dict[str, Any]:
        """Strategy parameters."""
        pass
    
    @abstractmethod
    def set_params(self, **kwargs) -> None:
        """Update strategy parameters."""
        pass
    
    @abstractmethod
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        pass
    
    @abstractmethod
    def signal(self, df: pd.DataFrame) -> int:
        """Generate trading signal: +1 (buy), -1 (sell), 0 (hold)."""
        pass
    
    @abstractmethod
    def volatility(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate volatility for position sizing."""
        pass
    
    @abstractmethod
    def stop_loss(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate stop loss price."""
        pass
    
    @abstractmethod
    def take_profit(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate take profit price."""
        pass


class IDataProvider(ABC):
    """Data provider interface for market data."""
    
    @abstractmethod
    def get_data(self, symbol: str, start: str, end: str, 
                interval: str = "1h") -> pd.DataFrame:
        """Get historical data for symbol."""
        pass
    
    @abstractmethod
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for symbol."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if data provider is available."""
        pass


class IRiskManager(ABC):
    """Risk management interface."""
    
    @abstractmethod
    def calculate_position_size(self, symbol: str, strategy: str, 
                              balance: float, volatility: Optional[float],
                              win_rate: Optional[float] = None) -> float:
        """Calculate position size based on risk parameters."""
        pass
    
    @abstractmethod
    def check_daily_risk_limit(self, current_pnl: float, balance: float) -> bool:
        """Check if daily risk limit is exceeded."""
        pass
    
    @abstractmethod
    def check_drawdown_limit(self, current_equity: float, peak_equity: float) -> bool:
        """Check if drawdown limit is exceeded."""
        pass
    
    @abstractmethod
    def get_risk_multiplier(self, symbol: str, strategy: str) -> float:
        """Get risk multiplier for symbol/strategy combination."""
        pass
