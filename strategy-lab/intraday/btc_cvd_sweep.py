# Antigravity yaptı (Developed by Antigravity)
import json
import numpy as np
import pandas as pd
from pathlib import Path
import warnings
from intraday.btc_data import load_btc
from intraday.config import INSTRUMENTS
from intraday.honest_engine import simulate_trades, metrics
from intraday.strategies import orderflow
from intraday.indicators import ema

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intraday"
OUT.mkdir(parents=True, exist_ok=True)

def write_vibe_artifacts(best_params, stats, r):
    run_card = {
        "schema_version": "vibe-trading-run-card-v1",
        "title": f"BTCUSDT Order Flow {best_params['mode'].upper()} 1H v1",
        "purpose": f"Trade BTCUSDT liquid breakout/sweep on 1H with order flow {best_params['mode']}.",
        "backtest": {
            "engine": "honest_engine",
            "symbol": "BTCUSDT",
            "timeframe": "1H",
            "fees_slippage": INSTRUMENTS["BTCUSDT"].cost_per_side * 2,
        },
        "chosen_params": best_params,
        "metrics": {
            "exp_r": float(stats.get("exp_r", 0)),
            "win_rate_pct": float(stats.get("win_rate", 0)),
            "total_trades": int(stats.get("trades", 0)),
            "profit_factor": float(stats.get("pf", 0)) if pd.notna(stats.get("pf", 0)) else 0,
            "total_R": float(r.sum()) if len(r) else 0.0
        }
    }
    
    with open(OUT / "btc_cvd_sweep_run_card.json", "w", encoding="utf-8") as f:
        json.dump(run_card, f, indent=2)
        
    # Generate Pine Script v6
    pine_code = f"""//@version=6
strategy("BTCUSDT Order Flow {best_params['mode'].upper()} 1H v1", overlay=true, initial_capital=10000, commission_type=strategy.commission.percent, commission_value=0.06, slippage=2)

lookback = input.int({best_params['lookback']}, "Lookback Period")
rr = input.float({best_params['min_rr']:.2f}, "Reward/Risk")
atrMult = input.float({best_params['atr_mult']:.2f}, "SL ATR Mult")
deltaZ = input.float({best_params.get('delta_z', 1.0):.2f}, "Delta Z-Score Threshold")

// CVD Basit Hesaplama
delta = volume * (close - open) / (high - low == 0 ? 1 : high - low)
var float cvd = 0.0
cvd := cvd + delta

rlo = ta.lowest(low, lookback)[1]
rhi = ta.highest(high, lookback)[1]

rloCvd = ta.lowest(cvd, lookback)[1]
rhiCvd = ta.highest(cvd, lookback)[1]

// Trend mode z-score
var float deltaMean = na
var float deltaStd = na
deltaMean := ta.sma(delta, 50)
deltaStd := ta.stdev(delta, 50)
dz = (delta - deltaMean) / (deltaStd == 0 ? 1 : deltaStd)

sweptLow = low < rlo and close > rlo
sweptHigh = high > rhi and close < rhi

// Sinyaller
var bool bullishSig = false
var bool bearishSig = false

if "{best_params['mode']}" == "trend"
    bullishSig := close > rhi and dz > deltaZ
    bearishSig := close < rlo and dz < -deltaZ
else if "{best_params['mode']}" == "divergence"
    bullishSig := sweptLow and cvd > rloCvd
    bearishSig := sweptHigh and cvd < rhiCvd
else
    bullishSig := sweptLow and delta > 0
    bearishSig := sweptHigh and delta < 0

trend = ta.ema(close, 200)

{"isTradeWindow = ((hour > 13) or (hour == 13 and minute >= 30)) and hour < 20" if best_params['window'] == "US" else "isTradeWindow = true"}

divLong = bullishSig and isTradeWindow {"and close > trend" if best_params['use_trend'] else ""}
divShort = bearishSig and isTradeWindow {"and close < trend" if best_params['use_trend'] else ""}

if divLong and strategy.position_size == 0
    strategy.entry("LONG", strategy.long)
    sl = low - ta.atr(14) * atrMult
    tp = strategy.position_avg_price + (strategy.position_avg_price - sl) * rr
    strategy.exit("SL/TP", "LONG", stop=sl, limit=tp)

if divShort and strategy.position_size == 0
    strategy.entry("SHORT", strategy.short)
    sl = high + ta.atr(14) * atrMult
    tp = strategy.position_avg_price - (sl - strategy.position_avg_price) * rr
    strategy.exit("SL/TP", "SHORT", stop=sl, limit=tp)
"""
    with open(OUT / "btc_cvd_sweep_v1.pine", "w", encoding="utf-8") as f:
        f.write(pine_code)

