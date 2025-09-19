import pandas as pd
import numpy as np
import yfinance as yf
from .strategy import Strategy
from .risk import RiskManager
from .paper_broker import PaperBroker

def fetch(pair: str, start: str, end: str, interval='1h') -> pd.DataFrame:
    # yfinance tickers for FX often use 'EURUSD=X'
    ticker = pair.upper() + '=X'
    df = yf.download(ticker, start=start, end=end, interval=interval, auto_adjust=True, progress=False)
    df = df.rename(columns={'Open':'Open','High':'High','Low':'Low','Close':'Close','Volume':'Volume'})
    df = df.dropna()
    return df

def run_backtest(pair: str, start: str, end: str, min_amt: float, max_amt: float, risk_pct: float):
    df = fetch(pair, start, end)
    strat = Strategy()
    df = strat.indicators(df)
    rm = RiskManager(min_amt=min_amt, max_amt=max_amt, risk_pct=risk_pct)
    broker = PaperBroker(balance=10_000.0)

    equity = []
    pos_side = 0

    for i in range(len(df)):
        window = df.iloc[:i+1]
        vol = strat.volatility(window)
        sig = strat.signal(window)
        px = window['Close'].iloc[-1]

        if sig == +1 and pos_side <= 0:
            if pos_side < 0:
                broker.exit(pair, px)
                pos_side = 0
            size = rm.adaptive_amount(broker.balance, vol) / px
            broker.enter(pair, +1, size, px)
            pos_side = +1

        elif sig == -1 and pos_side >= 0:
            if pos_side > 0:
                broker.exit(pair, px)
                pos_side = 0
            size = rm.adaptive_amount(broker.balance, vol) / px
            broker.enter(pair, -1, size, px)
            pos_side = -1

        # mark-to-market
        if pair in broker.positions:
            pos = broker.positions[pair]
            mtm = pos.side * pos.size * (px - pos.entry)
        else:
            mtm = 0.0
        equity.append(broker.balance + mtm)

    results = pd.DataFrame({'Equity': equity}, index=df.index)
    return results
