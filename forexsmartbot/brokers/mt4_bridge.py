import os, zmq, json
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class MT4Bridge:
    host: str
    port: int

    def __post_init__(self):
        self.ctx = zmq.Context()
        self.sock = self.ctx.socket(zmq.REQ)
        self.sock.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
        self.sock.connect(f"tcp://{self.host}:{self.port}")

    def send(self, cmd: str, **kwargs):
        payload = {'cmd': cmd, **kwargs}
        self.sock.send_string(json.dumps(payload))
        msg = self.sock.recv_string()
        return json.loads(msg)

    def price(self, symbol: str):
        return self.send('price', symbol=symbol)

    def order(self, symbol: str, side: int, volume: float, sl: float|None=None, tp: float|None=None):
        return self.send('order', symbol=symbol, side=side, volume=volume, sl=sl, tp=tp)

    def close_all(self, symbol: str):
        return self.send('close_all', symbol=symbol)
    
    def historical_data(self, symbol: str, timeframe: int, start_time: str, end_time: str):
        """Request historical data from MT4."""
        return self.send('historical_data', 
                        symbol=symbol, 
                        timeframe=timeframe, 
                        start_time=start_time, 
                        end_time=end_time)
    
    def symbol_info(self, symbol: str):
        """Get symbol information from MT4."""
        return self.send('symbol_info', symbol=symbol)
    
    def account_info(self):
        """Get account information from MT4."""
        return self.send('account_info')
    
    def ping(self):
        """Test connection to MT4."""
        return self.send('ping')
