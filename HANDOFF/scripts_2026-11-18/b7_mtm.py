"""B7 mark-to-market daily series (unit notional): close-to-close while held, cost on entry/exit day,
swap per night, plus intraday trough vs previous close (low-based). Saved to scratchpad csv."""
import pandas as pd, numpy as np
from intraday.history_fetch import load_history
from intraday.seffaf_adaylari import resample_nq_daily
from intraday.kaynak_adaylari import cost_of
d=resample_nq_daily(load_history("NASDAQ100","5m",start_year=2012))
t=pd.read_csv("outputs/intraday/seffaf_adaylari/B7_trades.csv",parse_dates=["entry_time","exit_time"])
cost=cost_of("NASDAQ100"); r=pd.Series(0.0,index=d.index); lo=pd.Series(0.0,index=d.index)
for _,x in t.iterrows():
    w=d.loc[(d.index>=x.entry_time)&(d.index<=x.exit_time)]
    pc=w.close.shift(1)
    for day in w.index[1:]:
        nights=(day-w.index[w.index.get_loc(day)-1]).days
        ret=w.close[day]/pc[day]-1-0.000118*nights
        trough=min(w.low[day]/pc[day]-1,0)-0.000118*nights
        if day==w.index[1]: ret-=cost; trough-=cost
        if day==w.index[-1]: ret-=cost
        r[day]+=ret; lo[day]+=min(trough,ret)
out=pd.DataFrame({"r":r,"lo":lo}); out.to_csv(r"C:/Users/quantum/AppData/Local/Temp/claude/4cb47cb1ec58a215/538274f1-0b4a-4f3d-9855-3209fb6723e4/scratchpad/b7_mtm.csv")
print("toplam trade-bazli",round((t.gross-2*cost-0.000118*t.nights).sum(),4),"mtm toplam",round(r.sum(),4))
print("en kotu gun close %",round(r.min()*100,2),r.idxmin().date(),"en kotu gun ici dip %",round(lo.min()*100,2),lo.idxmin().date())
s=r[r.index>="2022-01-01"]; print("2022+ en kotu gun %",round(s.min()*100,2),"pozisyonda gun %",round((s!=0).mean()*100,1))
eq=r.cumsum(); print("max equity DD (1x notional) %",round((eq.cummax()-eq).max()*100,1))
