t=open(r"../HANDOFF/scripts_2026-11-19/futsim.py",encoding="utf-8").read(); exec(t[:t.index("r,L=combo")])
r,L=combo(["SWEEP"]); nz=(r!=0).sum()/len(r)*365
print(f"SWEEP islem gunu/yil {nz:.0f} | gun getirisi !=0 medyan %{np.median(np.abs(r[r!=0]))*100:.2f} max %{r.max()*100:.2f}")
def dbg(mf,days):
    c={"cb_ok":0,"cons_fail":0,"funded":0,"pay":0}
    for ix in IDX:
        rr=r[ix]*mf; LL=L[ix]*mf; bal=peak=0; ph=0; cyc=0; cb=0; best=0; seen=False
        for d in range(days):
            x=day(rr[d],min(LL[d],rr[d],0),bal,peak)
            if x is None: break
            bal+=x; peak=max(peak,bal)
            if ph==0:
                if bal>=TGT: ph=1; bal=peak=0; c["funded"]+=1
                continue
            cyc+=1; cb+=x; best=max(best,x)
            if cb>=500/S and not seen: seen=True; c["cb_ok"]+=1; c["cons_fail"]+= best>.40*cb
            if cyc>=3 and cb>=500/S and best<=.40*cb: c["pay"]+=1; break
    print(f"x{mf} {days}g: fonlu {c['funded']} | $500'e ulasan {c['cb_ok']} (ilk ulastiginda tutarlilik bozuk {c['cons_fail']}) | payout {c['pay']} / {len(IDX)}")
for mf in (3.0,4.0): dbg(mf,90)
