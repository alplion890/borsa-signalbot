"""İndikatör ve yapı (market structure) yardımcıları.

Hepsi tamamen vektörel ve look-ahead'sızdır: bir bardaki sinyal yalnızca
o bar ve öncesindeki kapanmış verilere dayanır.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev_close = df["close"].shift()
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def daily_vwap(df: pd.DataFrame) -> pd.Series:
    hlc3 = (df["high"] + df["low"] + df["close"]) / 3
    day = pd.Index(df.index.date)
    vol = df["volume"].clip(lower=1e-9)
    pv = (hlc3 * vol).groupby(day).cumsum().to_numpy()
    cv = vol.groupby(day).cumsum().to_numpy()
    return pd.Series(pv / cv, index=df.index)


def htf_trend(entry_index: pd.Index, htf_df: pd.DataFrame) -> pd.Series:
    """HTF EMA20>EMA50 trend yönü, giriş zaman dilimine ffill ile hizalanır.

    +1 = boğa, -1 = ayı, 0 = belirsiz. shift(1) ile o anki HTF mumu
    kapanmadan kullanılmaz (look-ahead yok).
    """
    c = htf_df["close"]
    fast = ema(c, 20)
    slow = ema(c, 50)
    trend = pd.Series(0, index=c.index, dtype=int)
    trend[(c > fast) & (fast > slow)] = 1
    trend[(c < fast) & (fast < slow)] = -1
    trend = trend.shift(1).fillna(0)
    return trend.reindex(entry_index, method="ffill").fillna(0).astype(int)


def swing_high(df: pd.DataFrame, left: int = 3, right: int = 3) -> pd.Series:
    """Fraktal swing high seviyeleri (teyit gecikmesiyle ileri taşınır)."""
    h = df["high"]
    win = left + right + 1
    is_top = h == h.rolling(win, center=True).max()
    # teyit ancak 'right' bar sonra olur -> o kadar kaydır
    levels = h.where(is_top).shift(right)
    return levels.ffill()


def swing_low(df: pd.DataFrame, left: int = 3, right: int = 3) -> pd.Series:
    low = df["low"]
    win = left + right + 1
    is_bot = low == low.rolling(win, center=True).min()
    levels = low.where(is_bot).shift(right)
    return levels.ffill()


def rolling_high(df: pd.DataFrame, n: int) -> pd.Series:
    return df["high"].rolling(n).max().shift(1)


def rolling_low(df: pd.DataFrame, n: int) -> pd.Series:
    return df["low"].rolling(n).min().shift(1)


def prev_day_levels(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Önceki günün high/low seviyeleri (likidite hedefleri)."""
    day = pd.Index(df.index.date)
    daily_high = df["high"].groupby(day).transform("max")
    daily_low = df["low"].groupby(day).transform("min")
    # gün bazında tek değere indir, bir gün kaydır, geri yay
    dh = daily_high.groupby(day).last()
    dl = daily_low.groupby(day).last()
    pdh = dh.shift(1)
    pdl = dl.shift(1)
    date_idx = pd.Index(df.index.date)
    return (
        pd.Series(pdh.reindex(date_idx).to_numpy(), index=df.index),
        pd.Series(pdl.reindex(date_idx).to_numpy(), index=df.index),
    )


def session_mask(index: pd.DatetimeIndex, start_h: int, end_h: int) -> pd.Series:
    """UTC saatine göre likit seans maskesi."""
    h = index.hour
    if start_h <= end_h:
        m = (h >= start_h) & (h < end_h)
    else:  # gece aşırı seans
        m = (h >= start_h) | (h < end_h)
    return pd.Series(m, index=index)


