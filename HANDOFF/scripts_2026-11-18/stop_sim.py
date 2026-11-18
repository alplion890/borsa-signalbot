"""Firm simulation: portfolio with stops (NB k1, BTC21-23 k1.5, BTC gece k1.5, TOM k4, B7 k4) vs without."""
exec(open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/firms.py").read())
from intraday import stop_testi as st
from intraday.seffaf_adaylari import load_btc_1h
_t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/firms.py").read()
src=_t[_t.index("def journey"):_t.index("def boot_paths")]
src=src.replace("def journey(r, f, mc, mf, H)","def journey2(r, L, f, mc, mf, H)").replace("x=r[t]; t+=1","x=r[t]; xl=L[t]; t+=1")
src=src.replace("p=x*mf\n        floor","p=x*mf\n        q=min(xl*mf,p,0)\n        floor").replace("        q=min(p,0)*IK\n        if (f","        if (f")
exec(src); assert "xl*mf" in src
A="2022-01-01"; CAL=None
cn,cb=cost_of("NASDAQ100"),cost_of("BTCUSDT")
nq=st.nq_context(); P,D,AT=nq; bc=st.btc_context(); h1=load_btc_1h()
bases={"NOISE_BAND":(st.base_nb(D,AT),P,cn,1.0,.75),"AY_DONUMU_NQ":(st.base_tom(D,AT),P,cn,4.0,.5),
       "BTC_21_23":(st.base_btc_21_23(h1,bc[1],bc[2]),bc[0],cb,1.5,.35),"BTC_GECE":(st.base_btc_gece(h1,bc[1],bc[2]),bc[0],cb,1.5,.101)}
def daily_of(tr,scale,cost,datekey):
    x=tr.dropna(subset=["atr","gross"]); net=(x.gross-2*cost)*scale
    return net.groupby(pd.DatetimeIndex(x[datekey]).normalize()).sum()
ser={"stop":{},"nostop":{},"risk":{}}; risk=[]; rcount=[]
for k_,(b,p,c,k,sc) in bases.items():
    for lab,kk in (("nostop",None),("stop",k)):
        tr=st.apply_stop(p,b,kk); ser[lab][k_]=daily_of(tr,sc,c,"key")
        if lab=="stop":
            x=tr.dropna(subset=["atr","gross"]); rk=(x.gross-2*c)/(k*x.atr/x.entry)*0.005
            ser["risk"][k_]=rk.groupby(pd.DatetimeIndex(x.key).normalize()).sum()
            rcount.append((rk*0+.005).groupby(pd.DatetimeIndex(x.key).normalize()).sum())
            risk.append((sc*k*x.atr/x.entry).groupby(pd.DatetimeIndex(x.key).normalize()).sum())
# B7 mark-to-market
cl,lo_=D.close.to_numpy(float),D.low.to_numpy(float); di=pd.DatetimeIndex(D.index)
def b7_mtm(k,sc=.35,riskbud=None):
    sc0=sc; tr=st.b7_trades(P,D,AT,k); r=pd.Series(0.0,index=di); L=pd.Series(0.0,index=di); rk=pd.Series(0.0,index=di)
    for x in tr.itertuples():
        sc=riskbud/(k*x.atr/x.entry) if riskbud else sc0
        i0=di.get_loc(x.key); i1=di.get_loc(pd.Timestamp(x.exit_ts.tz_localize("UTC").tz_convert(st.NY).date()))
        for j in range(i0+1,i1+1):
            prev=cl[j-1]; last=j==i1; cur=x.exit if last else cl[j]
            ret=cur/prev-1-0.000118*(di[j]-di[j-1]).days-(cn if j==i0+1 else 0)-(cn if last else 0)
            low=ret if (last and x.stopped) else min(lo_[j]/prev-1,ret)
            r.iloc[j]+=ret*sc; L.iloc[j]+=min(low,ret)*sc
            if k: rk.iloc[j]+=sc*k*x.atr/x.entry
    return r,L,rk
b7={"nostop":b7_mtm(None),"stop":b7_mtm(4.0),"risk":b7_mtm(4.0,riskbud=.005)}
idx=pd.date_range(A,"2026-11-17")
def comp(series): return pd.concat(series,axis=1).reindex(idx).fillna(0).sum(axis=1).to_numpy()
base_fixed=pd.concat([(T[k][T[k].index>=A]*SC[k]).groupby(T[k][T[k].index>=A].index.normalize()).sum() for k in ("SWEEP","DONCHIAN_XAU")],axis=1).reindex(idx).fillna(0).sum(axis=1).to_numpy()
def portfolio(lab,with_b7):
    r=base_fixed+comp([s for s in ser[lab].values()]); L=np.minimum(r,0)*1.5
    if with_b7:
        br,bl,_=b7[lab]; br=br.reindex(idx).fillna(0).to_numpy(); bl=bl.reindex(idx).fillna(0).to_numpy()
        L=np.minimum(r,0)*1.5+bl; r=r+br
    return r,L
# open-risk upper bound (stopped): Sweep/Donchian 0.5% per trade-day
sd=pd.concat([(T[k][T[k].index>=A]*0+.005).groupby(T[k][T[k].index>=A].index.normalize()).sum() for k in ("SWEEP","DONCHIAN_XAU")],axis=1).sum(axis=1)
ro=pd.concat(risk+[sd],axis=1).reindex(idx).fillna(0).sum(axis=1); ro7=ro+b7["stop"][2].reindex(idx).fillna(0)
rc=pd.concat(rcount+[sd],axis=1).reindex(idx).fillna(0).sum(axis=1); rc7=rc+(b7["risk"][2].reindex(idx).fillna(0)>0)*.005
print(f"RISK-BOYUTLU acik risk ust sinir: 6li max %{rc.max()*100:.2f} >%3 gun %{100*(rc>.03).mean():.1f} | +B7 max %{rc7.max()*100:.2f} >%3 gun %{100*(rc7>.03).mean():.1f}")
print(f"ACIK RISK ust sinir (gun ici ayni gun toplami), risk x1: 6li max %{ro.max()*100:.2f} >%3 gun %{100*(ro>.03).mean():.1f} | +B7k4 max %{ro7.max()*100:.2f} >%3 gun %{100*(ro7>.03).mean():.1f}")
def journey_fx(r,L,mf,H,price=0.0,split=.80,mll=.08,dll=.08,buf=.04,cyc=14):
    cash=-price; nch=1; first=None; npay=0; t=0; bal=0; hw=0; locked=False; cs=0
    while t<H:
        x=r[t]*mf; q=min(L[t]*mf,x,0); t+=1
        floor=0.0 if locked else min(hw-mll,0.0)
        if q<=-dll or bal+q<=floor:
            cash-=price; nch+=1; bal=0; hw=0; locked=False; cs=t; continue
        bal+=x; hw=max(hw,bal); locked=locked or hw>=mll
        if t-cs>=cyc:
            cs=t
            if bal>buf:
                pay=bal-buf; npay+=1; cash+=pay*5000*split; bal-=pay; locked=True
                if first is None: first=t
    return first,None,cash,None,nch
H=365; NP=500; rng=np.random.default_rng(20261118); N=len(idx)
IDX=np.array([np.concatenate([np.arange(s,s+20) for s in rng.integers(0,N-20,H//20+1)])[:H] for _ in range(NP)])
def run(fn,r,L,mf):
    out=[fn(r[ix],L[ix],mf) for ix in IDX]
    fp=np.array([o[0] if o[0] else np.nan for o in out]); c=np.array([o[2] for o in out]); n=np.array([o[4] for o in out])
    pre=np.mean([ (o[4]>1 and (o[0] is None)) or False for o in out])
    return f"ilk payout med {np.nanmedian(fp):.0f}g (yok %{100*np.mean(np.isnan(fp)):.0f}) | 12ay net med ${np.median(c):.0f} zarar %{100*np.mean(c<0):.0f} | hesap ort {n.mean():.1f}"
FN=FIRMS["FN_INSTANT"]
firms={"FN_INSTANT 5K $149.99":lambda r,L,mf: journey2(r,L,FN,1,mf,H),
       "FXIFY Instant 5K (ucret HARIC, split %80 varsayim)":lambda r,L,mf: journey_fx(r,L,mf,H)}
sets=[("6li stop'suz","nostop",False),("6li stop'lu","stop",False),("6li+B7 0.35x stop'suz","nostop",True),("6li+B7 0.35x stop'lu(k4)","stop",True),("6li RISK-BOYUTLU stop'lu","risk",False),("6li+B7 RISK-BOYUTLU stop'lu","risk",True)]
for nm,lab,w in sets:
    r,L=portfolio(lab,w); print(f"{nm}: yil% {r.sum()/len(r)*365*100:.1f} sharpe {r.mean()/r.std()*np.sqrt(365):.2f} en kotu gun(stres) %{L.min()*100:.2f}")
for fn_name,fn in firms.items():
    print("\n===",fn_name)
    for mf in (1.0,0.5):
        for nm,lab,w in sets:
            r,L=portfolio(lab,w); print(f" x{mf} {nm}: {run(fn,r,L,mf)}")
        r,L=portfolio("risk",True); r0=r-r.mean(); print(f" x{mf} SIFIR-EDGE (6li+B7 risk-boyutlu): {run(fn,r0,np.minimum(L-(r-r0),0)*0+np.minimum(r0,0)*1.5,mf)}")
