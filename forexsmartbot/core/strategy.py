import pandas as pd
import numpy as np

class Strategy:
    """Simple trend/volatility aware strategy:
    - SMA crossover (fast over slow) for direction
    - ATR for stop distance and vol estimate
    - Exits on opposite cross or stop
    """
    def __init__(self, fast=20, slow=50, atr_window=14):
        self.fast = fast
        self.slow = slow
        self.atr_window = atr_window

    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out['SMA_fast'] = out['Close'].rolling(self.fast).mean()
        out['SMA_slow'] = out['Close'].rolling(self.slow).mean()
        tr = np.maximum(out['High']-out['Low'],
                        np.maximum(abs(out['High']-out['Close'].shift(1)),
                                   abs(out['Low']-out['Close'].shift(1))))
        out['ATR'] = tr.rolling(self.atr_window).mean()
        return out

    def signal(self, df: pd.DataFrame) -> int:
        if len(df) < max(self.fast, self.slow) + 2:
            return 0
        row = df.iloc[-1]
        prev = df.iloc[-2]
        # cross detection
        if float(row['SMA_fast']) > float(row['SMA_slow']) and float(prev['SMA_fast']) <= float(prev['SMA_slow']):
            return +1
        if float(row['SMA_fast']) < float(row['SMA_slow']) and float(prev['SMA_fast']) >= float(prev['SMA_slow']):
            return -1
        return 0

    def volatility(self, df: pd.DataFrame) -> float | None:
        if 'ATR' not in df:
            return None
        atr = float(df['ATR'].iloc[-1])
        price = float(df['Close'].iloc[-1])
        if pd.isna(atr) or pd.isna(price) or price == 0:
            return None
        return atr/price
