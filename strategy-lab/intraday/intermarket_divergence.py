# Antigravity yaptı (Developed by Antigravity)
import json
import numpy as np
import pandas as pd
import vectorbt as vbt
from pathlib import Path
import warnings
from intraday.data import load_ohlcv
from intraday.indicators import atr, htf_trend, swing_high, swing_low, rolling_high, rolling_low, ema
from intraday.strategies import smc_sweep

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "intermarket_divergence"
OUT.mkdir(parents=True, exist_ok=True)

INIT_CASH = 10_000.0
FEES = 0.00009  # NQ cost_per_side
SLIPPAGE = 0.0001
RISK_PER_TRADE_PCT = 1.5

def run_divergence_backtest(df_nq: pd.DataFrame, df_es: pd.DataFrame, lookback: int, use_div_filter: bool, atr_mult: float, rr: float):
    common_idx = df_nq.index.intersection(df_es.index)
    df_nq = df_nq.loc[common_idx]
    df_es = df_es.loc[common_idx]
    
    df_nq_1h = load_ohlcv("NASDAQ100", "1H", days=1095)
    trend_nq = htf_trend(df_nq.index, df_nq_1h)
    
    a = atr(df_nq, 14)
    buf = a * 0.25
    
    sh = swing_high(df_nq)
    sl = swing_low(df_nq)
    
    rlo_nq = rolling_low(df_nq, lookback)
    rhi_nq = rolling_high(df_nq, lookback)
    
    rlo_es = rolling_low(df_es, lookback)
    rhi_es = rolling_high(df_es, lookback)
    
    low_nq, high_nq, close_nq = df_nq["low"], df_nq["high"], df_nq["close"]
    low_es, high_es = df_es["low"], df_es["high"]
    
    swept_low = (low_nq < rlo_nq) & (close_nq > rlo_nq)
    swept_high = (high_nq > rhi_nq) & (close_nq < rhi_nq)
    
    div_long = swept_low
    if use_div_filter:
        div_long = swept_low & (low_es >= rlo_es)
        
    div_short = swept_high
    if use_div_filter:
        div_short = swept_high & (high_es <= rhi_es)
        
    long_raw = div_long & (trend_nq > 0)
    short_raw = div_short & (trend_nq < 0)
    
    long_entries = long_raw & ~long_raw.shift(1).fillna(False)
    short_entries = short_raw & ~short_raw.shift(1).fillna(False)
    
    long_sl_price = low_nq - buf
    long_sl_pct = (close_nq - long_sl_price) / close_nq
    long_sl_pct = long_sl_pct.where(long_entries).ffill()
    
    short_sl_price = high_nq + buf
    short_sl_pct = (short_sl_price - close_nq) / close_nq
    short_sl_pct = short_sl_pct.where(short_entries).ffill()
    
    sl_stop = pd.Series(np.nan, index=df_nq.index)
    sl_stop[long_entries] = long_sl_pct[long_entries]
    sl_stop[short_entries] = short_sl_pct[short_entries]
    sl_stop = sl_stop.clip(lower=0.002, upper=0.08)
    
    tp_stop = sl_stop * rr
    
    ma50 = close_nq.rolling(50).mean()
    exits = ((trend_nq > 0) & (close_nq < ma50)) | (close_nq < rlo_nq)
    short_exits = ((trend_nq < 0) & (close_nq > ma50)) | (close_nq > rhi_nq)
    
    risk_fraction = RISK_PER_TRADE_PCT / 100.0
    size = risk_fraction / sl_stop.fillna(0.01)
    size = size.clip(lower=0.01, upper=1.0)
    
    pf = vbt.Portfolio.from_signals(
        close_nq,
        entries=long_entries,
        exits=exits,
        short_entries=short_entries,
        short_exits=short_exits,
        init_cash=INIT_CASH,
        fees=FEES,
        slippage=SLIPPAGE,
        sl_stop=sl_stop.to_numpy(),
        tp_stop=tp_stop.to_numpy(),
        size=size.to_numpy(),
        size_type="percent",
        accumulate=False,
        upon_opposite_entry="close",
        freq="15min",
    )
    return pf

