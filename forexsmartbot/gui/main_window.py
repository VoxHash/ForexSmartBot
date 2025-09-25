from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QDoubleSpinBox, QTextEdit, QSpinBox, QCheckBox)
from PyQt6.QtCore import QTimer, Qt
from ..core.config import AppConfig
from ..core.strategy import Strategy
from ..core.risk import RiskManager
from ..core.paper_broker import PaperBroker
from ..brokers.mt4_bridge import MT4Bridge
import pandas as pd
import yfinance as yf
import os

class MainWindow(QMainWindow):
    def __init__(self, cfg: AppConfig):
        super().__init__()
        self.setWindowTitle("ForexSmartBot")
        self.cfg = cfg

        self.strategy = Strategy()
        self.rm = RiskManager(cfg.trade_amount_min, cfg.trade_amount_max, cfg.risk_pct)
        self.broker_mode = cfg.broker
        self.paper = PaperBroker(balance=cfg.account_balance)
        self.mt4 = None

        if self.broker_mode == "MT4":
            self.mt4 = MT4Bridge(cfg.mt4_host, cfg.mt4_port)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        # Top controls
        row = QHBoxLayout()
        layout.addLayout(row)

        row.addWidget(QLabel("Broker:"))
        self.broker_sel = QComboBox()
        self.broker_sel.addItems(["PAPER","MT4"])
        self.broker_sel.setCurrentText(self.broker_mode)
        row.addWidget(self.broker_sel)

        row.addWidget(QLabel("Pair:"))
        self.pair_sel = QComboBox()
        for s in cfg.symbols: self.pair_sel.addItem(s)
        row.addWidget(self.pair_sel)

        row.addWidget(QLabel("Min Amt"))
        self.min_amt = QDoubleSpinBox(); self.min_amt.setRange(0, 1e9); self.min_amt.setValue(cfg.trade_amount_min)
        row.addWidget(self.min_amt)

        row.addWidget(QLabel("Max Amt"))
        self.max_amt = QDoubleSpinBox(); self.max_amt.setRange(0, 1e9); self.max_amt.setValue(cfg.trade_amount_max)
        row.addWidget(self.max_amt)

        row.addWidget(QLabel("Risk %"))
        self.risk_pct = QDoubleSpinBox(); self.risk_pct.setRange(0.001, 1.0); self.risk_pct.setDecimals(3); self.risk_pct.setSingleStep(0.005)
        self.risk_pct.setValue(cfg.risk_pct)
        row.addWidget(self.risk_pct)

        row.addWidget(QLabel("Theme:"))
        self.theme_sel = QComboBox(); self.theme_sel.addItems(["Auto","Light","Dark"])
        row.addWidget(self.theme_sel)

        # Buttons
        btn_row = QHBoxLayout(); layout.addLayout(btn_row)
        self.btn_connect = QPushButton("Connect"); btn_row.addWidget(self.btn_connect)
        self.btn_start = QPushButton("Start Bot"); btn_row.addWidget(self.btn_start)
        self.btn_stop = QPushButton("Stop Bot"); btn_row.addWidget(self.btn_stop)

        # Status and log
        self.status_lbl = QLabel("Status: Idle")
        layout.addWidget(self.status_lbl)

        self.log = QTextEdit(); self.log.setReadOnly(True)
        layout.addWidget(self.log)

        # Timer
        self.timer = QTimer(self); self.timer.setInterval(10_000)  # 10 seconds polling
        self.timer.timeout.connect(self.on_tick)

        # Wire events
        self.btn_connect.clicked.connect(self.on_connect)
        self.btn_start.clicked.connect(self.on_start)
        self.btn_stop.clicked.connect(self.on_stop)

        self._pos_side = 0
        self._last_df = None

    def append_log(self, msg: str):
        self.log.append(msg)
        self.log.moveCursor(self.log.textCursor().MoveOperation.End)

    def fetch_data(self, pair: str) -> pd.DataFrame:
        tkr = pair.upper() + "=X"
        df = yf.download(tkr, period="3mo", interval="1h", auto_adjust=True, progress=False)
        df = df.dropna()
        if len(df) == 0:
            return pd.DataFrame(columns=['Open','High','Low','Close','Volume'])
        return df

    def on_connect(self):
        mode = self.broker_sel.currentText()
        self.broker_mode = mode
        if mode == "MT4":
            if self.mt4 is None:
                self.mt4 = MT4Bridge(self.cfg.mt4_host, self.cfg.mt4_port)
            self.append_log("Connected to MT4 bridge.")
        else:
            self.append_log("Using PAPER broker.")

    def on_start(self):
        self.rm.min_amt = float(self.min_amt.value())
        self.rm.max_amt = float(self.max_amt.value())
        self.rm.risk_pct = float(self.risk_pct.value())
        self.status_lbl.setText("Status: Running")
        self.timer.start()
        self.append_log("Bot started.")

    def on_stop(self):
        self.timer.stop()
        self.status_lbl.setText("Status: Stopped")
        self.append_log("Bot stopped.")

    def on_tick(self):
        pair = self.pair_sel.currentText()
        df = self.fetch_data(pair)
        df = self.strategy.indicators(df)
        self._last_df = df

        vol = self.strategy.volatility(df)
        sig = self.strategy.signal(df)
        price = float(df['Close'].iloc[-1])

        if self.broker_mode == "PAPER":
            if sig == +1 and self._pos_side <= 0:
                if self._pos_side < 0:
                    pnl = self.paper.exit(pair, price)
                    self.append_log(f"Closed SHORT {pair}, PnL {pnl:.2f}")
                    self._pos_side = 0
                amt = self.rm.adaptive_amount(self.paper.balance, vol)
                size = amt / price
                self.paper.enter(pair, +1, size, price)
                self.append_log(f"Opened LONG {pair} size={size:.6f} @ {price:.5f}")
                self._pos_side = +1

            elif sig == -1 and self._pos_side >= 0:
                if self._pos_side > 0:
                    pnl = self.paper.exit(pair, price)
                    self.append_log(f"Closed LONG {pair}, PnL {pnl:.2f}")
                    self._pos_side = 0
                amt = self.rm.adaptive_amount(self.paper.balance, vol)
                size = amt / price
                self.paper.enter(pair, -1, size, price)
                self.append_log(f"Opened SHORT {pair} size={size:.6f} @ {price:.5f}")
                self._pos_side = -1

            # mark to market
            if pair in self.paper.positions:
                pos = self.paper.positions[pair]
                mtm = pos.side * pos.size * (price - pos.entry)
            else:
                mtm = 0.0
            eq = self.paper.balance + mtm
            self.status_lbl.setText(f"Status: Running | Balance: {self.paper.balance:.2f} | Eqty: {eq:.2f}")

        else:  # MT4 mode (placeholder flow)
            self.append_log(f"Signal {sig} on {pair} @ {price:.5f} (MT4 live flow requires full ZMQ EA)")

