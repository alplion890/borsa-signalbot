"""Likidite Karakter Haritası — paranın nereye çekildiğini ölçer (READ-ONLY).

Amaç: her paritede smart money'nin AYAK İZLERİNİ ölçmek. Niyet ölçülemez;
fiyatın hangi likidite havuzuna, hangi saatte, ne sıklıkla gittiği ve
varınca ne yaptığı ölçülür. Sadece keskin matematiksel tanımlar kullanılır
(sübjektif order block çizimi yok). Hiçbir modüle dokunmaz.

Ölçümler (her sembol, 15m, ~3 yıl, yıl-yıl tutarlılık damgalı):
  A. Mıknatıs seviyeler — PDH/PDL/PWH/PWL/Asya-range vurulma oranları
  B. AMD / Power-of-3 — Londra Asya'yı süpürüp tersine mi gidiyor?
  C. Equal highs/lows avı — çift tepe/dip kaç barda alınıyor, sonra ne oluyor?
  D. FVG doldurma — 3-mum imbalance ne oranda, kaç barda dolduruluyor?
  E. Seans devir haritası — günün high/low'u hangi saatte oluşuyor?
  F. İlk hedef — gün önce PDH'ye mi PDL'ye mi gidiyor, dünün yönü bias mı?
  G. VWAP + EMA20/50 yaklaşımı — trend içinde bu değerlere düşüş alınıyor mu?

Kullanım:
    PYTHONPATH=. python -m intraday.liquidity_profiler
    PYTHONPATH=. python -m intraday.liquidity_profiler --symbols USDJPY GBPJPY
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from .data import load_ohlcv
from .indicators import atr, daily_vwap, ema, prev_day_levels

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday"

DEFAULT_SYMBOLS = ["XAUUSD", "NASDAQ100", "EURUSD", "GBPUSD",
                   "USDJPY", "EURJPY", "GBPJPY", "AUDUSD", "USDCAD", "USDCHF"]
TF = "15m"
LOOKBACK = 1080
FWD = 16          # olay sonrası izleme penceresi (15m -> 4 saat)
ASIA = (0, 7)     # UTC
LONDON = (7, 13)
NY = (13, 21)


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------
def _day_groups(df: pd.DataFrame):
    return df.groupby(pd.Index(df.index.date))


def _prev_week_levels(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Önceki ISO haftasının high/low'u, bar bazına yayılmış."""
    wk = df.index.to_period("W")
    wh = df["high"].groupby(wk).max()
    wl = df["low"].groupby(wk).min()
    pwh = wh.shift(1).reindex(wk).to_numpy()
    pwl = wl.shift(1).reindex(wk).to_numpy()
    return (pd.Series(pwh, index=df.index), pd.Series(pwl, index=df.index))


def _consistency(vals: list, threshold: float) -> str:
    vals = [v for v in vals if not (v is None or np.isnan(v))]
    if len(vals) < 3:
        return "[<3 yil]"
    above = [v > threshold for v in vals]
    if all(above) or not any(above):
        return "TUTARLI"
    return "tutarsiz"


def by_year(df: pd.DataFrame, fn):
    out = {}
    for yr, chunk in df.groupby(df.index.year):
        if len(chunk) < 3000:  # ~1.5 aydan kısa yıl parçalarını atla
            continue
        out[yr] = fn(chunk)
    return out


