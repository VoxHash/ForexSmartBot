#!/bin/bash
# macOS build script for ForexSmartBot
# Creates .dmg package

echo "ForexSmartBot v3.0.0 - macOS Builder"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root."
    exit 1
fi

if [ ! -d "forexsmartbot" ]; then
    echo "❌ Error: forexsmartbot directory not found. Please run this script from the project root."
    exit 1
fi

# Install build dependencies
echo "Installing build dependencies..."
pip3 install py2app

# Create setup.py for macOS
echo "Creating setup.py for macOS..."
cat > setup_macos.py << 'EOF'
from setuptools import setup
import os

APP = ['app.py']
DATA_FILES = [
    ('forexsmartbot/languages', ['forexsmartbot/languages/' + f for f in os.listdir('forexsmartbot/languages') if f.endswith('.json')]),
    ('assets', ['assets/' + f for f in os.listdir('assets') if os.path.isfile(os.path.join('assets', f))]),
]

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'assets/icons/forexsmartbot_256.icns',
    'plist': {
        'CFBundleName': 'ForexSmartBot',
        'CFBundleDisplayName': 'ForexSmartBot',
        'CFBundleIdentifier': 'com.voxhash.forexsmartbot',
        'CFBundleVersion': '3.0.0',
        'CFBundleShortVersionString': '3.0.0',
    },
    'packages': ['PyQt6', 'matplotlib', 'numpy', 'pandas', 'yfinance', 'requests'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
EOF

# Build the macOS app
echo "Building macOS application..."
python3 setup_macos.py py2app

# Create DMG
echo "Creating DMG package..."
if command -v hdiutil &> /dev/null; then
    hdiutil create -volname "ForexSmartBot" -srcfolder "dist/ForexSmartBot.app" -ov -format UDZO "dist/ForexSmartBot.dmg"
    echo "✅ macOS package built successfully!"
    echo "📁 Output: dist/ForexSmartBot.dmg"
else
    echo "⚠️  hdiutil not found. DMG creation skipped."
    echo "📁 App bundle: dist/ForexSmartBot.app"
fi
