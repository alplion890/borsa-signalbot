from pathlib import Path
import pandas as pd,numpy as np,json
from intraday.history_fetch import load_history
from intraday.long_history_ab import SPECS,run_spec,_sweep_build,_atr_rank
from intraday.honest_engine import simulate_trades
from intraday.config import INSTRUMENTS
out=Path('outputs/intraday/fairness_audit/20261027');results=[]
for spec in SPECS:
 df=load_history(spec.symbol,spec.tf,start_year=2012)
 if spec.name=='SWEEP_CORE':
  le,se,lsl,ltp,ssl,stp=spec.build(df);rank=_atr_rank(df);cap=pd.Series(np.select([rank<.33,rank<.67],[4.,6.],default=8.),index=df.index)
  ltp=pd.Series(np.minimum(ltp,df.close+(df.close-lsl)*cap),index=df.index);stp=pd.Series(np.maximum(stp,df.close-(ssl-df.close)*cap),index=df.index)
  r=simulate_trades(df,le&rank.notna(),se&rank.notna(),lsl,ltp,ssl,stp,INSTRUMENTS[spec.symbol],min_rr=spec.min_rr,max_rr=spec.max_rr,max_hold=spec.max_hold)
 else:r=run_spec(spec,df)
 r.to_csv(out/(spec.name+'_long_history_trades.csv'))
 row=dict(name=spec.name,bars=len(df),first=str(df.index.min()),last=str(df.index.max()),n=len(r),sum_r=float(r.sum()),mean_r=float(r.mean()),note='GBP future close dependency; provisional' if spec.name=='GBP_LONDON' else 'Current gap-v2 engine, archived fixed definition')
 results.append(row);print(json.dumps(row),flush=True)
(out/'long_history_rerun.json').write_text(json.dumps(results,indent=2))
