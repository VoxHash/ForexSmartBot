import os, zmq, json
from dataclasses import dataclass

@dataclass
class MT4Bridge:
    host: str
    port: int

    def __post_init__(self):
        self.ctx = zmq.Context()
        self.sock = self.ctx.socket(zmq.REQ)
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
