"""Kac hipotez deneyebiliriz? -- arama butcesi hesabi.

SORU (2026-08-21): "Yuksek CPU'lu sunucu kiralayip kurumsallar gibi devasa
tarama yapsak?" Tarama hizi darbogaz mi, yoksa baska bir sey mi?

CEVAP: darbogaz veri uzunlugu. N farkli konfig denersen, EN IYISI sirf sansla
`expected_max_sharpe(N)` kadar iyi gorunur; bu esik N ile ~sqrt(2 ln N)
buyur ama gozlem sayisi T ile duser. Yani:

    islem gucu  -> N'i buyutur -> esigi YUKSELTIR
    daha cok veri -> T'yi buyutur -> esigi DUSURUR

Olculen (2026-08-21, SWEEP_CORE rejim filtreli backtest, haftalik SR +0.383):

    3 yil veri  (35 aktif hafta)  -> butce ~37 hipotez
    14 yil veri (181 aktif hafta) -> butce ~1.6 MILYON hipotez

256 cekirdekli bir sunucu gunde ~6.8M konfig tarar, yani 3 yillik veriyle
butceyi yarim saniyede tuketir. Ayni parayla Dukascopy'den 14 yil veri
indirmek butceyi 43.000 kat buyutur -- ve bedavadir.

Calistir:
    python -m intraday.search_budget
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .overfit_stats import expected_max_sharpe, sharpe

LEDGER_DIR = Path(__file__).resolve().parent.parent / "outputs" / "intraday"


def sr_variance(observed_sr: float, n_obs: int) -> float:
    """SR tahmininin varyansi (Lo 2002 yaklasimi, normal getiri varsayimi)."""
    return (1.0 + 0.5 * observed_sr ** 2) / max(n_obs - 1, 1)


def trial_budget(observed_sr: float, n_obs: int, max_trials: int = 10 ** 15) -> int:
    """Kac denemeden SONRA bu SR sans esiginin altina duser.

    Yani: elimizdeki ornek bu kadar hipotezi finanse ediyor. Daha fazlasini
    denersen "en iyi bulgun" ile "sansin sana verdigi en iyi" ayirt edilemez.
    """
    if observed_sr <= 0:
        return 0
    var = sr_variance(observed_sr, n_obs)
    low, high = 1, max_trials
    while low < high:
        mid = (low + high) // 2
        if expected_max_sharpe(mid, var) < observed_sr:
            low = mid + 1
        else:
            high = mid
    return low - 1


def weekly_sharpe(r: pd.Series) -> tuple[float, int]:
    """Haftalik toplam R serisinden SR ve aktif hafta sayisi."""
    weekly = r.resample("W").sum()
    weekly = weekly[weekly != 0]
    return sharpe(weekly), len(weekly)


def report(observed_sr: float, n_obs: int, label: str = "") -> None:
    var = sr_variance(observed_sr, n_obs)
    butce = trial_budget(observed_sr, n_obs)
    print(f"\n  {label}: SR={observed_sr:+.3f}  gozlem={n_obs}  "
          f"BUTCE={butce:,} hipotez")
    print(f"  {'N deneme':>16} {'sans esigi':>12} {'gecer mi':>10}")
    for n in (1, 10, 100, 1_000, 10_000, 1_000_000, 6_800_000):
        esik = expected_max_sharpe(n, var)
        print(f"  {n:>16,} {esik:>+12.3f} "
              f"{'EVET' if observed_sr > esik else 'HAYIR':>10}")


def main() -> None:
    print("=" * 72)
    print("  ARAMA BUTCESI -- kac hipotez deneyebiliriz?")
    print("=" * 72)

    sweep = LEDGER_DIR / "sweep_regime_ledger.csv"
    if sweep.exists():
        r = pd.read_csv(sweep, index_col=0, parse_dates=True)["r"]
        sr, n = weekly_sharpe(r)
        report(sr, n, f"SWEEP backtest ({len(r)} islem, 3 yil)")

        # Ayni SR daha uzun veriyle: gozlem sayisi orantili buyur
        for yil in (7, 14, 21):
            olcek = yil / 2.7
            report(sr, int(n * olcek), f"AYNI SR, {yil} yil veri (varsayim)")

    fwd = LEDGER_DIR / "forward_ea" / "forward_ledger.csv"
    if fwd.exists():
        from .forward_ea.ledger import load_forward
        led = load_forward(fwd, include_candidates=False)
        r = led.set_index("entry_time")["r"]
        sr, n = weekly_sharpe(r)
        report(sr, n, f"FORWARD defteri havuz ({len(r)} islem)")

    print("\n" + "=" * 72)
    print("  SONUC: butceyi buyuten sey VERI UZUNLUGU, islem gucu degil.")
    print("  Islem gucu N'i buyutur -> esigi yukseltir -> butceyi TUKETIR.")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
