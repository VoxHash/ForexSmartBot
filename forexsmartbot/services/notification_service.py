"""Notification service for system alerts and messaging."""

import os
import platform
import subprocess
import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal


class NotificationService(QObject):
    """Service for handling notifications and alerts."""
    
    # Signals
    notification_sent = pyqtSignal(str, str)  # type, message
    
    def __init__(self, settings_manager=None):
        super().__init__()
        self.settings_manager = settings_manager
        self.telegram_config = self._load_telegram_config()
        self.discord_config = self._load_discord_config()
        
    def _load_telegram_config(self) -> Dict[str, Any]:
        """Load Telegram configuration from settings."""
        if not self.settings_manager:
            return {}
            
        return {
            'bot_token': self.settings_manager.get('telegram_bot_token', ''),
            'channel_id': self.settings_manager.get('telegram_channel_id', ''),
            'enabled': self.settings_manager.get('telegram_notifications', False)
        }
    
    def _load_discord_config(self) -> Dict[str, Any]:
        """Load Discord configuration from settings."""
        if not self.settings_manager:
            return {}
            
        return {
            'webhook_url': self.settings_manager.get('discord_webhook_url', ''),
            'enabled': self.settings_manager.get('discord_notifications', False)
        }
    
    def show_position_alert(self, position_type: str, symbol: str, side: str, 
                           entry_price: float, exit_price: float = None, 
                           pnl: float = None, stop_loss: float = None, 
                           take_profit: float = None):
        """Show system alert for position open/close."""
        try:
            # Temporarily disable notifications to prevent crashes
            # TODO: Re-enable after fixing win10toast issues
            return
            
            if position_type == "open":
                title = f"Position Opened - {symbol}"
                message = f"Symbol: {symbol}\nType: {side}\nEntry Price: {entry_price:.4f}"
                if stop_loss:
                    message += f"\nStop Loss: {stop_loss:.4f}"
                if take_profit:
                    message += f"\nTake Profit: {take_profit:.4f}"
            else:
                title = f"Position Closed - {symbol}"
                message = f"Symbol: {symbol}\nType: {side}\nEntry Price: {entry_price:.4f}\nExit Price: {exit_price:.4f}\nPnL: {pnl:+.2f}"
            
            # Show system toast notification
            self._show_system_notification(title, message)
            
            # Send to messaging platforms
            self._send_telegram_message(position_type, symbol, side, entry_price, 
                                      exit_price, pnl, stop_loss, take_profit)
            self._send_discord_message(position_type, symbol, side, entry_price, 
                                     exit_price, pnl, stop_loss, take_profit)
            
            self.notification_sent.emit(position_type, message)
            
        except Exception as e:
            print(f"Error showing position alert: {str(e)}")
    
    def _show_system_notification(self, title: str, message: str):
        """Show system notification based on OS."""
        try:
            system = platform.system().lower()
            
            if system == "windows":
                # Windows toast notification
                self._show_windows_notification(title, message)
            elif system == "darwin":  # macOS
                # macOS notification
                self._show_macos_notification(title, message)
            elif system == "linux":
                # Linux notification
                self._show_linux_notification(title, message)
                
        except Exception as e:
            print(f"Error showing system notification: {str(e)}")
    
    def _show_windows_notification(self, title: str, message: str):
        """Show Windows toast notification."""
        try:
            # Use Windows 10/11 toast notifications
            import win10toast
            toaster = win10toast.ToastNotifier()
            
            # Check if icon exists and use absolute path
            icon_path = os.path.join(os.getcwd(), "assets", "icons", "forexsmartbot_256.png")
            if not os.path.exists(icon_path):
                icon_path = None
                
            # Use try-except to handle any threading issues
            try:
                toaster.show_toast(
                    title, 
                    message, 
                    duration=5,  # Reduced duration
                    icon_path=icon_path,
                    threaded=False  # Keep threading disabled
                )
            except Exception as e:
                # If win10toast fails, try without icon
                toaster.show_toast(
                    title, 
                    message, 
                    duration=5,
                    icon_path=None,
                    threaded=False
                )
        except ImportError:
            # Fallback to Windows toast notification via PowerShell
            try:
                subprocess.run([
                    "powershell", "-Command",
                    f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null; $template = \'<toast><visual><binding template="ToastGeneric"><text>{title}</text><text>{message}</text></binding></visual></toast>\'; $xml = New-Object Windows.Data.Xml.Dom.XmlDocument; $xml.LoadXml($template); $toast = [Windows.UI.Notifications.ToastNotification]::new($xml); [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ForexSmartBot").Show($toast)'
                ], check=False)
            except Exception:
                # Final fallback to simple message box
                subprocess.run([
                    "powershell", "-Command",
                    f"Add-Type -AssemblyName System.Windows.Forms; "
                    f"[System.Windows.Forms.MessageBox]::Show('{message}', '{title}')"
                ], check=False)
        except Exception as e:
            print(f"Error showing Windows notification: {str(e)}")
    
    def _show_macos_notification(self, title: str, message: str):
        """Show macOS notification."""
        try:
            # Use osascript for native macOS notifications
            subprocess.run([
                "osascript", "-e",
                f'display notification "{message}" with title "{title}" subtitle "ForexSmartBot" sound name "Glass"'
            ], check=False)
        except Exception as e:
            print(f"Error showing macOS notification: {str(e)}")
    
    def _show_linux_notification(self, title: str, message: str):
        """Show Linux notification."""
        try:
            # Check if icon exists
            icon_path = "assets/icons/forexsmartbot_256.png"
            if not os.path.exists(icon_path):
                icon_path = None
                
            # Use notify-send for Linux desktop notifications
            cmd = ["notify-send", title, message, "-t", "10000", "-u", "normal"]
            if icon_path:
                cmd.extend(["-i", icon_path])
                
            subprocess.run(cmd, check=False)
        except Exception as e:
            print(f"Error showing Linux notification: {str(e)}")
    
    
    def _send_telegram_message(self, position_type: str, symbol: str, side: str, 
                              entry_price: float, exit_price: float = None, 
                              pnl: float = None, stop_loss: float = None, 
                              take_profit: float = None):
        """Send message to Telegram channel."""
        if not self.telegram_config.get('enabled') or not self.telegram_config.get('bot_token'):
            return
            
        try:
            bot_token = self.telegram_config['bot_token']
            channel_id = self.telegram_config['channel_id']
            
            if position_type == "open":
                text = f"🚀 *Position Opened*\n\n"
                text += f"Symbol: `{symbol}`\n"
                text += f"Type: `{side}`\n"
                text += f"Entry Price: `{entry_price:.4f}`\n"
                if stop_loss:
                    text += f"Stop Loss: `{stop_loss:.4f}`\n"
                if take_profit:
                    text += f"Take Profit: `{take_profit:.4f}`\n"
            else:
                text = f"📊 *Position Closed*\n\n"
                text += f"Symbol: `{symbol}`\n"
                text += f"Type: `{side}`\n"
                text += f"Entry Price: `{entry_price:.4f}`\n"
                text += f"Exit Price: `{exit_price:.4f}`\n"
                text += f"PnL: `{pnl:+.2f}`\n"
            
            text += f"\nTime: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': channel_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print("Telegram notification sent successfully")
            else:
                print(f"Failed to send Telegram notification: {response.text}")
                
        except Exception as e:
            print(f"Error sending Telegram message: {str(e)}")
    
    def _send_discord_message(self, position_type: str, symbol: str, side: str, 
                             entry_price: float, exit_price: float = None, 
                             pnl: float = None, stop_loss: float = None, 
                             take_profit: float = None):
        """Send message to Discord webhook."""
        if not self.discord_config.get('enabled') or not self.discord_config.get('webhook_url'):
            return
            
        try:
            webhook_url = self.discord_config['webhook_url']
            
            if position_type == "open":
                title = "🚀 Position Opened"
                color = 0x00ff00  # Green
                fields = [
                    {"name": "Symbol", "value": symbol, "inline": True},
                    {"name": "Type", "value": side, "inline": True},
                    {"name": "Entry Price", "value": f"{entry_price:.4f}", "inline": True}
                ]
                if stop_loss:
                    fields.append({"name": "Stop Loss", "value": f"{stop_loss:.4f}", "inline": True})
                if take_profit:
                    fields.append({"name": "Take Profit", "value": f"{take_profit:.4f}", "inline": True})
            else:
                title = "📊 Position Closed"
                color = 0xff0000 if pnl < 0 else 0x00ff00  # Red if loss, green if profit
                fields = [
                    {"name": "Symbol", "value": symbol, "inline": True},
                    {"name": "Type", "value": side, "inline": True},
                    {"name": "Entry Price", "value": f"{entry_price:.4f}", "inline": True},
                    {"name": "Exit Price", "value": f"{exit_price:.4f}", "inline": True},
                    {"name": "PnL", "value": f"{pnl:+.2f}", "inline": True}
                ]
            
            embed = {
                "title": title,
                "color": color,
                "fields": fields,
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "ForexSmartBot"
                }
            }
            
            data = {
                "embeds": [embed]
            }
            
            response = requests.post(webhook_url, json=data, timeout=10)
            if response.status_code == 204:
                print("Discord notification sent successfully")
            else:
                print(f"Failed to send Discord notification: {response.text}")
                
        except Exception as e:
            print(f"Error sending Discord message: {str(e)}")
    
    def update_config(self):
        """Update configuration from settings manager."""
        self.telegram_config = self._load_telegram_config()
        self.discord_config = self._load_discord_config()
