"""FN Stellar 1-Step: 6K $44.99 (NOVSTR) and 15K $129.99. Challenge risk multiplier scan to target 10-20 day first payout."""
t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/fn6k_cap.py",encoding="utf-8").read()
exec(t[:t.index("F=dict(")])
SET6=["SWEEP","NB6","DX6","BTC_21_23","BTC_GECE"]; SET15=NAMES
for size,price,keys,lbl in ((6000,44.99,SET6,"6K $44.99, 5 modul (%1 kapili gercek lot)"),(15000,129.99,SET15,"15K $129.99, 7 modul (ideal lot)")):
    F=dict(FIRMS["FN_1STEP"],size=size,price=price); r,L=combo(keys)
    print(f"\n=== FN 1-Step {lbl}")
    for mf in (1.0,2.0):
        for mc in (1,2,3,4,6):
            print(f" challenge x{mc} funded x{mf}: {run(lambda a,b,m,mc=mc: journey2(a,b,F,mc,m,H),r,L,mf)}")
    r0=r-r.mean(); print(f" SIFIR-EDGE challenge x4 funded x1: {run(lambda a,b,m: journey2(a,b,F,4,m,H),r0,np.minimum(r0,0)*1.5,1.0)}")
