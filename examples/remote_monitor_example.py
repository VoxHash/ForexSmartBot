"""
Example: Remote Monitor Usage
Demonstrates how to use the remote monitoring server.
"""

from forexsmartbot.cloud.remote_monitor import RemoteMonitorServer
from forexsmartbot.adapters.brokers.paper_broker import PaperBroker
import time

def main():
    # Initialize remote monitor server
    monitor = RemoteMonitorServer(host="127.0.0.1", port=8080)
    
    # Initialize broker (example)
    broker = PaperBroker(10000.0)
    broker.connect()
    
    # Register control callbacks
    def start_trading():
        print("Starting trading...")
        return True
    
    def stop_trading():
        print("Stopping trading...")
        return True
    
    monitor.register_control_callback('start_trading', start_trading)
    monitor.register_control_callback('stop_trading', stop_trading)
    
    # Start the monitor server
    monitor.start()
    
    print("Remote monitor server started on http://127.0.0.1:8080")
    print("Open this URL in your browser to access the monitoring dashboard")
    
    # Simulate trading data updates
    try:
        while True:
            # Update trading data
            balance = broker.get_balance()
            positions = broker.get_positions()
            
            monitor.update_trading_data({
                'balance': balance,
                'equity': balance,
                'positions': [
                    {
                        'symbol': pos.symbol,
                        'side': 'Long' if pos.side > 0 else 'Short',
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'pnl': pos.pnl if hasattr(pos, 'pnl') else 0
                    }
                    for pos in positions.values()
                ],
                'trades': [],
                'status': 'connected' if broker.is_connected() else 'disconnected'
            })
            
            time.sleep(3)  # Update every 3 seconds
            
    except KeyboardInterrupt:
        print("\nStopping remote monitor...")
        monitor.stop()

if __name__ == '__main__':
    main()

