exec(open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/firms.py").read())
import inspect
_t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/firms.py").read()
src=_t[_t.index("def journey"):_t.index("def boot_paths")].replace("def journey(r, f, mc, mf, H)","def journey2(r, L, f, mc, mf, H)")
src=src.replace("x=r[t]; t+=1","x=r[t]; xl=L[t]; t+=1")
src=src.replace("tgt,mind=f[\"phases\"][stage]; p=x*mc\n            q=min(p,0)*IK","tgt,mind=f[\"phases\"][stage]; p=x*mc\n            q=min(xl*mc,p,0)")
src=src.replace("p=x*mf\n        floor","p=x*mf\n        q=min(xl*mf,p,0)\n        floor").replace("        q=min(p,0)*IK\n        if (f","        if (f")
exec(src); assert "xl*mf" in src and "xl*mc" in src
S=r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad"
a="2022-01-01"; base=["SWEEP","DONCHIAN_XAU","NOISE_BAND","BTC_21_23","BTC_GECE","AY_DONUMU_NQ"]
rb=daily(base); idx=pd.date_range(a,periods=len(rb))
m=pd.read_csv(S+"/b7_mtm.csv",index_col=0,parse_dates=True).reindex(idx).fillna(0)
b2=pd.read_csv("outputs/intraday/seffaf_adaylari/B2_trades.csv",parse_dates=["date"]).set_index("date").net_central_swap.reindex(idx).fillna(0).to_numpy()*.5
def mk(f7,withb2):
    r=rb+f7*m.r.to_numpy()+(b2 if withb2 else 0); L=np.minimum(rb,0)*1.5+f7*m.lo.to_numpy()+(np.minimum(b2,0)*1.5 if withb2 else 0)
    return r,L
H=365; NP=500; rng=np.random.default_rng(20261118); N=len(rb)
IDX=np.array([np.concatenate([np.arange(s,s+20) for s in rng.integers(0,N-20,H//20+1)])[:H] for _ in range(NP)])
def run(r,L,f,mf):
    out=[]
    for ix in IDX:
        res=journey2(r[ix],L[ix],f,1,mf,H); fp=res[0]
        pre = journey2(r[ix][:fp],L[ix][:fp],f,1,mf,fp)[4]>1 if fp else res[4]>1
        out.append((fp,res[2],res[4],pre))
    fp=np.array([o[0] if o[0] else np.nan for o in out]); c=np.array([o[1] for o in out])
    return (f"ilkpayout-oncesi-patlama %{100*np.mean([o[3] for o in out]):.0f} | payout med {np.nanmedian(fp):.0f}g (1 yilda hic payout yok %{100*np.mean(np.isnan(fp)):.0f})"
            f" | 12ay net med ${np.median(c):.0f} zarar %{100*np.mean(c<0):.0f} | alinan hesap ort {np.mean([o[2] for o in out]):.1f}")
sets=[("6li",0,False),("6li+B7 0.2x",.2,False),("6li+B7 0.35x",.35,False),("6li+B7 0.5x",.5,False),("6li+B7 0.35x+B2(swapli)",.35,True)]
for fn in ("FN_INSTANT","FYFX_INST","MAVEN_INST"):
    f=FIRMS[fn]; print(f"\n=== {fn} {f['size']//1000}K ${f['price']} ===")
    for mf in (1.0,0.5):
        for nm,f7,wb in sets:
            r,L=mk(f7,wb); print(f" risk x{mf} {nm}: {run(r,L,f,mf)}")
        r,L=mk(.35,True); r0=r-r.mean(); print(f" risk x{mf} SIFIR-EDGE kontrol (6li+B7+B2): {run(r0,L-(r-r0).clip(max=0)*0,f,mf)}")
