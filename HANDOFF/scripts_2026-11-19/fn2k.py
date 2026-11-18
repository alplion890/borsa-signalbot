"""FN Stellar Instant 2K $41.99: min-lot effects (ASSUMED specs) + module sets + zero edge."""
t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/cheap_inst.py",encoding="utf-8").read()
exec(t[:t.index("MF=(0.25")])
EQ=2000.0; TGT=10.0
# Donchian XAU at real lots: 0.01 lot = 1 oz, step 1 oz
_e=x1.close.reindex(r0.index); rk_=np.where(le.reindex(r0.index),_e-lsl.reindex(r0.index),ssl.reindex(r0.index)-_e).astype(float); oz=np.maximum(1,np.floor(TGT/rk_)); eff=oz*rk_/EQ
dx_=pd.Series(T["DONCHIAN_XAU"].to_numpy()*eff,index=T["DONCHIAN_XAU"].index); dx_=dx_[dx_.index>=A]
M["DONCHIAN_minlot"]=(arr(dx_.groupby(dx_.index.normalize()).sum()),None)
M["DONCHIAN_minlot"]=(M["DONCHIAN_minlot"][0],np.minimum(M["DONCHIAN_minlot"][0],0)*1.5)
dr=pd.Series(eff,index=T["DONCHIAN_XAU"].index); dr=dr[dr.index>=A]
print(f"Donchian 2K gercek lot: islem basi risk medyan %{100*dr.median():.2f}, yillik getiri %{dx_.sum()/len(idx)*365*100:.1f} (ideal %0.5'te %{M['DONCHIAN_XAU'][0].sum()/len(idx)*365*100:.1f})")
# BTC at 0.01 BTC min lot
for k_ in ("BTC_21_23","BTC_GECE"):
    b,p,c,kk,_=bases[k_]; tr=st.apply_stop(p,b,kk).dropna(subset=["atr","gross"]); tr=tr[pd.DatetimeIndex(tr.key)>=A]
    need=TGT/(kk*tr.atr); lot=np.maximum(0.01,np.floor(need/0.01)*0.01); ret=(tr.gross-2*c)*lot*tr.entry/EQ
    s=ret.groupby(pd.DatetimeIndex(tr.key).normalize()).sum(); M[k_+"_minlot"]=(arr(s),np.minimum(arr(s),0)*1.5)
    print(f"{k_} 0.01 BTC: islem basi risk medyan %{100*(lot*kk*tr.atr/EQ).median():.2f}, yillik %{s.sum()/len(idx)*365*100:.1f} (ideal %{M[k_][0].sum()/len(idx)*365*100:.1f})")
base=["SWEEP","NOISE_BAND","AY_DONUMU_NQ","B7"]
SETS={"A) 7 modul ideal lot (onceki model)":NAMES,
      "B) 7 modul, XAU+BTC gercek min lot (0.01)":base+["DONCHIAN_minlot","BTC_21_23_minlot","BTC_GECE_minlot"],
      "C) XAU gercek min lot, BTC min 0.001 (ideal)":base+["DONCHIAN_minlot","BTC_21_23","BTC_GECE"],
      "D) XAU'suz, BTC min 0.001":base+["BTC_21_23","BTC_GECE"],
      "E) XAU'suz, BTC'siz (yalniz US100)":base}
for nm,keys in SETS.items():
    r,L=combo(keys); print(f"\n{nm}: yil %{r.sum()/len(r)*365*100:.1f} sharpe {r.mean()/r.std()*np.sqrt(365):.2f} en kotu gun(stres) %{L.min()*100:.2f}")
    for mf in (0.5,1.0): print(f"   x{mf}: {run(fn2,r,L,mf)}")
    r0=r-r.mean(); print(f"   SIFIR-EDGE x1: {run(fn2,r0,np.minimum(r0,0)*1.5,1.0)}")
