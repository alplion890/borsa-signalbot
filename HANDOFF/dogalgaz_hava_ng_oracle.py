"""Natural gas weather/storage oracle test (prereg HANDOFF/dogalgaz_hava_kahin_onkayit_2026-11-17.md).

usage: python -I ng_oracle.py <download_dir>
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

D = Path(sys.argv[1])
START, SPLIT = "2011-01-01", "2022-01-01"
ROW = re.compile(r"(\d{4})-[A-Za-z]{3}</td>(.*?)</tr>", re.S)
CELL = re.compile(r"(\d{2})/(\d{2})&nbsp;</td>\s*<td class='B3'>([\d,]+)")


def storage() -> pd.Series:
    s = (D / "storage.html").read_text(encoding="latin1")
    out = {pd.Timestamp(f"{y}-{m}-{d}"): float(v.replace(",", ""))
           for y, body in ROW.findall(s) for m, d, v in CELL.findall(body)}
    return pd.Series(out).sort_index()


def degree_days() -> pd.Series:
    parts = []
    for f in sorted(D.glob("*_20*.txt")):
        lines = [ln for ln in f.read_text(encoding="latin1").splitlines() if "|" in ln]
        hdr = lines[0].split("|")
        conus = next(ln for ln in lines if ln.startswith("CONUS")).split("|")
        s = pd.Series(pd.to_numeric(conus[1:], errors="coerce"),
                      index=pd.to_datetime(hdr[1:], format="%Y%m%d", errors="coerce"))
        parts.append(s[s.index.notna()])
    dd = pd.concat(parts).groupby(level=0).sum(min_count=1)  # HDD + CDD per day
    return dd.sort_index()


def dd_normal(dd: pd.Series) -> pd.Series:
    md = dd.index.strftime("%m-%d")
    norm = {}
    for t in dd.index[dd.index >= "2011-01-01"]:
        past = dd[(md == t.strftime("%m-%d")) & (dd.index < t) & (dd.index >= t - pd.DateOffset(years=10))]
        norm[t] = past.mean() if len(past) >= 8 else np.nan
    return pd.Series(norm)


def storage_surprise(st: pd.Series) -> pd.Series:
    ch = st.diff()
    wk = ch.index.isocalendar().week.to_numpy()
    out = {}
    for t, c in ch.loc[START:].items():
        w = t.isocalendar().week
        past = ch[(wk == w) & (ch.index < t) & (ch.index >= t - pd.DateOffset(years=5, days=3))]
        if len(past) >= 4 and np.isfinite(c):
            out[t] = c - past.mean()
    return pd.Series(out)


def trade(px: pd.DataFrame, start_after: pd.Timestamp, exit_weekday_offset: int, d: float, cost_bp: float):
    days = px.index
    after = days[days > start_after]
    if len(after) < 2:
        return None
    entry = after[0]
    target = start_after + pd.Timedelta(days=exit_weekday_offset)
    ex = days[(days >= target) & (days <= target + pd.Timedelta(days=2))]
    if not len(ex) or ex[0] <= entry:
        return None
    return d * (px.loc[ex[0], "Close"] / px.loc[entry, "Open"] - 1) - 2 * cost_bp / 1e4


def run_h1(px, sur, cost):
    r = {t: trade(px, t, 6, -np.sign(s), cost) for t, s in sur.items() if s != 0}  # Fri + 6 = Thu
    return pd.Series({k: v for k, v in r.items() if v is not None})


def run_h2(px, dd, norm, cost):
    dev = (dd - norm).dropna()
    weeks = dev.resample("W-SUN").sum(min_count=7).dropna()  # Mon..Sun sums
    r = {}
    for sun, v in weeks.items():
        if v == 0:
            continue
        fri_before = sun - pd.Timedelta(days=9)  # previous Friday; entry = next trading day (Mon)
        x = trade(px, fri_before + pd.Timedelta(days=2), 5, np.sign(v), cost)  # Sun -> Mon entry, Fri exit
        if x is not None:
            r[sun] = x
    return pd.Series(r), weeks


def report(name, r):
    t = r.mean() / r.std() * np.sqrt(len(r))
    a, b = r[r.index < SPLIT], r[r.index >= SPLIT]
    ta = a.mean() / a.std() * np.sqrt(len(a))
    tb = b.mean() / b.std() * np.sqrt(len(b))
    print(f"  {name}: n={len(r)} ort={r.mean()*1e4:+.1f}bp medyan={r.median()*1e4:+.1f}bp isabet={(r>0).mean()*100:.1f}% "
          f"t={t:+.2f} | <2022 {a.mean()*1e4:+.1f}bp t{ta:+.2f} | 2022+ {b.mean()*1e4:+.1f}bp t{tb:+.2f}")


def persistence(x: pd.Series) -> float:
    s = np.sign(x).replace(0, np.nan).dropna()
    p = s.shift(1)
    m = p.notna()
    return float((s[m] == p[m]).mean() * 100)


def load(tkr):
    px = yf.download(tkr, start="2010-06-01", auto_adjust=False, progress=False)
    px.columns = [c[0] if isinstance(c, tuple) else c for c in px.columns]
    return px[(px.Open > 0) & (px.Close > 0)]


def main():
    st, dd = storage(), degree_days()
    norm = dd_normal(dd)
    sur = storage_surprise(st)
    print("depolama", st.index[0].date(), "->", st.index[-1].date(), "| derece-gun", dd.index[0].date(), "->", dd.index[-1].date())
    _, weeks = run_h2(load("UNG"), dd, norm, 0.0)
    print(f"BAZ ORAN: depolama surprizi isaret kaliciligi %{persistence(sur):.1f} | hava sapmasi kaliciligi %{persistence(weeks):.1f}")
    for tkr in ("UNG", "NG=F"):
        px = load(tkr)
        for cost in (0.0, 5.0):
            print(f"{tkr} maliyet {cost}bp/yon (OLCULMEDI):")
            report("H1 depolama kahini", run_h1(px, sur, cost))
            report("H2 hava kahini   ", run_h2(px, dd, norm, cost)[0])


if __name__ == "__main__":
    main()
