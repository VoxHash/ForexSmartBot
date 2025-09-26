#!/bin/bash
# Linux build script for ForexSmartBot
# Creates .deb, .rpm, and .tar.gz packages

echo "ForexSmartBot v3.0.0 - Linux Builder"
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
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-dev build-essential
sudo apt-get install -y stdeb rpm python3-stdeb

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install stdeb

# Create setup.py for Linux packages
echo "Creating setup.py..."
cat > setup.py << 'EOF'
from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="forexsmartbot",
    version="3.0.0",
    author="VoxHash",
    author_email="support@voxhash.com",
    description="Advanced Forex Trading Bot with Machine Learning Strategies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/VoxHash/ForexSmartBot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "forexsmartbot=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "forexsmartbot": [
            "languages/*.json",
            "assets/icons/*.png",
            "assets/icons/*.ico",
        ],
    },
    data_files=[
        ("share/applications", ["forexsmartbot.desktop"]),
        ("share/pixmaps", ["assets/icons/forexsmartbot_256.png"]),
    ],
)
EOF

# Create desktop file
echo "Creating desktop file..."
cat > forexsmartbot.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=ForexSmartBot
Comment=Advanced Forex Trading Bot
Exec=forexsmartbot
Icon=forexsmartbot_256
Terminal=false
Categories=Office;Finance;
EOF

# Build packages
echo "Building packages..."

# Build .deb package
echo "Building .deb package..."
python3 setup.py --command-packages=stdeb.command bdist_deb

# Build .rpm package
echo "Building .rpm package..."
python3 setup.py bdist_rpm

# Build .tar.gz package
echo "Building .tar.gz package..."
python3 setup.py sdist

echo "✅ Linux packages built successfully!"
echo "📁 Output files:"
echo "   - .deb: dist/*.deb"
echo "   - .rpm: dist/*.rpm"
echo "   - .tar.gz: dist/*.tar.gz"

deactivate
