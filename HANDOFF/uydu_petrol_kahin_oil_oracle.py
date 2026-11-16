"""Satellite-oil oracle test (prereg HANDOFF/uydu_petrol_kahin_onkayit_2026-11-17.md).

usage: python -I oil_oracle.py <download_dir>
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

D = Path(sys.argv[1])
START = "2017-01-01"
ROW = re.compile(r"(\d{4})-[A-Za-z]{3}</td>(.*?)</tr>", re.S)
CELL = re.compile(r"(\d{2})/(\d{2})&nbsp;</td>\s*<td class='B3'>([\d,]+)")


def eia(name: str) -> pd.Series:
    s = (D / name).read_text(encoding="latin1")
    out = {}
    for year, body in ROW.findall(s):
        for mm, dd, val in CELL.findall(body):
            out[pd.Timestamp(f"{year}-{mm}-{dd}")] = float(val.replace(",", ""))
    return pd.Series(out).sort_index()


def naive_accuracy(stock: pd.Series) -> dict:
    ch = np.sign(stock.diff()).loc[START:].replace(0, np.nan).dropna()
    prev = ch.shift(1)
    m = prev.notna()
    return {"weeks": int(m.sum()), "naive_same_as_last_week_pct": float((ch[m] == prev[m]).mean() * 100),
            "share_down_pct": float((ch < 0).mean() * 100)}


def oracle(stock: pd.Series, px: pd.DataFrame, cost_bp: float) -> pd.DataFrame:
    rows = []
    days = px.index
    for wk_end, chg in stock.diff().loc[START:].items():
        if chg == 0 or np.isnan(chg):
            continue
        mon = days[days > wk_end]
        if len(mon) < 3:
            continue
        entry_day = mon[0]
        wed = wk_end + pd.Timedelta(days=5)  # Friday + 5 = Wednesday release
        exit_cands = days[(days >= wed) & (days <= wed + pd.Timedelta(days=2))]
        if not len(exit_cands) or exit_cands[0] <= entry_day:
            continue
        exit_day = exit_cands[0]
        d = -np.sign(chg)  # draw -> long
        ret = d * (px.loc[exit_day, "Close"] / px.loc[entry_day, "Open"] - 1) - 2 * cost_bp / 1e4
        rows.append({"week": wk_end, "dir": d, "ret": ret})
    return pd.DataFrame(rows).set_index("week")


def report(name: str, t: pd.DataFrame) -> None:
    r = t.ret
    tstat = r.mean() / r.std() * np.sqrt(len(r))
    a, b = r[r.index < "2022"], r[r.index >= "2022"]
    print(f"  {name}: n={len(r)} ort={r.mean()*1e4:+.1f}bp isabet={(r > 0).mean()*100:.1f}% t={tstat:+.2f} "
          f"2017-21={a.mean()*1e4:+.1f}bp 2022+={b.mean()*1e4:+.1f}bp yillik~{r.mean()*52*100:+.1f}%")


def degraded(t: pd.DataFrame, acc: float, reps: int = 1000) -> tuple[float, float]:
    rng = np.random.default_rng(20261117)
    raw = t.ret.to_numpy()  # zero-cost oracle returns; flip sign with prob 1-acc
    means = [np.mean(np.where(rng.random(len(raw)) < acc, raw, -raw)) for _ in range(reps)]
    return float(np.mean(means) * 1e4), float(np.quantile(means, 0.05) * 1e4)


def main() -> None:
    cush, us = eia("cushing.html"), eia("us.html")
    print("Cushing", cush.index[0].date(), "->", cush.index[-1].date(), len(cush),
          "| US", us.index[0].date(), "->", us.index[-1].date(), len(us))
    print("BAZ ORAN:", "Cushing", naive_accuracy(cush), "| US", naive_accuracy(us))
    px = yf.download("CL=F", start="2016-12-01", auto_adjust=False, progress=False)
    px.columns = [c[0] if isinstance(c, tuple) else c for c in px.columns]
    px = px[(px.Open > 0) & (px.Close > 0)]
    print("WTI", px.index[0].date(), "->", px.index[-1].date(), len(px))
    for cost in (0.0, 2.0):
        print(f"KAHIN (maliyet {cost} bp/yon, OLCULMEDI):")
        for name, s in (("H1 Cushing", cush), ("H2 ABD toplam", us)):
            report(name, oracle(s, px, cost))
    for name, s in (("H1 Cushing", cush), ("H2 ABD toplam", us)):
        t0 = oracle(s, px, 0.0)
        m, q5 = degraded(t0, 0.6348)
        print(f"%63.48 isabetle (maliyetsiz) {name}: ort {m:+.1f}bp, 5. yuzdelik {q5:+.1f}bp")


if __name__ == "__main__":
    main()
