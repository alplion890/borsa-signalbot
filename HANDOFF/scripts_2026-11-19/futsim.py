"""FundedNext Futures Rapid Pro 25K (+DLL add-on, $44.99) one-shot 30 days. Sweep on MNQ (continuous sizing; rounding ignored).
Rules (official help center, read 2026-11-20): target $1,500; MLL $1,000 EOD trailing, locks at 25,100, floating breach instant;
DLL $500 soft (day stops); funded: same MLL, withdraw every 3 days, needs $500 cycle profit, best day <=40% of cycle profit,
min $250, cap $600 (first 3), split 90%. Futures commission NOT measured (r carries CFD cost model)."""
t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/fn2k_c10.py",encoding="utf-8").read()
exec(t[:t.index("SETS={")])
S=25000.0; MLL=1000/S; LOCK=100/S; TGT=1500/S; DLL=500/S
def day(x,q,bal,peak):
    if DLL and q<=-DLL: x=max(x,-DLL); q=-DLL          # soft DLL: flattened at -$500
    floor=min(peak-MLL,LOCK)
    if bal+q<=floor: return None
    return x
def one(r,L,mf,days=30,cap=600,split=.90):
    bal=peak=0.0; ph="ch"; cyc=0; best=0.0; cb=0.0
    for d in range(days):
        x=day(r[d]*mf,min(L[d]*mf,r[d]*mf,0),bal,peak)
        if x is None: return ("patladi_challenge" if ph=="ch" else "patladi_fonlu"),d+1,0.0
        bal+=x; peak=max(peak,bal)
        if ph=="ch":
            if bal>=TGT: ph="fn"; bal=peak=0.0; cyc=0; best=0.0; cb=0.0
            continue
        cyc+=1; cb+=x; best=max(best,x)
        if cyc>=3 and cb>=500/S and best<=.40*cb and bal*S>=250:
            return "payout",d+1,min(bal*S,cap)*split
    return ("challenge_devam" if ph=="ch" else "fonlu_bekliyor"),days,0.0
def rep(nm,r,L,mfs):
    for mf in mfs:
        res=[one(r[ix],L[ix],mf) for ix in IDX]; k=np.array([a for a,_,_ in res]); d=np.array([b for _,b,_ in res]); amt=np.array([c for *_,c in res])
        pay=k=="payout"; u,c=np.unique(k,return_counts=True)
        print(f"{nm} x{mf}: 30 gunde payout %{100*pay.mean():.0f}"+(f" (gun medyan {np.median(d[pay]):.0f}, tutar medyan ${np.median(amt[pay]):.0f})" if pay.any() else "")+" | "+", ".join(f"{a} %{100*b/len(k):.0f}" for a,b in zip(u,c) if a!="payout"))
r,L=combo(["SWEEP"])
print(f"SWEEP yil %{r.sum()/len(r)*365*100:.1f} (risk %0.5/islem)")
rep("SWEEP",r,L,(1.0,2.0,3.0,4.0))
r0=r-r.mean(); rep("  SIFIR-EDGE",r0,np.minimum(r0,0)*1.5,(1.0,2.0,3.0,4.0))
# 60 gun penceresi
def rep60(mf):
    res=[one(r[ix],L[ix],mf,days=60) for ix in IDX]; k=np.array([a for a,_,_ in res]); print(f"SWEEP x{mf} 60 gunde payout %{100*(k=='payout').mean():.0f}")
for mf in (2.0,3.0): rep60(mf)
