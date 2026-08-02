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
                       entry_mode: str = "retest", trend: str = "vwap",
                       atr_max_rank: float = 0.67):
    """Final portfoydeki gold modulunun canli dedektoru.

    Son kapanmis bar bir ORB giris sinyali tasiyorsa VE (a) adx rejimi trend/strong
    (chop degil) VE (b) atr rejimi yuksek-vol degil ise Signal doner.

    (b) rangeci-rejim filtresi (2026-07-12): forward'da gold ORB'un tum kayiplari
    yuksek-vol patlama gunlerinde whipsaw timeout'tan geliyordu. gold_orb_regime
    taramasi 'adx>=trend & atr<high' kovasini 4/4 yil pozitif (exp +0.072, minYr
    +0.015) buldu; ham 'adx>=trend' 3/4 yil (minYr -0.009) idi. atr_max_rank=0.67
    = high_vol kovasini (rolling-500 pctile > 0.67) disla. gold_orb_regime ile ayni
    esik. atr_max_rank>=1.0 verilerek eski davranisa donulur.
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
        # rangeci/yuksek-vol whipsaw filtresi: atr_rank (rolling-500 pctile) high ise atla
        if atr_max_rank < 1.0:
            atr_pct = atr(df, ATR_LEN) / df["close"]
            atr_rank = atr_pct.rolling(500, min_periods=100).rank(pct=True).iloc[i]
            if not (atr_rank <= atr_max_rank):
                return None
        if bool(le.iloc[i]):
            return Signal(1, float(df["close"].iloc[i]), float(lsl.iloc[i]), float(ltp.iloc[i]))
        if bool(se.iloc[i]):
            return Signal(-1, float(df["close"].iloc[i]), float(ssl.iloc[i]), float(stp.iloc[i]))
        return None

    return detect


def _dual_thrust_detector(k: float = 0.3, n_days: int = 2, rr: float = 1.5,
                          adx_min: float = 30.0, max_hold: int = 48):
    """Dual Thrust range tanimiyla NQ ORB (ADAY -- kanitlanmadi).

    NQ_ORB ile ayni seans/SL mantigi/RR/hold/ADX filtresi; sadece tetik
    seviyesi farkli: seans acilisi +- k * max(HH-LC, HC-LL) (onceki n_days gun).
    Backtest A/B (intraday/dual_thrust_ab.py, 3 yil): 205 islem, exp_R +0.122,
    4/4 yil pozitif (baseline ORB15: +0.099, 3/4 yil). DSR 0.895 -- 0.95
    esigini GECMEDI, fark bootstrap'ta anlamsiz (%95 GA [-0.132, +0.178]).
    Bu yuzden aday: forward'da bagimsiz veri toplanacak.
    """
    from ..dual_thrust_ab import build_dual_thrust

    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 200:
            return None
        try:
            le, se, lsl, ltp, ssl, stp = build_dual_thrust(df, k, n_days, rr, max_hold)
        except Exception:
            return None
        i = -1
        if adx_min > 0 and not (_adx(df, 14).iloc[i] > adx_min):
            return None
        if bool(le.iloc[i]) and np.isfinite(lsl.iloc[i]) and np.isfinite(ltp.iloc[i]):
            return Signal(1, float(df["close"].iloc[i]), float(lsl.iloc[i]), float(ltp.iloc[i]))
        if bool(se.iloc[i]) and np.isfinite(ssl.iloc[i]) and np.isfinite(stp.iloc[i]):
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
                     adx_max: float = 0.0, dow: int | None = None,
                     range_regime: str | None = None):
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
        if range_regime is not None:
            h = df.index.hour + df.index.minute / 60.0
            in_range = (h >= case.range_start) & (h < case.range_end)
            daily_hi = df["high"].where(in_range).groupby(df.index.date).transform("max")
            daily_lo = df["low"].where(in_range).groupby(df.index.date).transform("min")
            range_pct = (daily_hi - daily_lo) / df["close"]
            daily_range = range_pct.groupby(df.index.date).last()
            rank = daily_range.rolling(20, min_periods=10).rank(pct=True).iloc[-1]
            current_regime = (
                "tight_range" if rank <= 0.33
                else "normal_range" if rank <= 0.67
                else "wide_range"
            )
            if pd.isna(rank) or current_regime != range_regime:
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


def _sweep_core_detector(adx_thresh: float = 25.0, min_rr: float = 2.0):
    """NQ sweep core canli dedektoru (geri yuklenen adx_lab ile birebir).

    VWAP trend + ADX>thresh + likidite sweep. TP swing seviyesi; RR ATR rejimine
    gore caplenir (low<0.33:4, mid<0.67:6, high:8). min_rr alti setup atlanir.

    ISIM UYARISI (2026-08-02): Modul adi "SWEEP_CORE_AVOID_MID_VWAP" ama bu
    dedektor mid-VWAP filtresini UYGULAMAZ ve uygulamamalidir. Isim tarihsel;
    veri surekliligi bozulmasin diye degistirilmedi (mevcut forward islemleri
    o ad altinda kayitli).

    Filtre neden UYGULANMIYOR -- taze veriyle test edildi (US100, 6 ay MT5 15m):
        filtresiz (bu dedektor)      n=19  exp_R +1.445
        filtreli (orijinal esikler)  n=13  exp_R +0.948
        filtreli (yeniden terzil)    n=14  exp_R +0.618
    Filtre performansi DUSURUYOR. Sebep: kova bazinda bakildiginda orijinal
    39-islemlik ornekte mid_vwap en kotu kovaydi (+0.332 vs near +1.031); taze
    veride TERSINE dondu (mid +2.013 vs near +0.696). Yani "ortayi at, iki ucu
    tut" deseninin yapisal bir hikayesi yok -- kucuk ornekte olusan gurultuydu
    ve isaret degistirdi. Klasik overfit.
    """
    from ..adx_lab import _make_signals  # geri yuklendi

    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 520:
            return None
        if df.index[-1].dayofweek == 2:  # quality_11: Carsamba kesin kapali
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
        div_long_series = (
            (nq["low"] < rlo) & (nq["close"] > rlo) & (es["low"] >= rlo_es)
            & (trend > 0)
        )
        div_short_series = (
            (nq["high"] > rhi) & (nq["close"] < rhi) & (es["high"] <= rhi_es)
            & (trend < 0)
        )
        div_long = bool(div_long_series.iloc[i]) and not bool(div_long_series.shift(1).fillna(False).iloc[i])
        div_short = bool(div_short_series.iloc[i]) and not bool(div_short_series.shift(1).fillna(False).iloc[i])
        entry = float(nq["close"].iloc[i])
        if div_long:
            sl = float(nq["low"].iloc[i] - buf.iloc[i]); risk = entry - sl
            if risk <= 0:
                return None
            return Signal(1, entry, sl, entry + rr * risk)
        if div_short:
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
                   _orb_detector(nq_orb, adx_min=28.0)),
        LiveModule("SWEEP_CORE_AVOID_MID_VWAP", "NASDAQ100", "15m", 1.0, 480,
                   _sweep_core_detector()),
        LiveModule("EUR_LONDON_FADE_EMA", "EURUSD", "5m", 1.0, 48,
                   _london_detector(
                       LondonCase("EURUSD", 2.0, 7.0, 11.0, "none", 1.5, "other_side", 1.0, 48),
                       adx_max=18.0, dow=3)),
        LiveModule("GBP_LONDON_STRONG_TREND", "GBPUSD", "5m", 0.25, 48,
                   _london_detector(
                       LondonCase("GBPUSD", 0.0, 7.0, 11.0, "ema", 1.5, "other_side", 1.0, 48),
                       dow=3, range_regime="normal_range")),
        # SWEEP_ES_DIV (w=2.0) KALDIRILDI 2026-07-04: forward test edge'i cürüttü.
        # Backtest avg_loss -0.09R fiziksel olarak sahte (igne-ince stop = sweep dibi
        # -0.25*ATR, ~7-13 puan; temiz dukascopy verisinde hic tetiklenmemis, timeout'ta
        # basabas kapanmis). Canli US100 CFD gürültüsünde ayni stop'lar aninda vuruluyor:
        # forward 10 islem, %20 win, -0.33R (backtest 19 islem, %47, +0.21R iddiasina karsi).
        # 19 islemlik örneklem zaten hic saglam degildi. En yüksek agirlik = en tehlikeli.
    ]


def candidate_modules() -> list[LiveModule]:
    """ADAYLAR: forward'da olculur, Telegram'a CIKMAZ.

    Neden ayri liste: `default_modules()` hem forward EA hem signalbot tarafindan
    kullaniliyor. Kanitlanmamis bir aday oraya konursa kullanicinin telefonuna
    sinyal duser. Aday once burada bagimsiz veri biriktirir; PSR/DSR yeterli
    olunca ELLE default_modules()'e tasinir.

    Isim onu `CAND_` ile baslar -> defterde bir bakista ayirt edilir.
    Agirlik 0.0: portfoy R'sine katilmaz, sadece kendi kaydini tutar.
    """
    sp500_orb = ORBCase("SP500", 14.5, 15, 20.5, "retest", "none", 1.5, "other_side", 1.0, 48)
    return [
        LiveModule("CAND_NQ_DUAL_THRUST", "NASDAQ100", "5m", 0.0, 48,
                   _dual_thrust_detector(k=0.3, n_days=2, rr=1.5, adx_min=30.0)),
        # NQ_ORB config'inin BIREBIR AYNISI, sadece sembol SP500 (broker: US500).
        # Amac iki katli: (a) forward veri hizini ~2x artirmak, (b) "ORB mantigi
        # endekslerde genellenebilir mi" hipotezini bagimsiz olarak sinamak.
        # Backtest (orb_cross_symbol.py, 3 yil): 270 islem, exp_R +0.031, 2/4 yil
        # pozitif -- NQ'dan (+0.099, 3/4) ZAYIF ama pozitif. Havuzlanmis NQ+SP500:
        # 556 islem, +0.066, PSR 0.925. Endeks disi sembollerde (XAU/XAG/EUR/GBP)
        # ayni config NEGATIF -- likidite profilerinin yapisal tezini dogruluyor.
        # US100 ile korelasyon yuksek: 2 islem != 2 bagimsiz kanit.
        LiveModule("CAND_SP500_ORB", "SP500", "5m", 0.0, 48,
                   _orb_detector(sp500_orb, adx_min=30.0)),
        # SWEEP_CORE'u diger ABD endekslerine yay (multi_index_lab.py, 6 ay MT5 M5).
        # Onceden yazilan karar kurali "HAVUZ exp_R>0 ve PSR>=0.80" idi; sweep
        # havuzu 60 islem, exp_R +0.423, PSR 0.929 ile GECTI -> ekleniyor.
        #
        # DURUST NUANS: havuzu tek basina NASDAQ tasiyor (US100 n=19 exp_R +1.379;
        # US500 +0.036, US30 +0.049, US2000 -0.141). Yani bu ekleme "sweep tum
        # endekslerde calisiyor" demek DEGIL. Amac tam tersini sinamak: sweep
        # NASDAQ'a mi ozgu, yoksa endeks geneli mi? Uc sembol de duz cikarsa
        # sweep'in NASDAQ mikroyapisina bagli oldugu kanitlanir.
        # Olcum icin eklendi, TICARET icin degil. weight=0.0, Telegram'a cikmaz.
        LiveModule("CAND_SWEEP_SP500", "SP500", "15m", 0.0, 480, _sweep_core_detector()),
        LiveModule("CAND_SWEEP_US30", "US30", "15m", 0.0, 480, _sweep_core_detector()),
        LiveModule("CAND_SWEEP_US2000", "US2000", "15m", 0.0, 480, _sweep_core_detector()),
    ]


def forward_test_modules() -> list[LiveModule]:
    """Forward EA'nin kosturdugu tam liste: canli portfoy + adaylar."""
    return [*default_modules(), *candidate_modules()]


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
