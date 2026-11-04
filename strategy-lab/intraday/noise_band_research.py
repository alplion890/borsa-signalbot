"""Preregistered Maven CFD tick-VWAP adaptation; offline research only."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parents[1]
DATA = LAB / 'outputs/intraday/research_panel/broker_history/NASDAQ100_5m_2b540c15f564fedb.csv'
OUT = LAB / 'outputs/intraday/noise_band/20261027'
HASH = '2b540c15f564fedb6ff634cdabd607b929c81f23d6d0a915133d7146f91bbf16'
# Official Nasdaq 2026 US equity calendar. This experiment uses cash hours.
HOLIDAYS = set('2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26 2026-12-25'.split())


def sessions(frame):
    local = frame.index.tz_convert('America/New_York')
    minute = local.hour * 60 + local.minute
    x = frame.loc[(minute >= 570) & (minute < 960)].copy()
    x['date'] = local[(minute >= 570) & (minute < 960)].strftime('%Y-%m-%d')
    x['minute'] = minute[(minute >= 570) & (minute < 960)]
    return {date: day for date, day in x.groupby('date')
            if date not in HOLIDAYS and pd.Timestamp(date).weekday() < 5
            and day.minute.tolist() == list(range(570, 960, 5))}


def previous_session(date):
    day = pd.Timestamp(date) - pd.Timedelta(days=1)
    while day.weekday() >= 5 or day.strftime('%Y-%m-%d') in HOLIDAYS:
        day -= pd.Timedelta(days=1)
    return day.strftime('%Y-%m-%d')


def simulate(frame):
    days = sessions(frame)
    history, trades, eligible = [], [], []
    for date, day in days.items():
        values = day[['open', 'high', 'low', 'close', 'volume']].to_numpy(float)
        o, h, l, c, v = values.T
        moves = abs(c / o[0] - 1)
        if len(history) < 14 or previous_session(date) not in days:
            history.append(moves)
            continue
        sigma = np.mean(history[-14:], axis=0)
        prev = float(days[previous_session(date)].close.iloc[-1])
        upper, lower = max(o[0], prev)*(1+sigma), min(o[0], prev)*(1-sigma)
        vwap = np.cumsum((h+l+c)/3*v)/np.cumsum(v)
        eligible.append(date)
        position = None
        for j in range(5, 72, 6):  # 09:55 close = 10:00 decision, through 15:30
            decision = day.index[j] + pd.Timedelta(minutes=5)
            fill = day.index[j+1]
            if position is not None:
                direction = position['direction']
                exit_now = c[j] <= max(upper[j], vwap[j]) if direction == 1 else c[j] >= min(lower[j], vwap[j])
                if exit_now:
                    position.update(exit_decision=str(decision), exit_time=str(fill), exit=float(o[j+1]), reason='band_vwap')
                    trades.append(position)
                    position = None
                continue
            direction = 1 if c[j] > upper[j] else -1 if c[j] < lower[j] else 0
            if direction:
                position = dict(date=date, direction=direction, entry_decision=str(decision), entry_time=str(fill), entry=float(o[j+1]), upper=float(upper[j]), lower=float(lower[j]), vwap=float(vwap[j]))
        if position is not None:
            close_time = day.index[-1] + pd.Timedelta(minutes=5)
            position.update(exit_decision=str(close_time), exit_time=str(close_time), exit=float(c[-1]), reason='session_close')
            trades.append(position)
        history.append(moves)
    return pd.DataFrame(trades), eligible


def daily_returns(trades, dates, factor):
    """Each entry allocates that day's opening equity; no intraday compounding."""
    daily = pd.Series(0., index=dates)
    if not trades.empty:
        net = trades.direction*(trades.exit/trades.entry-1) - factor*.00009*(1+trades.exit/trades.entry)
        daily.update(net.groupby(trades.date).sum())
    return daily


def stats(daily):
    equity = np.r_[1., (1+daily).cumprod().to_numpy()]
    return dict(days=len(daily), total_pct=float((equity[-1]-1)*100), mean_daily_bp=float(daily.mean()*10000), max_daily_close_drawdown_pct=float((1-equity/np.maximum.accumulate(equity)).max()*100))


def run():
    assert hashlib.sha256(DATA.read_bytes()).hexdigest() == HASH
    frame = pd.read_csv(DATA, index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index, utc=True)
    assert frame.index.is_unique and frame.index.is_monotonic_increasing
    trades, dates = simulate(frame)
    trades['gross'] = trades.direction*(trades.exit/trades.entry-1)
    trades['cost'] = .00009*(1+trades.exit/trades.entry)
    trades['net'] = trades.gross-trades.cost
    rng = np.random.default_rng(20261027)
    daily = daily_returns(trades, dates, 1)
    # Circular 5-session blocks preserve short-range daily dependence.
    starts = rng.integers(0, len(daily), size=(10000, (len(daily)+4)//5))
    indices = (starts[:, :, None]+np.arange(5)) % len(daily)
    bootstrap = daily.to_numpy()[indices.reshape(10000, -1)[:, :len(daily)]].mean(axis=1)
    random_means = []
    for _ in range(1000):
        signs = rng.choice([-1, 1], len(trades))
        random_means.append(float((signs*(trades.exit/trades.entry-1)-trades.cost).sum()/len(dates)))
    # Future deletion invariance on completed sessions, including sigma history.
    checks = []
    for cut in (len(dates)//2, len(dates)-10):
        end = pd.Timestamp(dates[cut], tz='America/New_York')+pd.Timedelta(hours=16)
        prefix, _ = simulate(frame.loc[frame.index < end.tz_convert('UTC')])
        expected = trades.loc[trades.date <= dates[cut], prefix.columns].reset_index(drop=True)
        pd.testing.assert_frame_equal(prefix.reset_index(drop=True), expected)
        checks.append(str(end))
    result = dict(data_sha256=HASH, code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), plan_sha256=hashlib.sha256((OUT/'PLAN.md').read_bytes()).hexdigest(), adaptation='Maven NASDAQ100 CFD 5m tick-VWAP; not paper or TikTok replication', complete_sessions=len(sessions(frame)), eligible_days=len(dates), first=dates[0], last=dates[-1], trades=len(trades), active_days=int((trades.groupby('date').size()>0).sum()), win_rate_pct=float((trades.net>0).mean()*100), costs={str(f):stats(daily_returns(trades, dates, f)) for f in (1,2,3)}, mean_daily_bp_ci95=(np.quantile(bootstrap,[.025,.975])*10000).tolist(), random_direction=dict(mean_daily_bp=float(np.mean(random_means)*10000), percentile_of_actual=float(np.mean(np.array(random_means)<=daily.mean())*100)), blocks={name:stats(daily.loc[mask]) for name,mask in [('before_july',daily.index<'2026-07-01'),('july_onward',daily.index>='2026-07-01')]}, prefix_checks=checks, limitations=['Daily-close drawdown, not intraday maximum', 'Same data previously seen; not blind OOS', 'Assumed proportional costs; no historical bid/ask', 'Tick-volume typical-price VWAP approximation', 'Session closing fill is idealized'])
    trades.to_csv(OUT/'trades.csv', index=False)
    daily.rename('net_return').to_csv(OUT/'daily.csv', index_label='date')
    (OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    run()
