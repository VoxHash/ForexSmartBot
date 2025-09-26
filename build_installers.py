#!/usr/bin/env python3
"""
Build script for creating ForexSmartBot installers
Supports Windows (.exe), Linux (.deb, .rpm, .tar.gz), and macOS (.dmg)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import platform

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running command {cmd}: {e}")
        return False

def build_windows_installer():
    """Build Windows .exe installer using PyInstaller."""
    print("Building Windows installer...")
    
    # Install PyInstaller if not already installed
    if not run_command("pip install pyinstaller"):
        return False
    
    # Create the PyInstaller spec file
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('forexsmartbot/languages', 'forexsmartbot/languages'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'matplotlib',
        'numpy',
        'pandas',
        'yfinance',
        'requests',
        'win10toast',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ForexSmartBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/forexsmartbot_256.ico'
)
"""
    
    with open('ForexSmartBot.spec', 'w') as f:
        f.write(spec_content)
    
    # Build the executable
    if run_command("pyinstaller ForexSmartBot.spec"):
        print("Windows installer built successfully!")
        return True
    return False

def build_linux_packages():
    """Build Linux packages (.deb, .rpm, .tar.gz)."""
    print("Building Linux packages...")
    
    # Create setup.py for Linux packages
    setup_content = """
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
    url="https://github.com/voxhash/forexsmartbot",
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
"""
    
    with open('setup.py', 'w') as f:
        f.write(setup_content)
    
    # Create desktop file
    desktop_content = """
[Desktop Entry]
Version=1.0
Type=Application
Name=ForexSmartBot
Comment=Advanced Forex Trading Bot
Exec=forexsmartbot
Icon=forexsmartbot_256
Terminal=false
Categories=Office;Finance;
"""
    
    with open('forexsmartbot.desktop', 'w') as f:
        f.write(desktop_content)
    
    # Build packages
    packages_built = []
    
    # Build .deb package
    if run_command("pip install stdeb"):
        if run_command("python setup.py --command-packages=stdeb.command bdist_deb"):
            packages_built.append("deb")
    
    # Build .rpm package
    if run_command("pip install rpm"):
        if run_command("python setup.py bdist_rpm"):
            packages_built.append("rpm")
    
    # Build .tar.gz package
    if run_command("python setup.py sdist"):
        packages_built.append("tar.gz")
    
    if packages_built:
        print(f"Linux packages built: {', '.join(packages_built)}")
        return True
    return False

def build_macos_package():
    """Build macOS .dmg package."""
    print("Building macOS package...")
    
    # Install required packages
    if not run_command("pip install py2app"):
        return False
    
    # Create setup.py for macOS
    setup_macos_content = """
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
"""
    
    with open('setup_macos.py', 'w') as f:
        f.write(setup_macos_content)
    
    # Build the macOS app
    if run_command("python setup_macos.py py2app"):
        print("macOS package built successfully!")
        return True
    return False

def main():
    """Main build function."""
    print("ForexSmartBot v3.0.0 - Installer Builder")
    print("=" * 50)
    
    current_os = platform.system().lower()
    
    if current_os == "windows":
        print("Building Windows installer...")
        if build_windows_installer():
            print("✅ Windows installer built successfully!")
        else:
            print("❌ Failed to build Windows installer")
    
    elif current_os == "linux":
        print("Building Linux packages...")
        if build_linux_packages():
            print("✅ Linux packages built successfully!")
        else:
            print("❌ Failed to build Linux packages")
    
    elif current_os == "darwin":
        print("Building macOS package...")
        if build_macos_package():
            print("✅ macOS package built successfully!")
        else:
            print("❌ Failed to build macOS package")
    
    else:
        print(f"Unsupported operating system: {current_os}")
        return False
    
    print("\nBuild process completed!")
    return True

if __name__ == "__main__":
    main()
