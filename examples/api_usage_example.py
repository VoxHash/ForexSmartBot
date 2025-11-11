"""
Example: API Usage
Demonstrates how to use the REST API and WebSocket API.
"""

from forexsmartbot.cloud.api_client import APIClient, WebSocketClient
import asyncio

def rest_api_example():
    """Example of using REST API."""
    # Initialize API client
    api_key = "YOUR_API_KEY"
    base_url = "http://localhost:5000"
    
    client = APIClient(api_key=api_key, base_url=base_url)
    
    try:
        # Get account balance
        balance = client.get_balance()
        print(f"Account Balance: ${balance:.2f}")
        
        # Get open positions
        positions = client.get_positions()
        print(f"Open Positions: {len(positions)}")
        for pos in positions:
            print(f"  {pos['symbol']}: {pos['side']} {pos['quantity']} @ {pos['entry_price']}")
        
        # Get current price
        price = client.get_price("EURUSD")
        print(f"EURUSD Price: {price:.4f}")
        
        # Create an order
        order = client.create_order(
            symbol="EURUSD",
            side=1,  # Buy
            quantity=1000,
            stop_loss=1.0980,
            take_profit=1.1100
        )
        print(f"Order created: {order['order_id']}")
        
        # Close positions for a symbol
        result = client.close_positions("EURUSD")
        print(f"Closed positions: {result['message']}")
        
    except Exception as e:
        print(f"Error: {e}")


async def websocket_example():
    """Example of using WebSocket API."""
    # Initialize WebSocket client
    client = WebSocketClient(url="ws://localhost:8765")
    
    try:
        # Connect
        await client.connect()
        print("Connected to WebSocket server")
        
        # Subscribe to price updates
        await client.subscribe("EURUSD")
        print("Subscribed to EURUSD price updates")
        
        # Get balance
        balance = await client.get_balance()
        print(f"Balance: ${balance:.2f}")
        
        # Get positions
        positions = await client.get_positions()
        print(f"Positions: {len(positions)}")
        
        # Listen for real-time updates
        def handle_update(data):
            print(f"Update received: {data}")
        
        print("Listening for updates...")
        await client.listen(handle_update)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()


def main():
    print("=== REST API Example ===")
    rest_api_example()
    
    print("\n=== WebSocket API Example ===")
    asyncio.run(websocket_example())

if __name__ == '__main__':
    main()

