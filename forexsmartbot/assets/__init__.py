"""Bundled static assets (icons) and path resolution for install + repo runs."""

from __future__ import annotations

from pathlib import Path

_PKG_ICONS = Path(__file__).resolve().parent / "icons"
_REPO_ICONS = Path(__file__).resolve().parents[2] / "assets" / "icons"

DEFAULT_ICON = "forexsmartbot_256.png"
DEFAULT_ICO = "forexsmartbot_256.ico"


def resolve_app_icon(filename: str = DEFAULT_ICON) -> str:
    """Return absolute path to an app icon that exists, preferring packaged assets.

    Search order:
    1. ``forexsmartbot/assets/icons/`` (wheel / editable package data)
    2. Repo-root ``assets/icons/`` (source checkout)
    3. ``./assets/icons/`` relative to CWD (PyInstaller / launcher)
    """
    candidates = [
        _PKG_ICONS / filename,
        _REPO_ICONS / filename,
        Path.cwd() / "assets" / "icons" / filename,
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return str(candidates[0])