def main():
    print("Binance BTCUSDT 1H verisi yükleniyor...")
    df = load_btc("1h", 1080)
    print(f"BTC verisi yüklendi: {len(df)} bar.")
    
    # Calculate trend series (HTF or 200 EMA)
    trend_ema = ema(df["close"], 200)
    trend = pd.Series(0, index=df.index)
    trend[df["close"] > trend_ema] = 1
    trend[df["close"] < trend_ema] = -1
    
    # Grid Search Parameters
    modes = ["trend", "absorption", "divergence"]
    lookbacks = [12, 24, 48]
    atr_mults = [1.0, 2.0, 3.0]
    min_rrs = [1.5, 2.0, 3.0]
    max_holds = [24, 48, 96]
    use_trends = [True, False]
    windows = ["US", "24H"]
    delta_zs = [0.5, 1.0, 1.5]
    
    results = []
    best_score = -999.0
    best_params = {}
    best_stats = {}
    best_r = None
    
    # Calculate trade windows
    h = df.index.hour
    is_us_window = (h >= 13) & (h < 20)
    is_24h_window = pd.Series(True, index=df.index)
    
    print("Grid Search başlıyor...")
    for mode in modes:
        cur_delta_zs = delta_zs if mode == "trend" else [1.0]
        for dz in cur_delta_zs:
            for lk in lookbacks:
                for am in atr_mults:
                    for rr in min_rrs:
                        for hold in max_holds:
                            for tr in use_trends:
                                for win in windows:
                                    sig = orderflow(
                                        df, 
                                        trend, 
                                        mode=mode, 
                                        lookback=lk, 
                                        delta_z=dz,
                                        sl_buf=am, 
                                        use_trend=tr
                                    )
                                    
                                    mask = is_us_window if win == "US" else is_24h_window
                                    le = sig.long_entry & mask
                                    se = sig.short_entry & mask
                                    
                                    r = simulate_trades(
                                        df,
                                        le, se,
                                        sig.long_sl, sig.long_tp,
                                        sig.short_sl, sig.short_tp,
                                        INSTRUMENTS["BTCUSDT"],
                                        min_rr=rr,
                                        max_rr=6.0,
                                        max_hold=hold
                                    )
                                    
                                    m_stats = metrics(r)
                                    trades = m_stats["trades"]
                                    exp_r = m_stats["exp_r"]
                                    pf = m_stats["pf"]
                                    
                                    if trades >= 15 and exp_r > 0 and pf > 1.05:
                                        print(f"mode={mode}, dz={dz}, lk={lk}, am={am}, rr={rr}, hold={hold}, tr={tr}, win={win} | Trades: {trades} | Exp R: {exp_r:.3f} | PF: {pf:.2f}")
                                    
                                    results.append({
                                        "mode": mode,
                                        "delta_z": dz,
                                        "lookback": lk,
                                        "atr_mult": am,
                                        "min_rr": rr,
                                        "max_hold": hold,
                                        "use_trend": tr,
                                        "window": win,
                                        "trades": trades,
                                        "exp_r": exp_r,
                                        "pf": pf,
                                        "win_rate": m_stats["win_rate"],
                                        "total_R": r.sum() if len(r) else 0.0
                                    })
                                    
                                    # Balance trade frequency (at least 30 trades) and expectancy using score
                                    score = exp_r + 0.0005 * trades if (trades >= 30 and exp_r > 0) else -999.0
                                    if score > best_score:
                                        best_score = score
                                        best_params = {
                                            "mode": mode,
                                            "delta_z": dz,
                                            "lookback": lk,
                                            "atr_mult": am,
                                            "min_rr": rr,
                                            "max_hold": hold,
                                            "use_trend": tr,
                                            "window": win
                                        }
                                        best_stats = m_stats
                                        best_r = r
                        
    pd.DataFrame(results).to_csv(OUT / "btc_sweep_grid_results.csv", index=False)
    
    if best_r is not None:
        print("\n--- EN İYİ BTC SİNYAL SONUÇLARI ---")
        print(best_params)
        print(best_stats)
        print(f"Toplam R: {best_r.sum():.2f}")
        write_vibe_artifacts(best_params, best_stats, best_r)
        
        # Ledger'ı kaydet
        ledger = pd.DataFrame()
        ledger["timestamp"] = pd.to_datetime(best_r.index)
        ledger["r"] = best_r.values
        ledger["setup"] = f"BTCUSDT_OF_{best_params['mode'].upper()}"
        
        ledger.to_csv(OUT / "btc_cvd_sweep_ledger.csv", index=False)
        print(f"Ledger kaydedildi: {OUT / 'btc_cvd_sweep_ledger.csv'}")
    else:
        print("Kriterleri karşılayan uygun strateji bulunamadı.")

if __name__ == "__main__":
    main()
