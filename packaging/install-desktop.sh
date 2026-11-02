#!/usr/bin/env bash
# Install ForexSmartBot into the user FreeDesktop application menu
# (~/.local/share/applications) so it appears under Office / All Applications
# and can be pinned to Favorites in Glytherra Studio / KDE / GNOME launchers.
#
# Usage (from repo root or packaging/):
#   ./packaging/install-desktop.sh
#
# Prerequisites: project .venv with forexsmartbot console script installed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$SCRIPT_DIR/forexsmartbot.desktop"
ICON_SRC="$PROJECT_ROOT/assets/icons"
EXEC="$PROJECT_ROOT/.venv/bin/forexsmartbot"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
HICOLOR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
DESKTOP_OUT="$APP_DIR/forexsmartbot.desktop"

if [[ ! -x "$EXEC" ]]; then
  echo "error: missing executable: $EXEC" >&2
  echo "Create the venv and install the package first, e.g.:" >&2
  echo "  python -m venv .venv && .venv/bin/pip install -e ." >&2
  exit 1
fi

if [[ ! -f "$ICON_SRC/forexsmartbot_256.png" ]]; then
  echo "error: missing icon: $ICON_SRC/forexsmartbot_256.png" >&2
  exit 1
fi

mkdir -p "$APP_DIR"
for size in 32 64 128 256 512; do
  src="$ICON_SRC/forexsmartbot_${size}.png"
  dest="$HICOLOR/${size}x${size}/apps"
  if [[ -f "$src" ]]; then
    mkdir -p "$dest"
    cp -f "$src" "$dest/forexsmartbot.png"
  fi
done
if [[ -f "$ICON_SRC/forexsmartbot.svg" ]]; then
  mkdir -p "$HICOLOR/scalable/apps"
  cp -f "$ICON_SRC/forexsmartbot.svg" "$HICOLOR/scalable/apps/forexsmartbot.svg"
fi

sed -e "s|@EXEC@|$EXEC|g" -e "s|@PATH@|$PROJECT_ROOT|g" "$TEMPLATE" > "$DESKTOP_OUT"
chmod 755 "$DESKTOP_OUT"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" || true
fi
if command -v xdg-desktop-menu >/dev/null 2>&1; then
  xdg-desktop-menu forceupdate || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -t "$HICOLOR" 2>/dev/null || true
fi
if command -v xdg-icon-resource >/dev/null 2>&1; then
  xdg-icon-resource install --novendor --size 256 "$ICON_SRC/forexsmartbot_256.png" forexsmartbot || true
fi
if command -v desktop-file-validate >/dev/null 2>&1; then
  desktop-file-validate "$DESKTOP_OUT"
fi

echo "Installed: $DESKTOP_OUT"
echo "Icon theme name: forexsmartbot (hicolor)"
echo
echo "Add to Favorites (Glytherra Studio / KDE-like launcher):"
echo "  1. Open the app menu → All Applications or Office"
echo "  2. Find ForexSmartBot (or search for it)"
echo "  3. Right-click → Add to Favorites  (or drag the icon onto Favorites)"
