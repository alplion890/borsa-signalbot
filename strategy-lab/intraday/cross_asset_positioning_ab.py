"""Bes tarihsel modulde genis makro taban + OI/COT/funding A/B.

Canli kurallari degistirmez. Gunluk veriler yayin gecikmeli, CFTC sali verisi
izleyen pazartesiden itibaren ve funding yalniz yayinlandiktan sonra kullanilir.
"""
from __future__ import annotations

import argparse
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

from .history_fetch import load_history
from .long_history_ab import run_spec, spec_by_name
from .macro_context_ab import (_summary, _weekly_delta_ci, delayed_change,
                               gbp_causal_build)
from .positioning_context_ab import _download_funding

OUT = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "cross_asset_positioning_ab"
CFTC = "https://www.cftc.gov/files/dea/history"
MODULES = ("SWEEP_CORE", "NQ_ORB", "GOLD_ORB", "EUR_LONDON", "GBP_LONDON")

# Her isaret long yon icin beklenen iliskiyi gosterir. +1 paralel, -1 ters.
RELATIONS = {
    "SWEEP_CORE": {"dxy": -1, "dgs2": -1, "dgs10": -1, "real": -1,
                   "breakeven": -1, "es": 1},
    "NQ_ORB": {"dxy": -1, "dgs2": -1, "dgs10": -1, "real": -1,
               "breakeven": -1, "es": 1},
    "GOLD_ORB": {"dxy": -1, "dgs10": -1, "real": -1,
                 "breakeven": 1, "eur": 1},
    "EUR_LONDON": {"dxy": -1, "dgs2": -1, "dgs10": -1, "gbp": 1},
    "GBP_LONDON": {"dxy": -1, "dgs2": -1, "dgs10": -1, "eur": 1},
}
MARKET = {
    "SWEEP_CORE": "nq", "NQ_ORB": "nq", "GOLD_ORB": "gold",
    "EUR_LONDON": "eur", "GBP_LONDON": "gbp",
}


def _macro_sources(refresh: bool) -> dict[str, pd.Series]:
    OUT.mkdir(parents=True, exist_ok=True)
    fred_path = OUT / "fred_rates.csv"
    market_path = OUT / "yahoo_cross_assets.csv"
    if refresh or not fred_path.exists():
        pd.read_csv(
            "https://fred.stlouisfed.org/graph/fredgraph.csv?"
            "id=DGS2,DGS10,DFII10,T10YIE"
        ).to_csv(fred_path, index=False)
    if refresh or not market_path.exists():
        tickers = {"dxy": "DX-Y.NYB", "es": "ES=F", "eur": "EURUSD=X",
                   "gbp": "GBPUSD=X"}
        pieces = []
        for name, ticker in tickers.items():
            raw = yf.Ticker(ticker).history(start="2012-01-01", interval="1d",
                                            auto_adjust=False)
            if raw.empty:
                raise RuntimeError(f"Yahoo {ticker} gunluk verisi bos")
            pieces.append(pd.DataFrame({"date": raw.index.date,
                                        "name": name,
                                        "close": raw["Close"].to_numpy()}))
        pd.concat(pieces, ignore_index=True).to_csv(market_path, index=False)
    fred = pd.read_csv(fred_path, parse_dates=["observation_date"])
    market = pd.read_csv(market_path, parse_dates=["date"])
    result = {}
    for name, column in {"dgs2": "DGS2", "dgs10": "DGS10",
                         "real": "DFII10", "breakeven": "T10YIE"}.items():
        values = pd.to_numeric(fred[column], errors="coerce")
        values.index = pd.DatetimeIndex(fred["observation_date"])
        result[name] = values.sort_index()
    for name, part in market.groupby("name"):
        values = pd.to_numeric(part["close"], errors="coerce")
        values.index = pd.DatetimeIndex(part["date"])
        result[str(name)] = values.sort_index()
    return result


def _read_zip(url: str) -> pd.DataFrame:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        result = pd.read_csv(archive.open(archive.namelist()[0]), low_memory=False)
    result.columns = result.columns.str.strip()
    return result