def write_vibe_artifacts(best_params, stats, pf):
    run_card = {
        "schema_version": "vibe-trading-run-card-v1",
        "title": "Intermarket Divergence NQ vs ES v1",
        "purpose": "Filter NQ liquid sweep entries using ES divergence correlation.",
        "backtest": {
            "engine": "vectorbt",
            "symbol": "NASDAQ100 vs SP500",
            "timeframe": "15m",
            "fees": FEES,
            "slippage": SLIPPAGE,
            "init_cash": INIT_CASH,
        },
        "chosen_params": best_params,
        "metrics": {
            "total_return_pct": float(stats.get("Total Return [%]", 0)),
            "max_drawdown_pct": float(stats.get("Max Drawdown [%]", 0)),
            "win_rate_pct": float(stats.get("Win Rate [%]", 0)),
            "total_trades": int(stats.get("Total Trades", 0)),
            "profit_factor": float(stats.get("Profit Factor", 0)) if pd.notna(stats.get("Profit Factor", 0)) else 0,
            "sharpe_ratio": float(stats.get("Sharpe Ratio", 0)) if pd.notna(stats.get("Sharpe Ratio", 0)) else 0,
        }
    }
    
    with open(OUT / "run_card.json", "w", encoding="utf-8") as f:
        json.dump(run_card, f, indent=2)
        
    # Generate Pine Script v6
    pine_code = f"""//@version=6
strategy("Intermarket Divergence NQ/ES v1", overlay=true, initial_capital=10000, commission_type=strategy.commission.percent, commission_value=0.009, slippage=1)

lookback = input.int({best_params['lookback']}, "Lookback Period")
rr = input.float({best_params['rr']:.2f}, "Reward/Risk")
atrMult = input.float({best_params['atr_mult']:.2f}, "SL ATR Mult")

esClose = request.security("US500", "15", close)
esLow = request.security("US500", "15", low)
esHigh = request.security("US500", "15", high)

rloNq = ta.lowest(low, lookback)[1]
rhiNq = ta.highest(high, lookback)[1]

rloEs = ta.lowest(esLow, lookback)[1]
rhiEs = ta.highest(esHigh, lookback)[1]

trend = ta.ema(close, 200)

sweptLow = low < rloNq and close > rloNq
sweptHigh = high > rhiNq and close < rhiNq

divLong = sweptLow and esLow >= rloEs and close > trend
divShort = sweptHigh and esHigh <= rhiEs and close < trend

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
    with open(OUT / "intermarket_divergence_v1.pine", "w", encoding="utf-8") as f:
        f.write(pine_code)

def main():
    print("Veriler yükleniyor...")
    df_nq = load_ohlcv("NASDAQ100", "15m", days=1095)
    df_es = load_ohlcv("SP500", "15m", days=1095)
    print(f"NQ veri barları: {len(df_nq)} | ES veri barları: {len(df_es)}")
    
    # Grid Search
    lookbacks = [20, 30, 40]
    atr_mults = [0.25, 0.5]
    rrs = [2.0, 3.0, 4.0]
    use_divs = [True, False]
    
    results = []
    best_sharpe = -999.0
    best_params = {}
    best_stats = {}
    best_pf = None
    
    print("Grid Search başlıyor...")
    for lk in lookbacks:
        for am in atr_mults:
            for rr in rrs:
                for div in use_divs:
                    pf = run_divergence_backtest(df_nq, df_es, lk, div, am, rr)
                    stats = pf.stats()
                    sharpe = stats.get("Sharpe Ratio", -9.0)
                    trades = stats.get("Total Trades", 0)
                    ret = stats.get("Total Return [%]", 0.0)
                    dd = stats.get("Max Drawdown [%]", 0.0)
                    
                    print(f"lk={lk}, am={am}, rr={rr}, div={div} | Trades: {trades} | Return: {ret:.2f}% | Sharpe: {sharpe:.2f}")
                    
                    results.append({
                        "lookback": lk,
                        "atr_mult": am,
                        "rr": rr,
                        "use_divergence": div,
                        "trades": trades,
                        "return_pct": ret,
                        "max_dd_pct": dd,
                        "sharpe": sharpe,
                    })
                    
                    if div and trades >= 10 and sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_params = {"lookback": lk, "atr_mult": am, "rr": rr, "use_divergence": div}
                        best_stats = stats
                        best_pf = pf
                        
    pd.DataFrame(results).to_csv(OUT / "grid_results.csv", index=False)
    
    if best_pf is not None:
        print("\n--- EN İYİ SİNYAL SONUÇLARI (FİLTRELİ) ---")
        print(best_params)
        print(best_stats)
        write_vibe_artifacts(best_params, best_stats, best_pf)
        
        # Ledger'ı kaydet
        trades = best_pf.trades.records_readable
        ledger = pd.DataFrame()
        ledger["timestamp"] = pd.to_datetime(trades["Entry Timestamp"])
        # PnL R cinsinden
        ledger["r"] = trades["PnL"] / (INIT_CASH * (RISK_PER_TRADE_PCT / 100.0))
        ledger["setup"] = "NQ_SWEEP_ES_DIV"
        
        intraday_out = ROOT / "outputs" / "intraday"
        intraday_out.mkdir(parents=True, exist_ok=True)
        ledger.to_csv(intraday_out / "intermarket_divergence_ledger.csv", index=False)
        print(f"Ledger kaydedildi: {intraday_out / 'intermarket_divergence_ledger.csv'}")
    else:
        print("Kriterleri karşılayan uygun strateji bulunamadı.")

if __name__ == "__main__":
    main()
