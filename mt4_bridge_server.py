#!/usr/bin/env python3
"""
MT4 Bridge Server
A ZeroMQ server that bridges between the Python ForexSmartBot and MT4.
This server listens for requests from the Python app and forwards them to MT4.
"""

import zmq
import json
import time
import threading
from datetime import datetime

class MT4BridgeServer:
    def __init__(self, host="127.0.0.1", port=5555):
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.running = False
        
    def start(self):
        """Start the bridge server."""
        try:
            self.socket.bind(f"tcp://{self.host}:{self.port}")
            self.running = True
            print(f"MT4 Bridge Server started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    # Wait for request with timeout
                    if self.socket.poll(1000):  # 1 second timeout
                        message = self.socket.recv_string()
                        request = json.loads(message)
                        
                        # Process the request
                        response = self.process_request(request)
                        
                        # Send response back
                        self.socket.send_string(json.dumps(response))
                    else:
                        # No request received, continue
                        time.sleep(0.1)
                        
                except zmq.Again:
                    # Timeout, continue
                    continue
                except Exception as e:
                    print(f"Error processing request: {e}")
                    self.socket.send_string(json.dumps({"error": str(e)}))
                    
        except Exception as e:
            print(f"Failed to start MT4 Bridge Server: {e}")
        finally:
            self.stop()
    
    def process_request(self, request):
        """Process incoming requests from the Python app."""
        cmd = request.get('cmd', '')
        
        if cmd == 'ping':
            return {"status": "ok", "message": "pong", "timestamp": datetime.now().isoformat()}
        
        elif cmd == 'price':
            symbol = request.get('symbol', 'EURUSD')
            # For now, return a simulated price
            # In a real implementation, this would query MT4
            price = self.get_simulated_price(symbol)
            return {"price": price, "symbol": symbol, "timestamp": datetime.now().isoformat()}
        
        elif cmd == 'balance':
            # Simulated account balance
            return {"balance": 10000.0, "timestamp": datetime.now().isoformat()}
        
        elif cmd == 'equity':
            # Simulated account equity
            return {"equity": 10000.0, "timestamp": datetime.now().isoformat()}
        
        elif cmd == 'symbol_info':
            symbol = request.get('symbol', 'EURUSD')
            return {
                "symbol": symbol,
                "bid": self.get_simulated_price(symbol),
                "ask": self.get_simulated_price(symbol) + 0.0001,
                "spread": 0.0001,
                "digits": 5,
                "point": 0.00001,
                "timestamp": datetime.now().isoformat()
            }
        
        elif cmd == 'historical_data':
            symbol = request.get('symbol', 'EURUSD')
            timeframe = request.get('timeframe', 60)
            start_time = request.get('start_time', '')
            end_time = request.get('end_time', '')
            
            # Generate simulated historical data
            data = self.generate_historical_data(symbol, timeframe)
            return {"data": data, "symbol": symbol, "timestamp": datetime.now().isoformat()}
        
        else:
            return {"error": f"Unknown command: {cmd}"}
    
    def get_simulated_price(self, symbol):
        """Generate a simulated price for testing."""
        base_prices = {
            'EURUSD': 1.1700,
            'GBPUSD': 1.2500,
            'USDJPY': 150.0,
            'GBPJPY': 200.0,
            'AUDUSD': 0.7500,
            'USDCAD': 1.3500,
            'USDCHF': 0.9200,
            'NZDUSD': 0.7000
        }
        
        base_price = base_prices.get(symbol, 1.0000)
        # Add some random variation
        import random
        variation = random.uniform(-0.001, 0.001)
        return round(base_price + variation, 5)
    
    def generate_historical_data(self, symbol, timeframe):
        """Generate simulated historical data."""
        import random
        from datetime import datetime, timedelta
        
        data = []
        base_price = self.get_simulated_price(symbol)
        
        # Generate 100 bars of data
        for i in range(100):
            timestamp = datetime.now() - timedelta(hours=i)
            open_price = base_price + random.uniform(-0.01, 0.01)
            close_price = open_price + random.uniform(-0.005, 0.005)
            high_price = max(open_price, close_price) + random.uniform(0, 0.002)
            low_price = min(open_price, close_price) - random.uniform(0, 0.002)
            volume = random.randint(1000, 10000)
            
            data.append({
                "time": int(timestamp.timestamp()),
                "open": round(open_price, 5),
                "high": round(high_price, 5),
                "low": round(low_price, 5),
                "close": round(close_price, 5),
                "volume": volume
            })
        
        return data
    
    def stop(self):
        """Stop the bridge server."""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        print("MT4 Bridge Server stopped")

def main():
    """Main function to run the bridge server."""
    server = MT4BridgeServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down MT4 Bridge Server...")
        server.stop()

if __name__ == "__main__":
    main()