def _positioning_sources(refresh: bool, end_year: int) -> pd.DataFrame:
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / "cftc_all_markets.csv"
    if cache.exists() and not refresh:
        data = pd.read_csv(cache)
        data["report_date"] = pd.to_datetime(data["report_date"], format="mixed")
        data["available_date"] = pd.to_datetime(data["available_date"], format="mixed")
        return data
    rows = []
    for year in range(2012, end_year + 1):
        tff = _read_zip(f"{CFTC}/fut_fin_txt_{year}.zip")
        names = tff["Market_and_Exchange_Names"].astype(str).str.strip()
        date_column = ("Report_Date_as_YYYY-MM-DD"
                       if "Report_Date_as_YYYY-MM-DD" in tff.columns
                       else "Report_Date_as_MM_DD_YYYY")
        market_masks = {
            "nq": names.str.contains("NASDAQ-100 Consolidated", case=False, na=False),
            "eur": names.str.match(r"^EURO FX - CHICAGO", case=False, na=False),
            "gbp": (names.str.contains("BRITISH POUND", case=False, na=False) &
                    ~names.str.contains("XRATE", case=False, na=False)),
        }
        for key, mask in market_masks.items():
            part = tff.loc[mask]
            for _, row in part.iterrows():
                rows.append({
                    "market": key,
                    "report_date": row[date_column],
                    "open_interest": row["Open_Interest_All"],
                    "trader_long": row["Lev_Money_Positions_Long_All"],
                    "trader_short": row["Lev_Money_Positions_Short_All"],
                })
        disagg = _read_zip(f"{CFTC}/fut_disagg_txt_{year}.zip")
        disagg_names = disagg["Market_and_Exchange_Names"].astype(str).str.strip()
        disagg_date = ("Report_Date_as_YYYY-MM-DD"
                       if "Report_Date_as_YYYY-MM-DD" in disagg.columns
                       else "Report_Date_as_MM_DD_YYYY")
        gold = disagg.loc[disagg_names == "GOLD - COMMODITY EXCHANGE INC."]
        for _, row in gold.iterrows():
            rows.append({
                "market": "gold",
                "report_date": row[disagg_date],
                "open_interest": row["Open_Interest_All"],
                "trader_long": row["M_Money_Positions_Long_All"],
                "trader_short": row["M_Money_Positions_Short_All"],
            })
    result = pd.DataFrame(rows)
    result["report_date"] = pd.to_datetime(
        result["report_date"], format="mixed", errors="coerce"
    )
    for column in ("open_interest", "trader_long", "trader_short"):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.dropna().sort_values(["market", "report_date"])
    result = result.drop_duplicates(["market", "report_date"], keep="last")
    result["available_date"] = result["report_date"] + pd.Timedelta(days=6)
    groups = result.groupby("market", sort=False)
    result["oi_change"] = groups["open_interest"].diff()
    result["trader_net"] = result["trader_long"] - result["trader_short"]
    result["cot_change"] = result.groupby("market", sort=False)["trader_net"].diff()
    result.to_csv(cache, index=False)
    return result


def _daily_context(module: str, dates: pd.DatetimeIndex,
                   sources: dict[str, pd.Series]) -> pd.DataFrame:
    data = {}
    for name in RELATIONS[module]:
        lag = 2 if name in {"dgs2", "dgs10", "real", "breakeven"} else 1
        data[name] = delayed_change(sources[name], dates, lag=lag)
    frame = pd.DataFrame(data, index=dates)
    frame["valid"] = frame.notna().all(axis=1)
    signed = pd.DataFrame({name: frame[name].apply(
        lambda value, relation=relation: 0 if pd.isna(value) or value == 0
        else (1 if value * relation > 0 else -1)
    ) for name, relation in RELATIONS[module].items()}, index=dates)
    frame["score"] = signed.sum(axis=1)
    # Cift sayida ozellikte esitlik gecmez: gercek cogunluk gerekir.
    frame["long_ok"] = frame["valid"] & (frame["score"] > 0)
    frame["short_ok"] = frame["valid"] & (frame["score"] < 0)
    return frame


def _asof_positioning(index: pd.DatetimeIndex, data: pd.DataFrame,
                      market: str, funding: pd.DataFrame) -> pd.DataFrame:
    bars = pd.DataFrame({"timestamp": pd.to_datetime(index, utc=True)})
    part = data.loc[data["market"] == market,
                    ["available_date", "oi_change", "cot_change"]].copy()
    part["available_at"] = pd.to_datetime(part.pop("available_date"), utc=True)
    result = pd.merge_asof(bars, part.sort_values("available_at"),
                           left_on="timestamp", right_on="available_at",
                           direction="backward").drop(columns="available_at")
    fund = funding[["available_at", "funding_3d"]].copy()
    fund["available_at"] = pd.to_datetime(fund["available_at"], format="mixed", utc=True)
    result = pd.merge_asof(result, fund.sort_values("available_at"),
                           left_on="timestamp", right_on="available_at",
                           direction="backward").drop(columns=["timestamp", "available_at"])
    result.index = index
    return result


