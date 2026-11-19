"""Exit-time replay for Sweep (NQ 15m) and Donchian XAU (1h): how many trades cross the daily break / weekend?"""
import numpy as np, pandas as pd
from intraday import meta_label_lab as m, donchian_xau_lab as dx
from intraday.honest_engine import simulate_trades
NY="America/New_York"
def replay(df,le,se,lsl,ltp,ssl,stp,r0,maxh):
    ix=df.index; pos=ix.get_indexer(r0.index); H=df.high.to_numpy(); L=df.low.to_numpy(); out=[]
    for t,i in zip(r0.index,pos):
        lg=bool(le.iloc[i]); sl=(lsl if lg else ssl).iloc[i]; tp=(ltp if lg else stp).iloc[i]; j=i+1; end=min(i+maxh,len(ix)-1)
        while j<=end:
            if (lg and (L[j]<=sl or H[j]>=tp)) or ((not lg) and (H[j]>=sl or L[j]<=tp)): break
            j+=1
        out.append((t,ix[min(j,end)]))
    return pd.DataFrame(out,columns=["t0","t1"])
def classify(x,name):
    a=pd.to_datetime(x.t0).dt.tz_localize("UTC").dt.tz_convert(NY); b=pd.to_datetime(x.t1).dt.tz_localize("UTC").dt.tz_convert(NY)
    sess=lambda s:(s-pd.Timedelta(hours=17)).dt.normalize()  # CFD day rolls at 17:00 NY
    over=(sess(b)>sess(a)); wk=(a.dt.isocalendar().week!=b.dt.isocalendar().week)|((b-a)>pd.Timedelta(days=2))
    hrs=(b-a).dt.total_seconds()/3600
    print(f"{name}: n={len(x)} | gunluk araya sarkan %{100*over.mean():.0f} | hafta sonuna sarkan %{100*wk.mean():.0f} | tutma saat medyan {hrs.median():.1f} p90 {hrs.quantile(.9):.1f}")
    return over,wk
spec=m.spec_by_name("SWEEP_CORE"); df=m.clean(m.load_history(spec.symbol,spec.tf,start_year=2012))
le,se,lsl,ltp,ssl,stp=m._sweep_inputs(df,spec)
r0=simulate_trades(df,le,se,lsl,ltp,ssl,stp,m.lcc.zero(spec.symbol),min_rr=spec.min_rr,max_rr=spec.max_rr,max_hold=spec.max_hold)
r0=r0[r0.index>="2022"]; x=replay(df,le,se,lsl,ltp,ssl,stp,r0,spec.max_hold); o,w=classify(x,"SWEEP 2022+")
print(f"   gun ici kalanlar ort R {r0[~o.to_numpy()].mean():.3f} (n {(~o).sum()}) | sarkanlar ort R {r0[o.to_numpy()].mean():.3f} (n {o.sum()})  [maliyetsiz R]")
x1=dx._resample_1h(m.clean(m.load_history("XAUUSD","5m",start_year=2012)))
le,se,lsl,ltp,ssl,stp=dx.build_signals(x1,dx.DonchianCase(20))
r0=simulate_trades(x1,le,se,lsl,ltp,ssl,stp,m.lcc.zero("XAUUSD"),min_rr=dx.RR-0.01,max_rr=dx.RR,max_hold=dx.MAX_HOLD_BARS)
r0=r0[r0.index>="2022"]; x=replay(x1,le,se,lsl,ltp,ssl,stp,r0,dx.MAX_HOLD_BARS); o,w=classify(x,"DONCHIAN XAU 2022+")
print(f"   gun ici kalanlar ort R {r0[~o.to_numpy()].mean():.3f} (n {(~o).sum()}) | sarkanlar ort R {r0[o.to_numpy()].mean():.3f} (n {o.sum()})  [maliyetsiz R]")
