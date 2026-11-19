"""MNQ ($2/pt) sizing for intraday set: NB k1 ATR stop, Sweep stop points (known dist). Futures prop accounts 25K/50K."""
import numpy as np, pandas as pd
from intraday import stop_testi as st
A="2022-01-01"
Pn,Dn,ATn=st.nq_context()
b=st.base_nb(Dn,ATn).dropna(subset=["atr"]); b=b[pd.DatetimeIndex(b.key)>=A]
stop=1.0*b.atr*2.0  # $ per 1 MNQ
print(f"NB n={len(b)} ATR pt medyan {b.atr.median():.0f} p90 {b.atr.quantile(.9):.0f} | 1 MNQ stop $ medyan {stop.median():.0f} p90 {stop.quantile(.9):.0f} max {stop.max():.0f}")
for eq in (25000,50000):
    for rp in (0.005,0.01):
        tgt=eq*rp; n=np.floor(tgt/stop); eff=n*stop/tgt
        print(f"  eq {eq} risk {rp*100:.1f}% (${tgt:.0f}): kontrat medyan {np.median(n):.0f} | 0 kontrat (islem yok) %{100*(n==0).mean():.0f} | gercek/hedef risk medyan {np.median(eff[n>0]):.2f}")
for nm,pts in (("Sweep medyan",29),("Sweep p90",57),("Sweep max",105)):
    print(f"{nm} {pts}pt -> 1 MNQ ${pts*2}")
