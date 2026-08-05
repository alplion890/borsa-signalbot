"""A/B: NQ_ORB kanitli motorunda TP kaynagini degistir.

Kathy Lien videosunun tek test edilebilir onerisi: "yonu kendi setup'inla
bul, TP'yi onceki gunun high/low'u yap." Inside-day filtresi sahte cikti
(bkz inside_day_lab.py) ama bu TP fikri ayri ve bagimsiz bir soru.

Ayni giris/SL (NQ_ORB kanitli konfigurasyon: NASDAQ100 ORB open=14.5
range=15 retest none rr=1.5 sl=other_side hold=48, adx>30 strong_trend
filtresi), iki TP varyanti:
  BASELINE : entry + rr * risk           (mevcut sabit-RR motor)
  PRIOR_DL : onceki takvim gununun high/low'u (Kathy Lien tarzi hedef)
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from . import data
from .config import INSTRUMENTS
from .edge_lab import _adx
from .honest_engine import simulate_trades, metrics, oos_metrics
from .internet_seed_strategies import ORBCase, _build_orb

SYMBOL = "NASDAQ100"
DAYS = 1080
CASE = ORBCase(SYMBOL, 14.5, 15, 20.5, "retest", "none", 1.5, "other_side", 1.0, 48)
ADX_MIN = 30.0   # strong_trend rejimi (kanitli filtre)


def make_folds(idx: pd.DatetimeIndex, n: int = 6):
    edges = pd.date_range(idx.min(), idx.max(), periods=n + 1)
    return [(edges[i], edges[i], edges[i], edges[i + 1]) for i in range(n)]


def prior_day_levels(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Onceki takvim gununun high/low'u, gun ici her bara ffill."""
    day = pd.Index(df.index.date)
    day_high = df["high"].groupby(day).transform("max")
    day_low = df["low"].groupby(day).transform("min")
    # onceki GUN'un degeri: gunluk ozet cikar, 1 kaydir, geri genislet
    daily = pd.DataFrame({"high": day_high, "low": day_low}, index=df.index)
    daily["day"] = day
    once = daily.drop_duplicates("day").set_index("day")
    prev = once.shift(1)
    prev_high = pd.Series(day, index=df.index).map(prev["high"])
    prev_low = pd.Series(day, index=df.index).map(prev["low"])
    return prev_high, prev_low


def run() -> None:
    instrument = INSTRUMENTS[SYMBOL]
    df = data.load_ohlcv(SYMBOL, "5m", DAYS)
    le, se, lsl, ltp_base, ssl, stp_base = _build_orb(df, CASE)

    adx = _adx(df, 14)
    regime_ok = adx > ADX_MIN
    le = le & regime_ok
    se = se & regime_ok

    prev_high, prev_low = prior_day_levels(df)
    entry = df["close"]

    # PRIOR_DL: TP = onceki gunun karsi seviyesi (long -> prev_high, short -> prev_low)
    # Yapisal olarak anlamsiz olabilir (TP entry'nin altinda kalabilir) -> NaN ile ele
    ltp_pd = prev_high.where(le & (prev_high > entry))
    stp_pd = prev_low.where(se & (prev_low < entry))

    le_pd = le & ltp_pd.notna()
    se_pd = se & stp_pd.notna()

    folds = make_folds(df.index)

    print(f"\n=== NQ_ORB A/B: TP kaynagi (kanitli giris/SL sabit, ADX>{ADX_MIN}) ===")
    print(f"{'varyant':<28} {'islem':>6} {'exp_R':>7} {'win%':>6} {'PF':>6} "
          f"{'OOS_R':>7} {'fold+':>6} {'top_R':>7}")

    r_base = simulate_trades(df, le, se, lsl, ltp_base, ssl, stp_base, instrument,
                              min_rr=0.5, max_rr=10.0, max_hold=CASE.max_hold)
    m_base = metrics(r_base)
    o_base = oos_metrics(r_base, folds) if len(r_base) else {}
    m_base.update(o_base)
    print(f"{'BASELINE (sabit 1.5R)':<28} {m_base['trades']:>6} {m_base['exp_r']:>7.3f} "
          f"{m_base['win_rate']:>6.1f} {m_base['pf']:>6.2f} "
          f"{m_base.get('oos_exp_r', np.nan):>7.3f} {str(m_base.get('pos_folds','-')):>6} "
          f"{m_base.get('total_R', 0):>7.1f}")

    r_pd = simulate_trades(df, le_pd, se_pd, lsl, ltp_pd, ssl, stp_pd, instrument,
                            min_rr=0.1, max_rr=10.0, max_hold=CASE.max_hold)
    m_pd = metrics(r_pd)
    o_pd = oos_metrics(r_pd, folds) if len(r_pd) else {}
    m_pd.update(o_pd)
    print(f"{'PRIOR_DAY_HL (Kathy Lien)':<28} {m_pd['trades']:>6} {m_pd['exp_r']:>7.3f} "
          f"{m_pd['win_rate']:>6.1f} {m_pd['pf']:>6.2f} "
          f"{m_pd.get('oos_exp_r', np.nan):>7.3f} {str(m_pd.get('pos_folds','-')):>6} "
          f"{m_pd.get('total_R', 0):>7.1f}")

    print(f"\n  Not: PRIOR_DL, TP yapisal olarak entry'nin yanlis tarafinda kaldiginda\n"
          f"  ({le.sum() + se.sum() - le_pd.sum() - se_pd.sum()} / {le.sum() + se.sum()} sinyal)\n"
          f"  o islemi atlar -- bu da videonun hedefinin genelde cok yakin/anlamsiz\n"
          f"  oldugu durumlari gosterir.")


if __name__ == "__main__":
    run()
