"""Üç intraday strateji çekirdeği.

Her strateji, giriş bar'ında *fiyat cinsinden* SL ve TP seviyesi üretir
(structure-based / esnek RR). RR filtresi ve maliyet engine'de uygulanır.

Sözleşme: build(...) -> Signals
  long_entry / short_entry : bool Series (giriş bar'ı)
  long_sl / long_tp / short_sl / short_tp : float Series (yalnız giriş
  bar'ında anlamlı; diğer barlarda NaN olabilir)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import indicators as ind
from .config import ATR_LEN, SL_ATR_BUFFER


@dataclass
class Signals:
    long_entry: pd.Series
    short_entry: pd.Series
    long_sl: pd.Series
    long_tp: pd.Series
    short_sl: pd.Series
    short_tp: pd.Series


def _empty(index) -> pd.Series:
    return pd.Series(np.nan, index=index)


def _new_signal(raw: pd.Series) -> pd.Series:
    """Sadece koşulun ilk True olduğu barı işaretle (tekrar girişi engelle)."""
    raw = raw.fillna(False).astype(bool)
    return raw & ~raw.shift(1).fillna(False).astype(bool)


# --- Strateji A: SMC likidite süpürme + yapı kırılımı --------------------
def smc_sweep(
    df: pd.DataFrame,
    trend: pd.Series,
    lookback: int = 20,
    sl_buf: float = SL_ATR_BUFFER,
    trend_mode: str = "strict",
    ote: bool = False,
) -> Signals:
    """Likidite süpürme + reddetme.

    lookback   : süpürülen dip/tepe likiditesinin bakış penceresi (bar)
    sl_buf     : SL'ye eklenen ATR tamponu
    trend_mode : 'strict' = HTF trend zorunlu; 'loose' = karşı trend yasak,
                 nötr (0) serbest -> daha fazla işlem
    ote        : True ise giriş, swing bacağının 0.618-0.786 (golden zone /
                 OTE) diliminde olmalı
    """
    a = ind.atr(df, ATR_LEN)
    buf = a * sl_buf
    sh = ind.swing_high(df)
    sl = ind.swing_low(df)
    rlo = ind.rolling_low(df, lookback)
    rhi = ind.rolling_high(df, lookback)

    low, high, close = df["low"], df["high"], df["close"]

    if trend_mode == "strict":
        bull, bear = trend > 0, trend < 0
    else:  # loose: sadece karşı trendde işlem yasak
        bull, bear = trend >= 0, trend <= 0

    # Long: önceki dip likiditesi süpürüldü (low<rolling_low) ama kapanış geri
    # yapının üstünde -> reddetme.
    swept_low = (low < rlo) & (close > rlo)
    long_raw = swept_low & bull
    # Short: tepe likiditesi süpürüldü, kapanış geri altta.
    swept_high = (high > rhi) & (close < rhi)
    short_raw = swept_high & bear

    if ote:
        # Golden zone / OTE: kapanış, süpürme bacağının %61.8-%78.6
        # geri çekilme diliminde olmalı (long için swing high -> sweep low bacağı).
        leg_l = (sh - low).replace(0, np.nan)
        retr_l = (sh - close) / leg_l          # 1'e yakın = dibe yakın giriş
        long_raw = long_raw & (retr_l >= 0.618) & (retr_l <= 0.786)
        leg_s = (high - sl).replace(0, np.nan)
        retr_s = (close - sl) / leg_s
        short_raw = short_raw & (retr_s >= 0.618) & (retr_s <= 0.786)

    long_e = _new_signal(long_raw)
    long_sl = (low - buf).where(long_e)              # süpürme dibi altı
    long_tp = sh.where(long_e)                       # üstteki likidite (swing high)

    short_e = _new_signal(short_raw)
    short_sl = (high + buf).where(short_e)
    short_tp = sl.where(short_e)

    return Signals(long_e, short_e, long_sl, long_tp, short_sl, short_tp)


# --- Strateji B: VWAP + EMA20 pullback (trend takip) ---------------------
def vwap_pullback(df: pd.DataFrame, trend: pd.Series) -> Signals:
    a = ind.atr(df, ATR_LEN)
    buf = a * SL_ATR_BUFFER
    vwap = ind.daily_vwap(df)
    e20 = ind.ema(df["close"], 20)
    sh = ind.swing_high(df)
    sl = ind.swing_low(df)

    low, high, close, op = df["low"], df["high"], df["close"], df["open"]

    # Long: trend boğa, fiyat VWAP üstü, EMA20'ye geri çekilip yeşil kapanış.
    pulled = (low <= e20) & (close > e20) & (close > op)
    long_e = _new_signal((trend > 0) & (close > vwap) & pulled)
    long_sl = (low - buf).where(long_e)
    long_tp = sh.where(long_e)

    pushed = (high >= e20) & (close < e20) & (close < op)
    short_e = _new_signal((trend < 0) & (close < vwap) & pushed)
    short_sl = (high + buf).where(short_e)
    short_tp = sl.where(short_e)

    return Signals(long_e, short_e, long_sl, long_tp, short_sl, short_tp)


# --- Strateji C: Açılış range kırılımı (ORB) -----------------------------
def orb(df: pd.DataFrame, trend: pd.Series, session_start_h: int) -> Signals:
    a = ind.atr(df, ATR_LEN)
    buf = a * SL_ATR_BUFFER
    idx = df.index
    day = pd.Index(idx.date)

    # Seans açılışının ilk 2 barı (30 dk) = açılış range'i
    in_session = pd.Series(idx.hour >= session_start_h, index=idx)
    bar_in_day = pd.Series(idx.hour * 4 + idx.minute // 15, index=idx)
    open_bar = session_start_h * 4
    or_window = in_session & (bar_in_day < open_bar + 2)

    or_high = df["high"].where(or_window).groupby(day).transform("max").ffill()
    or_low = df["low"].where(or_window).groupby(day).transform("min").ffill()
    or_range = (or_high - or_low)

    high, low, close = df["high"], df["low"], df["close"]
    after_or = in_session & (bar_in_day >= open_bar + 2)

    # Long: range üstünü kır, HTF boğa.
    # SL = kırılım barının dibi (yapısal, dar) -> RR'ye alan açar.
    # TP = ölçülü hareket: range yüksekliğinin 2.5x projeksiyonu (likidite hedefi).
    brk_up = (close > or_high) & after_or
    long_e = _new_signal(brk_up & (trend > 0))
    long_sl = (low - buf).where(long_e)
    long_tp = (or_high + 2.5 * or_range).where(long_e)

    brk_dn = (close < or_low) & after_or
    short_e = _new_signal(brk_dn & (trend < 0))
    short_sl = (high + buf).where(short_e)
    short_tp = (or_low - 2.5 * or_range).where(short_e)

    return Signals(long_e, short_e, long_sl, long_tp, short_sl, short_tp)


# --- Strateji D: CRT (Candle Range Theory) -------------------------------
def crt(
    df: pd.DataFrame,
    trend: pd.Series,
    htf_rule: str = "4H",
    window: tuple[int, int] | None = (7, 11),
    sl_buf: float = SL_ATR_BUFFER,
    use_trend: bool = False,
) -> Signals:
    """Önceki HTF mumunun range'i = likidite havuzu.

    Long: fiyat önceki HTF mumunun DİBİNİ süpürür ama 15m kapanış geri range
    içinde -> hedef önceki mumun TEPESİ (range'in karşı tarafı).
    Short simetrik. `window` UTC saat aralığı: (7,11) = Londra ilk seans —
    klasik 'ilk seansta CRT' kurulumu. None = tüm gün.
    CRT doğası gereği dönüş stratejisi: HTF trend filtresi varsayılan kapalı.
    """
    a = ind.atr(df, ATR_LEN)
    buf = a * sl_buf

    htf = df.resample(htf_rule).agg({"high": "max", "low": "min"}).dropna()
    ph = htf["high"].shift(1)
    pl = htf["low"].shift(1)
    floored = df.index.floor(htf_rule)
    prev_high = pd.Series(ph.reindex(floored).to_numpy(), index=df.index)
    prev_low = pd.Series(pl.reindex(floored).to_numpy(), index=df.index)

    low, high, close = df["low"], df["high"], df["close"]
    if window is None:
        win = pd.Series(True, index=df.index)
    else:
        h = df.index.hour
        win = pd.Series((h >= window[0]) & (h < window[1]), index=df.index)

    long_raw = (low < prev_low) & (close > prev_low) & win
    short_raw = (high > prev_high) & (close < prev_high) & win
    if use_trend:
        long_raw &= trend >= 0
        short_raw &= trend <= 0

    long_e = _new_signal(long_raw)
    long_sl = (low - buf).where(long_e)
    long_tp = prev_high.where(long_e)        # range'in karşı tarafı

    short_e = _new_signal(short_raw)
    short_sl = (high + buf).where(short_e)
    short_tp = prev_low.where(short_e)

    return Signals(long_e, short_e, long_sl, long_tp, short_sl, short_tp)


# --- Strateji E: EMA kesişimi --------------------------------------------
def ema_cross(
    df: pd.DataFrame,
    trend: pd.Series,
    fast: int = 9,
    slow: int = 21,
    sl_buf: float = SL_ATR_BUFFER,
    tp_lookback: int = 96,
    use_trend: bool = True,
) -> Signals:
    """Klasik EMA fast/slow kesişimi, HTF trend onaylı.

    SL = son swing dibi/tepesi; TP = son `tp_lookback` barın (≈24 saat)
    en yükseği/düşüğü (üstteki/alttaki likidite).
    """
    a = ind.atr(df, ATR_LEN)
    buf = a * sl_buf
    close = df["close"]
    ef = ind.ema(close, fast)
    es = ind.ema(close, slow)
    swl = ind.swing_low(df)
    swh = ind.swing_high(df)
    day_hi = ind.rolling_high(df, tp_lookback)
    day_lo = ind.rolling_low(df, tp_lookback)

    x_up = (ef > es) & (ef.shift(1) <= es.shift(1))
    x_dn = (ef < es) & (ef.shift(1) >= es.shift(1))
    if use_trend:
        x_up &= trend > 0
        x_dn &= trend < 0

    long_e = _new_signal(x_up)
    long_sl = (swl - buf).where(long_e)
    long_tp = day_hi.where(long_e)

    short_e = _new_signal(x_dn)
    short_sl = (swh + buf).where(short_e)
    short_tp = day_lo.where(short_e)

    return Signals(long_e, short_e, long_sl, long_tp, short_sl, short_tp)


# --- Strateji F: Order Flow (delta / CVD) — yüksek HTF -------------------
def orderflow(
    df: pd.DataFrame,
    trend: pd.Series,
    mode: str = "absorption",
    lookback: int = 20,
    delta_z: float = 1.0,
    sl_buf: float = SL_ATR_BUFFER,
    use_trend: bool = False,
) -> Signals:
    """Mum-bazlı agresör deltası (Binance taker-buy) ile order flow.

    df 'delta' ve 'cvd' sütunlarını içermeli (btc_data.load_btc).

    mode='absorption' (dönüş): fiyat son `lookback` dibini süpürür AMA mum
      deltası net ALICI (satış emildi) -> long. Tersi short. (footprint
      absorpsiyon mantığının HTF karşılığı)
    mode='divergence': fiyat daha düşük dip yapar ama CVD daha yüksek dip
      (gizli alım) -> long. Tersi short.
    mode='trend': güçlü delta (z-skor > delta_z) yönünde + kırılım -> devam.

    SL = süpürme/sinyal mumu dibi-tepesi (yapısal), TP = karşı swing likidite.
    """
    a = ind.atr(df, ATR_LEN)
    buf = a * sl_buf
    low, high, close = df["low"], df["high"], df["close"]
    delta, cvd = df["delta"], df["cvd"]
    sh = ind.swing_high(df)
    sl_ = ind.swing_low(df)
    rlo = ind.rolling_low(df, lookback)
    rhi = ind.rolling_high(df, lookback)

    if mode == "absorption":
        long_raw = (low < rlo) & (delta > 0)            # dibi süpürdü ama net alım
        short_raw = (high > rhi) & (delta < 0)
    elif mode == "divergence":
        cvd_lo = cvd.rolling(lookback).min()
        cvd_hi = cvd.rolling(lookback).max()
        long_raw = (low < rlo) & (cvd > cvd_lo.shift(1))   # fiyat LL, CVD değil
        short_raw = (high > rhi) & (cvd < cvd_hi.shift(1))
    elif mode == "trend":
        dz = (delta - delta.rolling(50).mean()) / delta.rolling(50).std()
        brk_up = close > rhi
        brk_dn = close < rlo
        long_raw = brk_up & (dz > delta_z)
        short_raw = brk_dn & (dz < -delta_z)
    else:
        raise ValueError(f"orderflow mode? {mode}")

    if use_trend:
        long_raw = long_raw & (trend >= 0)
        short_raw = short_raw & (trend <= 0)

    long_e = _new_signal(long_raw)
    long_sl = (low - buf).where(long_e)
    long_tp = sh.where(long_e)
    short_e = _new_signal(short_raw)
    short_sl = (high + buf).where(short_e)
    short_tp = sl_.where(short_e)
    return Signals(long_e, short_e, long_sl, long_tp, short_sl, short_tp)


def build(name: str, df: pd.DataFrame, trend: pd.Series, session_start_h: int, **kw) -> Signals:
    if name == "smc_sweep":
        return smc_sweep(df, trend, **kw)
    if name == "vwap_pullback":
        return vwap_pullback(df, trend)
    if name == "orb":
        return orb(df, trend, session_start_h)
    if name == "crt":
        return crt(df, trend, **kw)
    if name == "ema_cross":
        return ema_cross(df, trend, **kw)
    if name == "orderflow":
        return orderflow(df, trend, **kw)
    raise ValueError(f"Bilinmeyen strateji: {name}")
