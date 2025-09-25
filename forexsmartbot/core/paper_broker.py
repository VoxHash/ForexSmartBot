from dataclasses import dataclass, field
from typing import Dict, Optional
import time

@dataclass
class Position:
    side: int  # +1 long, -1 short
    entry: float
    size: float

@dataclass
class PaperBroker:
    balance: float = 10_000.0
    positions: Dict[str, Position] = field(default_factory=dict)

    def price(self, pair: str, df) -> Optional[float]:
        if df is None or len(df)==0: return None
        return float(df['Close'].iloc[-1])

    def enter(self, pair: str, side: int, size: float, price: float):
        self.positions[pair] = Position(side=side, entry=price, size=size)

    def exit(self, pair: str, price: float):
        if pair not in self.positions: return 0.0
        pos = self.positions.pop(pair)
        pnl = pos.side * pos.size * (price - pos.entry)
        self.balance += pnl
        return pnl
