"""
Startup Manager for ForexSmartBot
Handles automatic startup on Windows, macOS, and Linux
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional


class StartupManager:
    """Manages application startup on different operating systems."""
    
    def __init__(self, app_name: str = "ForexSmartBot"):
        self.app_name = app_name
        self.system = platform.system()
        self.startup_path = self._get_startup_path()
        
    def _get_startup_path(self) -> Optional[Path]:
        """Get the startup directory path for the current OS."""
        if self.system == "Windows":
            # Windows: Startup folder in Start Menu
            startup_dir = Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
        elif self.system == "Darwin":  # macOS
            # macOS: LaunchAgents directory
            startup_dir = Path.home() / 'Library' / 'LaunchAgents'
        elif self.system == "Linux":
            # Linux: autostart directory
            startup_dir = Path.home() / '.config' / 'autostart'
        else:
            return None
            
        # Create directory if it doesn't exist
        startup_dir.mkdir(parents=True, exist_ok=True)
        return startup_dir
    
    def is_startup_enabled(self) -> bool:
        """Check if the application is set to start on system startup."""
        if not self.startup_path:
            return False
            
        if self.system == "Windows":
            shortcut_path = self.startup_path / f"{self.app_name}.lnk"
            return shortcut_path.exists()
        elif self.system == "Darwin":  # macOS
            plist_path = self.startup_path / f"com.voxhash.{self.app_name.lower()}.plist"
            return plist_path.exists()
        elif self.system == "Linux":
            desktop_path = self.startup_path / f"{self.app_name.lower()}.desktop"
            return desktop_path.exists()
        
        return False
    
    def enable_startup(self, app_path: str) -> bool:
        """Enable application startup on system boot."""
        if not self.startup_path:
            return False
            
        try:
            if self.system == "Windows":
                return self._enable_windows_startup(app_path)
            elif self.system == "Darwin":  # macOS
                return self._enable_macos_startup(app_path)
            elif self.system == "Linux":
                return self._enable_linux_startup(app_path)
        except Exception as e:
            print(f"Error enabling startup: {e}")
            return False
            
        return False
    
    def disable_startup(self) -> bool:
        """Disable application startup on system boot."""
        if not self.startup_path:
            return False
            
        try:
            if self.system == "Windows":
                shortcut_path = self.startup_path / f"{self.app_name}.lnk"
                if shortcut_path.exists():
                    shortcut_path.unlink()
                    return True
                else:
                    # Already disabled
                    return True
            elif self.system == "Darwin":  # macOS
                plist_path = self.startup_path / f"com.voxhash.{self.app_name.lower()}.plist"
                if plist_path.exists():
                    plist_path.unlink()
                    return True
                else:
                    # Already disabled
                    return True
            elif self.system == "Linux":
                desktop_path = self.startup_path / f"{self.app_name.lower()}.desktop"
                if desktop_path.exists():
                    desktop_path.unlink()
                    return True
                else:
                    # Already disabled
                    return True
        except Exception as e:
            print(f"Error disabling startup: {e}")
            return False
            
        return True  # Return True if no startup files exist (already disabled)
    
    def _enable_windows_startup(self, app_path: str) -> bool:
        """Enable startup on Windows using PowerShell to create shortcut."""
        try:
            shortcut_path = self.startup_path / f"{self.app_name}.lnk"
            
            # Use PowerShell to create shortcut
            ps_script = f'$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut("{shortcut_path}"); $Shortcut.TargetPath = "{app_path}"; $Shortcut.WorkingDirectory = "{os.path.dirname(app_path)}"; $Shortcut.Description = "ForexSmartBot - Automated Trading Platform"; $Shortcut.Save()'
            
            subprocess.run([
                "powershell", "-Command", ps_script
            ], check=True, capture_output=True)
            
            return True
        except Exception as e:
            print(f"Error creating Windows shortcut: {e}")
            return False
    
    def _enable_macos_startup(self, app_path: str) -> bool:
        """Enable startup on macOS using LaunchAgent plist."""
        try:
            plist_path = self.startup_path / f"com.voxhash.{self.app_name.lower()}.plist"
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.voxhash.{self.app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/{self.app_name.lower()}.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/{self.app_name.lower()}.err</string>
</dict>
</plist>"""
            
            with open(plist_path, 'w') as f:
                f.write(plist_content)
            
            # Load the LaunchAgent
            subprocess.run([
                "launchctl", "load", str(plist_path)
            ], check=True)
            
            return True
        except Exception as e:
            print(f"Error creating macOS LaunchAgent: {e}")
            return False
    
    def _enable_linux_startup(self, app_path: str) -> bool:
        """Enable startup on Linux using desktop entry."""
        try:
            desktop_path = self.startup_path / f"{self.app_name.lower()}.desktop"
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Comment=Automated Trading Platform
Exec={app_path}
Icon={self.app_name.lower()}
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
"""
            
            with open(desktop_path, 'w') as f:
                f.write(desktop_content)
            
            # Make executable
            os.chmod(desktop_path, 0o755)
            
            return True
        except Exception as e:
            print(f"Error creating Linux desktop entry: {e}")
            return False
    
    def get_system_info(self) -> dict:
        """Get system information for startup configuration."""
        return {
            "system": self.system,
            "startup_path": str(self.startup_path) if self.startup_path else None,
            "is_supported": self.startup_path is not None,
            "is_enabled": self.is_startup_enabled()
        }
