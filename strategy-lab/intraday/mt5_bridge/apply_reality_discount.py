"""Reality-discount'u final ledger'a uygula -> reality-adjusted pass rate.

Fikir: reality_profiler her sembol icin gercek tek-yon maliyeti olcer. Eger
config varsayimi GERCEKTEN dusukse (IYIMSER), aradaki fark her trade'e ek R
maliyeti olarak dusulur. Sonra challenge sim yeniden kosturulur ve "kagit"
pass ile "gercekci" pass kiyaslanir.

Maliyet -> R donusumu:
    delta_R = -2 * delta_cost_ratio / stop_ratio
  (gidis-donus = 2 yon; stop_ratio = tipik stop mesafesi / fiyat, MT5 ATR'den)

Muhafazakar varsayim: sadece IYIMSER sembollerde ceza uygulanir (config'in
muhafazakar oldugu sembollere kredi VERILMEZ). Slippage carpani ile duyarlilik
bandi (0.5x / 1.0x / 2.0x) uretilir.

Calistir:
    python -m intraday.mt5_bridge.apply_reality_discount
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ..indicators import atr
from ..regime_router_quality_lift_scan import _challenge, _metrics, _weeks, _window_summary
from . import mt5_io

OUT = Path(__file__).resolve().parent.parent.parent / "outputs" / "intraday"
BRIDGE_OUT = OUT / "mt5_bridge"
BRIDGE_OUT.mkdir(parents=True, exist_ok=True)

LEDGER = OUT / "regime_router_final_validation_ledger.csv"
PROFILE = BRIDGE_OUT / "reality_profile.json"

# Final ledger'daki modul -> reality_profiler sembol anahtari + giris TF.
# BTC bu broker'da yok; ayri ele alinir (Binance).
MODULE_SYMBOL = {
    "SWEEP_CORE_AVOID_MID_VWAP": ("NASDAQ100", "15m"),
    "NQ_ORB_STRONG_TREND": ("NASDAQ100", "15m"),
    "SWEEP_ES_DIV": ("NASDAQ100", "15m"),
    "EUR_LONDON_FADE_EMA": ("EURUSD", "5m"),
    "GBP_LONDON_STRONG_TREND": ("GBPUSD", "5m"),
    "GOLD_NY_ORB_TREND": ("XAUUSD", "5m"),
}
BTC_MODULE = "BTCUSDT_OF_ABSORPTION"
STOP_MULT = 1.5  # tipik stop ~ 1.5 ATR (other_side ORB / sweep icin makul orta deger)


def _load_profile() -> dict[str, dict]:
    if not PROFILE.exists():
        raise FileNotFoundError(
            f"Once reality_profiler calistir: {PROFILE} yok.\n"
            f"  python -m intraday.mt5_bridge.reality_profiler"
        )
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    return {r["symbol"]: r for r in data}


def _stop_ratios(symbols: set[str]) -> dict[str, float]:
    """Sembol basina tipik stop mesafesi orani = median(ATR/close) * STOP_MULT."""
    out = {}
    with mt5_io.session():
        for key in symbols:
            tf = "15m" if key in ("NASDAQ100", "SP500") else "5m"
            try:
                df = mt5_io.ohlcv(key, tf, days=120)
                a = atr(df, 14)
                ratio = float((a / df["close"]).median()) * STOP_MULT
                out[key] = ratio
            except mt5_io.MT5Error:
                out[key] = np.nan
    return out


def _delta_cost_ratio(prof: dict, slip_mult: float) -> float:
    """Gercek - varsayilan maliyet (ceza-yonlu). slip_mult slippage'i olcekler."""
    assumed = prof.get("assumed_cost_per_side")
    spread = prof.get("spread_one_side_period_adj", 0.0)
    slip = prof.get("slippage_p90", 0.0)
    real = spread + slip * slip_mult
    if assumed is None or np.isnan(assumed):
        return 0.0
    return max(real - assumed, 0.0)  # muhafazakar: sadece ceza, kredi yok


