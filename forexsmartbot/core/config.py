from pydantic import BaseModel, Field
from typing import List, Literal
import os
from dotenv import load_dotenv

# Ensure .env is loaded before reading environment variables
# This is safe to call multiple times - it only loads if not already loaded
load_dotenv(override=False)

class AppConfig(BaseModel):
    broker: Literal["PAPER", "MT4"] = "PAPER"
    account_balance: float = 10_000

    trade_amount_min: float = 10
    trade_amount_max: float = 100
    risk_pct: float = 0.02
    max_drawdown_pct: float = 0.25

    mt4_host: str = "127.0.0.1"
    mt4_port: int = 5555

    symbols: List[str] = Field(default_factory=lambda: ["EURUSD","USDJPY","GBPUSD"])

    @classmethod
    def from_env(cls) -> "AppConfig":
        broker = os.getenv("BROKER", "PAPER").upper()
        account_balance = float(os.getenv("ACCOUNT_BALANCE", "10000"))
        trade_amount_min = float(os.getenv("TRADE_AMOUNT_MIN", "10"))
        trade_amount_max = float(os.getenv("TRADE_AMOUNT_MAX", "100"))
        risk_pct = float(os.getenv("RISK_PCT", "0.02"))
        max_dd = float(os.getenv("MAX_DRAWDOWN_PCT", "0.25"))
        mt4_host = os.getenv("MT4_ZMQ_HOST", "127.0.0.1")
        mt4_port = int(os.getenv("MT4_ZMQ_PORT", "5555"))
        symbols = [s.strip() for s in os.getenv("SYMBOLS","EURUSD,USDJPY,GBPUSD").split(",")]
        return cls(broker=broker, account_balance=account_balance,
                   trade_amount_min=trade_amount_min, trade_amount_max=trade_amount_max,
                   risk_pct=risk_pct, max_drawdown_pct=max_dd,
                   mt4_host=mt4_host, mt4_port=mt4_port, symbols=symbols)
