"""
Analytics Dialog
Provides UI for various analytics tools.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt
from typing import Optional


class AnalyticsDialog(QDialog):
    """Dialog for analytics tools."""
    
    def __init__(self, analytics_type: str, parent=None, language_manager=None, **kwargs):
        super().__init__(parent)
        self.analytics_type = analytics_type
        self.language_manager = language_manager
        self.kwargs = kwargs
        self.setWindowTitle(f"Analytics: {analytics_type.replace('_', ' ').title()}")
        self.setModal(False)  # Allow multiple windows
        self.resize(900, 700)
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        if self.analytics_type == 'portfolio':
            self.setup_portfolio_analytics(layout)
        elif self.analytics_type == 'risk':
            self.setup_risk_analytics(layout)
        elif self.analytics_type == 'performance':
            self.setup_performance_attribution(layout)
        elif self.analytics_type == 'charts':
            self.setup_charts(layout)
        elif self.analytics_type == 'market_depth':
            self.setup_market_depth(layout)
        elif self.analytics_type == 'correlation':
            self.setup_correlation(layout)
        elif self.analytics_type == 'economic_calendar':
            self.setup_economic_calendar(layout)
        elif self.analytics_type == 'trade_journal':
            self.setup_trade_journal(layout)
        else:
            layout.addWidget(QLabel(f"Analytics: {self.analytics_type}"))
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def setup_portfolio_analytics(self, layout):
        """Setup portfolio analytics UI."""
        from ..analytics.portfolio_analytics import PortfolioAnalytics
        
        title = QLabel("Portfolio Analytics")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        self.analytics = PortfolioAnalytics()
        portfolio = self.kwargs.get('portfolio')
        
        # Metrics table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.metrics_table)
        
        # Update metrics
        self.update_portfolio_metrics(portfolio)
    
    def update_portfolio_metrics(self, portfolio=None):
        """Update portfolio metrics table."""
        try:
            metrics = self.analytics.calculate_metrics(portfolio)
            
            if not metrics:
                self.metrics_table.setRowCount(1)
                self.metrics_table.setItem(0, 0, QTableWidgetItem("No data"))
                self.metrics_table.setItem(0, 1, QTableWidgetItem("No trades available"))
                return
            
            self.metrics_table.setRowCount(len(metrics))
            
            for i, (key, value) in enumerate(metrics.items()):
                self.metrics_table.setItem(i, 0, QTableWidgetItem(str(key).replace('_', ' ').title()))
                if isinstance(value, float):
                    if abs(value) > 1000:
                        self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{value:.2f}"))
                    elif abs(value) > 1:
                        self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{value:.4f}"))
                    else:
                        self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{value:.6f}"))
                else:
                    self.metrics_table.setItem(i, 1, QTableWidgetItem(str(value)))
        except Exception as e:
            self.metrics_table.setRowCount(1)
            self.metrics_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.metrics_table.setItem(0, 1, QTableWidgetItem(str(e)))
    
    def setup_risk_analytics(self, layout):
        """Setup risk analytics UI."""
        from ..analytics.risk_analytics import RiskAnalytics
        
        title = QLabel("Risk Analytics")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        self.risk_analytics = RiskAnalytics()
        portfolio = self.kwargs.get('portfolio')
        
        # Risk metrics table
        self.risk_table = QTableWidget()
        self.risk_table.setColumnCount(2)
        self.risk_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.risk_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.risk_table)
        
        # Update risk metrics
        self.update_risk_metrics(portfolio)
    
    def update_risk_metrics(self, portfolio=None):
        """Update risk metrics table."""
        try:
            # Calculate VaR
            var_result = self.risk_analytics.calculate_var(confidence_level=0.95)
            
            # Calculate CVaR
            cvar_result = self.risk_analytics.calculate_cvar(confidence_level=0.95)
            
            # Combine metrics
            metrics = {
                'VaR (95%)': var_result.get('var', 0.0),
                'CVaR (95%)': cvar_result.get('cvar', 0.0),
                'Max Drawdown': var_result.get('max_drawdown', 0.0),
                'Volatility': var_result.get('volatility', 0.0)
            }
            
            self.risk_table.setRowCount(len(metrics))
            
            for i, (key, value) in enumerate(metrics.items()):
                self.risk_table.setItem(i, 0, QTableWidgetItem(key))
                if isinstance(value, float):
                    self.risk_table.setItem(i, 1, QTableWidgetItem(f"{value:.4f}"))
                else:
                    self.risk_table.setItem(i, 1, QTableWidgetItem(str(value)))
        except Exception as e:
            self.risk_table.setRowCount(1)
            self.risk_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.risk_table.setItem(0, 1, QTableWidgetItem(str(e)))
    
    def setup_performance_attribution(self, layout):
        """Setup performance attribution UI."""
        from ..analytics.performance_attribution import PerformanceAttribution
        
        title = QLabel("Performance Attribution")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        self.attribution = PerformanceAttribution()
        portfolio = self.kwargs.get('portfolio')
        
        # Attribution table
        self.attribution_table = QTableWidget()
        self.attribution_table.setColumnCount(5)
        self.attribution_table.setHorizontalHeaderLabels(["Strategy", "Trades", "Total PnL", "Win Rate", "Volume"])
        self.attribution_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.attribution_table)
        
        # Update attribution
        self.update_performance_attribution(portfolio)
    
    def update_performance_attribution(self, portfolio=None):
        """Update performance attribution table."""
        try:
            # Get attribution by strategy
            attribution = self.attribution.analyze_by_strategy()
            
            if not attribution:
                self.attribution_table.setRowCount(1)
                self.attribution_table.setItem(0, 0, QTableWidgetItem("No data"))
                self.attribution_table.setItem(0, 1, QTableWidgetItem("No trades available"))
                return
            
            self.attribution_table.setRowCount(len(attribution))
            
            for i, (strategy, data) in enumerate(attribution.items()):
                total_trades = len(data.get('trades', []))
                total_pnl = data.get('total_pnl', 0.0)
                winning = data.get('winning_trades', 0)
                win_rate = (winning / total_trades * 100) if total_trades > 0 else 0.0
                volume = data.get('total_volume', 0.0)
                
                self.attribution_table.setItem(i, 0, QTableWidgetItem(strategy))
                self.attribution_table.setItem(i, 1, QTableWidgetItem(str(total_trades)))
                self.attribution_table.setItem(i, 2, QTableWidgetItem(f"{total_pnl:.2f}"))
                self.attribution_table.setItem(i, 3, QTableWidgetItem(f"{win_rate:.1f}%"))
                self.attribution_table.setItem(i, 4, QTableWidgetItem(f"{volume:.2f}"))
        except Exception as e:
            self.attribution_table.setRowCount(1)
            self.attribution_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.attribution_table.setItem(0, 1, QTableWidgetItem(str(e)))
    
    def setup_charts(self, layout):
        """Setup charts UI."""
        try:
            from ..ui.enhanced_charts import EnhancedChartWidget
            chart = EnhancedChartWidget(parent=self)
            layout.addWidget(chart)
        except ImportError:
            layout.addWidget(QLabel("Enhanced charts not available"))
    
    def setup_market_depth(self, layout):
        """Setup market depth UI."""
        try:
            from ..analytics.market_depth import MarketDepthWidget
            depth = MarketDepthWidget(parent=self)
            layout.addWidget(depth)
        except ImportError:
            layout.addWidget(QLabel("Market depth not available"))
    
    def setup_correlation(self, layout):
        """Setup correlation matrix UI."""
        try:
            from ..analytics.correlation_matrix import CorrelationMatrixWidget
            matrix = CorrelationMatrixWidget(parent=self)
            layout.addWidget(matrix)
        except ImportError:
            layout.addWidget(QLabel("Correlation matrix not available"))
    
    def setup_economic_calendar(self, layout):
        """Setup economic calendar UI."""
        try:
            from ..analytics.economic_calendar import EconomicCalendarWidget
            calendar = EconomicCalendarWidget(parent=self)
            layout.addWidget(calendar)
        except ImportError:
            layout.addWidget(QLabel("Economic calendar not available"))
    
    def setup_trade_journal(self, layout):
        """Setup trade journal UI."""
        try:
            from ..analytics.trade_journal import TradeJournalWidget
            journal = TradeJournalWidget(parent=self)
            layout.addWidget(journal)
        except ImportError:
            layout.addWidget(QLabel("Trade journal not available"))

