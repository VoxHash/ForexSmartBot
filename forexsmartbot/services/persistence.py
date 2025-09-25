"""Persistence services for settings, logging, and database."""

import json
import os
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from ..core.interfaces import Trade


class SettingsManager:
    """Manages application settings persistence."""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.forexsmartbot")
            
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.settings_file = self.config_dir / "settings.json"
        self._settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        default_settings = {
            "theme": "auto",
            "default_symbols": ["EURUSD", "USDJPY", "GBPUSD"],
            "broker_mode": "PAPER",
            "mt4_host": "127.0.0.1",
            "mt4_port": 5555,
            "risk_pct": 0.02,
            "trade_amount_min": 10.0,
            "trade_amount_max": 100.0,
            "max_drawdown_pct": 0.25,
            "daily_risk_cap": 0.05,
            "confirm_live_trades": True,
            "data_provider": "yfinance",
            "data_interval": "1h",
            "strategy": "SMA_Crossover",
            "strategy_params": {},
            "portfolio_mode": False,
            "selected_symbols": ["EURUSD"]
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle new settings
                    default_settings.update(loaded)
            except Exception:
                pass
                
        return default_settings
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value."""
        return self._settings.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """Set setting value."""
        self._settings[key] = value
        
    def save(self) -> bool:
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self._settings, f, indent=2)
            return True
        except Exception:
            return False
            
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self._settings = self._load_settings()
        self.save()


class DatabaseManager:
    """Manages SQLite database for trades and metrics."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            config_dir = Path(os.path.expanduser("~/.forexsmartbot"))
            config_dir.mkdir(exist_ok=True)
            db_path = config_dir / "trades.db"
            
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side INTEGER NOT NULL,
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    pnl REAL NOT NULL,
                    strategy TEXT NOT NULL,
                    notes TEXT
                )
            """)
            
            # Metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    equity_start REAL NOT NULL,
                    equity_end REAL NOT NULL,
                    drawdown REAL NOT NULL,
                    wins INTEGER NOT NULL,
                    losses INTEGER NOT NULL,
                    avg_win REAL NOT NULL,
                    avg_loss REAL NOT NULL,
                    total_trades INTEGER NOT NULL
                )
            """)
            
            conn.commit()
            
    def add_trade(self, trade: Trade) -> bool:
        """Add a completed trade to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trades (timestamp, symbol, side, quantity, entry_price, 
                                     exit_price, pnl, strategy, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.exit_time.isoformat(),
                    trade.symbol,
                    trade.side,
                    trade.quantity,
                    trade.entry_price,
                    trade.exit_price,
                    trade.pnl,
                    trade.strategy,
                    trade.notes
                ))
                conn.commit()
                return True
        except Exception:
            return False
            
    def get_trades(self, symbol: str = None, strategy: str = None, 
                  start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get trades from database with optional filters."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM trades WHERE 1=1"
                params = []
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                    
                if strategy:
                    query += " AND strategy = ?"
                    params.append(strategy)
                    
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                    
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                    
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception:
            return []
            
    def add_daily_metrics(self, date: str, equity_start: float, equity_end: float,
                         drawdown: float, wins: int, losses: int, 
                         avg_win: float, avg_loss: float, total_trades: int) -> bool:
        """Add daily metrics to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO metrics (date, equity_start, equity_end, drawdown,
                                       wins, losses, avg_win, avg_loss, total_trades)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (date, equity_start, equity_end, drawdown, wins, losses,
                     avg_win, avg_loss, total_trades))
                conn.commit()
                return True
        except Exception:
            return False
            
    def get_metrics(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get metrics from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM metrics WHERE 1=1"
                params = []
                
                if start_date:
                    query += " AND date >= ?"
                    params.append(start_date)
                    
                if end_date:
                    query += " AND date <= ?"
                    params.append(end_date)
                    
                query += " ORDER BY date DESC"
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception:
            return []


class LogManager:
    """Manages application logging."""
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.path.expanduser("~/.forexsmartbot/logs")
            
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        # Set up log rotation (keep last 30 days)
        self._cleanup_old_logs()
        
    def _cleanup_old_logs(self) -> None:
        """Remove log files older than 30 days."""
        try:
            cutoff_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)
            for log_file in self.log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
        except Exception:
            pass
            
    def get_logger(self, name: str) -> logging.Logger:
        """Get logger instance."""
        return logging.getLogger(name)
