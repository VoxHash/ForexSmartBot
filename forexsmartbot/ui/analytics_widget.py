"""
Live Analytics Dashboard widget for main window integration.

Shows KPI cards plus portfolio/risk tables, refreshed on a timer from the
live Portfolio.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QGroupBox, QGridLayout, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from typing import Optional


_CARD_STYLE = """
QFrame#metricCard {{
    background-color: palette(base);
    border: 1px solid palette(mid);
    border-radius: 6px;
    padding: 8px;
}}
QLabel#cardValue {{
    font-size: 18px;
    font-weight: bold;
}}
QLabel#cardLabel {{
    font-size: 11px;
    color: palette(mid);
}}
"""

_TONE_COLORS = {
    "positive": "#2e7d32",
    "negative": "#c62828",
    "neutral": "",
}


class PortfolioAnalyticsWidget(QWidget):
    """Live analytics dashboard: KPI cards + portfolio/risk metric tables."""

    def __init__(self, portfolio, parent=None, refresh_ms: int = 5000):
        super().__init__(parent)
        self.portfolio = portfolio
        self.refresh_ms = refresh_ms
        self._card_value_labels = []
        self.setup_ui()
        self.setup_timer()
        self.update_metrics()

    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Live Analytics")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        self.updated_label = QLabel("Updated: —")
        self.updated_label.setStyleSheet("font-size: 11px; color: palette(mid);")
        header.addWidget(self.updated_label)
        layout.addLayout(header)

        self.cards_frame = QFrame()
        self.cards_frame.setObjectName("metricCards")
        cards_layout = QHBoxLayout(self.cards_frame)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(8)
        self._card_value_labels = []
        for _ in range(6):
            card, value_label = self._make_card("—", "—")
            cards_layout.addWidget(card)
            self._card_value_labels.append(value_label)
        layout.addWidget(self.cards_frame)

        tables = QHBoxLayout()
        tables.setSpacing(10)

        portfolio_group = QGroupBox("Portfolio")
        portfolio_layout = QVBoxLayout(portfolio_group)
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.setAlternatingRowColors(True)
        self.metrics_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.metrics_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.metrics_table.verticalHeader().setVisible(False)
        portfolio_layout.addWidget(self.metrics_table)
        tables.addWidget(portfolio_group)

        risk_group = QGroupBox("Risk")
        risk_layout = QVBoxLayout(risk_group)
        self.risk_table = QTableWidget()
        self.risk_table.setColumnCount(2)
        self.risk_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.risk_table.horizontalHeader().setStretchLastSection(True)
        self.risk_table.setAlternatingRowColors(True)
        self.risk_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.risk_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.risk_table.verticalHeader().setVisible(False)
        risk_layout.addWidget(self.risk_table)
        tables.addWidget(risk_group)

        layout.addLayout(tables)
        self.setStyleSheet(_CARD_STYLE)

    def _make_card(self, label: str, value: str):
        """Create a KPI card frame; returns (frame, value_label)."""
        frame = QFrame()
        frame.setObjectName("metricCard")
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid = QGridLayout(frame)
        grid.setContentsMargins(10, 8, 10, 8)
        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        name_label = QLabel(label)
        name_label.setObjectName("cardLabel")
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(value_label, 0, 0)
        grid.addWidget(name_label, 1, 0)
        frame._name_label = name_label  # noqa: SLF001 — local card wiring
        return frame, value_label

    def setup_timer(self):
        """Setup live refresh timer."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(self.refresh_ms)

    def set_portfolio(self, portfolio) -> None:
        """Replace the portfolio source and refresh immediately."""
        self.portfolio = portfolio
        self.update_metrics()

    def update_metrics(self):
        """Refresh KPI cards and portfolio/risk tables from live portfolio."""
        try:
            from ..analytics.live_metrics import build_live_metrics

            snapshot = build_live_metrics(self.portfolio)
            self.updated_label.setText(
                f"Updated: {snapshot.timestamp.strftime('%H:%M:%S')}"
            )

            for i, (label, value, tone) in enumerate(snapshot.card_metrics()):
                if i >= len(self._card_value_labels):
                    break
                value_label = self._card_value_labels[i]
                value_label.setText(value)
                color = _TONE_COLORS.get(tone, "")
                if color:
                    value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
                else:
                    value_label.setStyleSheet("font-size: 18px; font-weight: bold;")
                card = value_label.parent()
                if card is not None and hasattr(card, "_name_label"):
                    card._name_label.setText(label)

            portfolio_rows = {
                "Equity": f"${snapshot.equity:,.2f}",
                "Balance": f"${snapshot.balance:,.2f}",
                "Realized P&L": f"${snapshot.realized_pnl:,.2f}",
                "Unrealized P&L": f"${snapshot.unrealized_pnl:,.2f}",
                "Daily P&L": f"${snapshot.daily_pnl:,.2f}",
                "Open Positions": str(snapshot.open_positions),
                "Total Trades": str(snapshot.total_trades),
                "Win Rate": f"{snapshot.win_rate:.1f}%",
                "Profit Factor": f"{snapshot.profit_factor:.3f}",
                "Sharpe Ratio": f"{snapshot.sharpe_ratio:.4f}",
                "Sortino Ratio": f"{snapshot.sortino_ratio:.4f}",
                "Avg Win": f"${snapshot.average_win:,.2f}",
                "Avg Loss": f"${snapshot.average_loss:,.2f}",
            }
            self._fill_table(self.metrics_table, portfolio_rows)

            risk_rows = {
                "Max Drawdown": f"${snapshot.max_drawdown:,.2f}",
                "Max Drawdown %": f"{snapshot.max_drawdown_pct:.2f}%",
                "Current Drawdown %": f"{snapshot.current_drawdown:.2f}%",
                "VaR (95%)": f"{snapshot.var_95:.4f}",
                "CVaR (95%)": f"{snapshot.cvar_95:.4f}",
                "Volatility": f"{snapshot.volatility:.4f}",
            }
            self._fill_table(self.risk_table, risk_rows)
        except Exception as e:
            self.metrics_table.setRowCount(1)
            self.metrics_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.metrics_table.setItem(0, 1, QTableWidgetItem(str(e)))
            self.risk_table.setRowCount(0)

    @staticmethod
    def _fill_table(table: QTableWidget, rows: dict) -> None:
        table.setRowCount(len(rows))
        for i, (key, value) in enumerate(rows.items()):
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(value))
