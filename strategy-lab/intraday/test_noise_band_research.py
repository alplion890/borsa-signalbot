import numpy as np
import pandas as pd
from .noise_band_research import sessions, simulate, previous_session, daily_returns


def fixture():
    parts=[]
    for date in pd.bdate_range('2026-03-02',periods=16):
        idx=pd.date_range(str(date.date())+' 09:30',periods=78,freq='5min',tz='America/New_York').tz_convert('UTC')
        parts.append(pd.DataFrame(dict(open=100.,high=100.,low=100.,close=100.,volume=1.),index=idx))
    return pd.concat(parts)


def test_flat_no_trades_and_dst():
    frame=fixture()
    trades, dates=simulate(frame)
    assert trades.empty and len(dates)==2
    days=sessions(frame)
    assert days['2026-03-06'].index[0].hour==14
    assert days['2026-03-09'].index[0].hour==13


def test_known_entry_exit_cost_and_no_lookahead():
    frame=fixture()
    idx=list(sessions(frame).values())[-1].index
    frame.loc[idx[5]:,'close']=101.
    frame.loc[idx[6]:,'open']=101.
    frame.loc[idx[5]:,'high']=101.
    trades, dates=simulate(frame)
    assert len(trades)==1
    trade=trades.iloc[0]
    assert trade.entry==101 and trade.exit==101 and trade.direction==1
    assert trade.entry_time==str(idx[6]) and trade.reason=='session_close'
    assert np.isclose(daily_returns(trades,dates,1).iloc[-1],-.00018)
    assert np.isclose(trade.upper,100.)  # current-day breakout excluded from sigma


def test_calendar_and_missing_bars():
    assert previous_session('2026-07-06')=='2026-07-02'
    frame=fixture()
    assert len(sessions(frame.iloc[1:]))==15
