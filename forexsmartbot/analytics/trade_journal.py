"""
Automated Trade Journaling Module
Captures screenshots, notes, and trade details automatically.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                            QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
from ..core.interfaces import Trade


class TradeJournalWidget(QWidget):
    """Widget for trade journaling."""
    
    def __init__(self, journal_dir: str = "journals", parent=None):
        super().__init__(parent)
        self.journal_dir = Path(journal_dir)
        self.journal_dir.mkdir(exist_ok=True)
        self.current_trade = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Trade Journal")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Journal entries table
        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(4)
        self.entries_table.setHorizontalHeaderLabels([
            'Date', 'Symbol', 'PnL', 'Notes'
        ])
        self.entries_table.setColumnWidth(0, 150)
        self.entries_table.setColumnWidth(1, 100)
        self.entries_table.setColumnWidth(2, 100)
        self.entries_table.setColumnWidth(3, 300)
        layout.addWidget(self.entries_table)
        
        # Notes editor
        notes_label = QLabel("Notes:")
        layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(150)
        layout.addWidget(self.notes_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Entry")
        self.save_button.clicked.connect(self.save_entry)
        button_layout.addWidget(self.save_button)
        
        self.screenshot_button = QPushButton("Capture Screenshot")
        self.screenshot_button.clicked.connect(self.capture_screenshot)
        button_layout.addWidget(self.screenshot_button)
        
        self.load_button = QPushButton("Load Journal")
        self.load_button.clicked.connect(self.load_journal)
        button_layout.addWidget(self.load_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
    def add_trade(self, trade: Trade):
        """Add a trade to the journal."""
        self.current_trade = trade
        self.notes_edit.clear()
        
    def save_entry(self):
        """Save journal entry."""
        if not self.current_trade:
            QMessageBox.warning(self, "No Trade", "No trade selected to journal.")
            return
            
        notes = self.notes_edit.toPlainText()
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'trade': {
                'symbol': self.current_trade.symbol,
                'side': self.current_trade.side,
                'entry_price': self.current_trade.entry_price,
                'exit_price': self.current_trade.exit_price,
                'quantity': self.current_trade.quantity,
                'pnl': self.current_trade.pnl,
                'entry_time': self.current_trade.entry_time.isoformat() if self.current_trade.entry_time else None,
                'exit_time': self.current_trade.exit_time.isoformat() if self.current_trade.exit_time else None
            },
            'notes': notes,
            'screenshots': []
        }
        
        # Save to file
        filename = f"trade_{self.current_trade.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.journal_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(entry, f, indent=2)
            
        # Update table
        self._add_entry_to_table(entry)
        
        QMessageBox.information(self, "Saved", f"Journal entry saved to {filepath}")
        
    def capture_screenshot(self):
        """Capture screenshot of current chart/window."""
        # In production, this would capture the actual chart
        QMessageBox.information(self, "Screenshot", "Screenshot captured (simulated)")
        
    def load_journal(self):
        """Load journal entries."""
        # Load all journal files
        journal_files = list(self.journal_dir.glob("trade_*.json"))
        
        self.entries_table.setRowCount(len(journal_files))
        
        for i, filepath in enumerate(sorted(journal_files, reverse=True)):
            try:
                with open(filepath, 'r') as f:
                    entry = json.load(f)
                    
                trade = entry.get('trade', {})
                
                # Date
                timestamp = entry.get('timestamp', 'N/A')
                self.entries_table.setItem(i, 0, QTableWidgetItem(timestamp[:10]))
                
                # Symbol
                symbol = trade.get('symbol', 'N/A')
                self.entries_table.setItem(i, 1, QTableWidgetItem(symbol))
                
                # PnL
                pnl = trade.get('pnl', 0.0)
                pnl_item = QTableWidgetItem(f"${pnl:.2f}")
                if pnl > 0:
                    pnl_item.setForeground(Qt.GlobalColor.green)
                elif pnl < 0:
                    pnl_item.setForeground(Qt.GlobalColor.red)
                self.entries_table.setItem(i, 2, pnl_item)
                
                # Notes preview
                notes = entry.get('notes', '')[:50]
                self.entries_table.setItem(i, 3, QTableWidgetItem(notes))
                
            except Exception as e:
                print(f"Error loading journal entry {filepath}: {e}")
                
    def _add_entry_to_table(self, entry: Dict):
        """Add entry to table."""
        row = self.entries_table.rowCount()
        self.entries_table.insertRow(row)
        
        trade = entry.get('trade', {})
        
        # Date
        timestamp = entry.get('timestamp', 'N/A')
        self.entries_table.setItem(row, 0, QTableWidgetItem(timestamp[:10]))
        
        # Symbol
        symbol = trade.get('symbol', 'N/A')
        self.entries_table.setItem(row, 1, QTableWidgetItem(symbol))
        
        # PnL
        pnl = trade.get('pnl', 0.0)
        pnl_item = QTableWidgetItem(f"${pnl:.2f}")
        if pnl > 0:
            pnl_item.setForeground(Qt.GlobalColor.green)
        elif pnl < 0:
            pnl_item.setForeground(Qt.GlobalColor.red)
        self.entries_table.setItem(row, 2, pnl_item)
        
        # Notes preview
        notes = entry.get('notes', '')[:50]
        self.entries_table.setItem(row, 3, QTableWidgetItem(notes))


class TradeJournalManager:
    """Manager for automated trade journaling."""
    
    def __init__(self, journal_dir: str = "journals"):
        self.journal_dir = Path(journal_dir)
        self.journal_dir.mkdir(exist_ok=True)
        self.auto_journal = True
        
    def journal_trade(self, trade: Trade, notes: Optional[str] = None,
                     screenshot_path: Optional[str] = None):
        """
        Automatically journal a trade.
        
        Args:
            trade: Trade to journal
            notes: Optional notes
            screenshot_path: Optional path to screenshot
        """
        if not self.auto_journal:
            return
            
        entry = {
            'timestamp': datetime.now().isoformat(),
            'trade': {
                'symbol': trade.symbol,
                'side': trade.side,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'pnl': trade.pnl,
                'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                'strategy': trade.strategy if hasattr(trade, 'strategy') else None
            },
            'notes': notes or '',
            'screenshots': [screenshot_path] if screenshot_path else []
        }
        
        # Save to file
        filename = f"trade_{trade.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.journal_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(entry, f, indent=2)
            
        return filepath

