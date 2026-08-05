"""Parite Karakter Profilcisi — Adım 1: Betimsel Röntgen (READ-ONLY).

Amaç: "Bu parite ne yapmayı seviyor?" sorusunu HAM VERİDEN ölçmek.
Strateji denemez, modül değiştirmez, hiçbir edge'e dokunmaz. Sadece
her sembolün istatistiksel parmak izini çıkarır.

Ölçülenler (her sembol için, hem tüm dönem hem yıl-yıl):
  1. Saatlik volatilite profili   -> parite hangi UTC saatinde yaşıyor?
  2. Seans drift'i                 -> belirli seansta sistematik yön var mı?
  3. Sweep davranışı (PDH/PDL)     -> likidite alınınca döner mi, devam mı?
  4. ORB takip oranı               -> açılış range kırılımı tutar mı, fake mi?
  5. Mean-reversion yarı ömrü      -> uzaklaşınca kaç barda geri döner? (AR1/OU)
  6. Trend kalıcılığı (Hurst)      -> trendci mi (>0.5) rangeci mi (<0.5)?

Her bulgu ayrıca yıl-yıl (2023/2024/2025+) tekrar hesaplanır: 3/3 yıl
aynı yönde değilse "tutarsız" damgası düşer (gürültü ayıklama).

Kullanım:
    PYTHONPATH=. python -m intraday.pair_profiler
    PYTHONPATH=. python -m intraday.pair_profiler --symbols XAUUSD:5m NASDAQ100:15m
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from .data import load_ohlcv
from .indicators import daily_vwap, prev_day_levels

# Taşıyıcı ikilinin doğal karakter kartı için varsayılan hedefler.
DEFAULT_TARGETS = [("XAUUSD", "5m"), ("NASDAQ100", "15m")]
LOOKBACK = 1080  # ~3 yıl (cache'de mevcut)

# UTC seans pencereleri (kaba, likidite bloklarına göre).
SESSIONS = {
    "Asya (0-7)": (0, 7),
    "Londra (7-13)": (7, 13),
    "NY (13-21)": (13, 21),
    "Geç (21-24)": (21, 24),
}


def _fwd_bars(tf: str) -> int:
    """Sweep/ORB için 'ileriye bakış' penceresi ~ 4 saatlik momentum."""
    return {"5m": 48, "15m": 16, "1H": 4, "4H": 1}[tf]


# ---------------------------------------------------------------------------
# 1. Saatlik volatilite + seans drift
# ---------------------------------------------------------------------------
def hourly_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Her UTC saati için ortalama bar aralığı (bps) ve net drift (bps)."""
    rng_pct = (df["high"] - df["low"]) / df["close"] * 1e4  # bar aralığı, bps
    ret_bps = df["close"].pct_change() * 1e4                # bar getirisi, bps
    h = df.index.hour
    out = pd.DataFrame({
        "range_bps": rng_pct.groupby(h).mean(),
        "drift_bps": ret_bps.groupby(h).mean(),
        "bars": ret_bps.groupby(h).count(),
    })
    out.index.name = "utc_hour"
    return out


