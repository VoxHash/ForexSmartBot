"""Linux / Qt desktop identity for process and window-manager isolation.

ForexSmartBot must not share ApplicationName, desktop file id, or WM_CLASS with
sibling VoxHash Qt apps. Without these, Wayland/KDE often sees the process as
generic ``python3`` and groups or closes windows together with other Python GUIs.

Call :func:`configure_qt_identity` **before** constructing ``QApplication``.
"""

from __future__ import annotations

# Freedesktop desktop entry basename (forexsmartbot.desktop) — Wayland app_id.
DESKTOP_FILE_ID = "forexsmartbot"
# Qt application name (display + QSettings app key).
APP_NAME = "ForexSmartBot"
ORGANIZATION_NAME = "VoxHash"
# Unique per-app domain so QStandardPaths / QSettings never collide with siblings.
ORGANIZATION_DOMAIN = "forexsmartbot.voxhash.dev"
# Must match packaging/forexsmartbot.desktop StartupWMClass and DESKTOP_FILE_ID.
STARTUP_WM_CLASS = DESKTOP_FILE_ID


def configure_qt_identity(version: str | None = None) -> None:
    """Set unique org/app/desktop ids on QCoreApplication / QGuiApplication.

    Must run before ``QApplication(...)`` so Wayland app_id and X11 WM_CLASS
    are not left as the interpreter name (``python3``).
    """
    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtGui import QGuiApplication

    from forexsmartbot import __version__

    QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
    QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setApplicationVersion(
        version if version is not None else __version__
    )
    QGuiApplication.setApplicationDisplayName(APP_NAME)
    # Matches packaging/install-desktop.sh → forexsmartbot.desktop (no .desktop suffix).
    QGuiApplication.setDesktopFileName(DESKTOP_FILE_ID)


def apply_desktop_identity(app, version: str | None = None) -> None:
    """Instance-level mirror of :func:`configure_qt_identity` (tests / late bind)."""
    from forexsmartbot import __version__

    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(version if version is not None else __version__)
    if hasattr(app, "setDesktopFileName"):
        app.setDesktopFileName(DESKTOP_FILE_ID)
