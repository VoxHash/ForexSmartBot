"""Trading controller for orchestrating the trading system."""

import pandas as pd
from typing import Dict, List, Optional, Callable
from datetime import datetime
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

from ..core.interfaces import IBroker, IStrategy, IDataProvider, IRiskManager
from ..core.portfolio import Portfolio
from ..core.interfaces import Trade, Position
from ..core.trade_manager import TradeManager


class TradingController(QObject):
    """Main trading controller that orchestrates the trading system."""
    
    # Signals for UI updates
    signal_trade_executed = pyqtSignal(dict)  # Trade executed
    signal_position_updated = pyqtSignal(dict)  # Position updated
    signal_equity_updated = pyqtSignal(float)  # Equity updated
    signal_error_occurred = pyqtSignal(str)  # Error occurred
    signal_log_message = pyqtSignal(str)  # Log message
    
    def __init__(self, broker: IBroker, data_provider: IDataProvider, 
                 risk_manager: IRiskManager, portfolio: Portfolio):
        super().__init__()
        
        self.broker = broker
        self.data_provider = data_provider
        self.risk_manager = risk_manager
        self.portfolio = portfolio
        
        # Advanced trade management
        self.trade_manager = TradeManager()
        
        self.strategies: Dict[str, IStrategy] = {}
        self.symbols: List[str] = []
        self.is_running = False
        
        # Trading state
        self.current_positions: Dict[str, Position] = {}
        self.last_signals: Dict[str, int] = {}
        
        # Timer for periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._trading_cycle)
        
    def add_strategy(self, symbol: str, strategy: IStrategy) -> None:
        """Add strategy for a symbol."""
        self.strategies[symbol] = strategy
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            
    def remove_strategy(self, symbol: str) -> None:
        """Remove strategy for a symbol."""
        if symbol in self.strategies:
            del self.strategies[symbol]
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            
    def set_symbols(self, symbols: List[str]) -> None:
        """Set trading symbols."""
        self.symbols = symbols
        
    def start_trading(self, interval_ms: int = 10000) -> bool:
        """Start trading with specified interval."""
        if not self.broker.is_connected():
            if not self.broker.connect():
                self.signal_error_occurred.emit("Failed to connect to broker")
                return False
                
        self.is_running = True
        self.timer.start(interval_ms)
        self.signal_log_message.emit("Trading started")
        return True
        
    def stop_trading(self) -> None:
        """Stop trading."""
        self.is_running = False
        self.timer.stop()
        self.signal_log_message.emit("Trading stopped")
        
    def _trading_cycle(self) -> None:
        """Main trading cycle executed by timer."""
        if not self.is_running:
            return
            
        try:
            # Update positions with advanced trade management
            self._update_positions_with_management()
            
            # Update portfolio with current positions
            self._update_portfolio()
            
            # Process each symbol
            for symbol in self.symbols:
                if symbol in self.strategies:
                    self._process_symbol(symbol)
                    
        except Exception as e:
            self.signal_error_occurred.emit(f"Trading cycle error: {str(e)}")
            
    def _process_symbol(self, symbol: str) -> None:
        """Process trading logic for a single symbol."""
        try:
            # Check if demo mode is enabled
            if hasattr(self, 'demo_mode') and self.demo_mode:
                self._process_symbol_demo(symbol)
                return
                
            strategy = self.strategies[symbol]
            
            # Get latest data
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - pd.Timedelta(days=90)).strftime('%Y-%m-%d')
            
            df = self.data_provider.get_data(symbol, start_date, end_date, "1h")
            if df.empty:
                return
                
            # Calculate indicators
            df = strategy.indicators(df)
            
            # Get current price
            current_price = self.data_provider.get_latest_price(symbol)
            if current_price is None:
                return
                
            # Generate signal
            signal = strategy.signal(df)
            volatility = strategy.volatility(df)
            
            # Update last signal
            self.last_signals[symbol] = signal
            
            # Process trading logic
            if signal != 0:
                self._execute_trade(symbol, signal, current_price, strategy, volatility)
            else:
                # Check for exit conditions
                self._check_exit_conditions(symbol, current_price, strategy)
                
        except Exception as e:
            self.signal_error_occurred.emit(f"Error processing {symbol}: {str(e)}")
            
    def _execute_trade(self, symbol: str, signal: int, price: float, 
                      strategy: IStrategy, volatility: Optional[float]) -> None:
        """Execute a trade based on signal."""
        try:
            # Check if we already have a position in this symbol
            if symbol in self.current_positions:
                current_pos = self.current_positions[symbol]
                
                # If signal is opposite to current position, close it first
                if (signal > 0 and current_pos.side < 0) or (signal < 0 and current_pos.side > 0):
                    self._close_position(symbol, price)
                    
                # If signal is same as current position, don't open new one
                elif (signal > 0 and current_pos.side > 0) or (signal < 0 and current_pos.side < 0):
                    return
                    
            # Calculate position size
            balance = self.portfolio.get_total_balance()
            win_rate = self.risk_manager.get_recent_win_rate(symbol, strategy.name)
            
            position_size = self.risk_manager.calculate_position_size(
                symbol, strategy.name, balance, volatility, win_rate
            )
            
            # Check risk limits
            if self.risk_manager.check_daily_risk_limit(0, balance):
                self.signal_log_message.emit(f"Daily risk limit exceeded for {symbol}")
                return
                
            # Calculate quantity
            quantity = position_size / price
            
            # Prepare data for strategy calculations
            current_data = {
                'Close': price,
                'High': price * 1.001,
                'Low': price * 0.999,
                'Open': price,
                'Volume': 1000
            }
            
            # Get stop loss and take profit from strategy
            stop_loss = strategy.stop_loss(current_data)
            take_profit = strategy.take_profit(current_data)
            
            # Submit order to broker
            order_id = self.broker.submit_order(symbol, signal, quantity, stop_loss, take_profit)
            
            if order_id:
                # Create position with advanced trade management
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
                
                # Add to trade manager for advanced management
                self.trade_manager.positions[symbol] = position
                
                self.current_positions[symbol] = position
                self.portfolio.add_position(position)
                
                self.signal_trade_executed.emit({
                    'symbol': symbol,
                    'side': 'LONG' if signal > 0 else 'SHORT',
                    'quantity': quantity,
                    'price': price,
                    'strategy': strategy.name
                })
                
                self.signal_log_message.emit(
                    f"Opened {symbol} {'LONG' if signal > 0 else 'SHORT'} "
                    f"qty={quantity:.6f} @ {price:.5f}"
                )
            else:
                self.signal_error_occurred.emit(f"Failed to submit order for {symbol}")
                
        except Exception as e:
            self.signal_error_occurred.emit(f"Error executing trade for {symbol}: {str(e)}")
            
    def _check_exit_conditions(self, symbol: str, price: float, strategy: IStrategy) -> None:
        """Check exit conditions for existing positions."""
        if symbol not in self.current_positions:
            return
            
        position = self.current_positions[symbol]
        
        # Check stop loss
        if position.stop_loss is not None:
            if (position.side > 0 and price <= position.stop_loss) or \
               (position.side < 0 and price >= position.stop_loss):
                self._close_position(symbol, price, "Stop Loss")
                return
                
        # Check take profit
        if position.take_profit is not None:
            if (position.side > 0 and price >= position.take_profit) or \
               (position.side < 0 and price <= position.take_profit):
                self._close_position(symbol, price, "Take Profit")
                return
                
    def _update_positions_with_management(self) -> None:
        """Update all positions with advanced trade management."""
        for symbol in list(self.current_positions.keys()):
            try:
                # Get current price
                current_price = self.data_provider.get_latest_price(symbol)
                if current_price is None:
                    continue
                
                # Update position with trade management
                position = self.trade_manager.update_position(symbol, current_price)
                if position:
                    # Check for stop loss hit
                    if self.trade_manager.check_stop_loss_hit(position, current_price):
                        self._close_position(symbol, current_price, "Stop Loss Hit")
                        continue
                    
                    # Update position in portfolio
                    self.portfolio.update_position(symbol, position)
                    
                    # Emit position update signal
                    self.signal_position_updated.emit({
                        'symbol': symbol,
                        'side': 'Long' if position.side > 0 else 'Short',
                        'quantity': position.get_remaining_quantity(),
                        'entry_price': position.entry_price,
                        'current_price': current_price,
                        'unrealized_pnl': position.unrealized_pnl,
                        'stop_loss': position.stop_loss,
                        'take_profit': position.take_profit,
                        'breakeven_triggered': position.breakeven_triggered
                    })
                    
            except Exception as e:
                self.signal_error_occurred.emit(f"Error updating position {symbol}: {str(e)}")
    
    def _close_position(self, symbol: str, price: float, reason: str = "Manual") -> None:
        """Close a position with advanced trade management."""
        if symbol not in self.current_positions:
            return
            
        # Use trade manager to close position
        trade = self.trade_manager.close_position(symbol, price, reason)
        
        if trade:
            # Add to portfolio
            self.portfolio.add_trade(trade)
            
            # Update risk manager
            self.risk_manager.add_trade_result(trade.pnl, symbol, trade.strategy)
            
            # Remove position
            del self.current_positions[symbol]
            self.portfolio.remove_position(symbol)
            
            # Update broker
            self.broker.close_all(symbol)
            
            self.signal_trade_executed.emit({
                'symbol': symbol,
                'action': 'CLOSED',
                'pnl': trade.pnl,
                'reason': reason,
                'breakeven_triggered': trade.breakeven_triggered,
                'partial_closes': len(trade.partial_closes)
            })
            
            self.signal_log_message.emit(
                f"Closed {symbol} {'LONG' if trade.side > 0 else 'SHORT'} "
                f"PnL={trade.pnl:.2f} ({reason})"
            )
        
    def _update_portfolio(self) -> None:
        """Update portfolio with current market data."""
        try:
            # Get current prices for all positions
            prices = {}
            for symbol in self.current_positions.keys():
                price = self.data_provider.get_latest_price(symbol)
                if price is not None:
                    prices[symbol] = price
                    
            # Update positions
            for symbol, position in self.current_positions.items():
                if symbol in prices:
                    position.current_price = prices[symbol]
                    position.unrealized_pnl = position.side * position.quantity * (
                        position.current_price - position.entry_price
                    )
                    
            # Update portfolio equity
            self.portfolio.update_equity(self.broker.get_balance())
            
            # Emit equity update
            self.signal_equity_updated.emit(self.portfolio.get_total_equity())
            
        except Exception as e:
            self.signal_error_occurred.emit(f"Error updating portfolio: {str(e)}")
            
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary."""
        metrics = self.portfolio.calculate_metrics()
        risk_summary = self.risk_manager.get_risk_summary()
        
        return {
            'equity': metrics.total_equity,
            'balance': metrics.total_balance,
            'unrealized_pnl': metrics.unrealized_pnl,
            'realized_pnl': metrics.realized_pnl,
            'max_drawdown': metrics.max_drawdown,
            'current_drawdown': metrics.current_drawdown,
            'win_rate': metrics.win_rate,
            'total_trades': metrics.total_trades,
            'risk_summary': risk_summary
        }

    def enable_demo_mode(self) -> None:
        """Enable demo mode with forced trading activity."""
        self.demo_mode = True
        self.demo_trade_counter = 0
        self.signal_log_message.emit("Demo mode enabled - will generate trading activity")
        
    def _process_symbol_demo(self, symbol: str) -> None:
        """Process trading logic for demo mode."""
        try:
            # Force some trading activity for demo
            self.demo_trade_counter += 1
            
            # Every 3rd cycle, create a trade
            if self.demo_trade_counter % 3 == 0:
                # Create a demo position
                from ..core.interfaces import Position
                import random
                
                side = random.choice([1, -1])
                quantity = random.uniform(0.05, 0.2)
                entry_price = random.uniform(1.1700, 1.1900)
                current_price = entry_price + random.uniform(-0.002, 0.002)
                pnl = side * quantity * (current_price - entry_price) * 10000
                
                position = Position(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    entry_price=entry_price,
                    current_price=current_price,
                    unrealized_pnl=pnl
                )
                
                self.current_positions[symbol] = position
                self.portfolio.add_position(position)
                
                action = "LONG" if side > 0 else "SHORT"
                self.signal_trade_executed.emit({
                    'symbol': symbol,
                    'side': action,
                    'quantity': quantity,
                    'price': entry_price,
                    'strategy': 'Demo Mode'
                })
                
                self.signal_log_message.emit(
                    f"Demo trade: {action} {symbol} qty={quantity:.3f} @ {entry_price:.4f} PnL=${pnl:.2f}"
                )
                
        except Exception as e:
            self.signal_error_occurred.emit(f"Demo trading error: {str(e)}")
