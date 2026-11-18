t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/cheap_inst.py",encoding="utf-8").read()
exec(t[:t.index("MF=(0.25")])
def maven_v(r,L,mf,flo=.01,dl=.02,tr=.03,cons=.20,thr=.03,log=None):
    f=MV; S=f["size"]; price=f["price"]; cash=-price; nch=1; first=None; npay=0; bal=hw=best=0.0; t=0
    while t<len(r):
        x=r[t]*mf; q=min(L[t]*mf,x,0); t+=1
        why=("acik%1" if q<=-flo else "gunluk%2" if q<=-dl else "kayan%3" if bal+q<=hw-tr else None)
        if why:
            if log is not None: log[why]=log.get(why,0)+1
            cash-=price; nch+=1; bal=hw=best=0.0; continue
        bal+=x; hw=max(hw,bal); best=max(best,x)
        if bal>=thr and best<=cons*bal:
            npay+=1; cash+=bal*S*f["split"]; first=first or t
            if npay==3: cash+=price
            bal=0.0; hw=0.0; best=0.0
    return first,None,cash,None,nch
r,L=combo(NAMES)
for mf in (0.5,1.0):
    lg={}; [maven_v(r[ix],L[ix],mf,log=lg) for ix in IDX]; print(f"x{mf} patlama nedeni (500 yol toplam): {lg}")
    for lbl,kw in (("tam kural",{}),("acik %1 yok",dict(flo=9)),("tutarlilik yok",dict(cons=9)),("kayan %3 yerine %6",dict(tr=.06)),
                   ("acik yok + tutarlilik yok",dict(flo=9,cons=9))):
        print(f"  x{mf} {lbl}: {run(lambda a,b,m: maven_v(a,b,m,**kw),r,L,mf)}")
# best day size vs consistency
print("en iyi gun dagilimi (risk boyutlu x1, 7li): p50 %.2f%% p90 %.2f%% max %.2f%%"%tuple(100*np.quantile(r[r>0],[.5,.9,1])))
r0=r-r.mean(); print("FN2K x1 SIFIR-EDGE:",run(fn2,r0,np.minimum(r0,0)*1.5,1.0))
print("FN2K x0.5 SIFIR-EDGE:",run(fn2,r0,np.minimum(r0,0)*1.5,0.5))
