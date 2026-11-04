from pathlib import Path
from dataclasses import replace
import json, hashlib
import numpy as np
import pandas as pd
from intraday.research_panel import jobs
from intraday.long_history_ab import spec_by_name,_sweep_build,_atr_rank,run_spec
from intraday.execution_audit import reference_trades
from intraday.honest_engine import simulate_trades,FILL_BAR_SL_FIRST
from intraday.config import INSTRUMENTS
out=Path('outputs/intraday/fairness_audit/20261027');out.mkdir(parents=True,exist_ok=True)
rows=[];details={}
for name in ['SWEEP_CORE','NQ_ORB','EUR_LONDON','GBP_LONDON']:
 symbol,tf,_=jobs.STRATEGIES[name]
 path=next(Path('outputs/intraday/research_panel/broker_history').glob(f'{symbol}_{tf}_*.csv'))
 frame=pd.read_csv(path,index_col=0,parse_dates=True)
 frame.index=pd.to_datetime(frame.index,utc=True).tz_localize(None)
 # Retain all earlier snapshot data as warmup; forbid entries outside common dates.
 frame=frame.loc[frame.index < '2026-10-15']
 spec=spec_by_name(name)
 le,se,lsl,ltp,ssl,stp=spec.build(frame)
 if name=='SWEEP_CORE':
  rank=_atr_rank(frame);cap=pd.Series(np.select([rank<.33,rank<.67],[4.,6.],default=8.),index=frame.index)
  ltp=pd.Series(np.minimum(ltp,frame.close+(frame.close-lsl)*cap),index=frame.index)
  stp=pd.Series(np.maximum(stp,frame.close-(ssl-frame.close)*cap),index=frame.index)
  le=le&rank.notna()&(np.arange(len(frame))>=519);se=se&rank.notna()&(np.arange(len(frame))>=519)
 mask=(frame.index>='2026-04-16')&(frame.index<'2026-10-15')
 signals=(le&mask,se&mask,lsl,ltp,ssl,stp)
 traces=[]
 for factor in (1,2,3):
  inst=replace(INSTRUMENTS[symbol],cost_per_side=INSTRUMENTS[symbol].cost_per_side*factor)
  actual=simulate_trades(frame,*signals,inst,min_rr=spec.min_rr,max_rr=spec.max_rr,max_hold=spec.max_hold)
  trace=reference_trades(frame,signals,inst,spec.min_rr,spec.max_rr,spec.max_hold,FILL_BAR_SL_FIRST)
  ref=pd.Series([x['r'] for x in trace],index=pd.to_datetime([x['signal_time'] for x in trace]))
  assert list(ref.index)==list(actual.index) and np.allclose(ref,actual)
  row=dict(strategy=name,cost_factor=factor,trades=len(actual),sum_r=float(actual.sum()),mean_r=float(actual.mean()),data_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
  # Fixed unit notional diagnostic; excludes compounding and differs from risk-sized R.
  nominal=np.array([x['direction']*(x['exit']/x['entry']-1)-2*inst.cost_per_side for x in trace])
  row.update(sum_unit_notional_pct=float(nominal.sum()*100),mean_unit_notional_trade_bp=float(nominal.mean()*10000))
  rows.append(row)
  traces += [dict(x,cost_factor=factor) for x in trace]
 pd.DataFrame(traces).to_csv(out/f'{name}_trades.csv',index=False)
 details[name]=dict(source=str(path),frame_bars=len(frame))
 if name=='SWEEP_CORE':
  old=run_spec(spec,frame);old=old[(old.index>='2026-04-16')&(old.index<'2026-10-15')]
  details[name]['three_sleeve_legacy']=dict(n=len(old),sum_r=float(old.sum()),mean_r=float(old.mean()))
  details[name]['single_book']=rows[-3]
  oldtrace=[]
  for m,rr in [(rank<.33,4.),((rank>=.33)&(rank<.67),6.),(rank>=.67,8.)]:
   z=reference_trades(frame,(le&m&mask,se&m&mask,lsl,spec.build(frame)[3],ssl,spec.build(frame)[5]),INSTRUMENTS[symbol],spec.min_rr,rr,spec.max_hold,FILL_BAR_SL_FIRST)
   oldtrace.extend(z)
  overlaps=0
  oldtrace.sort(key=lambda x:x['entry_bar'])
  for i,a in enumerate(oldtrace):
   for b in oldtrace[i+1:]:
    if b['entry_bar']>a['exit_bar']:break
    overlaps+=1
  details[name]['legacy_overlap_pairs']=overlaps
pd.DataFrame(rows).to_csv(out/'comparison.csv',index=False)
(out/'audit.json').write_text(json.dumps(dict(rows=rows,details=details,code_sha256=jobs.code_digest(jobs.LAB)),indent=2),encoding='utf-8')
print(json.dumps(dict(rows=rows,details=details),indent=2))
