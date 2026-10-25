"""Modern desktop shell for ForexSmartBot (VoxHash).

Layout rhythm inspired by polished multi-pane desktop apps (persistent left
nav, central content stage, dense bottom session strip). Palette and branding
are VoxHash / trading-domain — not a clone of any third-party product.

Capability reverse-engineering methodology referenced from MIT-licensed
https://github.com/morluto/rea (pattern study only; not vendored as a dependency).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class ShellColors:
    """Unique VoxHash dark palette (avoid Spotify #1DB954 and purple-AI defaults)."""

    bg: str = "#0B0F14"
    surface: str = "#121821"
    elevated: str = "#1A2332"
    border: str = "#2A3648"
    text: str = "#E8EEF7"
    muted: str = "#8B9BB4"
    accent: str = "#3D9CF0"  # VoxHash signal blue
    accent_dim: str = "#2A6FAD"
    profit: str = "#26C281"  # trading green ≠ #1DB954
    loss: str = "#E25555"
    warn: str = "#E6A23C"
    nav_hover: str = "#1E2A3A"
    nav_active: str = "#243447"


COLORS = ShellColors()


def build_app_stylesheet(colors: ShellColors = COLORS) -> str:
    """Global QSS for the modern shell."""
    c = colors
    return f"""
    QMainWindow, QDialog {{
        background-color: {c.bg};
        color: {c.text};
    }}
    QWidget {{
        color: {c.text};
        font-size: 13px;
    }}
    QMenuBar {{
        background-color: {c.surface};
        color: {c.text};
        border-bottom: 1px solid {c.border};
        padding: 2px 6px;
    }}
    QMenuBar::item:selected {{
        background-color: {c.nav_hover};
        border-radius: 4px;
    }}
    QMenu {{
        background-color: {c.elevated};
        border: 1px solid {c.border};
        padding: 4px;
    }}
    QMenu::item:selected {{
        background-color: {c.nav_hover};
    }}
    QStatusBar {{
        background-color: {c.surface};
        color: {c.muted};
        border-top: 1px solid {c.border};
    }}
    QTabWidget::pane {{
        border: 1px solid {c.border};
        background: {c.surface};
        border-radius: 8px;
        top: -1px;
    }}
    QTabBar::tab {{
        background: {c.elevated};
        color: {c.muted};
        padding: 8px 14px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}
    QTabBar::tab:selected {{
        background: {c.surface};
        color: {c.text};
        border-bottom: 2px solid {c.accent};
    }}
    QGroupBox {{
        background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 8px;
        margin-top: 12px;
        padding: 12px 10px 10px 10px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {c.muted};
    }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{
        background-color: {c.elevated};
        border: 1px solid {c.border};
        border-radius: 6px;
        padding: 6px 8px;
        selection-background-color: {c.accent_dim};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QPushButton {{
        background-color: {c.elevated};
        border: 1px solid {c.border};
        border-radius: 6px;
        padding: 8px 14px;
        color: {c.text};
    }}
    QPushButton:hover {{
        background-color: {c.nav_hover};
        border-color: {c.accent_dim};
    }}
    QPushButton:pressed {{
        background-color: {c.nav_active};
    }}
    QPushButton:disabled {{
        color: {c.muted};
        background-color: {c.surface};
    }}
    QTableWidget, QListWidget, QTreeWidget {{
        background-color: {c.elevated};
        alternate-background-color: {c.surface};
        border: 1px solid {c.border};
        border-radius: 6px;
        gridline-color: {c.border};
    }}
    QHeaderView::section {{
        background-color: {c.surface};
        color: {c.muted};
        border: none;
        border-bottom: 1px solid {c.border};
        padding: 6px 8px;
        font-weight: 600;
    }}
    QScrollBar:vertical {{
        background: {c.surface};
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c.border};
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QToolTip {{
        background-color: {c.elevated};
        color: {c.text};
        border: 1px solid {c.border};
        padding: 4px 8px;
    }}
    QSplitter::handle {{
        background-color: {c.border};
        width: 1px;
    }}
    /* Shell-specific */
    QFrame#ShellNavRail {{
        background-color: {c.surface};
        border-right: 1px solid {c.border};
    }}
    QFrame#ShellSessionBar {{
        background-color: {c.elevated};
        border-top: 1px solid {c.border};
        min-height: 56px;
        max-height: 64px;
    }}
    QFrame#ShellContentStage {{
        background-color: {c.bg};
    }}
    QLabel#ShellBrand {{
        color: {c.text};
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.5px;
        padding: 12px 10px 8px 10px;
    }}
    QLabel#ShellBrandSub {{
        color: {c.muted};
        font-size: 11px;
        padding: 0 10px 12px 10px;
    }}
    QPushButton#ShellNavButton {{
        text-align: left;
        background-color: transparent;
        border: none;
        border-radius: 6px;
        padding: 10px 12px;
        color: {c.muted};
        font-weight: 500;
    }}
    QPushButton#ShellNavButton:hover {{
        background-color: {c.nav_hover};
        color: {c.text};
    }}
    QPushButton#ShellNavButton[active="true"] {{
        background-color: {c.nav_active};
        color: {c.text};
        border-left: 3px solid {c.accent};
    }}
    QLabel#SessionMetricLabel {{
        color: {c.muted};
        font-size: 11px;
    }}
    QLabel#SessionMetricValue {{
        color: {c.text};
        font-size: 13px;
        font-weight: 600;
    }}
    """


class NavRail(QFrame):
    """Persistent left navigation for primary destinations."""

    navigated = pyqtSignal(int)

    def __init__(
        self,
        items: Sequence[Tuple[str, str]],
        parent: Optional[QWidget] = None,
    ):
        """
        Args:
            items: sequence of (object_name_key, display_label)
        """
        super().__init__(parent)
        self.setObjectName("ShellNavRail")
        self.setFixedWidth(188)
        self._buttons: List[QPushButton] = []
        self._index = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        brand = QLabel("ForexSmartBot")
        brand.setObjectName("ShellBrand")
        layout.addWidget(brand)
        sub = QLabel("VoxHash · Trading Desk")
        sub.setObjectName("ShellBrandSub")
        layout.addWidget(sub)

        for i, (_key, label) in enumerate(items):
            btn = QPushButton(label)
            btn.setObjectName("ShellNavButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("active", "true" if i == 0 else "false")
            btn.clicked.connect(self._make_handler(i))
            layout.addWidget(btn)
            self._buttons.append(btn)

        layout.addStretch(1)

    def _make_handler(self, index: int) -> Callable[[], None]:
        def _go() -> None:
            self.set_active(index)
            self.navigated.emit(index)

        return _go

    def set_active(self, index: int) -> None:
        self._index = index
        for i, btn in enumerate(self._buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    @property
    def current_index(self) -> int:
        return self._index


class SessionBar(QFrame):
    """Bottom session strip — equity / P&L / connection (trading analogue of a player bar)."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ShellSessionBar")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root = QHBoxLayout(self)
        root.setContentsMargins(16, 8, 16, 8)
        root.setSpacing(20)

        self.broker_value = self._add_metric(root, "Broker", "PAPER")
        self.connection_value = self._add_metric(root, "Connection", "Disconnected")
        self.trading_value = self._add_metric(root, "Session", "Stopped")
        self.balance_value = self._add_metric(root, "Balance", "$0.00")
        self.equity_value = self._add_metric(root, "Equity", "$0.00")
        self.pnl_value = self._add_metric(root, "Unrealized P&L", "$0.00")
        self.drawdown_value = self._add_metric(root, "Drawdown", "0.0%")

        root.addStretch(1)

        self.hint = QLabel("Desk ready")
        self.hint.setStyleSheet(f"color: {COLORS.muted}; font-size: 11px;")
        root.addWidget(self.hint)

    def _add_metric(self, layout: QHBoxLayout, label: str, initial: str) -> QLabel:
        col = QVBoxLayout()
        col.setSpacing(0)
        lbl = QLabel(label)
        lbl.setObjectName("SessionMetricLabel")
        val = QLabel(initial)
        val.setObjectName("SessionMetricValue")
        col.addWidget(lbl)
        col.addWidget(val)
        wrap = QWidget()
        wrap.setLayout(col)
        layout.addWidget(wrap)
        return val

    def update_metrics(
        self,
        *,
        broker: Optional[str] = None,
        connection: Optional[str] = None,
        trading: Optional[str] = None,
        balance: Optional[str] = None,
        equity: Optional[str] = None,
        pnl: Optional[str] = None,
        drawdown: Optional[str] = None,
        hint: Optional[str] = None,
        connected: Optional[bool] = None,
        pnl_positive: Optional[bool] = None,
    ) -> None:
        if broker is not None:
            self.broker_value.setText(broker)
        if connection is not None:
            self.connection_value.setText(connection)
            color = COLORS.profit if connected else COLORS.loss
            if connected is None:
                color = COLORS.text
            self.connection_value.setStyleSheet(
                f"color: {color}; font-size: 13px; font-weight: 600;"
            )
        if trading is not None:
            self.trading_value.setText(trading)
        if balance is not None:
            self.balance_value.setText(balance)
        if equity is not None:
            self.equity_value.setText(equity)
        if pnl is not None:
            self.pnl_value.setText(pnl)
            if pnl_positive is True:
                self.pnl_value.setStyleSheet(
                    f"color: {COLORS.profit}; font-size: 13px; font-weight: 600;"
                )
            elif pnl_positive is False:
                self.pnl_value.setStyleSheet(
                    f"color: {COLORS.loss}; font-size: 13px; font-weight: 600;"
                )
            else:
                self.pnl_value.setStyleSheet(
                    f"color: {COLORS.text}; font-size: 13px; font-weight: 600;"
                )
        if drawdown is not None:
            self.drawdown_value.setText(drawdown)
        if hint is not None:
            self.hint.setText(hint)
