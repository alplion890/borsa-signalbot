"""Intraday-only set (Sweep + NB + BTC_21_23, risk-sized 0.5%) on candidate instant accounts."""
t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/cheap_inst.py",encoding="utf-8").read()
exec(t[:t.index("MF=(0.25")])
def inst(r,L,mf,size,price,mll,trail,lock,dll,cons,thr,split,cyc=0):
    cash=-price; nch=1; first=None; npay=0; bal=0.0; peak=0.0; best=0.0; t=0; cs=0
    while t<len(r):
        x=r[t]*mf; q=min(L[t]*mf,x,0); t+=1
        floor=(min(peak-mll,0.0) if lock else peak-mll) if trail else -mll
        if (dll and q<=-dll) or bal+q<=floor:
            cash-=price; nch+=1; bal=peak=best=0.0; cs=t; continue
        bal+=x; best=max(best,x)
        if trail: peak=max(peak,bal)  # EOD trailing on closing balance
        if bal>=thr and (cons is None or best<=cons*bal) and t-cs>=cyc:
            npay+=1; cash+=bal*size*split; first=first or t; bal=0.0; best=0.0; cs=t
            if trail and not lock: peak=0.0
    return first,None,cash,None,nch
FIRMSI={
 "Instant Funding Evolve 10K $49 (4% kayan EOD, kilitsiz varsayim; %40 tutarlilik; min $250)":dict(size=10000,price=49,mll=.04,trail=True,lock=False,dll=None,cons=.40,thr=.025,split=.80),
 "  ayni, kayan baslangicta kilitlenir varsayimi":dict(size=10000,price=49,mll=.04,trail=True,lock=True,dll=None,cons=.40,thr=.025,split=.80),
 "FTM Instant Pro 5K $37.95 (3% statik, 3% gunluk, %15 tutarlilik, %50 pay)":dict(size=5000,price=37.95,mll=.03,trail=False,lock=False,dll=.03,cons=.15,thr=.01,split=.50),
 "FN Stellar Instant 2K $41.99 (6% kayan kilitli, 14 gun)":dict(size=2000,price=41.99,mll=.06,trail=True,lock=True,dll=None,cons=None,thr=.01,split=.70,cyc=14),
}
SET=["SWEEP","NOISE_BAND","BTC_21_23"]
r,L=combo(SET); print(f"GUN ICI SET {SET}: yil %{r.sum()/len(r)*365*100:.1f} sharpe {r.mean()/r.std()*np.sqrt(365):.2f} en kotu gun(stres) %{L.min()*100:.2f}")
for nm,f in FIRMSI.items():
    print("\n"+nm)
    for mf in (0.5,1.0,2.0): print(f"   risk x{mf}: {run(lambda a,b,m,f=f: inst(a,b,m,**f),r,L,mf)}")
    r0=r-r.mean(); print(f"   SIFIR-EDGE x1: {run(lambda a,b,m,f=f: inst(a,b,m,**f),r0,np.minimum(r0,0)*1.5,1.0)}")