# ---------------------------------------------------------------------------
# A. Mıknatıs seviyeler — vurulma oranı + vurulma saati
# ---------------------------------------------------------------------------
def magnet_levels(df: pd.DataFrame) -> dict:
    pdh, pdl = prev_day_levels(df)
    pwh, pwl = _prev_week_levels(df)
    hrs = df.index.hour

    res = {}
    for name, level, side in (("PDH", pdh, "up"), ("PDL", pdl, "dn"),
                              ("PWH", pwh, "up"), ("PWL", pwl, "dn")):
        hit_days = 0
        tot_days = 0
        hit_hours = []
        lv = level.to_numpy()
        hi = df["high"].to_numpy()
        lo = df["low"].to_numpy()
        day = pd.Index(df.index.date)
        for d, idx in df.groupby(day).indices.items():
            l0 = lv[idx[0]]
            if np.isnan(l0):
                continue
            tot_days += 1
            if side == "up":
                mask = hi[idx] >= l0
            else:
                mask = lo[idx] <= l0
            if mask.any():
                hit_days += 1
                hit_hours.append(hrs[idx[np.argmax(mask)]])
        if tot_days:
            hh = pd.Series(hit_hours)
            res[name] = {
                "hit_pct": hit_days / tot_days * 100,
                "peak_hour": int(hh.mode().iloc[0]) if len(hh) else -1,
            }
    # Asya range uçları: Londra+NY (7-21) içinde vurulma
    asia_hit_h = asia_hit_l = asia_days = 0
    for d, g in _day_groups(df):
        a = g[(g.index.hour >= ASIA[0]) & (g.index.hour < ASIA[1])]
        rest = g[(g.index.hour >= LONDON[0]) & (g.index.hour < NY[1])]
        if len(a) < 8 or len(rest) < 8:
            continue
        asia_days += 1
        if rest["high"].max() >= a["high"].max():
            asia_hit_h += 1
        if rest["low"].min() <= a["low"].min():
            asia_hit_l += 1
    if asia_days:
        res["AsiaH"] = {"hit_pct": asia_hit_h / asia_days * 100, "peak_hour": -1}
        res["AsiaL"] = {"hit_pct": asia_hit_l / asia_days * 100, "peak_hour": -1}
    return res


# ---------------------------------------------------------------------------
# B. AMD / Power-of-3
# ---------------------------------------------------------------------------
def amd_cycle(df: pd.DataFrame) -> dict:
    """Londra tek taraf süpürme oranı + süpürme sonrası günün ters kapanması."""
    one_side = both = none = 0
    manip = 0        # tek taraf süpürüldü VE gün ters yönde kapandı
    ny_follow = 0    # NY, Londra'nın net yönünü sürdürdü
    ny_tot = 0
    days = 0
    for d, g in _day_groups(df):
        a = g[(g.index.hour >= ASIA[0]) & (g.index.hour < ASIA[1])]
        lon = g[(g.index.hour >= LONDON[0]) & (g.index.hour < LONDON[1])]
        ny = g[(g.index.hour >= NY[0]) & (g.index.hour < NY[1])]
        if len(a) < 8 or len(lon) < 8 or len(ny) < 8:
            continue
        days += 1
        ah, al = a["high"].max(), a["low"].min()
        swept_up = lon["high"].max() > ah
        swept_dn = lon["low"].min() < al
        if swept_up and swept_dn:
            both += 1
        elif not swept_up and not swept_dn:
            none += 1
        else:
            one_side += 1
            day_close = g["close"].iloc[-1]
            mid = (ah + al) / 2
            # manipülasyon: yukarı süpürüp altta kapanış (veya tersi)
            if swept_up and day_close < mid:
                manip += 1
            if swept_dn and day_close > mid:
                manip += 1
        # NY devamı: Londra net yönü vs NY net yönü
        lon_dir = np.sign(lon["close"].iloc[-1] - lon["open"].iloc[0])
        ny_dir = np.sign(ny["close"].iloc[-1] - ny["open"].iloc[0])
        if lon_dir != 0 and ny_dir != 0:
            ny_tot += 1
            if lon_dir == ny_dir:
                ny_follow += 1
    return {
        "days": days,
        "london_one_side_pct": one_side / days * 100 if days else np.nan,
        "manip_pct": manip / one_side * 100 if one_side else np.nan,
        "ny_follows_london_pct": ny_follow / ny_tot * 100 if ny_tot else np.nan,
    }


