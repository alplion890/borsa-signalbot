"""One account, no rebuy: P(first payout within 30 days), P(blow within 30 days), first payout amount. FN Instant 2K $41.99."""
t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/fn2k_c10.py",encoding="utf-8").read()
exec(t[:t.index("SETS={")])
def one(r,L,mf,size=2000,mll=.06,split=.70,days=30):
    bal=peak=0.0
    for t_ in range(days):
        x=r[t_]*mf; q=min(L[t_]*mf,x,0); floor=min(peak-mll,0.0)
        if bal+q<=floor: return "patladi",t_+1,0.0
        bal+=x; peak=max(peak,bal)
        if bal>=.05 or (t_+1>=14 and bal>=.01): return "payout",t_+1,bal*size*split
    return "bekliyor",days,0.0
for nm,keys in (("Sweep+NB(min lot)+BTC 21-23+BTC gece",["SWEEP","NB_minlot","BTC_21_23","BTC_GECE"]),("Sweep+NB(min lot) (BTC sigmazsa)",["SWEEP","NB_minlot"])):
    r,L=combo(keys)
    for mf in (1.0,2.0,3.0):
        res=[one(r[ix],L[ix],mf) for ix in IDX]; k=np.array([a for a,_,_ in res]); d=np.array([b for _,b,_ in res]); amt=np.array([c for *_,c in res])
        pay=k=="payout"
        print(f"{nm} risk x{mf}: 30 gunde payout %{100*pay.mean():.0f} (gun medyan {np.median(d[pay]):.0f}, tutar medyan ${np.median(amt[pay]):.0f}) | patlama %{100*(k=='patladi').mean():.0f} | hala bekliyor %{100*(k=='bekliyor').mean():.0f}")
    r0=r-r.mean(); res=[one(r0[ix],np.minimum(r0[ix],0)*1.5,1.0) for ix in IDX]; k=np.array([a for a,_,_ in res])
    print(f"   SIFIR-EDGE x1: payout %{100*(k=='payout').mean():.0f} patlama %{100*(k=='patladi').mean():.0f}")
