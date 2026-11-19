"""FN Stellar Lite 5K $29.99 / 10K $59.99: 8%+4%, 4% daily, 8% static, 10 business-day payout, refund 3rd."""
t=open(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/fn6k_cap.py",encoding="utf-8").read()
exec(t[:t.index("F=dict(")])
for size,price,keys,lbl in ((5000,29.99,["SWEEP","NB6","DX6","BTC_21_23","BTC_GECE"],"5K $29.99, 5 modul (%1 kapi, 6K lot yaklasigi)"),(10000,59.99,NAMES,"10K $59.99, 7 modul (ideal lot)")):
    for md in (2,5):
        F=dict(FIRMS["FN_LITE"],size=size,price=price,phases=[(.08,md),(.04,md)]); r,L=combo(keys)
        print(f"\n=== FN Lite {lbl}, min {md} gun/faz")
        for mc in (1,2,3,4,6): print(f" challenge x{mc} funded x1: {run(lambda a,b,m,mc=mc: journey2(a,b,F,mc,m,H),r,L,1.0)}")
        if md==2:
            r0=r-r.mean(); print(f" SIFIR-EDGE x4: {run(lambda a,b,m: journey2(a,b,F,4,m,H),r0,np.minimum(r0,0)*1.5,1.0)}")
