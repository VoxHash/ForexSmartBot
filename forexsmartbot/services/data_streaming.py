"""
Real-time Data Streaming Optimization Module
Optimizes data streaming for high-performance real-time updates.
"""

import asyncio
import queue
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime
import pandas as pd
from ..core.interfaces import IDataProvider


class DataStreamManager:
    """Manages optimized real-time data streaming."""
    
    def __init__(self, data_provider: IDataProvider, update_interval: float = 1.0):
        self.data_provider = data_provider
        self.update_interval = update_interval
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self.stream_thread = None
        self.data_queue = queue.Queue()
        
    def subscribe(self, symbol: str, callback: Callable):
        """
        Subscribe to real-time updates for a symbol.
        
        Args:
            symbol: Trading symbol
            callback: Callback function to call with updates
        """
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        
    def unsubscribe(self, symbol: str, callback: Callable):
        """Unsubscribe from updates."""
        if symbol in self.subscribers:
            if callback in self.subscribers[symbol]:
                self.subscribers[symbol].remove(callback)
                
    def start_streaming(self):
        """Start the data streaming thread."""
        if self.running:
            return
            
        self.running = True
        self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.stream_thread.start()
        
    def stop_streaming(self):
        """Stop the data streaming thread."""
        self.running = False
        if self.stream_thread:
            self.stream_thread.join(timeout=2.0)
            
    def _stream_loop(self):
        """Main streaming loop."""
        import time
        
        while self.running:
            try:
                # Get latest prices for all subscribed symbols
                for symbol in list(self.subscribers.keys()):
                    try:
                        price = self.data_provider.get_latest_price(symbol)
                        if price is not None:
                            # Notify all subscribers
                            for callback in self.subscribers.get(symbol, []):
                                try:
                                    callback(symbol, price, datetime.now())
                                except Exception as e:
                                    print(f"Error in subscriber callback: {e}")
                    except Exception as e:
                        print(f"Error getting price for {symbol}: {e}")
                        
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Error in streaming loop: {e}")
                time.sleep(self.update_interval)


class OptimizedDataCache:
    """Optimized data cache for high-performance access."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, pd.DataFrame] = {}
        self.access_times: Dict[str, datetime] = {}
        
    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Get data from cache."""
        if key in self.cache:
            self.access_times[key] = datetime.now()
            return self.cache[key]
        return None
        
    def set(self, key: str, data: pd.DataFrame):
        """Set data in cache."""
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
            
        self.cache[key] = data
        self.access_times[key] = datetime.now()
        
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.access_times.clear()

