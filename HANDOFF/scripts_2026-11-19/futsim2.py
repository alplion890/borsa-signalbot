"""Rapid Pro 25K one-shot 30d with Sweep (risk-sized, mf) + NB at fixed 1 MNQ."""
t=open(r"../HANDOFF/scripts_2026-11-19/futsim.py",encoding="utf-8").read(); exec(t[:t.index("r,L=combo")])
u=open(r"../HANDOFF/scripts_2026-11-19/nbfut.py",encoding="utf-8").read(); exec(u[u.index("def nb_fut"):u.index("if __name__")])
nb,_=nb_fut(25000); nbL=np.minimum(nb,0)*1.5
rs,Ls=combo(["SWEEP"])
for mf in (1.0,2.0,3.0):
    r=rs*mf+nb; L=Ls*mf+nbL
    res=[one(r[ix],L[ix],1.0) for ix in IDX]; k=np.array([a for a,_,_ in res]); d=np.array([b for _,b,_ in res]); amt=np.array([c for *_,c in res]); pay=k=="payout"
    uu,cc=np.unique(k,return_counts=True)
    print(f"Sweep x{mf} + NB 1MNQ: 30g payout %{100*pay.mean():.0f}"+(f" (gun {np.median(d[pay]):.0f}, ${np.median(amt[pay]):.0f})" if pay.any() else "")+" | "+", ".join(f"{a} %{100*b/len(k):.0f}" for a,b in zip(uu,cc) if a!="payout"))
    r0=r-r.mean(); res=[one(r0[ix],np.minimum(r0[ix],0)*1.5,1.0) for ix in IDX]; k0=np.array([a for a,_,_ in res])
    print(f"   SIFIR-EDGE: payout %{100*(k0=='payout').mean():.0f}, patlama %{100*np.char.startswith(k0.astype(str),'patladi').mean():.0f}")
