"""
Export Dialog for ForexSmartBot
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QComboBox, QPushButton, QTextEdit,
                             QGroupBox, QCheckBox, QFileDialog, QMessageBox,
                             QDateEdit, QSpinBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
import pandas as pd
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional


class ExportDialog(QDialog):
    """Dialog for exporting trading data."""
    
    def __init__(self, portfolio, parent=None):
        super().__init__(parent)
        self.portfolio = portfolio
        self.setWindowTitle("Export Trading Data")
        self.setModal(True)
        self.resize(500, 600)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QFormLayout(options_group)
        
        # Export type
        self.export_type_combo = QComboBox()
        self.export_type_combo.addItems(['Trades', 'Positions', 'Portfolio Metrics', 'All Data'])
        options_layout.addRow("Export Type:", self.export_type_combo)
        
        # File format
        self.format_combo = QComboBox()
        self.format_combo.addItems(['CSV', 'JSON', 'Excel'])
        options_layout.addRow("Format:", self.format_combo)
        
        # Date range
        self.date_range_checkbox = QCheckBox("Filter by date range")
        self.date_range_checkbox.toggled.connect(self.toggle_date_range)
        options_layout.addRow(self.date_range_checkbox)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setEnabled(False)
        options_layout.addRow("Start Date:", self.start_date_edit)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setEnabled(False)
        options_layout.addRow("End Date:", self.end_date_edit)
        
        # Symbol filter
        self.symbol_filter_checkbox = QCheckBox("Filter by symbol")
        self.symbol_filter_checkbox.toggled.connect(self.toggle_symbol_filter)
        options_layout.addRow(self.symbol_filter_checkbox)
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'])
        self.symbol_combo.setEnabled(False)
        options_layout.addRow("Symbol:", self.symbol_combo)
        
        # Include options
        self.include_metrics_checkbox = QCheckBox("Include performance metrics")
        self.include_metrics_checkbox.setChecked(True)
        options_layout.addRow(self.include_metrics_checkbox)
        
        self.include_positions_checkbox = QCheckBox("Include current positions")
        self.include_positions_checkbox.setChecked(True)
        options_layout.addRow(self.include_positions_checkbox)
        
        layout.addWidget(options_group)
        
        # Preview section
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        self.refresh_preview_button = QPushButton("Refresh Preview")
        self.refresh_preview_button.clicked.connect(self.refresh_preview)
        preview_layout.addWidget(self.refresh_preview_button)
        
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_data)
        button_layout.addWidget(self.export_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Initial preview
        self.refresh_preview()
        
    def toggle_date_range(self, checked):
        """Toggle date range filter."""
        self.start_date_edit.setEnabled(checked)
        self.end_date_edit.setEnabled(checked)
        
    def toggle_symbol_filter(self, checked):
        """Toggle symbol filter."""
        self.symbol_combo.setEnabled(checked)
        
    def refresh_preview(self):
        """Refresh data preview."""
        try:
            export_type = self.export_type_combo.currentText()
            
            if export_type == 'Trades':
                data = self.get_trades_data()
            elif export_type == 'Positions':
                data = self.get_positions_data()
            elif export_type == 'Portfolio Metrics':
                data = self.get_metrics_data()
            else:  # All Data
                data = self.get_all_data()
            
            # Convert to preview text
            if isinstance(data, list) and data:
                preview_text = f"Found {len(data)} records:\n\n"
                for i, item in enumerate(data[:5]):  # Show first 5 items
                    preview_text += f"{i+1}. {str(item)}\n"
                if len(data) > 5:
                    preview_text += f"... and {len(data) - 5} more records"
            elif isinstance(data, dict):
                preview_text = "Data summary:\n\n"
                for key, value in data.items():
                    preview_text += f"{key}: {value}\n"
            else:
                preview_text = "No data available"
                
            self.preview_text.setPlainText(preview_text)
            
        except Exception as e:
            self.preview_text.setPlainText(f"Error generating preview: {str(e)}")
            
    def get_trades_data(self):
        """Get trades data."""
        try:
            trades = self.portfolio.trades
            
            # Apply filters
            if self.date_range_checkbox.isChecked():
                start_date = self.start_date_edit.date().toPyDate()
                end_date = self.end_date_edit.date().toPyDate()
                trades = [t for t in trades if start_date <= t.entry_time.date() <= end_date]
            
            if self.symbol_filter_checkbox.isChecked():
                symbol = self.symbol_combo.currentText()
                trades = [t for t in trades if t.symbol == symbol]
            
            return [
                {
                    'symbol': trade.symbol,
                    'side': 'Long' if trade.side > 0 else 'Short',
                    'size': trade.size,
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'pnl': trade.pnl,
                    'entry_time': trade.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'exit_time': trade.exit_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'strategy': trade.strategy
                }
                for trade in trades
            ]
        except Exception as e:
            return []
            
    def get_positions_data(self):
        """Get positions data."""
        try:
            positions = list(self.portfolio.positions.values())
            
            if self.symbol_filter_checkbox.isChecked():
                symbol = self.symbol_combo.currentText()
                positions = [p for p in positions if p.symbol == symbol]
            
            return [
                {
                    'symbol': pos.symbol,
                    'side': 'Long' if pos.side > 0 else 'Short',
                    'size': pos.size,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'strategy': getattr(pos, 'strategy', 'Unknown')
                }
                for pos in positions
            ]
        except Exception as e:
            return []
            
    def get_metrics_data(self):
        """Get portfolio metrics data."""
        try:
            metrics = self.portfolio.calculate_metrics()
            return {
                'total_balance': metrics.total_balance,
                'total_equity': metrics.total_equity,
                'unrealized_pnl': metrics.unrealized_pnl,
                'realized_pnl': metrics.realized_pnl,
                'daily_pnl': metrics.daily_pnl,
                'max_drawdown': metrics.max_drawdown,
                'current_drawdown': metrics.current_drawdown,
                'win_rate': metrics.win_rate,
                'profit_factor': metrics.profit_factor,
                'total_trades': metrics.total_trades,
                'winning_trades': metrics.winning_trades,
                'losing_trades': metrics.losing_trades,
                'avg_win': metrics.avg_win,
                'avg_loss': metrics.avg_loss,
                'largest_win': metrics.largest_win,
                'largest_loss': metrics.largest_loss
            }
        except Exception as e:
            return {}
            
    def get_all_data(self):
        """Get all data."""
        return {
            'trades': self.get_trades_data(),
            'positions': self.get_positions_data(),
            'metrics': self.get_metrics_data(),
            'export_time': datetime.now().isoformat()
        }
        
    def export_data(self):
        """Export data to file."""
        try:
            # Get file path
            format_type = self.format_combo.currentText()
            if format_type == 'CSV':
                file_filter = "CSV Files (*.csv)"
                default_name = f"trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            elif format_type == 'JSON':
                file_filter = "JSON Files (*.json)"
                default_name = f"trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            else:  # Excel
                file_filter = "Excel Files (*.xlsx)"
                default_name = f"trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Trading Data", default_name, file_filter
            )
            
            if not file_path:
                return
                
            # Get data
            export_type = self.export_type_combo.currentText()
            
            if export_type == 'Trades':
                data = self.get_trades_data()
            elif export_type == 'Positions':
                data = self.get_positions_data()
            elif export_type == 'Portfolio Metrics':
                data = self.get_metrics_data()
            else:  # All Data
                data = self.get_all_data()
            
            # Export based on format
            if format_type == 'CSV':
                self.export_to_csv(file_path, data)
            elif format_type == 'JSON':
                self.export_to_json(file_path, data)
            else:  # Excel
                self.export_to_excel(file_path, data)
                
            QMessageBox.information(self, "Export Complete", f"Data exported to {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
            
    def export_to_csv(self, file_path, data):
        """Export data to CSV."""
        if isinstance(data, list) and data:
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
        elif isinstance(data, dict):
            # Convert dict to DataFrame
            df = pd.DataFrame([data])
            df.to_csv(file_path, index=False)
        else:
            raise ValueError("No data to export")
            
    def export_to_json(self, file_path, data):
        """Export data to JSON."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
            
    def export_to_excel(self, file_path, data):
        """Export data to Excel."""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            if isinstance(data, list) and data:
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name='Data', index=False)
            elif isinstance(data, dict):
                if 'trades' in data and 'positions' in data and 'metrics' in data:
                    # All data
                    if data['trades']:
                        pd.DataFrame(data['trades']).to_excel(writer, sheet_name='Trades', index=False)
                    if data['positions']:
                        pd.DataFrame(data['positions']).to_excel(writer, sheet_name='Positions', index=False)
                    if data['metrics']:
                        pd.DataFrame([data['metrics']]).to_excel(writer, sheet_name='Metrics', index=False)
                else:
                    # Single data type
                    df = pd.DataFrame([data])
                    df.to_excel(writer, sheet_name='Data', index=False)
            else:
                raise ValueError("No data to export")
