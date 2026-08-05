# Antigravity yaptı (Developed by Antigravity)
import sys
import warnings
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday"
OUT.mkdir(parents=True, exist_ok=True)

from intraday.regime_router_quality_lift_scan import (
    SWEEP, NQ, EUR, GBP, PRIORITY,
    _with_module, _combo_metrics, _challenge, _window_summary,
)
from intraday.regime_router_overfit_validation import _source_data, _rows_for_candidate
from intraday.gold_orb_regime import build_orb_ledger
from intraday.regime_router_factory import _load_ledger

GOLD = "GOLD_NY_ORB_TREND"
SWEEP_DIV = "SWEEP_ES_DIV"
BTC = "BTCUSDT_OF_ABSORPTION"

PRIORITY[GOLD] = 5
PRIORITY[SWEEP_DIV] = 1 
PRIORITY[BTC] = 6  # Kripto önceliği (en düşük öncelik, çakışmada diğerleri tercih edilir)

def _gold_parts(weight: float) -> pd.DataFrame:
    led, _ = build_orb_ledger("XAUUSD", 13.5, days=1080, entry_mode="retest", trend="vwap")
    sub = led[led.adx_regime.isin(["trend", "strong_trend"])]
    sub = sub.copy()
    sub["setup"] = "XAUUSD NY-ORB vwap 13.5/60 rr1.0"
    return _with_module(sub, GOLD, f"{GOLD}_trend", weight)

def _evaluate(parts) -> dict:
    ledger, m = _combo_metrics(parts)
    ws = _window_summary(_challenge(ledger))
    return {
        "trades": m["trades"],
        "tr_wk": round(m["trades_per_week"], 2),
        "exp_r": round(m["exp_r"], 3),
        "pf": round(m["pf"], 3),
        "pass_pct": round(ws["pass_pct"], 2),
        "timeout_pct": round(ws["timeout_pct"], 2),
        "daily_dd_pct": round(ws["daily_dd_pct"], 2),
        "total_dd_pct": round(ws["total_dd_pct"], 2),
        "median_pass_day": ws["median_pass_day"],
        "pos_years": m["positive_years"],
        "min_year_R": round(m["min_year_R"], 2),
    }

def main():
    print("="*100)
    print("  BTCUSDT CVD SWEEP + GOLD NY-ORB + ES DIV ROUTER ENTEGRASYONU")
    print("="*100)
    
    sweep, internet = _source_data()
    c = _rows_for_candidate("quality_11", sweep, internet)
    w = c["weights"]
    
    # Altın ve Divergence verilerini yükle
    div_ledger = _load_ledger(OUT / "intermarket_divergence_ledger.csv")
    div_parts = _with_module(div_ledger, SWEEP_DIV, "div_sweep", 2.0)
    gp_base = _gold_parts(1.0)
    
    # Yeni BTC verisini yükle
    btc_ledger = _load_ledger(OUT / "btc_cvd_sweep_ledger.csv")
    
    # Baz model parçaları (Sweep + NQ + EUR + GBP)
    base_parts = [
        _with_module(c["sweep"], SWEEP, "q11_sweep", w[SWEEP]),
        _with_module(c["nq"], NQ, "q11_nq", w[NQ]),
        _with_module(c["eur"], EUR, "q11_eur", w[EUR]),
        _with_module(c["gbp"], GBP, "q11_gbp", w[GBP]),
    ]
    
    # 1. Entegrasyon: Altın + Divergence (BTC yok)
    current_portfolio = base_parts + [gp_base, div_parts]
    res_current = _evaluate(current_portfolio)
    print("\n[MEVCUT PORTFÖY] Sweep + NQ + EUR + GBP + Gold(w=1.0) + ES_Div(w=2.0):")
    print(f"  Pass Rate: {res_current['pass_pct']}% | Timeout: {res_current['timeout_pct']}% | DD(d/t): {res_current['daily_dd_pct']}/{res_current['total_dd_pct']}%")
    print(f"  Exp R: {res_current['exp_r']} | PF: {res_current['pf']} | Trades/Wk: {res_current['tr_wk']} | Trades: {res_current['trades']}")
    
    # 2. Entegrasyon: BTC Ağırlık Taraması (w = 0.1 - 1.5)
    print("\n  BTC AĞIRLIK TARAMASI VE ETKİSİ:")
    print("-" * 100)
    print(f"{'Ağırlık':<8} | {'Pass Rate':<10} | {'Timeout':<9} | {'Daily DD':<9} | {'Total DD':<9} | {'Trades/Wk':<9} | {'Expectancy':<10} | {'PF':<6}")
    print("-" * 100)
    
    best_pass = res_current['pass_pct']
    best_w = 0.0
    best_res = res_current
    
    weights = [round(x / 100, 2) for x in range(1, 31)] + [0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5]
    for weight in weights:
        btc_parts = _with_module(btc_ledger, BTC, "btc_sweep", weight)
        portfolio = current_portfolio + [btc_parts]
        res = _evaluate(portfolio)
        print(f"{weight:<8.2f} | {res['pass_pct']:<9.2f}% | {res['timeout_pct']:<8.2f}% | {res['daily_dd_pct']:<8.2f}% | {res['total_dd_pct']:<8.2f}% | {res['tr_wk']:<9.2f} | {res['exp_r']:<10.3f} | {res['pf']:<6.3f}")
        
        # Dengeli finalist: pass hedefini gec, daily DD'yi 5 altinda ve total DD'yi 10 altinda tut.
        if (
            res['pass_pct'] >= 50.0
            and res['pass_pct'] > best_pass
            and res['daily_dd_pct'] <= 5.0
            and res['total_dd_pct'] <= 10.0
        ):
            best_pass = res['pass_pct']
            best_w = weight
            best_res = res
            
    print("-" * 100)
    if best_w > 0:
        print(f"\n[MUHAFAZAKAR FINAL] BTC Entegrasyonu Başarılı! Seçilen Ağırlık: {best_w:.2f}")
        print(f"  Pass Rate: {best_res['pass_pct']}% (Önceki: {res_current['pass_pct']}%)")
        print(f"  Timeout: {best_res['timeout_pct']}% (Önceki: {res_current['timeout_pct']}%)")
        print(f"  Daily DD Fail: {best_res['daily_dd_pct']}% (Önceki: {res_current['daily_dd_pct']}%)")
        print(f"  Total DD Fail: {best_res['total_dd_pct']}% (Önceki: {res_current['total_dd_pct']}%)")
    else:
        print("\n[EN İYİ SONUÇ] Portföy pass rate'ini ve DD sınırlarını iyileştiren bir BTC ağırlığı bulunamadı. BTC'yi devre dışı tutmak veya daha sıkı filtrelemek gerekiyor.")

if __name__ == "__main__":
    main()
