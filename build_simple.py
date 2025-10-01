#!/usr/bin/env python3
"""
Simple build script for ForexSmartBot
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
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        print(f"Success: {cmd}")
        return True
    except Exception as e:
        print(f"Exception running command {cmd}: {e}")
        return False

def build_executable():
    """Build standalone executable using PyInstaller."""
    print("Building ForexSmartBot executable...")
    
    # Install PyInstaller if not already installed
    print("Installing PyInstaller...")
    if not run_command("pip install pyinstaller"):
        return False
    
    # Create the build command
    cmd = [
        "pyinstaller",
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
    
    # Convert list to string for subprocess
    cmd_str = " ".join(cmd)
    
    print(f"Running: {cmd_str}")
    if run_command(cmd_str):
        print("✅ Executable built successfully!")
        print("📁 Output: dist/ForexSmartBot.exe")
        return True
    else:
        print("❌ Failed to build executable")
        return False

def main():
    """Main build function."""
    print("ForexSmartBot v3.0.0 - Simple Builder")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ Error: app.py not found. Please run this script from the project root.")
        return False
    
    if not os.path.exists("forexsmartbot"):
        print("❌ Error: forexsmartbot directory not found. Please run this script from the project root.")
        return False
    
    # Build the executable
    if build_executable():
        print("\n🎉 Build completed successfully!")
        print("📁 The executable is located in: dist/ForexSmartBot.exe")
        print("🚀 You can now distribute this executable!")
        return True
    else:
        print("\n❌ Build failed!")
        return False

if __name__ == "__main__":
    main()