def _simulate(spec, data: pd.DataFrame, long_mask: pd.Series,
              short_mask: pd.Series) -> pd.Series:
    def filtered(frame: pd.DataFrame):
        le, se, lsl, ltp, ssl, stp = spec.build(frame)
        return le & long_mask, se & short_mask, lsl, ltp, ssl, stp
    return run_spec(replace(spec, build=filtered), data)


def run(refresh: bool = False) -> dict:
    sources = _macro_sources(refresh)
    positioning = _positioning_sources(refresh, 2026)
    # Tek indirme, butun modullerde ayni point-in-time funding serisi.
    funding = _download_funding(refresh, pd.Timestamp("2026-12-31"))
    report = {"method": {
        "macro": RELATIONS,
        "daily_lag": "FRED 2 business days; Yahoo 1 business day; 5-day change",
        "cot_lag": "Tuesday report available following Monday 00:00 UTC",
        "funding": "BTCUSDT trailing 9 published observations (~3 days)",
    }, "modules": {}}
    for module in MODULES:
        spec = spec_by_name(module)
        if module == "GBP_LONDON":
            spec = replace(spec, build=gbp_causal_build)
        prices = load_history(spec.symbol, spec.tf, start_year=2012)
        dates = pd.DatetimeIndex(prices.index.normalize().unique())
        daily = _daily_context(module, dates, sources)
        aligned = daily.reindex(prices.index.normalize()).set_axis(prices.index)
        pos = _asof_positioning(prices.index, positioning, MARKET[module], funding)
        macro_valid = aligned["valid"].fillna(False).astype(bool)
        macro_long = aligned["long_ok"].fillna(False).astype(bool)
        macro_short = aligned["short_ok"].fillna(False).astype(bool)
        cot_valid = pos[["oi_change", "cot_change"]].notna().all(axis=1)
        funding_valid = pos["funding_3d"].notna()
        masks = {
            "macro_coverage_baseline": (macro_valid, macro_valid),
            "macro_cross_asset": (macro_long, macro_short),
            "macro_cot_coverage_reference": (macro_long & cot_valid,
                                             macro_short & cot_valid),
            "macro_plus_oi": (macro_long & cot_valid & (pos["oi_change"] >= 0),
                              macro_short & cot_valid & (pos["oi_change"] >= 0)),
            "macro_plus_cot": (macro_long & cot_valid & (pos["cot_change"] >= 0),
                               macro_short & cot_valid & (pos["cot_change"] <= 0)),
            "macro_funding_coverage_reference": (macro_long & funding_valid,
                                                 macro_short & funding_valid),
            "macro_plus_funding": (macro_long & funding_valid & (pos["funding_3d"] >= 0),
                                   macro_short & funding_valid & (pos["funding_3d"] <= 0)),
        }
        results = {name: _simulate(spec, prices, lm, sm)
                   for name, (lm, sm) in masks.items()}
        references = {
            "macro_cross_asset": "macro_coverage_baseline",
            "macro_plus_oi": "macro_cot_coverage_reference",
            "macro_plus_cot": "macro_cot_coverage_reference",
            "macro_plus_funding": "macro_funding_coverage_reference",
        }
        item = {"symbol": spec.symbol, "timeframe": spec.tf, "variants": {}}
        for name, result in results.items():
            summary = {"full": _summary(result), "reference": references.get(name)}
            if name in references:
                summary["delta_weekly_R_ci95"] = _weekly_delta_ci(
                    results[references[name]], result
                )
            for label, lo, hi in (("2012_2021", 2012, 2021),
                                  ("2022_2026", 2022, 2026)):
                part = result[(result.index.year >= lo) & (result.index.year <= hi)]
                summary[label] = _summary(part)
            item["variants"][name] = summary
            folder = OUT / module
            folder.mkdir(parents=True, exist_ok=True)
            result.rename("R").to_csv(folder / f"trades_{name}.csv", index_label="entry_utc")
        report["modules"][module] = item
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