# ---------------------------------------------------------------------------
# C. Equal highs / lows avı
# ---------------------------------------------------------------------------
def equal_levels_hunt(df: pd.DataFrame, tol_atr: float = 0.10,
                      lookback: int = 96, max_wait: int = 480) -> dict:
    """Çift tepe (equal highs) tespiti: iki swing high ATR toleransında eşit.

    Oluştuktan sonra kaç barda 'alınıyor' (raid) ve raid sonrası FWD bar
    içinde dönüş mü devam mı?
    """
    a = atr(df, 14).to_numpy()
    hi = df["high"].to_numpy()
    lo = df["low"].to_numpy()
    cl = df["close"].to_numpy()
    n = len(df)
    # basit swing: 3 sol 3 sağ fraktal
    sw_hi = np.zeros(n, dtype=bool)
    sw_lo = np.zeros(n, dtype=bool)
    for i in range(3, n - 3):
        if hi[i] == hi[i - 3:i + 4].max():
            sw_hi[i] = True
        if lo[i] == lo[i - 3:i + 4].min():
            sw_lo[i] = True

    def _hunt(idx_swings, level_arr, is_high: bool):
        events = raided = reversed_ = 0
        wait_bars = []
        swings = list(np.where(idx_swings)[0])
        for k in range(1, len(swings)):
            i2 = swings[k]
            # geriye bak: lookback içinde toleransta eş swing var mı
            for j in range(k - 1, -1, -1):
                i1 = swings[j]
                if i2 - i1 > lookback:
                    break
                tol = tol_atr * a[i2]
                if abs(level_arr[i2] - level_arr[i1]) <= tol:
                    # arada seviye kırılmamış olmalı
                    lvl = max(level_arr[i1], level_arr[i2]) if is_high else \
                          min(level_arr[i1], level_arr[i2])
                    between = level_arr[i1 + 1:i2]
                    if is_high and (between > lvl).any():
                        continue
                    if not is_high and (between < lvl).any():
                        continue
                    events += 1
                    # raid ara (teyit gecikmesi: fraktal +3 bar sonra kesinleşir)
                    end = min(i2 + 3 + max_wait, n)
                    seg_hi = hi[i2 + 3:end]
                    seg_lo = lo[i2 + 3:end]
                    if is_high:
                        w = np.argmax(seg_hi > lvl) if (seg_hi > lvl).any() else -1
                    else:
                        w = np.argmax(seg_lo < lvl) if (seg_lo < lvl).any() else -1
                    if w >= 0:
                        raided += 1
                        wait_bars.append(w)
                        ri = i2 + 3 + w
                        fe = min(ri + FWD, n) - 1
                        if is_high and cl[fe] < lvl:
                            reversed_ += 1
                        if not is_high and cl[fe] > lvl:
                            reversed_ += 1
                    break
        return events, raided, reversed_, wait_bars

    eh_ev, eh_raid, eh_rev, eh_wait = _hunt(sw_hi, hi, True)
    el_ev, el_raid, el_rev, el_wait = _hunt(sw_lo, lo, False)
    ev = eh_ev + el_ev
    raid = eh_raid + el_raid
    rev = eh_rev + el_rev
    waits = eh_wait + el_wait
    return {
        "eq_events": ev,
        "raid_pct": raid / ev * 100 if ev else np.nan,
        "median_wait_bars": float(np.median(waits)) if waits else np.nan,
        "post_raid_reversal_pct": rev / raid * 100 if raid else np.nan,
    }


# ---------------------------------------------------------------------------
# D. FVG doldurma (keskin 3-mum tanımı)
# ---------------------------------------------------------------------------
def fvg_fill(df: pd.DataFrame, min_atr: float = 0.30, horizon: int = 96) -> dict:
    """Bullish FVG: low[i] > high[i-2] (boşluk). Bearish simetrik.

    Sadece anlamlı boşluklar (>= min_atr x ATR). Doldurma: fiyatın boşluğun
    başlangıç sınırına geri dönmesi. horizon = 1 gün (96 x 15m).
    """
    a = atr(df, 14).to_numpy()
    hi = df["high"].to_numpy()
    lo = df["low"].to_numpy()
    n = len(df)
    tot = filled = 0
    fill_bars = []
    for i in range(2, n):
        gap_up = lo[i] - hi[i - 2]
        gap_dn = lo[i - 2] - hi[i]
        if gap_up > min_atr * a[i]:
            tot += 1
            end = min(i + 1 + horizon, n)
            seg = lo[i + 1:end]
            w = np.argmax(seg <= hi[i - 2]) if (seg <= hi[i - 2]).any() else -1
            if w >= 0:
                filled += 1
                fill_bars.append(w)
        elif gap_dn > min_atr * a[i]:
            tot += 1
            end = min(i + 1 + horizon, n)
            seg = hi[i + 1:end]
            w = np.argmax(seg >= lo[i - 2]) if (seg >= lo[i - 2]).any() else -1
            if w >= 0:
                filled += 1
                fill_bars.append(w)
    return {
        "fvg_count": tot,
        "fill_pct_1d": filled / tot * 100 if tot else np.nan,
        "median_fill_bars": float(np.median(fill_bars)) if fill_bars else np.nan,
    }