def _adjust_ledger(ledger: pd.DataFrame, profile: dict, stop_ratios: dict,
                   slip_mult: float) -> tuple[pd.DataFrame, dict]:
    adj = ledger.copy()
    delta_by_module: dict[str, float] = {}
    delta_r = np.zeros(len(adj))
    for module, (sym, _tf) in MODULE_SYMBOL.items():
        mask = (adj["module"] == module).to_numpy()
        if not mask.any():
            continue
        prof = profile.get(sym)
        sr = stop_ratios.get(sym, np.nan)
        if prof is None or np.isnan(sr) or sr <= 0:
            continue
        dcr = _delta_cost_ratio(prof, slip_mult)
        d_r = -2.0 * dcr / sr  # gidis-donus, R cinsinden (negatif = ceza)
        delta_r[mask] = d_r
        delta_by_module[module] = d_r
    # BTC: MT5'te yok -> degisiklik yok, ayri Binance check'i gerekir.
    adj["r"] = pd.to_numeric(adj["r"], errors="coerce") + delta_r
    adj["weighted_r"] = adj["r"] * pd.to_numeric(adj["weight"], errors="coerce")
    return adj, delta_by_module


def _summary(ledger: pd.DataFrame) -> dict:
    m = _metrics(ledger["weighted_r"])
    m["trades_per_week"] = m["trades"] / _weeks(ledger.index)
    w = _challenge(ledger)
    return {**m, **_window_summary(w)}


def main(slip_mults=(0.5, 1.0, 2.0)) -> None:
    print("\n" + "=" * 100)
    print("  REALITY-ADJUSTED PASS — kagit backtest vs gercek maliyet (MT5 olcumlu)")
    print("=" * 100 + "\n")

    if not LEDGER.exists():
        print(f"  Final ledger yok: {LEDGER}\n  Once: python -m intraday.regime_router_final_validation")
        return

    ledger = pd.read_csv(LEDGER, index_col=0, parse_dates=[0])
    profile = _load_profile()
    symbols = {sym for sym, _ in MODULE_SYMBOL.values()}
    stop_ratios = _stop_ratios(symbols)

    print("  Tipik stop orani (median ATR*1.5 / fiyat):")
    for k, v in stop_ratios.items():
        print(f"    {k:10} {v:.5f}" if not np.isnan(v) else f"    {k:10} (yok)")
    print()

    base = _summary(ledger)
    rows = [{"scenario": "kagit (baseline)", "slip_mult": 0.0, **base}]
    deltas_report = {}

    for sm in slip_mults:
        adj, deltas = _adjust_ledger(ledger, profile, stop_ratios, sm)
        s = _summary(adj)
        rows.append({"scenario": f"reality slip x{sm}", "slip_mult": sm, **s})
        deltas_report[f"slip_x{sm}"] = deltas

    df = pd.DataFrame(rows)
    cols = ["scenario", "trades", "trades_per_week", "exp_r", "pf", "total_R",
            "pass_pct", "timeout_pct", "daily_dd_pct", "total_dd_pct"]
    print(df[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    print("\n  Modul basina uygulanan R cezasi (trade basina):")
    for scen, dd in deltas_report.items():
        parts = ", ".join(f"{m.split('_')[0]}:{v:+.4f}R" for m, v in dd.items() if v != 0)
        print(f"    {scen:12} {parts or '(ceza yok — tum semboller muhafazakar)'}")

    btc_n = int((ledger["module"] == BTC_MODULE).sum())
    if btc_n:
        print(f"\n  NOT: {btc_n} BTC trade'i ({BTC_MODULE}) MT5'te spot yok -> ayarlanmadi.")
        print("       BTC reality-check'i Binance verisinden ayrica yapilmali.")

    out_csv = BRIDGE_OUT / "reality_adjusted_pass.csv"
    df.to_csv(out_csv, index=False)
    run_card = {
        "stop_mult": STOP_MULT,
        "stop_ratios": stop_ratios,
        "scenarios": df[cols].to_dict("records"),
        "module_r_penalty": deltas_report,
        "btc_unadjusted_trades": btc_n,
    }
    (BRIDGE_OUT / "reality_adjusted_run_card.json").write_text(
        json.dumps(run_card, indent=2, default=float), encoding="utf-8"
    )

    base_pass = rows[0]["pass_pct"]
    real_pass = [r["pass_pct"] for r in rows if r["slip_mult"] == 1.0][0]
    print(f"\n  SONUC: kagit pass %{base_pass:.1f} -> reality (slip x1.0) pass %{real_pass:.1f} "
          f"(fark {real_pass - base_pass:+.1f} puan)")
    print(f"  CSV: {out_csv}")
    print("\n" + "=" * 100 + "\n")


if __name__ == "__main__":
    main()
