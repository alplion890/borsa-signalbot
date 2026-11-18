"""FN 2K with official index contract size 10 (min lot 0.01 ASSUMED). NB at real min lot."""
t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/cheap_inst.py",encoding="utf-8").read()
exec(t[:t.index("MF=(0.25")])
EQ=2000.0; TGT=10.0
b,p,c,kk,_=bases["NOISE_BAND"]; tr=st.apply_stop(p,b,kk).dropna(subset=["atr","gross"]); tr=tr[pd.DatetimeIndex(tr.key)>=A]
need=TGT/(kk*tr.atr*10); lot=np.maximum(0.01,np.floor(need/0.01)*0.01); effr=lot*10*kk*tr.atr/EQ
ret=(tr.gross-2*c)*lot*10*tr.entry/EQ; s=ret.groupby(pd.DatetimeIndex(tr.key).normalize()).sum()
M["NB_minlot"]=(arr(s),np.minimum(arr(s),0)*1.5)
print(f"NB 2K kontrat 10: islem basi risk medyan %{100*effr.median():.2f} p90 %{100*effr.quantile(.9):.2f} max %{100*effr.max():.2f}")
SETS={"F) yalniz Sweep":["SWEEP"],"G1) Sweep + BTC 2 modul (BTC min 0.001 ise)":["SWEEP","BTC_21_23","BTC_GECE"],
      "G2) Sweep + NB gercek min lot + BTC 2 modul":["SWEEP","NB_minlot","BTC_21_23","BTC_GECE"],
      "G3) Sweep + NB gercek min lot":["SWEEP","NB_minlot"]}
for nm,keys in SETS.items():
    r,L=combo(keys); print(f"\n{nm}: yil %{r.sum()/len(r)*365*100:.1f} sharpe {r.mean()/r.std()*np.sqrt(365):.2f} en kotu gun(stres) %{L.min()*100:.2f}")
    print(f"   x1: {run(fn2,r,L,1.0)}")
    r0=r-r.mean(); print(f"   SIFIR-EDGE x1: {run(fn2,r0,np.minimum(r0,0)*1.5,1.0)}")