def session_drift(df: pd.DataFrame) -> pd.DataFrame:
    """Seans başına net getiri (bps) + tutarlılık (pozitif gün oranı)."""
    ret = df["close"].pct_change().fillna(0.0)
    day = pd.Index(df.index.date)
    rows = {}
    for name, (s, e) in SESSIONS.items():
        mask = (df.index.hour >= s) & (df.index.hour < e)
        sess_ret = ret.where(mask, 0.0)
        by_day = sess_ret.groupby(day).sum()
        by_day = by_day[by_day != 0.0]  # o seansı içermeyen günleri at
        rows[name] = {
            "mean_bps": by_day.mean() * 1e4,
            "up_day_pct": (by_day > 0).mean() * 100,
            "days": len(by_day),
        }
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------------
# 2. Sweep davranışı: PDH/PDL alınınca döner mi devam mı?
# ---------------------------------------------------------------------------
def sweep_behavior(df: pd.DataFrame, tf: str) -> dict:
    """Önceki gün high/low ilk kez süpürülünce ileri N barın davranışı.

    Reversal = süpürülen seviyenin ters tarafına dönüş.
    Continuation = süpürme yönünde devam.
    """
    pdh, pdl = prev_day_levels(df)
    fwd = _fwd_bars(tf)
    close = df["close"].to_numpy()
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    pdh_a = pdh.to_numpy()
    pdl_a = pdl.to_numpy()
    day = np.array([d.toordinal() for d in df.index.date])
    n = len(df)

    up_rev = up_cont = dn_rev = dn_cont = 0
    seen_up = seen_dn = False
    cur_day = -1
    for i in range(n - fwd):
        if day[i] != cur_day:
            cur_day = day[i]
            seen_up = seen_dn = False
        # sweep yukarı: bu gün ilk kez high PDH'yi geçti
        if not seen_up and not np.isnan(pdh_a[i]) and high[i] > pdh_a[i]:
            seen_up = True
            future = close[i + 1: i + 1 + fwd]
            if future[-1] < pdh_a[i]:
                up_rev += 1
            else:
                up_cont += 1
        # sweep aşağı: bu gün ilk kez low PDL'yi kırdı
        if not seen_dn and not np.isnan(pdl_a[i]) and low[i] < pdl_a[i]:
            seen_dn = True
            future = close[i + 1: i + 1 + fwd]
            if future[-1] > pdl_a[i]:
                dn_rev += 1
            else:
                dn_cont += 1

    up_tot = up_rev + up_cont
    dn_tot = dn_rev + dn_cont
    tot = up_tot + dn_tot
    rev = up_rev + dn_rev
    return {
        "sweep_events": tot,
        "reversal_pct": (rev / tot * 100) if tot else np.nan,
        "up_reversal_pct": (up_rev / up_tot * 100) if up_tot else np.nan,
        "dn_reversal_pct": (dn_rev / dn_tot * 100) if dn_tot else np.nan,
    }


# ---------------------------------------------------------------------------
# 3. ORB takip oranı: açılış range kırılımı tutar mı?
# ---------------------------------------------------------------------------
def orb_followthrough(df: pd.DataFrame, tf: str, open_h: int, or_bars: int) -> dict:
    """Seans açılışının ilk `or_bars` barı = opening range.

    Range'in ilk kırılımı, ileri pencere sonunda yönünde mi kaldı (takip)
    yoksa ters tarafa mı döndü (fake)?
    """
    fwd = _fwd_bars(tf)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()
    hours = df.index.hour.to_numpy()
    day = np.array([d.toordinal() for d in df.index.date])
    n = len(df)

    hold = fake = 0
    i = 0
    cur_day = -1
    while i < n - fwd:
        # seans açılış barını yakala (günün open_h'yi gören ilk barı)
        if day[i] != cur_day and hours[i] >= open_h:
            cur_day = day[i]
            if i + or_bars >= n:
                break
            or_hi = high[i: i + or_bars].max()
            or_lo = low[i: i + or_bars].min()
            j = i + or_bars
            broke = 0
            brk_lvl = np.nan
            end = min(j + fwd, n)
            while j < end and broke == 0:
                if high[j] > or_hi:
                    broke, brk_lvl = 1, or_hi
                elif low[j] < or_lo:
                    broke, brk_lvl = -1, or_lo
                j += 1
            if broke != 0:
                final = close[end - 1]
                if broke == 1:
                    hold += 1 if final > brk_lvl else 0
                    fake += 0 if final > brk_lvl else 1
                else:
                    hold += 1 if final < brk_lvl else 0
                    fake += 0 if final < brk_lvl else 1
        i += 1

    tot = hold + fake
    return {
        "orb_days": tot,
        "hold_pct": (hold / tot * 100) if tot else np.nan,
        "fake_pct": (fake / tot * 100) if tot else np.nan,
    }


