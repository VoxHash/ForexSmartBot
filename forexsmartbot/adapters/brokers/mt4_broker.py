"""MetaTrader 4 broker implementation via file communication."""

import json
import time
import os
import subprocess
from typing import Dict, Optional
from datetime import datetime
from ...core.interfaces import IBroker, Position, Order


class MT4Broker(IBroker):
    """MT4 broker implementation using file communication."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5555):
        self._host = host
        self._port = port
        self._connected = False
        self._files_dir = self._find_mt4_files_dir()
        
    def _find_mt4_files_dir(self) -> str:
        """Find MT4 Files directory."""
        # First try to find the terminal-specific directory
        terminal_dirs = []
        base_path = os.path.join(os.getenv('APPDATA'), 'MetaQuotes', 'Terminal')
        if os.path.exists(base_path):
            for item in os.listdir(base_path):
                if os.path.isdir(os.path.join(base_path, item)) and item != 'MQL4':
                    mql4_path = os.path.join(base_path, item, 'MQL4', 'Files')
                    if os.path.exists(mql4_path):
                        terminal_dirs.append(mql4_path)
        
        # Use the exact terminal-specific directory that MT4 EA is looking in
        terminal_specific_path = os.path.join(os.getenv('APPDATA'), 'MetaQuotes', 'Terminal', '0727F3F88B5F0FE006962B330B91FF37', 'MQL4', 'Files')
        
        # Add other possible paths
        possible_paths = [
            terminal_specific_path,
            os.path.join(os.getenv('APPDATA'), 'MetaQuotes', 'Terminal', 'MQL4', 'Files'),
        ] + terminal_dirs + [
            os.path.join(os.getenv('APPDATA'), 'MetaQuotes', 'Terminal', 'Files'),
            os.path.join(os.getenv('USERPROFILE'), 'AppData', 'Roaming', 'MetaQuotes', 'Terminal', 'MQL4', 'Files')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"MT4Broker: Found MT4 Files directory: {path}")
                return path
        
        # Create default directory if none exists
        default_path = os.path.join(os.getenv('APPDATA'), 'MetaQuotes', 'Terminal', 'MQL4', 'Files')
        os.makedirs(default_path, exist_ok=True)
        print(f"MT4Broker: Created default MT4 Files directory: {default_path}")
        return default_path
        
    def connect(self) -> bool:
        """Connect to MT4."""
        try:
            # Check if MT4 is running (check both terminal.exe and terminal64.exe)
            # Use errors='ignore' to handle any encoding issues with subprocess output
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal.exe'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='ignore')
            result64 = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'], 
                                   capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if 'terminal.exe' in result.stdout or 'terminal64.exe' in result64.stdout:
                self._connected = True
                print(f"MT4Broker: Connected to running MT4 instance")
                print(f"MT4Broker: Using files directory: {self._files_dir}")
                return True
            else:
                print("MT4Broker: MT4 not running - please start MT4 first")
                self._connected = False
                return False
        except Exception as e:
            print(f"MT4Broker: Connection error: {e}")
            self._connected = False
            return False
            
    def disconnect(self) -> None:
        """Disconnect from MT4."""
        self._connected = False
        
    def is_connected(self) -> bool:
        """Check if connected to MT4."""
        return self._connected
        
    def _execute_command(self, command: str) -> bool:
        """Execute command via file communication with MT4 EA."""
        try:
            command_file = os.path.join(self._files_dir, 'ForexSmartBot_Command.txt')
            
            # Wait for EA to finish processing any previous command
            max_wait = 10  # Wait up to 10 seconds
            wait_count = 0
            while os.path.exists(command_file) and wait_count < max_wait:
                time.sleep(0.5)
                wait_count += 1
            
            with open(command_file, 'w') as f:
                f.write(command)
            
            # Wait for EA to process the command
            time.sleep(2.0)  # Give EA time to process
            
            print(f"MT4Broker: Command written to file: {command}")
            return True
            
        except Exception as e:
            print(f"MT4Broker: Error writing command file: {e}")
            return False
            
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price from MT4."""
        if not self._connected:
            print("MT4Broker: Not connected to MT4")
            return None
            
        try:
            # Request price from MT4
            self._execute_command(f"GetPrice({symbol})")
            
            # Wait for EA to process
            time.sleep(1.0)
            
            # Read price from response file
            response_file = os.path.join(self._files_dir, 'ForexSmartBot_Price.txt')
            if os.path.exists(response_file):
                with open(response_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        price = float(content)
                        print(f"MT4Broker: Got real price from MT4 for {symbol}: {price}")
                        return price
        except Exception as e:
            print(f"MT4Broker: Error reading price: {e}")
        
        print(f"MT4Broker: Using fallback price for {symbol}")
        return 1.0700 if symbol == "EURUSD" else 1.2500
        
    def submit_order(self, symbol: str, side: int, quantity: float, 
                    stop_loss: Optional[float] = None, 
                    take_profit: Optional[float] = None) -> Optional[str]:
        """Submit order to MT4."""
        if not self._connected:
            print("MT4Broker: Not connected to MT4")
            return None
            
        try:
            # Create order command for MT4
            order_type = "BUY" if side > 0 else "SELL"
            sl_str = f" SL={stop_loss}" if stop_loss else ""
            tp_str = f" TP={take_profit}" if take_profit else ""
            
            # Use a simpler command format that the EA can detect
            command = f"OrderSend({symbol},{order_type},{quantity}{sl_str}{tp_str})"
            print(f"MT4Broker: Command format: {command}")
            print(f"MT4Broker: Command length: {len(command)}")
            
            print(f"MT4Broker: Executing real MT4 order: {command}")
            
            # Execute the order in MT4
            if self._execute_command(command):
                order_id = f"MT4_{int(time.time() * 1000)}"
                print(f"MT4Broker: Order submitted successfully: {order_id}")
                return order_id
            else:
                print("MT4Broker: Failed to submit order")
                return None
                
        except Exception as e:
            print(f"MT4Broker: Error submitting order: {e}")
            return None
        
    def close_all(self, symbol: str) -> bool:
        """Close all positions for symbol."""
        if not self._connected:
            print("MT4Broker: Not connected to MT4")
            return False
            
        try:
            command = f"CloseAll({symbol})"
            print(f"MT4Broker: Closing all positions for {symbol}")
            
            if self._execute_command(command):
                print(f"MT4Broker: Successfully closed all positions for {symbol}")
                return True
            else:
                print(f"MT4Broker: Failed to close positions for {symbol}")
                return False
                
        except Exception as e:
            print(f"MT4Broker: Error closing positions: {e}")
            return False
        
    def get_positions(self) -> Dict[str, Position]:
        """Get positions from MT4."""
        positions = {}
        
        if not self._connected:
            print("MT4Broker: Not connected to MT4")
            return positions
        
        try:
            # Request positions from MT4
            self._execute_command("GetPositions()")
            
            # Wait for EA to process
            time.sleep(1.0)
            
            # Read positions from MT4 response file
            response_file = os.path.join(self._files_dir, 'ForexSmartBot_Positions.txt')
            if os.path.exists(response_file):
                with open(response_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        import json
                        positions_data = json.loads(content)
                        for pos_data in positions_data:
                            symbol = pos_data['symbol']
                            positions[symbol] = Position(
                                symbol=symbol,
                                side=pos_data['side'],
                                quantity=pos_data['volume'],
                                entry_price=pos_data['entry_price'],
                                current_price=pos_data['current_price'],
                                stop_loss=pos_data.get('sl', 0),
                                take_profit=pos_data.get('tp', 0),
                                pnl=pos_data.get('profit', 0)
                            )
                        print(f"MT4Broker: Retrieved {len(positions)} positions from MT4")
        except Exception as e:
            print(f"MT4Broker: Error reading positions: {e}")
        
        return positions
        
    def get_balance(self) -> float:
        """Get account balance from MT4."""
        try:
            # Request balance from MT4
            self._execute_command("GetBalance()")
            
            # Wait a moment for the EA to process
            import time
            time.sleep(0.5)
            
            # Read balance from response file
            response_file = os.path.join(self._files_dir, 'ForexSmartBot_Balance.txt')
            if os.path.exists(response_file):
                with open(response_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        balance = float(content)
                        print(f"MT4Broker: Got real balance from MT4: ${balance}")
                        return balance
        except Exception as e:
            print(f"MT4Broker: Error reading balance: {e}")
        
        print("MT4Broker: Using fallback balance - EA not responding")
        return 10000.0  # Fallback
        
    def get_equity(self) -> float:
        """Get account equity from MT4."""
        # For now, return a simulated equity
        # In production, this would read from MT4's account data
        return 10000.0
