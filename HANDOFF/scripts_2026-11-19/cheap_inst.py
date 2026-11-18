"""Which modules block cheap instants (Maven 5K $18.05, FN 2K $41.99)? Per-module diagnostics + subset/risk scan."""
t=open(r"C:/Users/quantum/OneDrive/Masaüstü/borsa/HANDOFF/scripts_2026-11-18/stop_sim.py",encoding="utf-8").read()
t=t[:t.index("FN=FIRMS")]
t=t.replace('print(f"RISK-BOYUTLU','_=(f"RISK-BOYUTLU').replace('print(f"ACIK RISK','_=(f"ACIK RISK')
exec(t)
import itertools
def arr(s): return s.reindex(idx).fillna(0).to_numpy()
M={}
for k in ("SWEEP","DONCHIAN_XAU"):
    s=T[k][T[k].index>=A]*SC[k]; r_=arr(s.groupby(s.index.normalize()).sum()); M[k]=(r_,np.minimum(r_,0)*1.5)
for k,s in ser["risk"].items(): r_=arr(s); M[k]=(r_,np.minimum(r_,0)*1.5)
br,bl,_=b7["risk"]; M["B7"]=(arr(br),np.minimum(arr(bl),arr(br)))
NAMES=list(M)
print("MODUL TESHIS (risk boyutlu x1, 2022+): yil% | gun ici zarar >%1 gun% | >%2 gun% | en iyi gun / toplam kar")
for k,(r_,L_) in M.items():
    tot=r_.sum(); print(f" {k:13s} {r_.sum()/len(r_)*365*100:5.1f} | {100*(L_<-.01).mean():4.1f} | {100*(L_<-.02).mean():4.1f} | {r_.max()/tot*100 if tot>0 else float('nan'):5.1f}%")
def combo(keys):
    r_=sum(M[k][0] for k in keys); L_=sum(M[k][1] for k in keys); return r_,L_
MV=dict(FIRMS["MAVEN_INST"]); FN2=dict(FIRMS["FN_INSTANT"],size=2000,price=41.99)
def maven(r,L,mf):
    """Maven Instant: trailing 3% equity, daily 2%, floating loss 1% (approx by intraday worst L), consistency 20%."""
    f=MV; S=f["size"]; price=f["price"]; cash=-price; nch=1; first=None; npay=0; bal=hw=best=0.0; t=0
    while t<len(r):
        x=r[t]*mf; q=min(L[t]*mf,x,0); t+=1
        if q<=-0.01 or q<=-0.02 or bal+q<=hw-0.03:
            cash-=price; nch+=1; bal=hw=best=0.0; continue
        bal+=x; hw=max(hw,bal); best=max(best,x)
        if bal>=0.03 and best<=0.20*bal:
            npay+=1; cash+=bal*S*f["split"]; first=first or t
            if npay==3: cash+=price
            bal=0.0; hw=0.0; best=0.0
    return first,None,cash,None,nch
def fn2(r,L,mf): return journey2(r,L,FN2,1,mf,H)
def show(lbl,keys,fn,mfs):
    r,L=combo(keys); out=[]
    for mf in mfs: out.append(f"x{mf}: {run(fn,r,L,mf)}")
    print(f" {lbl}\n   "+"\n   ".join(out))
MF=(0.25,0.5,1.0)
for fname,fn in (("MAVEN_INST 5K $18.05",maven),("FN_INSTANT 2K $41.99",fn2)):
    print(f"\n===== {fname}")
    show("HEPSI (7)",NAMES,fn,MF)
    for k in NAMES: show(f"-{k}",[n for n in NAMES if n!=k],fn,MF)
    for k in NAMES: show(f"yalniz {k}",[k],fn,MF)
