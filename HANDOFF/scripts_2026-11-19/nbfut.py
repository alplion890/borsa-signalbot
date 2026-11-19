"""NB on MNQ at fixed 1 contract ($2/pt) for account size EQ; returns daily series key NB_fut. Futures commission NOT measured (CFD cost c used)."""
t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/fn2k_c10.py",encoding="utf-8").read()
exec(t[:t.index("SETS={")])
def nb_fut(EQ,ncon=1):
    b,p,c,kk,_=bases["NOISE_BAND"]; tr=st.apply_stop(p,b,kk).dropna(subset=["atr","gross"]); tr=tr[pd.DatetimeIndex(tr.key)>=A]
    ret=(tr.gross-2*c)*ncon*2.0*tr.entry/EQ; s=ret.groupby(pd.DatetimeIndex(tr.key).normalize()).sum()
    risk=kk*tr.atr*2.0*ncon
    return arr(s),risk
if __name__=="__main__":
    for EQ in (25000,50000):
        a,rk=nb_fut(EQ); print(f"NB 1 MNQ @{EQ}: yil %{a.sum()/len(a)*365*100:.1f} | islem gunu/yil {(a!=0).sum()/len(a)*365:.0f} | stop $ medyan {rk.median():.0f} | en kotu gun %{a.min()*100:.2f}")
