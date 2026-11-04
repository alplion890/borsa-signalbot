from pathlib import Path
import pandas as pd,numpy as np,json,hashlib
from dataclasses import replace
from intraday.config import INSTRUMENTS
from intraday.honest_engine import simulate_trades
p=Path('outputs/intraday/research_panel/broker_history/EURUSD_5m_4623d9ba5c95278e.csv');raw=p.read_bytes();m=json.loads(p.with_suffix('.csv.json').read_text());assert hashlib.sha256(raw).hexdigest()==m['data_sha256'];d=pd.read_csv(p,index_col=0,parse_dates=True);d=d[d.high!=d.low]
def ema(s,n):
 x=s.copy();x.iloc[:n-1]=np.nan;x.iloc[n-1]=s.iloc[:n].mean();return x.ewm(span=n,adjust=False).mean()
def build(d):
 fast,slow=ema(d.close,30),ema(d.close,50);up=(fast>slow).shift(1).rolling(7).sum()==7;dn=(fast<slow).shift(1).rolling(7).sum()==7
 mean=d.close.rolling(15).mean();sd=d.close.rolling(15).std(ddof=0);tr=pd.concat([d.high-d.low,(d.high-d.close.shift()).abs(),(d.low-d.close.shift()).abs()],axis=1).max(axis=1);tr.iloc[0]=np.nan;r=1.1*tr.ewm(alpha=1/7,min_periods=7).mean();valid=np.arange(len(d))>=200
 return up&(d.close<=mean-1.5*sd)&valid,dn&(d.close>=mean+1.5*sd)&valid,d.close-r,d.close+1.5*r,d.close+r,d.close-1.5*r
sig=build(d)
for cut in (1000,len(d)//2,len(d)-100):
 for a,b in zip(sig,build(d.iloc[:cut])):np.testing.assert_allclose(a.iloc[:cut].astype(float),b.astype(float),equal_nan=True)
out=Path('../video-research/youtube-simple-20261030/video06');rows=[]
for mode in ('bar_sl_first','1m_then_sl_first'):
 for f in (1,2,3):
  r=simulate_trades(d,*sig,replace(INSTRUMENTS['EURUSD'],cost_per_side=INSTRUMENTS['EURUSD'].cost_per_side*f),min_rr=1.49,max_rr=1.5,max_hold=len(d)+1,fill_mode=mode);r.to_csv(out/f'trades_{mode}_{f}.csv',header=['net_r']);eq=np.r_[0.,r.cumsum().to_numpy()];rows.append(dict(mode=mode,cost=f,n=len(r),sum_r=float(r.sum()),mean_r=float(r.mean()),win_pct=float((r>0).mean()*100),closed_trade_dd_r=float((np.maximum.accumulate(eq)-eq).max()),trades_per_week=len(r)/((d.index[-1]-d.index[200]).total_seconds()/604800)))
result=dict(data_sha256=m['data_sha256'],first=str(d.index[200]),last=str(d.index[-1]),prefix_checks=3,results=rows,limitations=['Indicator library version approximation','No 1m; stop-first','No swap or historical bid/ask','Data-end liquidation'])
(out/'backtest.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
