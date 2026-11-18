t=open(r"C:/Users/quantum/OneDrive/Masaüstü/borsa/HANDOFF/scripts_2026-11-18/stop_sim.py",encoding="utf-8").read()
t=t[:t.index("FN=FIRMS")]
t=t.replace('print(f"RISK-BOYUTLU','_=(f"RISK-BOYUTLU').replace('print(f"ACIK RISK','_=(f"ACIK RISK')
exec(t)
sets=[("6li+B7 RISK-BOYUTLU (islem basi %0.5)","risk",True),("6li+B7 stop'lu mevcut lot","stop",True)]
for key in ("FN_LITE","FN_2STEP","FN_1STEP"):
    F=FIRMS[key]; print(f"\n=== {key} {F['size']} ${F['price']}")
    for nm,lab,w in sets:
        r,L=portfolio(lab,w)
        for mc in (1,2,3):
            print(f" {nm} challenge x{mc}: {run(lambda a,b,mf: journey2(a,b,F,mc,mf,H),r,L,1.0)}")
    r,L=portfolio("risk",True); r0=r-r.mean()
    print(f" SIFIR-EDGE risk-boyutlu x3: {run(lambda a,b,mf: journey2(a,b,F,3,mf,H),r0,np.minimum(r0,0)*1.5,1.0)}")