# ---------------------------------------------------------------------------
# 4. Mean-reversion yarı ömrü (AR1 / Ornstein-Uhlenbeck)
# ---------------------------------------------------------------------------
def mean_reversion_halflife(df: pd.DataFrame) -> float:
    """VWAP'tan sapmanın ortalamaya dönüş yarı ömrü (bar cinsinden).

    Ham fiyat seviyesi durağan değildir (trendli varlıkta AR1 anlamsız,
    yarı ömür sonsuza yakın çıkar). Bunun yerine durağan bir seri olan
    günlük-VWAP'tan sapma (close - vwap) kullanılır:

        delta_d = a + b * d_{t-1} ; b<0 -> sapma VWAP'a geri çekiliyor
        yarı ömür = -ln(2)/ln(1+b)

    Gün sınırları atlanır (VWAP her gün sıfırlanır; gün geçişindeki
    sapma sıçraması AR1'i kirletmesin diye o çiftler dışlanır).
    Küçük yarı ömür = güçlü VWAP mıknatısı, büyük = sapma kalıcı (trendci).
    """
    dev = (df["close"] - daily_vwap(df)).to_numpy()
    same_day = pd.Index(df.index.date).to_numpy()
    ok = ~np.isnan(dev)
    # ardışık çift (t-1, t) aynı güne aitse ve ikisi de geçerliyse kullan
    pair_ok = ok[:-1] & ok[1:] & (same_day[:-1] == same_day[1:])
    lag = dev[:-1][pair_ok]
    delta = (dev[1:] - dev[:-1])[pair_ok]
    if len(lag) < 100:
        return np.nan
    lag_c = lag - lag.mean()
    denom = np.dot(lag_c, lag_c)
    if denom == 0:
        return np.inf
    b = np.dot(lag_c, delta - delta.mean()) / denom
    if b >= 0 or b <= -1:
        return np.inf if b >= 0 else 1.0
    return float(-np.log(2) / np.log(1 + b))


# ---------------------------------------------------------------------------
# 5. Hurst üssü (trendci vs rangeci)
# ---------------------------------------------------------------------------
def hurst_exponent(df: pd.DataFrame, max_lag: int = 100) -> float:
    """Toplam-varyans yöntemiyle Hurst. >0.5 trendci, <0.5 mean-reverting."""
    ts = np.log(df["close"].to_numpy())
    lags = list(range(2, max_lag))
    tau = np.array([np.std(ts[lag:] - ts[:-lag]) for lag in lags])
    good = tau > 0
    if good.sum() < 5:
        return np.nan
    poly = np.polyfit(np.log(np.array(lags)[good]), np.log(tau[good]), 1)
    return float(poly[0])


# ---------------------------------------------------------------------------
# Yıl-yıl tutarlılık sarmalayıcı
# ---------------------------------------------------------------------------
def by_year(df: pd.DataFrame, fn):
    out = {}
    for yr, chunk in df.groupby(df.index.year):
        if len(chunk) < 500:
            continue
        out[yr] = fn(chunk)
    return out


def _consistency(vals: list, threshold: float) -> str:
    """Tüm yıllar eşiğin aynı tarafında mı? Tutarlılık damgası."""
    if not vals or any(np.isnan(v) for v in vals):
        return "[veri eksik]"
    above = [v > threshold for v in vals]
    if all(above) or not any(above):
        return "TUTARLI (tum yillar ayni taraf)"
    return "TUTARSIZ (yillar ayrisiyor - gurultu suphesi)"


