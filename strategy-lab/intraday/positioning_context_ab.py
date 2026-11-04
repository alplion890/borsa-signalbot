"""NQ SWEEP_CORE icin makro + COT/OI + BTC funding A/B deneyi.

Bu dosya canli kurali degistirmez. CFTC TFF raporunu ihtiyatli olarak rapor
haftasini izleyen pazartesiden itibaren, Binance funding'i ise gercek yayin
zamanindan sonra kullanir. Her varyant yalniz kendi veri kapsamindaki baseline
ile karsilastirilir.

Calistir: python -m intraday.positioning_context_ab [--refresh]
"""
from __future__ import annotations

import argparse
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .history_fetch import load_history
from .long_history_ab import run_spec, spec_by_name
from .macro_context_ab import _sources, _summary, _weekly_delta_ci, delayed_change

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "positioning_context_ab"
CFTC_ARCHIVE = "https://www.cftc.gov/files/dea/history"
BINANCE_FUNDING = "https://fapi.binance.com/fapi/v1/fundingRate"


def _download_cot(refresh: bool, end_year: int) -> pd.DataFrame:
    """CFTC TFF futures-only NASDAQ-100 consolidated haftalik verisi."""
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / "cftc_nasdaq_tff.csv"
    if cache.exists() and not refresh:
        return pd.read_csv(cache, parse_dates=["report_date", "available_date"])

    urls = [("2006_2016", f"{CFTC_ARCHIVE}/fin_fut_txt_2006_2016.zip")]
    urls += [(str(year), f"{CFTC_ARCHIVE}/fut_fin_txt_{year}.zip")
             for year in range(2017, end_year + 1)]
    pieces: list[pd.DataFrame] = []
    for label, url in urls:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            name = archive.namelist()[0]
            raw = pd.read_csv(archive.open(name), low_memory=False)
        market = raw["Market_and_Exchange_Names"].astype(str)
        nq = raw.loc[market.str.contains("NASDAQ-100 Consolidated", case=False, na=False)].copy()
        if nq.empty:
            raise RuntimeError(f"CFTC {label} arsivinde NASDAQ-100 bulunamadi")
        pieces.append(nq)

    raw = pd.concat(pieces, ignore_index=True)
    dates = pd.to_datetime(raw["Report_Date_as_YYYY-MM-DD"], errors="coerce")
    result = pd.DataFrame({
        "report_date": dates,
        "open_interest": pd.to_numeric(raw["Open_Interest_All"], errors="coerce"),
        "asset_long": pd.to_numeric(raw["Asset_Mgr_Positions_Long_All"], errors="coerce"),
        "asset_short": pd.to_numeric(raw["Asset_Mgr_Positions_Short_All"], errors="coerce"),
        "lev_long": pd.to_numeric(raw["Lev_Money_Positions_Long_All"], errors="coerce"),
        "lev_short": pd.to_numeric(raw["Lev_Money_Positions_Short_All"], errors="coerce"),
    }).dropna().sort_values("report_date").drop_duplicates("report_date", keep="last")
    # Tuesday data is normally published Friday afternoon. Monday availability
    # is deliberately conservative and avoids release-time/DST lookahead.
    result["available_date"] = result["report_date"] + pd.Timedelta(days=6)
    result["oi_change"] = result["open_interest"].diff()
    result["lev_net_change"] = (result["lev_long"] - result["lev_short"]).diff()
    result["asset_net_change"] = (result["asset_long"] - result["asset_short"]).diff()
    result.to_csv(cache, index=False)
    return result


