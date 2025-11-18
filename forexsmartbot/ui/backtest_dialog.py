"""
Backtest Dialog for ForexSmartBot
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QDoubleSpinBox,
                             QPushButton, QTextEdit, QProgressBar, QGroupBox,
                             QDateEdit, QSpinBox, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QFont
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from ..strategies import get_strategy
from ..adapters.data import YFinanceProvider, CSVProvider, MultiProvider
from ..core.portfolio import Portfolio
from ..core.risk_engine import RiskEngine, RiskConfig
from ..services.gpu_backtest import GPUBacktestService
from ..services.backtest import BacktestService
from ..utils.gpu_utils import get_gpu_manager, GPUManager


class BacktestWorker(QThread):
    """Worker thread for running backtests."""
    
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    backtest_completed = pyqtSignal(dict)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
    def run(self):
        """Run the backtest."""
        try:
            self.log_updated.emit("Starting backtest...")
            self.progress_updated.emit(10)
            
            # Initialize components
            portfolio = Portfolio(self.config['initial_balance'])
            risk_config = RiskConfig(
                base_risk_pct=self.config['risk_pct'],
                max_risk_pct=self.config['max_risk_pct'],
                daily_risk_cap=self.config['daily_risk_cap'],
                max_drawdown_pct=self.config['max_drawdown_pct']
            )
            risk_engine = RiskEngine(risk_config)
            
            # Log configuration for debugging
            self.log_updated.emit(f"Risk per trade: {self.config['risk_pct']:.2%}")
            self.log_updated.emit(f"Max risk: {self.config['max_risk_pct']:.2%}")
            self.log_updated.emit(f"Leverage: {self.config['leverage']}")
            self.log_updated.emit(f"Initial balance: ${self.config['initial_balance']:,.2f}")
            
            # Get data
            self.log_updated.emit("Loading data...")
            self.progress_updated.emit(20)
            
            # Use MultiProvider for better data source handling
            data_provider = MultiProvider()
            
            # Check if GPU is available and use GPU backtest if possible
            gpu_manager = get_gpu_manager()
            use_gpu = gpu_manager.is_gpu_available()
            
            if use_gpu:
                self.log_updated.emit("GPU acceleration available - attempting GPU backtest")
                try:
                    # Extract strategy name
                    strategy_name = self.config['strategy']
                    for emoji in ['🟢 ', '🟡 ', '🔴 ', '⚪ ']:
                        if emoji in strategy_name:
                            strategy_name = strategy_name.replace(emoji, '')
                    if ' (' in strategy_name:
                        strategy_name = strategy_name.split(' (')[0]
                    
                    # Get strategy
                    strategy = get_strategy(strategy_name)
                    if not strategy:
                        self.log_updated.emit(f"Strategy {strategy_name} not found, using CPU")
                        use_gpu = False
                    else:
                        # Set strategy parameters
                        if hasattr(strategy, 'set_params'):
                            if strategy_name == 'SMA_Crossover':
                                strategy.set_params(fast_period=10, slow_period=20)
                            elif strategy_name == 'BreakoutATR':
                                strategy.set_params(lookback_period=20, atr_multiplier=2.0)
                            elif strategy_name == 'RSI_Reversion':
                                strategy.set_params(rsi_period=14, oversold=30, overbought=70)
                        
                        # Create risk config
                        risk_config = RiskConfig(
                            base_risk_pct=self.config['risk_pct'],
                            max_risk_pct=self.config['max_risk_pct'],
                            daily_risk_cap=self.config['daily_risk_cap'],
                            max_drawdown_pct=self.config['max_drawdown_pct']
                        )
                        
                        # Run GPU backtest
                        self.log_updated.emit("Running GPU-accelerated backtest...")
                        self.progress_updated.emit(40)
                        
                        symbol = f"{self.config['symbol']}=X" if '=X' not in self.config['symbol'] else self.config['symbol']
                        gpu_backtest = GPUBacktestService(data_provider, use_gpu=True)
                        results = gpu_backtest.run_backtest(
                            strategy=strategy,
                            symbol=symbol,
                            start_date=self.config['start_date'],
                            end_date=self.config['end_date'],
                            initial_balance=self.config['initial_balance'],
                            risk_config=risk_config
                        )
                        
                        if 'error' not in results:
                            self.log_updated.emit("GPU backtest completed successfully!")
                            self.progress_updated.emit(90)
                            self.backtest_completed.emit(results)
                            return
                        else:
                            self.log_updated.emit(f"GPU backtest error: {results.get('error', 'Unknown')}, falling back to CPU")
                            use_gpu = False
                            
                except Exception as e:
                    self.log_updated.emit(f"GPU backtest failed: {str(e)}, falling back to CPU")
                    use_gpu = False
            
            # Fallback to CPU backtest
            if not use_gpu:
                self.log_updated.emit("Using CPU backtest service")
            
            df = data_provider.get_data(
                f"{self.config['symbol']}=X",
                self.config['start_date'],
                self.config['end_date'],
                self.config['interval']
            )
            
            if df.empty:
                self.log_updated.emit("No data available, using sample data")
                df = self.create_sample_data()
            
            # Ensure proper column names (case insensitive)
            df.columns = df.columns.str.title()
            if 'Close' not in df.columns:
                df['Close'] = df['Adj Close'] if 'Adj Close' in df.columns else df['Close']
                
            self.log_updated.emit(f"Loaded {len(df)} data points")
            self.progress_updated.emit(30)
            
            # Extract strategy name from risk level indicator
            strategy_name = self.config['strategy']
            # Remove emoji prefixes
            for emoji in ['🟢 ', '🟡 ', '🔴 ', '⚪ ']:
                if emoji in strategy_name:
                    strategy_name = strategy_name.replace(emoji, '')
            # Remove risk level suffix in parentheses
            if ' (' in strategy_name:
                strategy_name = strategy_name.split(' (')[0]
            
            # Get strategy
            strategy = get_strategy(strategy_name)
            if not strategy:
                self.log_updated.emit(f"Strategy {strategy_name} not found")
                return
                
            # Set strategy parameters based on strategy type
            if hasattr(strategy, 'set_params'):
                if strategy_name == 'SMA_Crossover':
                    strategy.set_params(
                        fast_period=10,  # Shorter period for more signals
                        slow_period=20,  # Shorter period for more signals
                        atr_period=14
                    )
                elif strategy_name == 'BreakoutATR':
                    strategy.set_params(
                        lookback_period=10,  # Shorter period for more signals
                        atr_period=14,
                        atr_multiplier=1.0,  # More sensitive
                        min_breakout_pct=0.0005  # Lower threshold
                    )
                elif strategy_name == 'RSI_Reversion':
                    strategy.set_params(
                        rsi_period=14,
                        oversold_level=30,  # More sensitive
                        overbought_level=70,  # More sensitive
                        atr_period=14
                    )
                elif strategy_name == 'Mean_Reversion':
                    strategy.set_params(
                        bb_period=20,
                        bb_std=2.0,
                        rsi_period=14,
                        rsi_oversold=30,
                        rsi_overbought=70,
                        lookback_period=20
                    )
                elif strategy_name == 'Scalping_MA':
                    strategy.set_params(
                        ema_fast=5,
                        ema_medium=10,
                        ema_slow=20,
                        rsi_period=14,
                        rsi_oversold=35,
                        rsi_overbought=65,
                        atr_period=14,
                        lookback_period=20
                    )
                elif strategy_name == 'Momentum_Breakout':
                    strategy.set_params(
                        fast_ema=12,
                        slow_ema=26,
                        signal_ema=9,
                        atr_period=14,
                        breakout_period=20,
                        momentum_threshold=0.02,
                        lookback_period=20
                    )
                elif strategy_name == 'News_Trading':
                    strategy.set_params(
                        volatility_period=20,
                        volatility_threshold=0.015,
                        atr_period=14,
                        breakout_period=5,
                        momentum_period=10,
                        lookback_period=20
                    )
                elif strategy_name == 'ML_Adaptive_SuperTrend':
                    strategy.set_params(
                        lookback_period=20,
                        atr_period=14,
                        atr_multiplier=2.0,
                        volatility_period=50,
                        n_clusters=3,
                        min_samples=100
                    )
                elif strategy_name == 'Adaptive_Trend_Flow':
                    strategy.set_params(
                        lookback_period=20,
                        ema_fast=12,
                        ema_slow=26,
                        rsi_period=14,
                        atr_period=14,
                        ml_period=50,
                        trend_threshold=0.6,
                        min_samples=100
                    )
                
            self.log_updated.emit(f"Using strategy: {strategy_name}")
            self.progress_updated.emit(40)
            
            # Run backtest
            self.log_updated.emit("Running backtest...")
            trades = []
            positions = {}
            last_signal_time = None
            signal_cooldown = 5  # Minimum bars between signals
            
            for i, (timestamp, row) in enumerate(df.iterrows()):
                if i % 100 == 0:
                    progress = 40 + int((i / len(df)) * 50)
                    self.progress_updated.emit(progress)
                
                # Get current data slice
                current_data = df.iloc[:i+1]
                
                try:
                    # Calculate indicators first
                    current_data = strategy.indicators(current_data)
                    
                    # Generate signal
                    signal = strategy.signal(current_data)
                    
                    # Debug: Log signal generation
                    if i % 50 == 0:  # Log every 50th iteration
                        if self.config['strategy'] == 'SMA_Crossover':
                            sma_fast = current_data['SMA_fast'].iloc[-1] if 'SMA_fast' in current_data.columns else 0
                            sma_slow = current_data['SMA_slow'].iloc[-1] if 'SMA_slow' in current_data.columns else 0
                            self.log_updated.emit(f"Row {i}: SMA_fast={sma_fast:.4f}, SMA_slow={sma_slow:.4f}, Signal={signal}")
                        elif self.config['strategy'] == 'BreakoutATR':
                            donchian_high = current_data['Donchian_high'].iloc[-1] if 'Donchian_high' in current_data.columns else 0
                            donchian_low = current_data['Donchian_low'].iloc[-1] if 'Donchian_low' in current_data.columns else 0
                            atr = current_data['ATR'].iloc[-1] if 'ATR' in current_data.columns else 0
                            self.log_updated.emit(f"Row {i}: Donchian_high={donchian_high:.4f}, Donchian_low={donchian_low:.4f}, ATR={atr:.4f}, Signal={signal}")
                        elif self.config['strategy'] == 'RSI_Reversion':
                            rsi = current_data['RSI'].iloc[-1] if 'RSI' in current_data.columns else 0
                            atr = current_data['ATR'].iloc[-1] if 'ATR' in current_data.columns else 0
                            self.log_updated.emit(f"Row {i}: RSI={rsi:.2f}, ATR={atr:.4f}, Signal={signal}")
                        elif self.config['strategy'] == 'ML_Adaptive_SuperTrend':
                            supertrend = current_data['SuperTrend'].iloc[-1] if 'SuperTrend' in current_data.columns else 0
                            direction = current_data['Direction'].iloc[-1] if 'Direction' in current_data.columns else 0
                            atr = current_data['ATR'].iloc[-1] if 'ATR' in current_data.columns else 0
                            self.log_updated.emit(f"Row {i}: SuperTrend={supertrend:.4f}, Direction={direction:.0f}, ATR={atr:.4f}, Signal={signal}")
                        elif self.config['strategy'] == 'Adaptive_Trend_Flow':
                            trend_flow = current_data['Trend_Flow'].iloc[-1] if 'Trend_Flow' in current_data.columns else 0
                            signal_strength = current_data['Signal_Strength'].iloc[-1] if 'Signal_Strength' in current_data.columns else 0
                            ml_score = current_data['ML_Trend_Score'].iloc[-1] if 'ML_Trend_Score' in current_data.columns else 0
                            self.log_updated.emit(f"Row {i}: Trend_Flow={trend_flow:.3f}, Signal_Strength={signal_strength:.3f}, ML_Score={ml_score:.3f}, Signal={signal}")
                        else:
                            self.log_updated.emit(f"Row {i}: Signal={signal}")
                        
                except Exception as e:
                    self.log_updated.emit(f"Error processing data at row {i}: {str(e)}")
                    continue
                
                if signal != 0:
                    # Check signal cooldown
                    if last_signal_time is not None and (i - last_signal_time) < signal_cooldown:
                        continue
                    
                    # Only trade if we don't have a position or if signal is opposite to current position
                    should_trade = False
                    
                    if self.config['symbol'] not in positions:
                        # No position, open new one
                        should_trade = True
                    else:
                        # Check if signal is opposite to current position
                        current_side = positions[self.config['symbol']]['side']
                        if (signal > 0 and current_side < 0) or (signal < 0 and current_side > 0):
                            should_trade = True
                    
                    if should_trade:
                        # Calculate position size based on risk per trade and leverage
                        current_balance = portfolio.get_total_balance()
                        risk_amount = current_balance * self.config['risk_pct']
                        
                        # Extract leverage from config (e.g., "1:200 (Maximum Risk)" -> 200)
                        leverage_str = self.config.get('leverage', '1:10 (Moderate)')
                        try:
                            leverage = float(leverage_str.split(':')[1].split(' ')[0])
                        except:
                            leverage = 10.0  # Default leverage
                        
                        # Calculate position size with proper risk management
                        try:
                            atr = current_data['ATR'].iloc[-1]
                            if pd.notna(atr) and atr > 0:
                                # Position size = Risk Amount / (ATR * 2)
                                # Leverage affects the actual trade size, not position sizing
                                position_size = risk_amount / (atr * 2)
                            else:
                                # Fallback: risk 1% of account per pip
                                position_size = risk_amount / 0.0001
                        except:
                            position_size = risk_amount / 0.0001
                        
                        # Ensure minimum position size
                        position_size = max(position_size, 0.01)
                        
                        if self.config['symbol'] in positions:
                            # Close existing position first
                            pos = positions[self.config['symbol']]
                            exit_price = row['Close']
                            
                            # Calculate PnL with leverage and spread
                            price_diff = (exit_price - pos['entry_price']) * pos['side']
                            # Apply leverage to the position size for PnL calculation
                            leveraged_size = pos['size'] * leverage
                            
                            # Get spread from config (convert pips to price units)
                            spread_pips = self.config.get('broker_spread', 2.0)
                            spread_cost = spread_pips * 0.0001 * leveraged_size  # Convert pips to price units
                            
                            # Calculate PnL: price difference minus spread cost
                            pnl = (price_diff * leveraged_size) - spread_cost
                            
                            trade = {
                                'symbol': self.config['symbol'],
                                'side': pos['side'],
                                'size': pos['size'],
                                'entry_price': pos['entry_price'],
                                'exit_price': exit_price,
                                'pnl': pnl,
                                'entry_time': pos['entry_time'],
                                'exit_time': timestamp,
                                'strategy': self.config['strategy']
                            }
                            trades.append(trade)
                            
                            # Create Trade object for portfolio
                            from forexsmartbot.core.interfaces import Trade
                            trade_obj = Trade(
                                symbol=self.config['symbol'],
                                side=pos['side'],
                                quantity=pos['size'],
                                entry_price=pos['entry_price'],
                                exit_price=exit_price,
                                pnl=pnl,
                                strategy=self.config['strategy'],
                                entry_time=pos['entry_time'],
                                exit_time=timestamp
                            )
                            portfolio.add_trade(trade_obj)
                            
                            # Update portfolio balance with the trade PnL
                            current_balance = portfolio.get_total_balance()
                            new_balance = current_balance + pnl
                            portfolio.balance_history.append(new_balance)
                            portfolio.equity_history.append(new_balance)
                            portfolio.timestamps.append(timestamp)
                            
                            self.log_updated.emit(f"{'SELL' if pos['side'] > 0 else 'BUY'} signal at {exit_price:.4f}, PnL: ${pnl:.2f}")
                            del positions[self.config['symbol']]
                        
                        # Open new position
                        entry_price = row['Close']
                        positions[self.config['symbol']] = {
                            'side': signal,
                            'size': position_size,
                            'entry_price': entry_price,
                            'entry_time': timestamp
                        }
                        self.log_updated.emit(f"{'BUY' if signal > 0 else 'SELL'} signal at {entry_price:.4f}")
                        last_signal_time = i
            
            # Close any remaining positions
            for symbol, pos in positions.items():
                exit_price = df['Close'].iloc[-1]
                
                # Calculate PnL with leverage
                leverage_str = self.config.get('leverage', '1:10 (Moderate)')
                try:
                    leverage = float(leverage_str.split(':')[1].split(' ')[0])
                except:
                    leverage = 10.0
                
                price_diff = (exit_price - pos['entry_price']) * pos['side']
                # Apply leverage to the position size for PnL calculation
                leveraged_size = pos['size'] * leverage
                
                # Get spread from config (convert pips to price units)
                spread_pips = self.config.get('broker_spread', 2.0)
                spread_cost = spread_pips * 0.0001 * leveraged_size  # Convert pips to price units
                
                # Calculate PnL: price difference minus spread cost
                pnl = (price_diff * leveraged_size) - spread_cost
                
                trade = {
                    'symbol': symbol,
                    'side': pos['side'],
                    'size': pos['size'],
                    'entry_price': pos['entry_price'],
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'entry_time': pos['entry_time'],
                    'exit_time': df.index[-1],
                    'strategy': self.config['strategy']
                }
                trades.append(trade)
                
                # Create Trade object for portfolio
                from forexsmartbot.core.interfaces import Trade
                trade_obj = Trade(
                    symbol=symbol,
                    side=pos['side'],
                    quantity=pos['size'],
                    entry_price=pos['entry_price'],
                    exit_price=exit_price,
                    pnl=pnl,
                    strategy=self.config['strategy'],
                    entry_time=pos['entry_time'],
                    exit_time=df.index[-1]
                )
                portfolio.add_trade(trade_obj)
                
                # Update portfolio balance with the trade PnL
                current_balance = portfolio.get_total_balance()
                new_balance = current_balance + pnl
                portfolio.balance_history.append(new_balance)
                portfolio.equity_history.append(new_balance)
                portfolio.timestamps.append(df.index[-1])
            
            self.progress_updated.emit(90)
            
            # Calculate results
            self.log_updated.emit("Calculating results...")
            metrics = portfolio.calculate_metrics()
            
            results = {
                'trades': trades,
                'metrics': metrics,
                'data_points': len(df),
                'strategy': self.config['strategy'],
                'symbol': self.config['symbol'],
                'start_date': self.config['start_date'],
                'end_date': self.config['end_date']
            }
            
            self.progress_updated.emit(100)
            self.log_updated.emit("Backtest completed successfully!")
            self.backtest_completed.emit(results)
            
        except Exception as e:
            self.log_updated.emit(f"Backtest error: {str(e)}")
            
    def create_sample_data(self):
        """Create sample data for backtesting."""
        # Create data based on the requested interval
        interval = self.config.get('interval', '1h')
        if interval == '1h':
            freq = '1H'
        elif interval == '4h':
            freq = '4H'
        elif interval == '1d':
            freq = '1D'
        else:
            freq = '1H'
            
        dates = pd.date_range(start=self.config['start_date'], end=self.config['end_date'], freq=freq)
        np.random.seed(42)
        
        # Set base price based on symbol
        if 'EUR' in self.config['symbol']:
            base_price = 1.1800
        elif 'GBP' in self.config['symbol']:
            base_price = 1.2500
        elif 'JPY' in self.config['symbol']:
            base_price = 150.0
        elif 'AUD' in self.config['symbol']:
            base_price = 0.7500
        elif 'CAD' in self.config['symbol']:
            base_price = 1.3500
        elif 'CHF' in self.config['symbol']:
            base_price = 0.9200
        elif 'NZD' in self.config['symbol']:
            base_price = 0.7000
        else:
            base_price = 1.0000
        
        # Create realistic price movements
        price_changes = np.random.randn(len(dates)) * 0.0005  # Smaller changes for more realistic data
        prices = base_price + np.cumsum(price_changes)
        
        # Ensure prices stay within reasonable bounds
        prices = np.clip(prices, base_price * 0.5, base_price * 2.0)
        
        return pd.DataFrame({
            'Open': prices,
            'High': prices + np.abs(np.random.randn(len(dates))) * 0.0002,
            'Low': prices - np.abs(np.random.randn(len(dates))) * 0.0002,
            'Close': prices + np.random.randn(len(dates)) * 0.0001,
            'Volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)


class BacktestDialog(QDialog):
    """Dialog for configuring and running backtests."""
    
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.setWindowTitle(self.tr("backtest_configuration", "Backtest Configuration"))
        self.setModal(True)
        self.resize(600, 700)
        
        self.worker = None
        self.results = None
        
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
        
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Configuration section
        config_group = QGroupBox(self.tr("backtest_configuration", "Backtest Configuration"))
        config_layout = QFormLayout(config_group)
        
        # Strategy selection - Load all strategies dynamically from module
        self.strategy_combo = QComboBox()
        
        # Get all available strategies from the strategies module
        from forexsmartbot.strategies import STRATEGIES, RISK_LEVELS
        
        # Organize strategies by risk level
        low_risk_strategies = RISK_LEVELS.get('Low_Risk', [])
        medium_risk_strategies = RISK_LEVELS.get('Medium_Risk', [])
        high_risk_strategies = RISK_LEVELS.get('High_Risk', [])
        
        # Get all strategies and categorize them
        all_strategies = list(STRATEGIES.keys())
        
        # Add ML strategies to appropriate risk levels
        ml_strategies = ['LSTM_Strategy', 'SVM_Strategy', 'Ensemble_ML_Strategy', 
                        'Transformer_Strategy', 'RL_Strategy', 'Multi_Timeframe']
        for ml_strategy in ml_strategies:
            if ml_strategy in all_strategies and ml_strategy not in high_risk_strategies:
                high_risk_strategies.append(ml_strategy)
        
        # Add strategies with risk level indicators
        for strategy in low_risk_strategies:
            if strategy in all_strategies:
                self.strategy_combo.addItem(f"🟢 {strategy} ({self.tr('low_risk', 'Low Risk')})")
        for strategy in medium_risk_strategies:
            if strategy in all_strategies:
                self.strategy_combo.addItem(f"🟡 {strategy} ({self.tr('medium_risk', 'Medium Risk')})")
        for strategy in high_risk_strategies:
            if strategy in all_strategies:
                self.strategy_combo.addItem(f"🔴 {strategy} ({self.tr('high_risk', 'High Risk')})")
        
        # Add any remaining strategies that weren't categorized
        for strategy in all_strategies:
            if strategy not in low_risk_strategies + medium_risk_strategies + high_risk_strategies:
                self.strategy_combo.addItem(f"⚪ {strategy}")
            
        config_layout.addRow(f"{self.tr('strategy', 'Strategy')}:", self.strategy_combo)
        
        # Symbol selection
        self.symbol_combo = QComboBox()
        # Major pairs (highest liquidity, best for trading)
        major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD']
        # Minor pairs (good liquidity, active trading)
        minor_pairs = ['EURGBP', 'EURJPY', 'GBPJPY', 'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'CADCHF', 'CADJPY', 'CHFJPY', 'EURAUD', 'EURCAD', 'EURCHF', 'EURNZD', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPNZD', 'NZDCAD', 'NZDCHF', 'NZDJPY']
        # Exotic pairs (higher volatility, more opportunities)
        exotic_pairs = ['USDTRY', 'USDZAR', 'USDMXN', 'USDPLN', 'USDCZK', 'USDHUF', 'USDSEK', 'USDNOK', 'USDDKK', 'USDRUB', 'USDCNH', 'USDSGD', 'USDHKD', 'USDTWD', 'USDKRW', 'USDINR', 'USDBRL', 'USDARS', 'USDCLP', 'USDCOP']
        
        # Combine all pairs in order of trading quality
        all_pairs = major_pairs + minor_pairs + exotic_pairs
        self.symbol_combo.addItems(all_pairs)
        config_layout.addRow(f"{self.tr('symbols', 'Symbol')}:", self.symbol_combo)
        
        # Date range - Default to 5 years of data
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addYears(-5))
        self.start_date_edit.setCalendarPopup(True)
        config_layout.addRow(f"{self.tr('start_date', 'Start Date')}:", self.start_date_edit)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        config_layout.addRow(f"{self.tr('end_date', 'End Date')}:", self.end_date_edit)
        
        # Interval
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(['1h', '4h', '1d'])
        self.interval_combo.setCurrentText('1h')
        config_layout.addRow(f"{self.tr('interval', 'Interval')}:", self.interval_combo)
        
        # Risk parameters
        self.initial_balance_spin = QDoubleSpinBox()
        self.initial_balance_spin.setRange(1000, 1000000)
        self.initial_balance_spin.setValue(10000)
        self.initial_balance_spin.setSuffix(" $")
        config_layout.addRow(f"{self.tr('initial_balance', 'Initial Balance')}:", self.initial_balance_spin)
        
        self.risk_pct_spin = QDoubleSpinBox()
        self.risk_pct_spin.setRange(0.01, 10.0)
        self.risk_pct_spin.setValue(1.0)
        self.risk_pct_spin.setSuffix(" %")
        config_layout.addRow(f"{self.tr('risk_per_trade', 'Risk per Trade')}:", self.risk_pct_spin)
        
        self.max_risk_pct_spin = QDoubleSpinBox()
        self.max_risk_pct_spin.setRange(0.01, 20.0)
        self.max_risk_pct_spin.setValue(5.0)
        self.max_risk_pct_spin.setSuffix(" %")
        config_layout.addRow(f"{self.tr('max_risk', 'Max Risk')}:", self.max_risk_pct_spin)
        
        # Leverage selection
        self.leverage_combo = QComboBox()
        leverage_options = [
            f"1:1 ({self.tr('no_leverage', 'No Leverage')})",
            f"1:5 ({self.tr('conservative', 'Conservative')})",
            f"1:10 ({self.tr('moderate', 'Moderate')})", 
            f"1:20 ({self.tr('aggressive', 'Aggressive')})",
            f"1:50 ({self.tr('high_risk', 'High Risk')})",
            f"1:100 ({self.tr('very_high_risk', 'Very High Risk')})",
            f"1:200 ({self.tr('maximum_risk', 'Maximum Risk')})",
            f"1:300 ({self.tr('extreme_risk', 'Extreme Risk')})",
            f"1:500 ({self.tr('ultra_high_risk', 'Ultra High Risk')})",
            f"1:1000 ({self.tr('maximum_leverage', 'Maximum Leverage')})",
            f"1:2000 ({self.tr('extreme_leverage', 'Extreme Leverage')})"
        ]
        self.leverage_combo.addItems(leverage_options)
        self.leverage_combo.setCurrentText(f"1:10 ({self.tr('moderate', 'Moderate')})")
        config_layout.addRow(f"{self.tr('leverage', 'Leverage')}:", self.leverage_combo)
        
        # Broker spread configuration
        self.broker_spread_spin = QDoubleSpinBox()
        self.broker_spread_spin.setRange(0.0, 50.0)
        self.broker_spread_spin.setDecimals(1)
        self.broker_spread_spin.setSingleStep(0.1)
        self.broker_spread_spin.setValue(2.0)
        self.broker_spread_spin.setSuffix(" pips")
        config_layout.addRow(f"{self.tr('broker_spread', 'Broker Spread')}:", self.broker_spread_spin)
        
        layout.addWidget(config_group)
        
        # Progress section
        progress_group = QGroupBox(self.tr("backtest_progress", "Backtest Progress"))
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        progress_layout.addWidget(self.log_text)
        
        layout.addWidget(progress_group)
        
        # Results section
        results_group = QGroupBox(self.tr("backtest_results", "Backtest Results"))
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setVisible(False)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.run_button = QPushButton(self.tr("run_backtest", "Run Backtest"))
        self.run_button.clicked.connect(self.run_backtest)
        button_layout.addWidget(self.run_button)
        
        self.export_button = QPushButton(self.tr("export_results", "Export Results"))
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        self.close_button = QPushButton(self.tr("close", "Close"))
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def run_backtest(self):
        """Run the backtest."""
        try:
            # Get configuration
            config = {
                'strategy': self.strategy_combo.currentText(),
                'symbol': self.symbol_combo.currentText(),
                'start_date': self.start_date_edit.date().toString('yyyy-MM-dd'),
                'end_date': self.end_date_edit.date().toString('yyyy-MM-dd'),
                'interval': self.interval_combo.currentText(),
                'initial_balance': self.initial_balance_spin.value(),
                'risk_pct': self.risk_pct_spin.value() / 100,
                'max_risk_pct': self.max_risk_pct_spin.value() / 100,
                'leverage': self.leverage_combo.currentText(),
                'broker_spread': self.broker_spread_spin.value(),
                'daily_risk_cap': 0.05,
                'max_drawdown_pct': 0.25
            }
            
            # Clear previous results
            self.results = None
            self.results_text.clear()
            self.results_text.setVisible(False)
            self.log_text.clear()  # Clear progress log
            self.export_button.setEnabled(False)
            
            # Start worker
            self.worker = BacktestWorker(config)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.log_updated.connect(self.update_log)
            self.worker.backtest_completed.connect(self.on_backtest_completed)
            self.worker.start()
            
            # Update UI
            self.run_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start backtest: {str(e)}")
            
    def update_progress(self, value):
        """Update progress bar."""
        self.progress_bar.setValue(value)
        
    def update_log(self, message):
        """Update log text."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def on_backtest_completed(self, results):
        """Handle backtest completion."""
        self.results = results
        self.run_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        
        # Display results
        self.display_results(results)
        
    def display_results(self, results):
        """Display backtest results."""
        try:
            metrics = results['metrics']
            trades = results['trades']
            
            results_text = f"""
BACKTEST RESULTS
================

Strategy: {results['strategy']}
Symbol: {results['symbol']}
Period: {results['start_date']} to {results['end_date']}
Data Points: {results['data_points']}

PERFORMANCE METRICS
===================
Total Balance: ${metrics.total_balance:.2f}
Total Equity: ${metrics.total_equity:.2f}
Unrealized PnL: ${metrics.unrealized_pnl:.2f}
Realized PnL: ${metrics.realized_pnl:.2f}
Daily PnL: ${metrics.daily_pnl:.2f}
Max Drawdown: {metrics.max_drawdown:.2f}%
Current Drawdown: {metrics.current_drawdown:.2f}%

TRADE STATISTICS
================
Total Trades: {metrics.total_trades}
Winning Trades: {metrics.winning_trades}
Losing Trades: {metrics.losing_trades}
Win Rate: {metrics.win_rate:.1%}
Profit Factor: {metrics.profit_factor:.2f}
Average Win: ${metrics.avg_win:.2f}
Average Loss: ${metrics.avg_loss:.2f}
Largest Win: ${metrics.largest_win:.2f}
Largest Loss: ${metrics.largest_loss:.2f}

RECENT TRADES
=============
"""
            
            # Add recent trades
            if trades:
                for trade in trades[-10:]:  # Show last 10 trades
                    results_text += f"{trade['exit_time'].strftime('%Y-%m-%d %H:%M')} | "
                    results_text += f"{trade['symbol']} | "
                    results_text += f"{'BUY' if trade['side'] > 0 else 'SELL'} | "
                    results_text += f"${trade['pnl']:.2f}\n"
            else:
                results_text += "No trades executed during this backtest period.\n"
            
            self.results_text.setPlainText(results_text)
            self.results_text.setVisible(True)
            
        except Exception as e:
            self.results_text.setPlainText(f"Error displaying results: {str(e)}")
            self.results_text.setVisible(True)
            
    def export_results(self):
        """Export backtest results."""
        if not self.results:
            return
            
        try:
            # Save results to JSON file
            filename = f"backtest_{self.results['strategy']}_{self.results['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            export_data = {
                'config': {
                    'strategy': self.results['strategy'],
                    'symbol': self.results['symbol'],
                    'start_date': self.results['start_date'],
                    'end_date': self.results['end_date']
                },
                'metrics': {
                    'total_balance': self.results['metrics'].total_balance,
                    'total_equity': self.results['metrics'].total_equity,
                    'realized_pnl': self.results['metrics'].realized_pnl,
                    'max_drawdown': self.results['metrics'].max_drawdown,
                    'win_rate': self.results['metrics'].win_rate,
                    'profit_factor': self.results['metrics'].profit_factor,
                    'total_trades': self.results['metrics'].total_trades
                },
                'trades': [
                    {
                        'symbol': trade['symbol'],
                        'side': trade['side'],
                        'size': trade['size'],
                        'entry_price': trade['entry_price'],
                        'exit_price': trade['exit_price'],
                        'pnl': trade['pnl'],
                        'entry_time': trade['entry_time'].isoformat(),
                        'exit_time': trade['exit_time'].isoformat(),
                        'strategy': trade['strategy']
                    }
                    for trade in self.results['trades']
                ]
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            QMessageBox.information(self, "Export Complete", f"Results exported to {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export results: {str(e)}")