# ---------------------------------------------------------------------------
# Kimlik kartı yazıcı
# ---------------------------------------------------------------------------
def profile_symbol(symbol: str, tf: str) -> None:
    df = load_ohlcv(symbol, tf, LOOKBACK)
    print("=" * 68)
    print(f"  KIMLIK KARTI: {symbol} {tf}  ({len(df)} bar, "
          f"{df.index[0].date()} -> {df.index[-1].date()})")
    print("=" * 68)

    # 1. Saatlik profil — en canlı 5 saat
    hp = hourly_profile(df)
    top = hp.sort_values("range_bps", ascending=False).head(5)
    print("\n[1] SAATLIK VOLATILITE - parite hangi saatte yasiyor? (UTC)")
    print("    en hareketli 5 saat (bar araligi, bps):")
    for h, row in top.iterrows():
        print(f"      {h:02d}:00 UTC  range={row['range_bps']:6.1f} bps  "
              f"drift={row['drift_bps']:+6.2f} bps")

    # 2. Seans drift
    sd = session_drift(df)
    print("\n[2] SEANS DRIFT - sistematik yon var mi?")
    for name, row in sd.iterrows():
        flag = "<-- DIKKAT" if row["up_day_pct"] > 55 or row["up_day_pct"] < 45 else ""
        print(f"      {name:16s} ort={row['mean_bps']:+6.1f}bps  "
              f"yukari-gun={row['up_day_pct']:4.1f}%  (n={int(row['days'])}) {flag}")

    # 3. Sweep davranışı + yıl-yıl
    sw = sweep_behavior(df, tf)
    sw_yr = by_year(df, lambda c: sweep_behavior(c, tf))
    yr_rev = [round(v["reversal_pct"], 1) for v in sw_yr.values()]
    print("\n[3] SWEEP (PDH/PDL) - likidite alininca doner mi devam mi?")
    print(f"      olay={sw['sweep_events']}  REVERSAL={sw['reversal_pct']:.1f}%  "
          f"(devam={100 - sw['reversal_pct']:.1f}%)")
    print(f"      up-sweep reversal={sw['up_reversal_pct']:.1f}%  "
          f"dn-sweep reversal={sw['dn_reversal_pct']:.1f}%")
    print(f"      yil-yil reversal%: {dict(zip(sw_yr.keys(), yr_rev))}  "
          f"{_consistency(yr_rev, 50)}")

    # 4. ORB takip — NY açılışı (13 UTC) baz alınır
    open_h = 13
    or_bars = {"5m": 6, "15m": 2, "1H": 1, "4H": 1}[tf]
    orb = orb_followthrough(df, tf, open_h, or_bars)
    orb_yr = by_year(df, lambda c: orb_followthrough(c, tf, open_h, or_bars))
    yr_hold = [round(v["hold_pct"], 1) for v in orb_yr.values()]
    print("\n[4] ORB TAKIP - NY acilis (13 UTC) range kirilimi tutar mi?")
    print(f"      gun={orb['orb_days']}  TAKIP={orb['hold_pct']:.1f}%  "
          f"fake={orb['fake_pct']:.1f}%")
    print(f"      yil-yil takip%: {dict(zip(orb_yr.keys(), yr_hold))}  "
          f"{_consistency(yr_hold, 50)}")

    # 5. Mean-reversion yarı ömrü
    hl = mean_reversion_halflife(df)
    hl_yr = by_year(df, mean_reversion_halflife)
    hl_str = "sonsuz (donmuyor=trendci)" if np.isinf(hl) else f"{hl:.1f} bar"
    print(f"\n[5] VWAP SAPMASI YARI OMRU (mean-reversion): {hl_str}")
    print(f"      yil-yil: {{{', '.join(f'{k}:{v:.1f}' for k, v in hl_yr.items())}}}")

    # 6. Hurst
    hu = hurst_exponent(df)
    hu_yr = by_year(df, hurst_exponent)
    tag = "TRENDCI" if hu > 0.52 else ("RANGECI" if hu < 0.48 else "NOTR")
    print(f"\n[6] HURST USSU: {hu:.3f}  -> {tag}")
    print(f"      yil-yil: {{{', '.join(f'{k}:{v:.3f}' for k, v in hu_yr.items())}}}")
    print()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=None,
                    help="format SEMBOL:TF, orn XAUUSD:5m NASDAQ100:15m")
    args = ap.parse_args()
    targets = DEFAULT_TARGETS
    if args.symbols:
        targets = [tuple(s.split(":")) for s in args.symbols]
    for sym, tf in targets:
        profile_symbol(sym, tf)


if __name__ == "__main__":
    main()