# ---------------------------------------------------------------------------
# E. Seans devir haritası — günün high/low'u hangi saatte?
# ---------------------------------------------------------------------------
def day_extreme_hours(df: pd.DataFrame) -> dict:
    hi_hours, lo_hours = [], []
    for d, g in _day_groups(df):
        if len(g) < 48:
            continue
        hi_hours.append(g["high"].idxmax().hour)
        lo_hours.append(g["low"].idxmin().hour)
    hh = pd.Series(hi_hours).value_counts(normalize=True) * 100
    ll = pd.Series(lo_hours).value_counts(normalize=True) * 100

    def _sess_share(s):
        asia = s[(s.index >= ASIA[0]) & (s.index < ASIA[1])].sum()
        lon = s[(s.index >= LONDON[0]) & (s.index < LONDON[1])].sum()
        ny = s[(s.index >= NY[0]) & (s.index < NY[1])].sum()
        return asia, lon, ny

    ha, hl_, hn = _sess_share(hh)
    la, ll_, ln = _sess_share(ll)
    return {
        "high_asia_pct": ha, "high_london_pct": hl_, "high_ny_pct": hn,
        "low_asia_pct": la, "low_london_pct": ll_, "low_ny_pct": ln,
        "top_high_hours": list(hh.head(2).index), "top_low_hours": list(ll.head(2).index),
    }


# ---------------------------------------------------------------------------
# F. İlk hedef — önce PDH mi PDL mi?
# ---------------------------------------------------------------------------
def first_target(df: pd.DataFrame) -> dict:
    pdh, pdl = prev_day_levels(df)
    lv_h = pdh.to_numpy()
    lv_l = pdl.to_numpy()
    hi = df["high"].to_numpy()
    lo = df["low"].to_numpy()
    day = pd.Index(df.index.date)
    cl = df["close"].to_numpy()

    first_h = first_l = 0
    cont = tot_cond = 0  # dünün yönü -> bugün ilk hedef aynı yönde mi
    groups = df.groupby(day).indices
    dates = sorted(groups.keys())
    prev_dir = {}
    for d in dates:
        idx = groups[d]
        prev_dir[d] = np.sign(cl[idx[-1]] - cl[idx[0]])
    for k, d in enumerate(dates):
        idx = groups[d]
        h0, l0 = lv_h[idx[0]], lv_l[idx[0]]
        if np.isnan(h0) or np.isnan(l0):
            continue
        th = np.argmax(hi[idx] >= h0) if (hi[idx] >= h0).any() else 10 ** 9
        tl = np.argmax(lo[idx] <= l0) if (lo[idx] <= l0).any() else 10 ** 9
        if th == tl:
            continue
        went_up = th < tl
        if went_up:
            first_h += 1
        else:
            first_l += 1
        if k > 0:
            pdir = prev_dir[dates[k - 1]]
            if pdir != 0:
                tot_cond += 1
                if (pdir > 0 and went_up) or (pdir < 0 and not went_up):
                    cont += 1
    tot = first_h + first_l
    return {
        "days_with_target": tot,
        "first_pdh_pct": first_h / tot * 100 if tot else np.nan,
        "prevday_continuation_pct": cont / tot_cond * 100 if tot_cond else np.nan,
    }