def _download_funding(refresh: bool, end: pd.Timestamp) -> pd.DataFrame:
    """Binance BTCUSDT funding gecmisi; yalniz yayinlanmis gozlemler."""
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / "binance_btcusdt_funding.csv"
    if cache.exists() and not refresh:
        cached = pd.read_csv(cache)
        cached["available_at"] = pd.to_datetime(
            cached["available_at"], format="mixed", utc=True
        )
        return cached

    start_ms = int(pd.Timestamp("2019-09-01", tz="UTC").timestamp() * 1000)
    end_ms = int(pd.Timestamp(end).tz_localize("UTC").timestamp() * 1000)
    rows: list[dict] = []
    while start_ms <= end_ms:
        response = requests.get(
            BINANCE_FUNDING,
            params={"symbol": "BTCUSDT", "startTime": start_ms,
                    "endTime": end_ms, "limit": 1000},
            timeout=30,
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        rows.extend(batch)
        next_ms = int(batch[-1]["fundingTime"]) + 1
        if next_ms <= start_ms:
            raise RuntimeError("Binance funding sayfalama ilerlemedi")
        start_ms = next_ms
        if len(batch) < 1000:
            break
    result = pd.DataFrame({
        "available_at": pd.to_datetime([r["fundingTime"] for r in rows], unit="ms", utc=True),
        "funding_rate": [float(r["fundingRate"]) for r in rows],
    }).drop_duplicates("available_at").sort_values("available_at")
    result["funding_3d"] = result["funding_rate"].rolling(9, min_periods=6).mean()
    result.to_csv(cache, index=False)
    return result


def _asof_features(trade_index: pd.DatetimeIndex, cot: pd.DataFrame,
                   funding: pd.DataFrame) -> pd.DataFrame:
    """Her bara o anda bilinen son COT ve funding degerini tasi."""
    bars = pd.DataFrame({"timestamp": pd.to_datetime(trade_index, utc=True)})
    cot_known = cot[["available_date", "oi_change", "lev_net_change",
                     "asset_net_change"]].copy()
    cot_known["available_at"] = pd.to_datetime(cot_known.pop("available_date"), utc=True)
    merged = pd.merge_asof(
        bars.sort_values("timestamp"), cot_known.sort_values("available_at"),
        left_on="timestamp", right_on="available_at", direction="backward",
    )
    fund = funding[["available_at", "funding_3d"]].copy()
    fund["available_at"] = pd.to_datetime(
        fund["available_at"], format="mixed", utc=True
    )
    merged = pd.merge_asof(
        merged.drop(columns="available_at").sort_values("timestamp"),
        fund.sort_values("available_at"), left_on="timestamp", right_on="available_at",
        direction="backward", allow_exact_matches=True,
    )
    merged.index = trade_index
    return merged.drop(columns=["timestamp", "available_at"])


def _simulate(spec, frame: pd.DataFrame, long_mask: pd.Series,
              short_mask: pd.Series) -> pd.Series:
    def filtered(data: pd.DataFrame):
        le, se, lsl, ltp, ssl, stp = spec.build(data)
        return le & long_mask, se & short_mask, lsl, ltp, ssl, stp
    return run_spec(replace(spec, build=filtered), frame)


def _variant(report: dict, name: str, result: pd.Series,
             reference_name: str, reference: pd.Series) -> None:
    report["variants"][name] = {
        "reference": reference_name,
        "full": _summary(result),
        "delta_weekly_R_ci95": _weekly_delta_ci(reference, result),
    }
    for label, lo, hi in (("2012_2021", 2012, 2021), ("2022_2026", 2022, 2026)):
        part = result[(result.index.year >= lo) & (result.index.year <= hi)]
        report["variants"][name][label] = _summary(part)


def run(refresh: bool = False) -> dict:
    spec = spec_by_name("SWEEP_CORE")
    frame = load_history(spec.symbol, spec.tf, start_year=2012)
    cot = _download_cot(refresh, int(frame.index.max().year))
    funding = _download_funding(refresh, pd.Timestamp(frame.index.max()).normalize())
    features = _asof_features(frame.index, cot, funding)

    real, dxy = _sources(refresh)
    dates = pd.DatetimeIndex(frame.index.normalize().unique())
    macro_daily = pd.DataFrame({
        "real_5d": delayed_change(real, dates, lag=2),
        "dxy_5d": delayed_change(dxy, dates, lag=1),
    }, index=dates)
    macro = macro_daily.reindex(frame.index.normalize()).set_axis(frame.index)

    cot_ok = features[["oi_change", "lev_net_change"]].notna().all(axis=1)
    fund_ok = features["funding_3d"].notna()
    macro_ok = macro.notna().all(axis=1)
    macro_long = (macro["real_5d"] <= 0) & (macro["dxy_5d"] <= 0)
    macro_short = (macro["real_5d"] >= 0) & (macro["dxy_5d"] >= 0)
    oi_up = features["oi_change"] >= 0
    lev_long = features["lev_net_change"] >= 0
    lev_short = features["lev_net_change"] <= 0
    fund_long = features["funding_3d"] >= 0
    fund_short = features["funding_3d"] <= 0

    masks = {
        "cot_baseline": (cot_ok, cot_ok),
        "oi_rising": (cot_ok & oi_up, cot_ok & oi_up),
        "leveraged_alignment": (cot_ok & lev_long, cot_ok & lev_short),
        "macro_cot_baseline": (cot_ok & macro_ok, cot_ok & macro_ok),
        "macro_both": (cot_ok & macro_ok & macro_long,
                       cot_ok & macro_ok & macro_short),
        "macro_both_oi": (cot_ok & macro_ok & macro_long & oi_up,
                          cot_ok & macro_ok & macro_short & oi_up),
        "macro_both_leveraged": (cot_ok & macro_ok & macro_long & lev_long,
                                 cot_ok & macro_ok & macro_short & lev_short),
        "funding_baseline": (fund_ok, fund_ok),
        "funding_alignment": (fund_ok & fund_long, fund_ok & fund_short),
        "macro_funding_baseline": (fund_ok & macro_ok, fund_ok & macro_ok),
        "macro_both_funding_reference": (fund_ok & macro_ok & macro_long,
                                         fund_ok & macro_ok & macro_short),
        "macro_both_funding": (fund_ok & macro_ok & macro_long & fund_long,
                               fund_ok & macro_ok & macro_short & fund_short),
    }
    results = {name: _simulate(spec, frame, lm, sm)
               for name, (lm, sm) in masks.items()}
    references = {
        "oi_rising": "cot_baseline",
        "leveraged_alignment": "cot_baseline",
        "macro_both": "macro_cot_baseline",
        "macro_both_oi": "macro_both",
        "macro_both_leveraged": "macro_both",
        "funding_alignment": "funding_baseline",
        "macro_both_funding": "macro_both_funding_reference",
    }
    report = {
        "hypotheses": {
            "oi_rising": "Haftalik NQ open interest artisi iki yonde de katilim teyidi",
            "leveraged_alignment": "Leveraged Money haftalik net degisimi islem yonunu teyit eder",
            "funding_alignment": "BTC 3 gun ortalama funding isareti NQ islem yonuyle aynidir",
            "macro_additions": "OI/COT/funding, reel faiz + DXY filtresine ek deger katar",
        },
        "scope": "SWEEP_CORE historical mirror; live rule unchanged; exploratory A/B",
        "data": {
            "price_first": str(frame.index.min()), "price_last": str(frame.index.max()),
            "bars": len(frame), "cot_rows": len(cot), "funding_rows": len(funding),
            "cot_policy": "Tuesday report used from following Monday 00:00 UTC",
            "funding_policy": "Published timestamp; trailing 9 observations (~3 days)",
        },
        "variants": {},
    }
    for name in ("cot_baseline", "macro_cot_baseline", "funding_baseline",
                 "macro_funding_baseline", "macro_both_funding_reference"):
        report["variants"][name] = {"reference": None, "full": _summary(results[name])}
    for name, reference_name in references.items():
        _variant(report, name, results[name], reference_name, results[reference_name])
    for name, result in results.items():
        result.rename("R").to_csv(OUT / f"trades_{name}.csv", index_label="entry_utc")
    features.to_csv(OUT / "bar_features.csv", index_label="bar_utc")
    (OUT / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.refresh), indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
