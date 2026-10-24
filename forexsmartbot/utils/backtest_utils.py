"""Helpers for backtest dialog (importable without spinning up the full UI)."""


def parse_strategy_label(label: str) -> str:
    """Strip risk emoji / suffix from a combo display label."""
    name = label or ""
    for emoji in ("🟢 ", "🟡 ", "🔴 ", "⚪ "):
        if emoji in name:
            name = name.replace(emoji, "")
    if " (" in name:
        name = name.split(" (")[0]
    return name.strip()
