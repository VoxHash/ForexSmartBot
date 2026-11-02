"""Offscreen smoke tests for the modern VoxHash GUI shell."""

from __future__ import annotations

import os
import sys

import pytest

# Must be set before QApplication is created
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt6.QtWidgets")

from PyQt6.QtWidgets import QApplication

from forexsmartbot.ui.shell import COLORS, NavRail, SessionBar, build_app_stylesheet
from forexsmartbot.ui.theme import ThemeManager


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_shell_colors_are_unique_branding():
    """VoxHash palette must not use Spotify brand green as identity."""
    assert COLORS.accent.lower() != "#1db954"
    assert COLORS.profit.lower() != "#1db954"
    assert COLORS.accent.startswith("#")
    assert COLORS.bg.startswith("#")


def test_stylesheet_builds(qapp):
    css = build_app_stylesheet()
    assert "ShellNavRail" in css
    assert "ShellSessionBar" in css
    assert COLORS.accent in css
    assert "#1DB954" not in css and "#1db954" not in css


def test_theme_manager_applies_dark_qss(qapp):
    tm = ThemeManager()
    mode = tm.apply_theme(qapp, force="dark")
    assert mode == "dark"
    assert "ShellNavRail" in (qapp.styleSheet() or "")


def test_nav_rail_and_session_bar(qapp):
    items = [("trading", "Trading"), ("analytics", "Analytics"), ("charts", "Charts")]
    rail = NavRail(items)
    assert rail.current_index == 0
    seen = []
    rail.navigated.connect(seen.append)
    rail._buttons[2].click()
    assert seen == [2]
    assert rail.current_index == 2

    bar = SessionBar()
    bar.update_metrics(
        broker="PAPER",
        connection="Connected",
        trading="Running",
        balance="$10,000.00",
        equity="$10,050.00",
        pnl="$50.00",
        drawdown="0.0%",
        connected=True,
        pnl_positive=True,
        hint="Live",
    )
    assert bar.broker_value.text() == "PAPER"
    assert bar.connection_value.text() == "Connected"
    assert bar.equity_value.text() == "$10,050.00"


def test_enhanced_main_window_launches(qapp):
    """E2E: main window constructs, nav switches tabs, paper broker path exists."""
    from forexsmartbot.ui.enhanced_main_window import EnhancedMainWindow

    window = EnhancedMainWindow()
    try:
        assert window.features_tabs.count() == 7
        assert hasattr(window, "nav_rail")
        assert hasattr(window, "session_bar")
        assert window.features_tabs.tabBar().isHidden()

        window.navigate_to(1)
        assert window.features_tabs.currentIndex() == 1
        assert "Analytics" in window.stage_title.text()

        window.navigate_to(2)
        assert window.features_tabs.currentIndex() == 2

        # Paper path still initialized
        assert window.broker is not None
        assert window.trading_status_widget.broker_status.text()

        # Menu entry points still wired
        assert callable(window.run_backtest)
        assert callable(window.show_settings)
    finally:
        window.close()
        window.deleteLater()


def test_enhanced_main_window_resizes_freely(qapp):
    """Window must accept small and large sizes without crashing or a large floor."""
    from forexsmartbot.ui.enhanced_main_window import EnhancedMainWindow

    window = EnhancedMainWindow()
    try:
        assert window.minimumWidth() <= 800
        assert window.minimumHeight() <= 500
        assert window.maximumWidth() >= 100000
        assert window.maximumHeight() >= 100000
        # Layout must not advertise a desktop-blocking minimum
        assert window.minimumSizeHint().width() <= 800
        assert window.minimumSizeHint().height() <= 500

        for width, height in ((720, 480), (800, 500), (1280, 720), (1920, 1080)):
            window.resize(width, height)
            qapp.processEvents()
            assert window.width() == width
            assert window.height() == height
    finally:
        window.close()
        window.deleteLater()


def test_legacy_main_window_resizes_freely(qapp):
    """Legacy MainWindow also keeps a small usable minimum and accepts resize."""
    from forexsmartbot.ui.main_window import MainWindow

    window = MainWindow()
    try:
        assert window.minimumWidth() <= 800
        assert window.minimumHeight() <= 500
        window.resize(800, 500)
        qapp.processEvents()
        assert window.width() == 800
        assert window.height() == 500
        window.resize(1600, 900)
        qapp.processEvents()
        assert window.width() == 1600
    finally:
        window.close()
        window.deleteLater()
