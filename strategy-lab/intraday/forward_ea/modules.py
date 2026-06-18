"""Canli sinyal ureticileri.

Her LiveModule: en son KAPANMIS bar uzerinde sinyal var mi diye bakar; varsa
(dir, entry, sl, tp) doner. Backtest sinyal mantigini birebir kullanir (ayni
fonksiyonlar), sadece "son bar"a uygular.

Ilk somut modul: Gold NY-ORB (temiz + MT5'te mevcut). Digerleri (NQ sweep, EUR
London, ES div) ayni protokolle eklenir — README'ye bak.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from ..config import INSTRUMENTS, ATR_LEN
from ..edge_lab import _adx
from ..indicators import atr
from ..internet_seed_strategies import ORBCase, LondonCase, _build_orb, _build_london


@dataclass(frozen=True)
class Signal:
    direction: int
    entry: float
    sl: float
    tp: float


@dataclass(frozen=True)
class LiveModule:
    name: str
    symbol_key: str          # mt5_io sembol anahtari (XAUUSD, NASDAQ100...)
    tf: str                  # "5m" | "15m"
    weight: float
    max_hold_bars: int
    detect: Callable[[pd.DataFrame], Signal | None]

    @property
    def cost_per_side(self) -> float:
        return INSTRUMENTS[self.symbol_key].cost_per_side


def _gold_orb_detector(open_hour: float = 13.5, range_minutes: int = 60,
                       rr: float = 1.0, max_hold: int = 48,
                       adx_thresh_strong: float = 30.0,
                       entry_mode: str = "retest", trend: str = "vwap"):
    """Final portfoydeki gold modulunun canli dedektoru.

    Son kapanmis bar bir ORB giris sinyali tasiyorsa ve adx rejimi trend/strong
    ise Signal doner. Backtest gold_orb_regime ile ayni filtre.
    """
    case = ORBCase("XAUUSD", open_hour, range_minutes, 21.0, entry_mode, trend,
                   rr, "other_side", 1.0, max_hold)

    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 200:
            return None
        le, se, lsl, ltp, ssl, stp = _build_orb(df, case)
        i = -1  # son kapanmis bar (caller son bari kapanmis verir)
        adx = _adx(df, 14).iloc[i]
        if not (adx > 20):           # chop'u disla (trend/strong_trend tut)
            return None
        if bool(le.iloc[i]):
            return Signal(1, float(df["close"].iloc[i]), float(lsl.iloc[i]), float(ltp.iloc[i]))
        if bool(se.iloc[i]):
            return Signal(-1, float(df["close"].iloc[i]), float(ssl.iloc[i]), float(stp.iloc[i]))
        return None

    return detect


def _orb_detector(case: ORBCase, adx_min: float):
    """Genel ORB dedektoru (NQ/Gold). adx_min: rejim filtresi (0=filtre yok)."""
    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 200:
            return None
        le, se, lsl, ltp, ssl, stp = _build_orb(df, case)
        i = -1
        if adx_min > 0 and not (_adx(df, 14).iloc[i] > adx_min):
            return None
        if bool(le.iloc[i]):
            return Signal(1, float(df["close"].iloc[i]), float(lsl.iloc[i]), float(ltp.iloc[i]))
        if bool(se.iloc[i]):
            return Signal(-1, float(df["close"].iloc[i]), float(ssl.iloc[i]), float(stp.iloc[i]))
        return None
    return detect


def _london_detector(case: LondonCase, adx_min: float = 0.0,
                     adx_max: float = 0.0, dow: int | None = None):
    """Genel London breakout dedektoru (EUR/GBP).

    Filtreler final ledger'dan birebir geri cikarildi:
      EUR: adx<20 (chop) + Persembe (dow=3)
      GBP: Persembe (dow=3) + ema (case icinde)
    """
    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 200:
            return None
        le, se, lsl, ltp, ssl, stp = _build_london(df, case)
        i = -1
        if dow is not None and df.index[i].dayofweek != dow:
            return None
        adx_val = _adx(df, 14).iloc[i]
        if adx_min > 0 and not (adx_val > adx_min):
            return None
        if adx_max > 0 and not (adx_val < adx_max):
            return None
        if bool(le.iloc[i]):
            return Signal(1, float(df["close"].iloc[i]), float(lsl.iloc[i]), float(ltp.iloc[i]))
        if bool(se.iloc[i]):
            return Signal(-1, float(df["close"].iloc[i]), float(ssl.iloc[i]), float(stp.iloc[i]))
        return None
    return detect


def _sweep_core_detector(adx_thresh: float = 25.0, min_rr: float = 2.5):
    """NQ sweep core canli dedektoru (geri yuklenen adx_lab ile birebir).

    VWAP trend + ADX>thresh + likidite sweep. TP swing seviyesi; RR ATR rejimine
    gore caplenir (low<0.33:4, mid<0.67:6, high:8). min_rr alti setup atlanir.
    Seyrek ama yuksek-beklentili edge (+0.76R).
    """
    from ..adx_lab import _make_signals  # geri yuklendi

    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 520:
            return None
        le, se, lsl, ltp, ssl, stp, a = _make_signals(df, adx_thresh)
        i = -1
        atr_pct = (a / df["close"])
        rank = atr_pct.rolling(500, min_periods=100).rank(pct=True).iloc[i]
        if pd.isna(rank):
            return None
        max_rr = 4.0 if rank < 0.33 else (6.0 if rank < 0.67 else 8.0)

        if bool(le.iloc[i]):
            entry = float(df["close"].iloc[i]); sl = float(lsl.iloc[i]); tp = float(ltp.iloc[i])
            risk = entry - sl
            if risk <= 0:
                return None
            rr = (tp - entry) / risk
            if rr < min_rr:
                return None
            tp = entry + min(rr, max_rr) * risk
            return Signal(1, entry, sl, tp)
        if bool(se.iloc[i]):
            entry = float(df["close"].iloc[i]); sl = float(ssl.iloc[i]); tp = float(stp.iloc[i])
            risk = sl - entry
            if risk <= 0:
                return None
            rr = (entry - tp) / risk
            if rr < min_rr:
                return None
            tp = entry - min(rr, max_rr) * risk
            return Signal(-1, entry, sl, tp)
        return None

    return detect


_ESDIV_CACHE: dict = {}


def _es_div_detector(lookback: int = 40, rr: float = 3.0, buf_mult: float = 0.25):
    """NQ sweep + ES divergence (w=2.0). NQ+ES cift-feed, run_card paramlari.

    ES/1H feed cache'li cekilir (warmup'ta tekrar fetch'i onler).
    Sinyal: NQ likidite sweep AMA ES teyit etmiyor (divergence) + 1H trend.
    """
    from ..indicators import htf_trend, rolling_high, rolling_low, atr

    def _feeds(n_nq: int):
        from ..mt5_bridge import mt5_io
        key = n_nq // 500  # kaba cache anahtari (warmup boyunca sabit kalir)
        if "es" not in _ESDIV_CACHE:
            _ESDIV_CACHE["es"] = mt5_io.ohlcv("SP500", "15m", days=120)
            _ESDIV_CACHE["h1"] = mt5_io.ohlcv("NASDAQ100", "1H", days=120)
        return _ESDIV_CACHE["es"], _ESDIV_CACHE["h1"]

    def detect(df_nq: pd.DataFrame) -> Signal | None:
        if len(df_nq) < lookback + 60:
            return None
        df_es, df_h1 = _feeds(len(df_nq))
        idx = df_nq.index.intersection(df_es.index)
        if len(idx) < lookback + 60 or df_nq.index[-1] not in idx:
            return None
        nq = df_nq.loc[idx]; es = df_es.loc[idx]
        trend = htf_trend(nq.index, df_h1)
        a = atr(nq, 14); buf = a * buf_mult
        rlo = rolling_low(nq, lookback); rhi = rolling_high(nq, lookback)
        rlo_es = rolling_low(es, lookback); rhi_es = rolling_high(es, lookback)
        i = -1
        swept_low = (nq["low"].iloc[i] < rlo.iloc[i]) and (nq["close"].iloc[i] > rlo.iloc[i])
        swept_high = (nq["high"].iloc[i] > rhi.iloc[i]) and (nq["close"].iloc[i] < rhi.iloc[i])
        div_long = swept_low and (es["low"].iloc[i] >= rlo_es.iloc[i])
        div_short = swept_high and (es["high"].iloc[i] <= rhi_es.iloc[i])
        entry = float(nq["close"].iloc[i])
        if div_long and trend.iloc[i] > 0:
            sl = float(nq["low"].iloc[i] - buf.iloc[i]); risk = entry - sl
            if risk <= 0:
                return None
            return Signal(1, entry, sl, entry + rr * risk)
        if div_short and trend.iloc[i] < 0:
            sl = float(nq["high"].iloc[i] + buf.iloc[i]); risk = sl - entry
            if risk <= 0:
                return None
            return Signal(-1, entry, sl, entry - rr * risk)
        return None

    return detect


def default_modules() -> list[LiveModule]:
    """DOGRULANMIS canli moduller (forward test backtest ile uyumlu).

    Sadece ORB-ailesi temiz tasinabiliyor: Gold + NQ ORB. Her ikisi de 30g
    warmup'ta backtest win-rate'iyle uyumlu ve pozitif cikti.

    Devre disi (forward test / altyapi engeli):
      EUR/GBP London : forward test wiring'in dogrulanmis modulle ESLESMEDIGINI
                       gosterdi (EUR 30g'de 28 trade, -6.01R, asiri tetik). Backtest
                       EUR/GBP modulunun tam filtre config'i (fade + rejim) portlanmali.
                       experimental_modules() icinde, varsayilan KAPALI.
      SWEEP_CORE (w=1.0)  : NQ likidite-sweep ureteci mevcut kodda yok.
      SWEEP_ES_DIV (w=2.0): NQ+ES cift-feed + divergence gerekir.
      BTC (w=0.11)        : bu broker'da spot BTC yok (Binance feed).
    """
    nq_orb = ORBCase("NASDAQ100", 14.5, 15, 20.5, "retest", "none", 1.5, "other_side", 1.0, 48)
    return [
        LiveModule("GOLD_NY_ORB_TREND", "XAUUSD", "5m", 1.0, 48, _gold_orb_detector()),
        LiveModule("NQ_ORB_STRONG_TREND", "NASDAQ100", "5m", 1.0, 48,
                   _orb_detector(nq_orb, adx_min=30.0)),
        LiveModule("SWEEP_CORE_AVOID_MID_VWAP", "NASDAQ100", "15m", 1.0, 480,
                   _sweep_core_detector()),
        LiveModule("EUR_LONDON_FADE_EMA", "EURUSD", "5m", 1.0, 48,
                   _london_detector(
                       LondonCase("EURUSD", 2.0, 7.0, 11.0, "none", 1.5, "other_side", 1.0, 48),
                       adx_max=20.0, dow=3)),
        LiveModule("GBP_LONDON_STRONG_TREND", "GBPUSD", "5m", 0.25, 48,
                   _london_detector(
                       LondonCase("GBPUSD", 0.0, 7.0, 11.0, "ema", 1.5, "other_side", 1.0, 48),
                       dow=3)),
        LiveModule("SWEEP_ES_DIV", "NASDAQ100", "15m", 2.0, 480, _es_div_detector()),
    ]


def experimental_modules() -> list[LiveModule]:
    """Henuz dogrulanmamis moduller — forward test esleme sorunu gosterdi.

    Bunlari devreye almak icin backtest modulunun TAM config'i (filtre/rejim)
    pinlenmeli. Su an canli portfoye DAHIL DEGIL.
    """
    eur_london = LondonCase("EURUSD", 2.0, 7.0, 11.0, "none", 1.5, "other_side", 1.0, 48)
    gbp_london = LondonCase("GBPUSD", 0.0, 7.0, 11.0, "ema", 1.5, "other_side", 1.0, 48)
    return [
        LiveModule("EUR_LONDON_FADE_EMA", "EURUSD", "5m", 1.0, 48,
                   _london_detector(eur_london, adx_min=0.0)),
        LiveModule("GBP_LONDON_STRONG_TREND", "GBPUSD", "5m", 0.25, 48,
                   _london_detector(gbp_london, adx_min=30.0)),
    ]
