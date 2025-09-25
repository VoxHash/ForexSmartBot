from dataclasses import dataclass
import numpy as np

@dataclass
class RiskManager:
    min_amt: float
    max_amt: float
    risk_pct: float = 0.02

    def adaptive_amount(self, balance: float, vol: float | None, winrate_hint: float | None = None) -> float:
        # Kelly-lite sizing (clipped) + volatility targeting
        # winrate_hint default 0.5; edge=(2*W - 1), b=1 (R:R 1:1 approx)
        W = 0.5 if winrate_hint is None else float(winrate_hint)
        edge = max(0.0, 2*W - 1.0)  # 0..1
        kelly_frac = edge  # conservative
        base_amt = balance * min(self.risk_pct + 0.5*kelly_frac*self.risk_pct, 0.05)

        if vol is None or vol <= 0:
            amt = base_amt
        else:
            target_vol = 0.01  # target daily vol of PnL ~1%
            amt = base_amt * (target_vol / min(vol, 0.2))

        return float(np.clip(amt, self.min_amt, self.max_amt))