def calc_volume_profile_for_day(day_df: pd.DataFrame, bins: int = 100) -> tuple[float, float, float]:
    """Tek bir günün DataFrame'inden VAH, VAL ve POC hesaplar."""
    if day_df.empty or day_df["volume"].sum() == 0:
        return np.nan, np.nan, np.nan
        
    prices = (day_df["high"] + day_df["low"] + day_df["close"]) / 3
    volumes = day_df["volume"]
    
    # Fiyat aralığını bul
    p_min, p_max = day_df["low"].min(), day_df["high"].max()
    if p_min == p_max:
        return p_min, p_min, p_min
        
    # Fiyat dilimlerini oluştur
    bin_edges = np.linspace(p_min, p_max, bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bin_volumes = np.zeros(bins)
    
    # Hacimleri dilimlere dağıt (hlc3'ün en yakın olduğu dilime)
    for p, v in zip(prices, volumes):
        idx = np.abs(bin_centers - p).argmin()
        bin_volumes[idx] += v
        
    # POC: En yüksek hacimli dilimin fiyatı
    poc_idx = bin_volumes.argmax()
    poc = bin_centers[poc_idx]
    
    # Value Area (%70) hesaplama
    total_volume = bin_volumes.sum()
    va_volume_target = total_volume * 0.70
    
    # POC'den başla, en yüksek hacimli komşuyu ekle
    va_indices = {poc_idx}
    va_volume = bin_volumes[poc_idx]
    
    left = poc_idx - 1
    right = poc_idx + 1
    
    while va_volume < va_volume_target:
        # Sol ve sağ komşuları karşılaştır
        left_vol = bin_volumes[left] if left >= 0 else -1
        right_vol = bin_volumes[right] if right < bins else -1
        
        if left_vol == -1 and right_vol == -1:
            break
            
        if left_vol >= right_vol:
            va_indices.add(left)
            va_volume += left_vol
            left -= 1
        else:
            va_indices.add(right)
            va_volume += right_vol
            right += 1
            
    # VAH ve VAL: Value Area içindeki en yüksek ve en düşük fiyatlar
    va_prices = bin_centers[list(va_indices)]
    val = va_prices.min()
    vah = va_prices.max()
    
    return vah, val, poc


def daily_volume_profile(df: pd.DataFrame, bins: int = 100) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Tüm DataFrame için bir önceki günün VAH, VAL ve POC değerlerini hesaplar.
    Look-ahead bias içermez (her bar için bir önceki güne ait VAH/VAL/POC değerlerini taşır).
    """
    day_groups = df.groupby(df.index.date)
    daily_results = {}
    
    # Her günün kendi profilini hesapla
    for date, group in day_groups:
        vah, val, poc = calc_volume_profile_for_day(group, bins)
        daily_results[date] = (vah, val, poc)
        
    # Günlük sonuçları bir gün kaydır (shift 1)
    sorted_dates = sorted(daily_results.keys())
    shifted_results = {}
    for i in range(len(sorted_dates)):
        current_date = sorted_dates[i]
        if i == 0:
            shifted_results[current_date] = (np.nan, np.nan, np.nan)
        else:
            prev_date = sorted_dates[i - 1]
            shifted_results[current_date] = daily_results[prev_date]
            
    # Sonuçları bar bazında DataFrame'e eşle
    vah_list, val_list, poc_list = [], [], []
    for ts in df.index:
        date = ts.date()
        vah, val, poc = shifted_results.get(date, (np.nan, np.nan, np.nan))
        vah_list.append(vah)
        val_list.append(val)
        poc_list.append(poc)
        
    return (
        pd.Series(vah_list, index=df.index, name="vah"),
        pd.Series(val_list, index=df.index, name="val"),
        pd.Series(poc_list, index=df.index, name="poc")
    )



def adx(df: pd.DataFrame, n: int = 14, shift: int = 1) -> pd.Series:
    """Wilder ADX. Son bar SHIFT'li -- kapanmamis barla karar verilmez.

    `edge_lab._adx`'ten buraya tasindi (2026-09-01): telefon brifingi bunu
    bulutta hesapliyor ve `edge_lab` modul seviyesinde `data` + `honest_engine`
    cekiyor. Ikinci bir kopya yazmak bu projedeki tekrar eden hata olurdu
    (whitelist iki kopya, defterin bes okuyucusu, iki eslestirici), o yuzden
    govdesi tek yerde: edge_lab da artik buradan import ediyor.
    """
    h, lo, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([h - lo, (h - pc).abs(), (lo - pc).abs()], axis=1).max(axis=1)
    dm_p = (h - h.shift(1)).clip(lower=0).where((h - h.shift(1)) > (lo.shift(1) - lo), 0)
    dm_m = (lo.shift(1) - lo).clip(lower=0).where((lo.shift(1) - lo) > (h - h.shift(1)), 0)
    atr_n = tr.ewm(alpha=1 / n, adjust=False).mean()
    di_p = 100 * dm_p.ewm(alpha=1 / n, adjust=False).mean() / atr_n.replace(0, np.nan)
    di_m = 100 * dm_m.ewm(alpha=1 / n, adjust=False).mean() / atr_n.replace(0, np.nan)
    dx = 100 * (di_p - di_m).abs() / (di_p + di_m).replace(0, np.nan)
    sonuc = dx.ewm(alpha=1 / n, adjust=False).mean()
    return sonuc.shift(shift) if shift else sonuc
