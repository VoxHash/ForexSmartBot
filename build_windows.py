#!/usr/bin/env python3
"""
Windows build script for ForexSmartBot
Creates a standalone executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd):
    """Run a command and return the result."""
    try:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        print(f"Success!")
        return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    """Main build function."""
    print("ForexSmartBot v3.0.0 - Windows Builder")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ Error: app.py not found. Please run this script from the project root.")
        return False
    
    if not os.path.exists("forexsmartbot"):
        print("❌ Error: forexsmartbot directory not found. Please run this script from the project root.")
        return False
    
    # Install PyInstaller
    print("Installing PyInstaller...")
    if not run_command("pip install pyinstaller"):
        return False
    
    # Build the executable
    print("Building executable...")
    cmd = [
        "python", "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=ForexSmartBot",
        "--icon=assets/icons/forexsmartbot_256.ico",
        "--add-data=forexsmartbot/languages;forexsmartbot/languages",
        "--add-data=assets;assets",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=matplotlib",
        "--hidden-import=numpy",
        "--hidden-import=pandas",
        "--hidden-import=yfinance",
        "--hidden-import=requests",
        "--hidden-import=win10toast",
        "app.py"
    ]
    
    # Convert to string
    cmd_str = " ".join(cmd)
    
    if run_command(cmd_str):
        print("✅ Executable built successfully!")
        print("📁 Output: dist/ForexSmartBot.exe")
        return True
    else:
        print("❌ Build failed!")
        return False

if __name__ == "__main__":
    main()
