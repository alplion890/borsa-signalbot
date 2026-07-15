"""Paper pozisyon yonetimi — honest (SL-once) fill modeli.

Backtest honest_engine ile ayni mantik: bir bar icinde hem SL hem TP varsa SL
once sayilir (en kotu durum). Maliyet config.cost_per_side'dan dusulur. Sonuc
her trade icin R-katsayisi.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class PaperPosition:
    module: str
    symbol: str
    direction: int          # +1 long, -1 short
    entry_time: pd.Timestamp
    entry: float
    sl: float
    tp: float
    weight: float
    max_hold_bars: int
    cost_per_side: float
    bars_held: int = 0
    status: str = "open"     # open | tp | sl | timeout
    exit_time: pd.Timestamp | None = None
    exit: float | None = None
    r: float | None = None

    @property
    def risk(self) -> float:
        return abs(self.entry - self.sl)

    def update(self, bar_time: pd.Timestamp, high: float, low: float, close: float) -> bool:
        """Yeni bar ile pozisyonu guncelle. Kapandiysa True doner."""
        if self.status != "open":
            return True
        self.bars_held += 1
        risk = self.risk
        if risk <= 0:
            self._close(bar_time, close, "sl", 0.0)
            return True

        if self.direction == 1:
            hit_sl = low <= self.sl
            hit_tp = high >= self.tp
        else:
            hit_sl = high >= self.sl
            hit_tp = low <= self.tp

        # SL-once (en kotu durum) — backtest ile ayni
        if hit_sl:
            self._close(bar_time, self.sl, "sl", -1.0)
            return True
        if hit_tp:
            r = abs(self.tp - self.entry) / risk
            self._close(bar_time, self.tp, "tp", r)
            return True
        if self.bars_held >= self.max_hold_bars:
            r = self.direction * (close - self.entry) / risk
            self._close(bar_time, close, "timeout", r)
            return True
        return False

    def _close(self, t: pd.Timestamp, price: float, status: str, gross_r: float) -> None:
        # gidis-donus maliyeti R cinsinden: 2 * cost_ratio * entry / risk
        cost_r = 2.0 * self.cost_per_side * self.entry / self.risk if self.risk > 0 else 0.0
        self.status = status
        self.exit_time = t
        self.exit = price
        self.r = float(gross_r - cost_r)

    def to_row(self) -> dict:
        return {
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "module": self.module,
            "symbol": self.symbol,
            "dir": self.direction,
            "entry": self.entry,
            "sl": self.sl,
            "tp": self.tp,
            "exit": self.exit,
            "bars_held": self.bars_held,
            "status": self.status,
            "r": self.r,
            "weight": self.weight,
            "weighted_r": (self.r * self.weight) if self.r is not None else None,
        }


@dataclass
class Book:
    """Acik pozisyonlar + kapanmis trade ledger'i."""
    open_positions: list[PaperPosition] = field(default_factory=list)
    closed: list[dict] = field(default_factory=list)

    def has_open(self, module: str, symbol: str) -> bool:
        return any(p.module == module and p.symbol == symbol for p in self.open_positions)

    def add(self, pos: PaperPosition) -> None:
        self.open_positions.append(pos)

    def update_symbol(self, symbol: str, bar_time, high, low, close) -> None:
        still_open = []
        for p in self.open_positions:
            if p.symbol != symbol:
                still_open.append(p)
                continue
            if p.update(bar_time, high, low, close):
                self.closed.append(p.to_row())
            else:
                still_open.append(p)
        self.open_positions = still_open

    def ledger(self) -> pd.DataFrame:
        if not self.closed:
            return pd.DataFrame()
        df = pd.DataFrame(self.closed)
        # entry_time state JSON'dan str, bu dongude Timestamp gelebilir -> normalize
        df["entry_time"] = pd.to_datetime(df["entry_time"])
        return df.set_index("entry_time").sort_index()
