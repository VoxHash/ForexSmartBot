"""Interactive Brokers TWS broker adapter."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from ...core.interfaces import IBroker, Position


class IBTWSBroker(IBroker):
    """Interactive Brokers broker via TWS / IB Gateway using ib_insync."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        account_id: str = "",
    ):
        self._host = host
        self._port = int(port)
        self._client_id = int(client_id)
        self._account_id = account_id
        self._connected = False
        self._contracts: Dict[str, object] = {}
        self._orders: Dict[str, Tuple[str, float]] = {}
        self._ib = None

        try:
            from ib_insync import IB

            self._ib = IB()
        except Exception:
            self._ib = None

    def connect(self) -> bool:
        if self._ib is None:
            print("IBTWSBroker: ib_insync is not installed. Install with: pip install ib_insync")
            return False
        try:
            self._ib.connect(self._host, self._port, clientId=self._client_id, timeout=10)
            self._connected = bool(self._ib.isConnected())
            return self._connected
        except Exception as e:
            print(f"IBTWSBroker: Connection failed: {e}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        try:
            if self._ib is not None and self._ib.isConnected():
                self._ib.disconnect()
        finally:
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected and self._ib is not None and self._ib.isConnected()

    def _get_contract(self, symbol: str):
        if symbol in self._contracts:
            return self._contracts[symbol]

        from ib_insync import Forex

        normalized = symbol.replace("=", "").replace("/", "").upper()
        if normalized.endswith("X"):
            normalized = normalized[:-1]
        if len(normalized) != 6:
            raise ValueError(f"Unsupported symbol format for IB Forex: {symbol}")

        contract = Forex(normalized)
        self._ib.qualifyContracts(contract)
        self._contracts[symbol] = contract
        return contract

    def get_price(self, symbol: str) -> Optional[float]:
        if not self.is_connected():
            return None
        try:
            contract = self._get_contract(symbol)
            ticker = self._ib.reqMktData(contract, "", False, False)
            self._ib.sleep(0.5)

            if ticker and ticker.last and ticker.last > 0:
                return float(ticker.last)
            if ticker and ticker.bid and ticker.ask and ticker.bid > 0 and ticker.ask > 0:
                return float((ticker.bid + ticker.ask) / 2.0)
            if ticker and ticker.close and ticker.close > 0:
                return float(ticker.close)
            return None
        except Exception as e:
            print(f"IBTWSBroker: get_price failed for {symbol}: {e}")
            return None

    def submit_order(
        self,
        symbol: str,
        side: int,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Optional[str]:
        if not self.is_connected():
            return None
        try:
            from ib_insync import LimitOrder, MarketOrder, StopOrder

            contract = self._get_contract(symbol)
            action = "BUY" if side > 0 else "SELL"
            exit_action = "SELL" if action == "BUY" else "BUY"
            order_qty = float(abs(quantity))
            if order_qty <= 0:
                return None

            order = MarketOrder(action, order_qty, transmit=True)
            if self._account_id:
                order.account = self._account_id

            # If SL/TP are provided, place as linked child orders for risk control.
            if stop_loss is not None or take_profit is not None:
                order.transmit = False

            trade = self._ib.placeOrder(contract, order)
            self._ib.sleep(0.5)

            order_id = str(trade.order.orderId)
            self._orders[order_id] = (symbol, order_qty)

            if stop_loss is not None:
                sl_order = StopOrder(
                    action=exit_action,
                    totalQuantity=order_qty,
                    stopPrice=float(stop_loss),
                    parentId=trade.order.orderId,
                    transmit=(take_profit is None),
                )
                if self._account_id:
                    sl_order.account = self._account_id
                self._ib.placeOrder(contract, sl_order)

            if take_profit is not None:
                tp_order = LimitOrder(
                    action=exit_action,
                    totalQuantity=order_qty,
                    lmtPrice=float(take_profit),
                    parentId=trade.order.orderId,
                    transmit=True,
                )
                if self._account_id:
                    tp_order.account = self._account_id
                self._ib.placeOrder(contract, tp_order)

            self._ib.sleep(0.3)
            return order_id
        except Exception as e:
            print(f"IBTWSBroker: submit_order failed for {symbol}: {e}")
            return None

    def close_all(self, symbol: str) -> bool:
        if not self.is_connected():
            return False
        try:
            from ib_insync import MarketOrder

            closed_any = False
            target = symbol.replace("=", "").replace("/", "").upper()
            if target.endswith("X"):
                target = target[:-1]

            for pos in self._ib.positions():
                local_symbol = (pos.contract.localSymbol or "").replace(".", "").upper()
                con_symbol = f"{pos.contract.symbol}{getattr(pos.contract, 'currency', '')}".upper()
                if target not in (local_symbol, con_symbol):
                    continue

                qty = float(pos.position)
                if qty == 0:
                    continue
                action = "SELL" if qty > 0 else "BUY"
                order = MarketOrder(action, abs(qty))
                if self._account_id:
                    order.account = self._account_id
                self._ib.placeOrder(pos.contract, order)
                closed_any = True

            if closed_any:
                self._ib.sleep(0.5)
            return closed_any
        except Exception as e:
            print(f"IBTWSBroker: close_all failed for {symbol}: {e}")
            return False

    def get_positions(self) -> Dict[str, Position]:
        positions: Dict[str, Position] = {}
        if not self.is_connected():
            return positions

        try:
            for pos in self._ib.positions():
                qty = float(pos.position)
                if qty == 0:
                    continue

                symbol = f"{pos.contract.symbol}{getattr(pos.contract, 'currency', '')}"
                market_price = self.get_price(symbol) or float(pos.avgCost)
                side = 1 if qty > 0 else -1
                unrealized = side * abs(qty) * (market_price - float(pos.avgCost))

                positions[symbol] = Position(
                    symbol=symbol,
                    side=side,
                    quantity=abs(qty),
                    entry_price=float(pos.avgCost),
                    current_price=float(market_price),
                    unrealized_pnl=float(unrealized),
                )
        except Exception as e:
            print(f"IBTWSBroker: get_positions failed: {e}")

        return positions

    def get_balance(self) -> float:
        if not self.is_connected():
            return 0.0
        try:
            values = self._ib.accountSummary()
            for row in values:
                if row.tag == "TotalCashValue" and (not self._account_id or row.account == self._account_id):
                    return float(row.value)
        except Exception as e:
            print(f"IBTWSBroker: get_balance failed: {e}")
        return 0.0

    def get_equity(self) -> float:
        if not self.is_connected():
            return 0.0
        try:
            values = self._ib.accountSummary()
            for row in values:
                if row.tag == "NetLiquidation" and (not self._account_id or row.account == self._account_id):
                    return float(row.value)
        except Exception as e:
            print(f"IBTWSBroker: get_equity failed: {e}")
        return 0.0
