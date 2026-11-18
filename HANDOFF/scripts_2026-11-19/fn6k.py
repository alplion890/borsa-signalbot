"""FN Stellar 2-Step 6K $34.99 (NOVSTR): real min lots at 6K (index contract 10, gold 100, min 0.01 ASSUMED; BTC 0.001 ASSUMED)."""
t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/cheap_inst.py",encoding="utf-8").read()
exec(t[:t.index("MF=(0.25")])
EQ=6000.0; TGT=0.005*EQ
def nq_min(key,trf,c,kk,pp=10):
    tr=trf.dropna(subset=["atr","gross"]); tr=tr[pd.DatetimeIndex(tr.key)>=A]
    lot=np.maximum(0.01,np.floor(TGT/(kk*tr.atr*pp)/0.01)*0.01); eff=lot*pp*kk*tr.atr/EQ
    s=((tr.gross-2*c)*lot*pp*tr.entry/EQ).groupby(pd.DatetimeIndex(tr.key).normalize()).sum()
    print(f"{key} 6K: risk medyan %{100*eff.median():.2f} p90 %{100*eff.quantile(.9):.2f} max %{100*eff.max():.2f}")
    return arr(s)
b,p,c,kk,_=bases["NOISE_BAND"]; r_=nq_min("NB",st.apply_stop(p,b,kk),c,kk); M["NB6"]=(r_,np.minimum(r_,0)*1.5)
b,p,c,kk,_=bases["AY_DONUMU_NQ"]; r_=nq_min("TOM",st.apply_stop(p,b,kk),c,kk); M["TOM6"]=(r_,np.minimum(r_,0)*1.5)
b7t=st.b7_trades(P,D,AT,4.0); r_=nq_min("B7(kapanis bazli)",b7t.assign(gross=b7t.exit/b7t.entry-1) if "gross" not in b7t else b7t,cn,4.0); M["B76"]=(r_,np.minimum(r_,0)*1.5)
_e=x1.close.reindex(r0.index); rk_=np.where(le.reindex(r0.index),_e-lsl.reindex(r0.index),ssl.reindex(r0.index)-_e).astype(float)
oz=np.maximum(1,np.floor(TGT/rk_)); eff=oz*rk_/EQ; dx_=pd.Series(T["DONCHIAN_XAU"].to_numpy()*eff,index=T["DONCHIAN_XAU"].index); dx_=dx_[dx_.index>=A]
dr=pd.Series(eff,index=T["DONCHIAN_XAU"].index); dr=dr[dr.index>=A]; print(f"Donchian 6K: risk medyan %{100*dr.median():.2f} p90 %{100*dr.quantile(.9):.2f} max %{100*dr.max():.2f}")
r_=arr(dx_.groupby(dx_.index.normalize()).sum()); M["DX6"]=(r_,np.minimum(r_,0)*1.5)
F=dict(FIRMS["FN_2STEP"],price=34.99)
SETS={"S1) Sweep+NB+Donchian+BTC2 (6K gercek lot)":["SWEEP","NB6","DX6","BTC_21_23","BTC_GECE"],
      "S2) S1 + B7 + Ay donumu (gercek lot)":["SWEEP","NB6","DX6","BTC_21_23","BTC_GECE","B76","TOM6"],
      "S3) BTC'siz: Sweep+NB+Donchian":["SWEEP","NB6","DX6"]}
for nm,keys in SETS.items():
    r,L=combo(keys); print(f"\n{nm}: yil %{r.sum()/len(r)*365*100:.1f} sharpe {r.mean()/r.std()*np.sqrt(365):.2f} en kotu gun(stres) %{L.min()*100:.2f}")
    for mc in (1,2,3): print(f"   challenge x{mc}: {run(lambda a,b,mf: journey2(a,b,F,mc,mf,H),r,L,1.0)}")
    r0=r-r.mean(); print(f"   SIFIR-EDGE x2: {run(lambda a,b,mf: journey2(a,b,F,2,mf,H),r0,np.minimum(r0,0)*1.5,1.0)}")
