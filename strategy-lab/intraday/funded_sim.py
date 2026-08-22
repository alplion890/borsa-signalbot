"""Funded faz simulasyonu -- challenge'i gectikten SONRA ne oluyor?

Challenge kolay tarafi: +4% hedef, -10% SABIT dip, sure limiti yok.
Funded zor tarafi (Maven kurallari):
  - gunluk zarar limiti %4
  - max zarar %8 TRAILING (en yuksek bakiyeden takip eder)
  - %20 tutarlilik: tek gunun kari toplam karin %20'sini gecemez
  - odeme icin min 5 farkli islem gunu

SWEEP_CORE icin ozel risk: edge'i NADIR BUYUK kazanclardan geliyor (+6R'ler).
%20 tutarlilik kurali tam da bunu cezalandirir -- tek gunde +6R alirsan o gun
toplam karin cok buyuk bir kismi olur ve odeme kilitlenir. Bu dosya o etkiyi
olcer.

Calistirma:
    python -m intraday.funded_sim
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

TRADING_DAYS_YEAR = 252
DAILY_LOSS_LIMIT = 0.04
TRAILING_DD = 0.08
CONSISTENCY = 0.20
MIN_PAYOUT_DAYS = 5


def load_sweep_r() -> np.ndarray:
    """SWEEP_CORE birlesik R dagilimi: MT5 6 ay + canli forward."""
    from pathlib import Path

    from .multi_index_lab import _instrument, fetch, run_sweep

    fr, co = fetch(["US100"], 180)
    df = fr["US100"]
    mt5_r = run_sweep(df, _instrument("US100", co["US100"], float(df["close"].iloc[-1])))
    from .forward_ea.ledger import load_forward
    live = load_forward()   # backfill haric -- kanit sayimi
    live_r = live[live["module"] == "SWEEP_CORE_AVOID_MID_VWAP"]["r"].to_numpy()
    return np.concatenate([mt5_r.to_numpy(), live_r])


def simulate(R: np.ndarray, risk: float, trades_per_year: float,
             payout_target: float, horizon_days: int, n_runs: int = 20000,
             seed: int = 0) -> dict:
    """Gun gun funded hesap simulasyonu.

    Doner: hayatta kalma, odeme alma, ve odemeyi engelleyen sebeplerin dagilimi.
    """
    rng = np.random.default_rng(seed)
    p_trade = trades_per_year / TRADING_DAYS_YEAR
    blown = paid = 0
    days_to_payout: list[int] = []
    blocked_by_consistency = 0

    for _ in range(n_runs):
        eq = 0.0          # baslangica gore kar (oran)
        peak = 0.0        # trailing DD icin en yuksek nokta
        day_profits: list[float] = []
        dead = False
        for day in range(horizon_days):
            n_today = rng.poisson(p_trade)
            if n_today == 0:
                continue
            day_pnl = float(np.sum(rng.choice(R, n_today) * risk))
            # gunluk zarar limiti
            if day_pnl <= -DAILY_LOSS_LIMIT:
                blown += 1
                dead = True
                break
            eq += day_pnl
            peak = max(peak, eq)
            # trailing max drawdown
            if (peak - eq) >= TRAILING_DD:
                blown += 1
                dead = True
                break
            day_profits.append(day_pnl)
            # odeme kontrolu
            if eq >= payout_target:
                # Tutarlilik: en iyi GUNUN kari <= NET toplam karin %20'si.
                # Payda net kar (eq), pozitif gunlerin toplami degil -- kaybeden
                # gunler paydayi kucultur, yani kural bu haliyle daha sikidir.
                pos = [d for d in day_profits if d > 0]
                if len(day_profits) >= MIN_PAYOUT_DAYS and pos and eq > 0:
                    if max(pos) <= CONSISTENCY * eq:
                        paid += 1
                        days_to_payout.append(day)
                        dead = True
                        break
                    blocked_by_consistency += 1
        if not dead:
            pass
    return {
        "risk": risk,
        "patladi_%": round(100 * blown / n_runs, 1),
        "odeme_aldi_%": round(100 * paid / n_runs, 1),
        "medyan_gun": int(np.median(days_to_payout)) if days_to_payout else None,
        "medyan_hafta": round(np.median(days_to_payout) / 5, 1) if days_to_payout else None,
        "tutarlilik_engeli": blocked_by_consistency,
    }


def run() -> None:
    R = load_sweep_r()
    print(f"\nSWEEP_CORE R dagilimi: n={len(R)} exp_R={R.mean():+.3f} "
          f"en buyuk={R.max():+.2f}R")
    print(f"Kurallar: gunluk zarar %{DAILY_LOSS_LIMIT*100:.0f} | trailing DD "
          f"%{TRAILING_DD*100:.0f} | tutarlilik %{CONSISTENCY*100:.0f} | "
          f"min {MIN_PAYOUT_DAYS} islem gunu")

    for tpy, etiket in [(38, "sadece NASDAQ (~38 islem/yil)"),
                        (120, "4 endeks (~120 islem/yil)")]:
        print(f"\n{'='*70}\n{etiket} -- 1 yil ufuk, odeme hedefi %5 kar\n{'='*70}")
        print(f"{'risk':>6}{'patladi':>10}{'odeme':>9}{'medyan sure':>14}{'tutarlilik engeli':>20}")
        rows = []
        for risk in (0.0035, 0.005, 0.0075, 0.01, 0.015):
            r = simulate(R, risk, tpy, payout_target=0.05, horizon_days=252)
            rows.append({**r, "kapsam": etiket})
            sure = f"{r['medyan_hafta']} hafta" if r["medyan_hafta"] else "-"
            print(f"{risk*100:>5.2f}%{r['patladi_%']:>9.1f}%{r['odeme_aldi_%']:>8.1f}%"
                  f"{sure:>14}{r['tutarlilik_engeli']:>20}")
    print("\nNOT: 'tutarlilik engeli' = hedefe ulasildi ama tek gunun kari toplamin")
    print("     %20'sini astigi icin odeme kilitlendi (sayac, kosum degil).")


if __name__ == "__main__":
    run()
