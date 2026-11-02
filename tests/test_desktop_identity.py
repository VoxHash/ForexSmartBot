"""Process / window-manager identity must stay unique vs sibling VoxHash apps."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt6.QtWidgets")

from forexsmartbot.desktop_identity import (
    APP_NAME,
    DESKTOP_FILE_ID,
    ORGANIZATION_DOMAIN,
    ORGANIZATION_NAME,
    STARTUP_WM_CLASS,
    apply_desktop_identity,
    configure_qt_identity,
)


@pytest.fixture(scope="module")
def qapp_identity():
    from PyQt6.QtWidgets import QApplication

    if QApplication.instance() is None:
        configure_qt_identity()
        app = QApplication([])
    else:
        app = QApplication.instance()
        apply_desktop_identity(app)
    return app


def test_constants_are_unique_and_stable():
    assert ORGANIZATION_NAME == "VoxHash"
    assert ORGANIZATION_DOMAIN == "forexsmartbot.voxhash.dev"
    assert APP_NAME == "ForexSmartBot"
    assert DESKTOP_FILE_ID == "forexsmartbot"
    assert STARTUP_WM_CLASS == DESKTOP_FILE_ID

    sibling_names = {
        "YTSDownloader",
        "DB Storage Manager",
        "Telegram Multi-Account Message Sender",
        "HandForge",
        "python3",
        "python",
    }
    assert APP_NAME not in sibling_names

    sibling_desktop_ids = {
        "ytsdownloader",
        "db-storage-manager",
        "telegram-multi-account-sender",
        "dev.voxhash.telegram-multi-account-sender",
        "dev.voxhash.HandForge",
        "python3",
        "python",
    }
    assert DESKTOP_FILE_ID not in sibling_desktop_ids


def test_qt_identity_fields(qapp_identity):
    app = qapp_identity
    assert app.organizationName() == ORGANIZATION_NAME
    assert app.organizationDomain() == ORGANIZATION_DOMAIN
    assert app.applicationName() == APP_NAME
    assert app.applicationDisplayName() == APP_NAME
    assert app.desktopFileName() == DESKTOP_FILE_ID


def test_desktop_file_startup_wm_class_matches():
    root = Path(__file__).resolve().parents[1]
    desktop = root / "packaging" / "forexsmartbot.desktop"
    text = desktop.read_text(encoding="utf-8")
    assert f"StartupWMClass={STARTUP_WM_CLASS}" in text
    assert f"Name={APP_NAME}" in text
    assert "StartupWMClass=python" not in text
    assert "StartupWMClass=ForexSmartBot" not in text


def test_install_desktop_script_targets_unique_id():
    root = Path(__file__).resolve().parents[1]
    script = (root / "packaging" / "install-desktop.sh").read_text(encoding="utf-8")
    assert "forexsmartbot.desktop" in script
    assert 'DESKTOP_OUT="$APP_DIR/forexsmartbot.desktop"' in script