# ---------------------------------------------------------------------------
# G. VWAP + EMA20/50 yaklaşım davranışı (kullanıcı eklemesi)
# ---------------------------------------------------------------------------
def value_touch_behavior(df: pd.DataFrame) -> dict:
    """Trend içinde fiyat değer bölgesine (EMA20/EMA50/VWAP) düşünce ne olur?

    Uptrend tanımı: EMA20 > EMA50 ve kapanış EMA20 üstü (bir önceki bar
    itibarıyla, look-ahead yok). Dokunuş: bar'ın low'u seviyeye değdi.
    Sıçrama: FWD bar içinde dokunuş barının high'ının üstünde kapanış,
    ÖNCE EMA50'nin (0.5 ATR payla) altında kapanış OLMADAN.
    Downtrend simetrik. Oranlar iki yön birleşik.
    """
    e20 = ema(df["close"], 20).to_numpy()
    e50 = ema(df["close"], 50).to_numpy()
    vw = daily_vwap(df).to_numpy()
    a = atr(df, 14).to_numpy()
    hi = df["high"].to_numpy()
    lo = df["low"].to_numpy()
    cl = df["close"].to_numpy()
    n = len(df)
    up = np.zeros(n, dtype=bool)
    dn = np.zeros(n, dtype=bool)
    up[1:] = (e20[:-1] > e50[:-1]) & (cl[:-1] > e20[:-1])
    dn[1:] = (e20[:-1] < e50[:-1]) & (cl[:-1] < e20[:-1])

    def _events(level: np.ndarray, fail_level: np.ndarray):
        """(dokunuş, sıçrama) sayıları — up+down birleşik."""
        touch = bounce = 0
        i = 1
        while i < n - FWD:
            hit_up = up[i] and lo[i] <= level[i] and not np.isnan(level[i])
            hit_dn = dn[i] and hi[i] >= level[i] and not np.isnan(level[i])
            if hit_up or hit_dn:
                touch += 1
                ok = False
                for j in range(i + 1, i + 1 + FWD):
                    if hit_up:
                        if cl[j] < fail_level[j] - 0.5 * a[j]:
                            break
                        if cl[j] > hi[i]:
                            ok = True
                            break
                    else:
                        if cl[j] > fail_level[j] + 0.5 * a[j]:
                            break
                        if cl[j] < lo[i]:
                            ok = True
                            break
                bounce += 1 if ok else 0
                i += 4  # aynı dokunuşu tekrar sayma
            else:
                i += 1
        return touch, bounce

    out = {}
    for name, lvl in (("EMA20", e20), ("EMA50", e50), ("VWAP", vw)):
        t, b = _events(lvl, e50)
        out[f"{name}_touches"] = t
        out[f"{name}_bounce_pct"] = b / t * 100 if t else np.nan
    return out


