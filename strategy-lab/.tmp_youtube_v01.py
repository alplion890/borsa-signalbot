import ast,json
from pathlib import Path
import pandas as pd,numpy as np
from dataclasses import replace
from intraday.config import INSTRUMENTS
from intraday.honest_engine import simulate_trades
p=Path('outputs/intraday/research_panel/broker_history/EURUSD_5m_4623d9ba5c95278e.csv');d=pd.read_csv(p,index_col=0,parse_dates=True);split=d.index[int(len(d)*.6)];d=d[d.high!=d.low];day=d.index.normalize();v=((d.high+d.low+d.close)/3*d.volume).groupby(day).cumsum()/d.volume.groupby(day).cumsum();up=(d[['open','close']].min(axis=1)>v).rolling(16).sum()==16;dn=(d[['open','close']].max(axis=1)<v).rolling(16).sum()==16
change=d.close.diff();gain=change.clip(lower=0).ewm(alpha=1/16,min_periods=16).mean();loss=(-change.clip(upper=0)).ewm(alpha=1/16,min_periods=16).mean();rsi=100*gain/(gain+loss);avg=d.close.rolling(14).mean();std=d.close.rolling(14).std(ddof=0);le=up&(d.close<=avg-2*std)&(rsi<45);se=dn&(d.close>=avg+2*std)&(rsi>55);le.iloc[:200]=False;se.iloc[:200]=False
tr=pd.concat([d.high-d.low,(d.high-d.close.shift()).abs(),(d.low-d.close.shift()).abs()],axis=1).max(axis=1);tr.iloc[0]=np.nan;atr=tr.ewm(alpha=1/7,min_periods=7).mean();rows=[];out=Path('../video-research/youtube-simple-20261030/video01')
def run(part,sl,rr,f):
 c=part.close;risk=atr.loc[part.index]*sl;sig=le.loc[part.index],se.loc[part.index],c-risk,c+risk*rr,c+risk,c-risk*rr
 return simulate_trades(part,*sig,replace(INSTRUMENTS['EURUSD'],cost_per_side=INSTRUMENTS['EURUSD'].cost_per_side*f),min_rr=rr-.01,max_rr=rr,max_hold=len(part)+1,fill_mode='1m_then_sl_first')
for sl in (1.2,2.,3.):
 for rr in (1.,1.5,2.):
  r=run(d.loc[d.index<split],sl,rr,1);rows.append(dict(sl=sl,rr=rr,n=len(r),mean=float(r.mean()) if len(r) else None,sum=float(r.sum())))
valid=[x for x in rows if x['n']>=20];best=sorted(valid,key=lambda x:(-x['mean'],x['sl'],x['rr']))[0] if valid else None;held=[]
if best:
 for f in (1,2,3):
  r=run(d.loc[d.index>=split],best['sl'],best['rr'],f);r.to_csv(out/f'grid_selected_validation_{f}.csv',header=['net_r']);held.append(dict(cost=f,n=len(r),mean=float(r.mean()) if len(r) else None,sum=float(r.sum())))
x=dict(split=str(split),development=rows,selected=best,validation=held);(out/'exit_grid.json').write_text(json.dumps(x,indent=2));print(json.dumps(x))
