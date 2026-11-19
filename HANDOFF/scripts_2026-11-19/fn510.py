t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/cheap_inst.py",encoding="utf-8").read()
exec(t[:t.index("MF=(0.25")])
for size,price in ((5000,104.99),(10000,209.99)):
    F=dict(FIRMS["FN_INSTANT"],size=size,price=price)
    for nm,keys in (("7 modul",NAMES),("B7+Ay donumu'suz 5 modul",[n for n in NAMES if n not in ("B7","AY_DONUMU_NQ")])):
        r,L=combo(keys)
        for mf in (1.0,2.0): print(f"FN {size//1000}K ${price} {nm} risk x{mf}: {run(lambda a,b,m: journey2(a,b,F,1,m,H),r,L,mf)}")
    r,L=combo(NAMES); r0=r-r.mean(); print(f"FN {size//1000}K SIFIR-EDGE x1: {run(lambda a,b,m: journey2(a,b,F,1,m,H),r0,np.minimum(r0,0)*1.5,1.0)}")