# ---------------------------------------------------------------------------
# Kart + CSV
# ---------------------------------------------------------------------------
def profile(symbol: str) -> list[dict]:
    df = load_ohlcv(symbol, TF, LOOKBACK)
    rows = []
    print("=" * 72)
    print(f"  LIKIDITE KARTI: {symbol} {TF}  ({len(df)} bar, "
          f"{df.index[0].date()} -> {df.index[-1].date()})")
    print("=" * 72)

    # A
    mg = magnet_levels(df)
    print("\n[A] MIKNATIS SEVIYELER (gunluk vurulma orani):")
    for k, v in mg.items():
        ph = f" tepe-saat={v['peak_hour']:02d}UTC" if v["peak_hour"] >= 0 else ""
        print(f"      {k:6s} vurulma={v['hit_pct']:5.1f}%{ph}")
        rows.append({"symbol": symbol, "metric": f"magnet_{k}_hit_pct",
                     "value": round(v["hit_pct"], 1), "yearly": "", "consistent": ""})

    # B
    amd = amd_cycle(df)
    amd_yr = by_year(df, amd_cycle)
    manip_yr = [round(v["manip_pct"], 1) for v in amd_yr.values()]
    c_b = _consistency(manip_yr, 50)
    print(f"\n[B] AMD/PO3: Londra tek-taraf supurme={amd['london_one_side_pct']:.1f}% "
          f"| supurme sonrasi TERS kapanis={amd['manip_pct']:.1f}% "
          f"| NY Londra'yi surdurme={amd['ny_follows_london_pct']:.1f}%")
    print(f"      yil-yil manip%: {dict(zip(amd_yr.keys(), manip_yr))} [{c_b}]")
    rows.append({"symbol": symbol, "metric": "amd_manip_pct",
                 "value": round(amd["manip_pct"], 1),
                 "yearly": str(manip_yr), "consistent": c_b})
    rows.append({"symbol": symbol, "metric": "ny_follows_london_pct",
                 "value": round(amd["ny_follows_london_pct"], 1), "yearly": "", "consistent": ""})

    # C
    eq = equal_levels_hunt(df)
    eq_yr = by_year(df, equal_levels_hunt)
    rev_yr = [round(v["post_raid_reversal_pct"], 1) for v in eq_yr.values()]
    c_c = _consistency(rev_yr, 50)
    print(f"\n[C] EQUAL H/L AVI: olay={eq['eq_events']} raid={eq['raid_pct']:.1f}% "
          f"medyan-bekleme={eq['median_wait_bars']:.0f} bar "
          f"| raid sonrasi DONUS={eq['post_raid_reversal_pct']:.1f}%")
    print(f"      yil-yil donus%: {dict(zip(eq_yr.keys(), rev_yr))} [{c_c}]")
    rows.append({"symbol": symbol, "metric": "eq_raid_reversal_pct",
                 "value": round(eq["post_raid_reversal_pct"], 1),
                 "yearly": str(rev_yr), "consistent": c_c})

    # D
    fv = fvg_fill(df)
    fv_yr = by_year(df, fvg_fill)
    fill_yr = [round(v["fill_pct_1d"], 1) for v in fv_yr.values()]
    c_d = _consistency(fill_yr, 50)
    print(f"\n[D] FVG DOLDURMA: adet={fv['fvg_count']} "
          f"1-gun-icinde-dolan={fv['fill_pct_1d']:.1f}% "
          f"medyan={fv['median_fill_bars']:.0f} bar")
    print(f"      yil-yil dolum%: {dict(zip(fv_yr.keys(), fill_yr))} [{c_d}]")
    rows.append({"symbol": symbol, "metric": "fvg_fill_pct_1d",
                 "value": round(fv["fill_pct_1d"], 1),
                 "yearly": str(fill_yr), "consistent": c_d})

    # E
    ex = day_extreme_hours(df)
    print("\n[E] GUNUN UCLARI HANGI SEANSTA?")
    print(f"      HIGH: asya={ex['high_asia_pct']:.0f}% londra={ex['high_london_pct']:.0f}% "
          f"ny={ex['high_ny_pct']:.0f}%  (tepe saatler {ex['top_high_hours']})")
    print(f"      LOW : asya={ex['low_asia_pct']:.0f}% londra={ex['low_london_pct']:.0f}% "
          f"ny={ex['low_ny_pct']:.0f}%  (tepe saatler {ex['top_low_hours']})")
    rows.append({"symbol": symbol, "metric": "day_high_ny_pct",
                 "value": round(ex["high_ny_pct"], 1), "yearly": "", "consistent": ""})

    # F
    ft = first_target(df)
    ft_yr = by_year(df, first_target)
    cont_yr = [round(v["prevday_continuation_pct"], 1) for v in ft_yr.values()]
    c_f = _consistency(cont_yr, 50)
    print(f"\n[F] ILK HEDEF: once-PDH={ft['first_pdh_pct']:.1f}% "
          f"| dunun yonunde devam={ft['prevday_continuation_pct']:.1f}%")
    print(f"      yil-yil devam%: {dict(zip(ft_yr.keys(), cont_yr))} [{c_f}]")
    rows.append({"symbol": symbol, "metric": "prevday_continuation_pct",
                 "value": round(ft["prevday_continuation_pct"], 1),
                 "yearly": str(cont_yr), "consistent": c_f})

    # G
    vt = value_touch_behavior(df)
    vt_yr = by_year(df, value_touch_behavior)
    print("\n[G] DEGER DOKUNUSU (trend icinde geri cekilme alinir mi?):")
    for name in ("EMA20", "EMA50", "VWAP"):
        yr_vals = [round(v[f"{name}_bounce_pct"], 1) for v in vt_yr.values()]
        c_g = _consistency(yr_vals, 50)
        print(f"      {name:6s} dokunus={vt[f'{name}_touches']:5d} "
              f"sicrama={vt[f'{name}_bounce_pct']:5.1f}%  "
              f"yil-yil {dict(zip(vt_yr.keys(), yr_vals))} [{c_g}]")
        rows.append({"symbol": symbol, "metric": f"{name}_bounce_pct",
                     "value": round(vt[f"{name}_bounce_pct"], 1),
                     "yearly": str(yr_vals), "consistent": c_g})
    print()
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=DEFAULT_SYMBOLS)
    args = ap.parse_args()
    all_rows = []
    for sym in args.symbols:
        try:
            all_rows.extend(profile(sym))
        except Exception as e:
            print(f"  {sym}: HATA {type(e).__name__}: {e}")
    out = OUT / "liquidity_profiles.csv"
    pd.DataFrame(all_rows).to_csv(out, index=False)
    print(f"CSV: {out}")


if __name__ == "__main__":
    main()
