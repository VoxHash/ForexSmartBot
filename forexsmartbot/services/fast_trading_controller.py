"""Fast Trading Controller - Optimized for sniper-like execution speed.

This controller prioritizes speed over analysis, perfect for fast scalping
and sniper trading where milliseconds matter.
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QThread
import logging

from ..core.interfaces import IBroker, IStrategy, IDataProvider, IRiskManager
from ..core.portfolio import Portfolio
from ..core.interfaces import Trade, Position

logger = logging.getLogger(__name__)


class FastTradingController(QObject):
    """High-speed trading controller optimized for minimal latency."""
    
    signal_trade_executed = pyqtSignal(dict)
    signal_error_occurred = pyqtSignal(str)
    signal_log_message = pyqtSignal(str)
    
    def __init__(self, broker: IBroker, data_provider: IDataProvider,
                 risk_manager: IRiskManager, portfolio: Portfolio,
                 fast_mode: bool = True):
        super().__init__()
        
        self.broker = broker
        self.data_provider = data_provider
        self.risk_manager = risk_manager
        self.portfolio = portfolio
        self.fast_mode = fast_mode
        
        self.strategies: Dict[str, IStrategy] = {}
        self.symbols: List[str] = []
        self.is_running = False
        
        self.current_positions: Dict[str, Position] = {}
        self.last_signals: Dict[str, int] = {}
        self.last_execution_time: Dict[str, float] = {}
        
        # Fast mode settings
        self.min_execution_interval = 0.1 if fast_mode else 1.0  # 100ms minimum between trades
        self.max_concurrent_positions = 5 if fast_mode else 10
        
        # Pre-calculated values cache
        self._position_size_cache: Dict[str, float] = {}
        self._cache_timestamp: Dict[str, float] = {}
        self._cache_ttl = 5.0  # Cache for 5 seconds
        
        # Timer for trading cycle
        self.timer = QTimer()
        self.timer.timeout.connect(self._fast_trading_cycle)
        self.timer.setSingleShot(False)
        
    def add_strategy(self, symbol: str, strategy: IStrategy) -> None:
        """Add strategy for a symbol."""
        self.strategies[symbol] = strategy
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            
    def start_trading(self, interval_ms: int = 100) -> bool:
        """Start fast trading with minimal interval (default 100ms)."""
        if not self.broker.is_connected():
            if not self.broker.connect():
                self.signal_error_occurred.emit("Failed to connect to broker")
                return False
                
        self.is_running = True
        # Use minimal interval for fast mode
        actual_interval = min(interval_ms, 100) if self.fast_mode else interval_ms
        self.timer.start(actual_interval)
        self.signal_log_message.emit(f"Fast trading started (interval: {actual_interval}ms)")
        return True
        
    def stop_trading(self) -> None:
        """Stop trading."""
        self.is_running = False
        self.timer.stop()
        self.signal_log_message.emit("Trading stopped")
        
    def _fast_trading_cycle(self) -> None:
        """Ultra-fast trading cycle with minimal overhead."""
        if not self.is_running:
            return
            
        try:
            # Update positions quickly
            self._update_positions_fast()
            
            # Process symbols in parallel-ready order
            for symbol in self.symbols:
                if symbol in self.strategies:
                    self._process_symbol_fast(symbol)
                    
        except Exception as e:
            logger.error(f"Error in fast trading cycle: {e}", exc_info=True)
            self.signal_error_occurred.emit(f"Trading cycle error: {str(e)}")
            
    def _process_symbol_fast(self, symbol: str) -> None:
        """Process symbol with minimal latency."""
        try:
            # Check execution cooldown (non-blocking)
            current_time = time.time()
            if symbol in self.last_execution_time:
                elapsed = current_time - self.last_execution_time[symbol]
                if elapsed < self.min_execution_interval:
                    return  # Skip if too soon
                    
            # Check concurrent position limit
            if len(self.current_positions) >= self.max_concurrent_positions:
                if symbol not in self.current_positions:
                    return  # Don't open new positions if at limit
                    
            # Get current price (fast path)
            try:
                current_price = self.data_provider.get_current_price(symbol)
                if not current_price or current_price <= 0:
                    return
            except Exception:
                return  # Skip if price unavailable
                
            # Get strategy signal (use cached indicators if available)
            strategy = self.strategies[symbol]
            
            # Fast signal generation - use minimal data
            try:
                # Get minimal historical data for fast strategies
                if hasattr(strategy, 'generate_signal_fast'):
                    signal = strategy.generate_signal_fast(symbol, current_price)
                else:
                    # Fallback to standard signal generation
                    historical_data = self.data_provider.get_historical_data(
                        symbol, period='1d', interval='1m'
                    )
                    if historical_data is None or len(historical_data) < 2:
                        return
                    signal = strategy.generate_signal(historical_data)
            except Exception as e:
                logger.debug(f"Signal generation error for {symbol}: {e}")
                return
                
            # Process signal
            if signal != 0 and signal != self.last_signals.get(symbol, 0):
                self._execute_trade_fast(symbol, signal, current_price, strategy)
                self.last_signals[symbol] = signal
                self.last_execution_time[symbol] = current_time
                
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}", exc_info=True)
            
    def _execute_trade_fast(self, symbol: str, signal: int, price: float,
                           strategy: IStrategy) -> None:
        """Execute trade with minimal latency."""
        try:
            # Check existing position
            if symbol in self.current_positions:
                current_pos = self.current_positions[symbol]
                if (signal > 0 and current_pos.side > 0) or (signal < 0 and current_pos.side < 0):
                    return  # Same direction, skip
                elif (signal > 0 and current_pos.side < 0) or (signal < 0 and current_pos.side > 0):
                    # Close opposite position first
                    self._close_position_fast(symbol, price)
                    
            # Calculate position size (use cache if available)
            balance = self.portfolio.get_total_balance()
            cache_key = f"{symbol}_{balance:.0f}"
            current_time = time.time()
            
            if (cache_key in self._position_size_cache and 
                cache_key in self._cache_timestamp and
                current_time - self._cache_timestamp[cache_key] < self._cache_ttl):
                position_size = self._position_size_cache[cache_key]
            else:
                # Calculate fresh
                win_rate = self.risk_manager.get_recent_win_rate(symbol, strategy.name)
                position_size = self.risk_manager.calculate_position_size(
                    symbol, strategy.name, balance, None, win_rate
                )
                self._position_size_cache[cache_key] = position_size
                self._cache_timestamp[cache_key] = current_time
                
            # Quick risk check
            if position_size < 10.0:  # Minimum trade size
                return
                
            # Calculate quantity
            quantity = position_size / price
            
            # Get stop loss/take profit (use defaults if strategy is slow)
            try:
                # Try fast stop/tp calculation
                stop_loss = strategy.stop_loss({'Close': price}) if hasattr(strategy, 'stop_loss') else None
                take_profit = strategy.take_profit({'Close': price}) if hasattr(strategy, 'take_profit') else None
            except Exception:
                # Use default risk/reward if strategy calculation fails
                risk_pct = 0.01  # 1% default risk
                stop_loss = price * (1 - risk_pct) if signal > 0 else price * (1 + risk_pct)
                take_profit = price * (1 + risk_pct * 2) if signal > 0 else price * (1 - risk_pct * 2)
                
            # Submit order immediately (non-blocking if possible)
            order_id = self.broker.submit_order(symbol, signal, quantity, stop_loss, take_profit)
            
            if order_id:
                # Create position
                position = Position(
                    symbol=symbol,
                    side=signal,
                    quantity=quantity,
                    entry_price=price,
                    current_price=price,
                    unrealized_pnl=0.0,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    strategy=strategy.name
                )
                
                self.current_positions[symbol] = position
                self.portfolio.add_position(position)
                
                self.signal_trade_executed.emit({
                    'symbol': symbol,
                    'side': 'LONG' if signal > 0 else 'SHORT',
                    'quantity': quantity,
                    'price': price,
                    'strategy': strategy.name,
                    'execution_time_ms': (time.time() - self.last_execution_time.get(symbol, time.time())) * 1000
                })
                
                logger.info(f"Fast trade: {symbol} {'LONG' if signal > 0 else 'SHORT'} "
                          f"qty={quantity:.6f} @ {price:.5f}")
            else:
                self.signal_error_occurred.emit(f"Order submission failed for {symbol}")
                
        except Exception as e:
            logger.error(f"Error executing fast trade for {symbol}: {e}", exc_info=True)
            self.signal_error_occurred.emit(f"Trade execution error: {str(e)}")
            
    def _close_position_fast(self, symbol: str, price: float) -> None:
        """Close position quickly."""
        if symbol not in self.current_positions:
            return
            
        try:
            position = self.current_positions.pop(symbol)
            pnl = position.side * position.quantity * (price - position.entry_price)
            
            # Create trade record
            trade = Trade(
                symbol=symbol,
                side=position.side,
                quantity=position.quantity,
                entry_price=position.entry_price,
                exit_price=price,
                pnl=pnl,
                strategy=position.strategy,
                entry_time=position.timestamp,
                exit_time=datetime.now()
            )
            
            self.portfolio.add_trade(trade)
            self.portfolio.remove_position(symbol)
            
            # Close via broker
            self.broker.close_position(symbol)
            
        except Exception as e:
            logger.error(f"Error closing position {symbol}: {e}", exc_info=True)
            
    def _update_positions_fast(self) -> None:
        """Update positions with current prices (optimized)."""
        if not self.current_positions:
            return
            
        try:
            # Batch price updates if broker supports it
            if hasattr(self.broker, 'get_all_prices'):
                prices = self.broker.get_all_prices(list(self.current_positions.keys()))
                for symbol, position in self.current_positions.items():
                    if symbol in prices:
                        position.current_price = prices[symbol]
                        position.unrealized_pnl = position.side * position.quantity * (
                            position.current_price - position.entry_price
                        )
            else:
                # Individual updates (slower but works)
                for symbol, position in list(self.current_positions.items()):
                    try:
                        current_price = self.data_provider.get_current_price(symbol)
                        if current_price:
                            position.current_price = current_price
                            position.unrealized_pnl = position.side * position.quantity * (
                                current_price - position.entry_price
                            )
                    except Exception:
                        pass  # Skip if price unavailable
                        
        except Exception as e:
            logger.debug(f"Error updating positions: {e}")
            
    def clear_cache(self) -> None:
        """Clear cached values to free memory."""
        self._position_size_cache.clear()
        self._cache_timestamp.clear()
        
    def get_performance_stats(self) -> dict:
        """Get performance statistics."""
        return {
            'active_positions': len(self.current_positions),
            'cache_size': len(self._position_size_cache),
            'fast_mode': self.fast_mode,
            'min_interval_ms': self.min_execution_interval * 1000
        }
