"""2K account: min-lot feasibility per module (risk-sized 0.5%/trade). Contract specs ASSUMED (FN not verified)."""
import numpy as np, pandas as pd
exec(open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/stats4.py").read().split("def st(s)")[0])
from intraday import stop_testi as st
from intraday.seffaf_adaylari import load_btc_1h
EQ=2000.0; RISK=0.005*EQ; A="2022-01-01"
def report(name,stop_usd_per_min_lot,notional_min_lot=None):
    s=pd.Series(stop_usd_per_min_lot); eff=s/EQ*100
    print(f"{name}: n={len(s)} | en kucuk lotta risk medyan %{eff.median():.2f} p90 %{eff.quantile(.9):.2f} max %{eff.max():.2f} | hedef %0.5'i asan islem %{100*(s>RISK).mean():.0f}")
# XAU Donchian: contract 100 oz, min 0.01 -> 1 oz -> stop $ per oz
x=risk[r0.index>=A]; px=e[r0.index>=A]
print(f"XAU fiyat son {float(x1.close.iloc[-1]):.1f} | Donchian stop $/oz medyan {np.median(x):.2f} p10 {np.quantile(x,.1):.2f} p90 {np.quantile(x,.9):.2f}")
report("DONCHIAN_XAU (0.01 lot = 1 oz)",x*1.0)
# BTC modules k=1.5 ATR stop; contract 1 BTC
h1=load_btc_1h(); P,D,AT=st.btc_context()
for nm,b in (("BTC_21_23",st.base_btc_21_23(h1,D,AT)),("BTC_GECE",st.base_btc_gece(h1,D,AT))):
    b=b.dropna(subset=["atr"]); b=b[pd.DatetimeIndex(b.key)>=A]
    stop=1.5*b.atr; need_notional=RISK/(stop/b.entry)
    for ml in (0.01,0.001):
        report(f"{nm} k1.5 (min {ml} BTC)",stop*ml)
    print(f"   {nm}: gereken pozisyon (notional) medyan ${need_notional.median():.0f}; 0.01 BTC notional medyan ${(b.entry*0.01).median():.0f}; BTC son ${float(b.entry.iloc[-1]):.0f}; 1:1 kaldiracta tavan ${EQ:.0f}")
# US100 modules: contract 1 -> 0.01 lot = $0.01/pt
Pn,Dn,ATn=st.nq_context()
for nm,b,k in (("NOISE_BAND",st.base_nb(Dn,ATn),1.0),("AY_DONUMU",st.base_tom(Dn,ATn),4.0)):
    b=b.dropna(subset=["atr"]); b=b[pd.DatetimeIndex(b.key)>=A]
    report(f"{nm} k{k} (0.01 lot=$0.01/puan)",k*b.atr*0.01)
    print(f"   {nm}: gereken notional medyan ${(RISK/(k*b.atr/b.entry)).median():.0f} (endeks 1:10 tavan ${EQ*10:.0f})")
b7=st.b7_trades(Pn,Dn,ATn,4.0); b7=b7[pd.DatetimeIndex(b7.key)>=A]
report("B7 k4 (0.01 lot)",4*b7.atr*0.01); print(f"   B7 gereken notional medyan ${(RISK/(4*b7.atr/b7.entry)).median():.0f}")
print("SWEEP: US100 0.01 lot $0.01/puan -> 1000 puandan kisa her stop icin 0.5% risk karsilanir (stop mesafesi dosyada yok)")
