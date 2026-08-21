"""Uzun gecmis indirici -- yil yil, kesintiye dayanikli.

NEDEN: tum backtestler 3 yillik pencereyle (`LOOKBACK_DAYS`) kosuyordu. O
ornek ~37 hipotez finanse ediyor (bkz `search_budget.py`); 14 yil ~1.6 milyon.
Yani deneme butcesini buyuten sey islem gucu degil veri uzunlugu.

TASARIM -- neden yil yil:
`data.load_ohlcv` 14 yili tek istekte indirip tek dosyaya yaziyor. Indirme
yarim kalirsa (PC kapanir, ag koparsa) o sembol bastan iner. Burada her yil
AYRI dosyaya duser ve once `.part` olarak yazilip sonra yerine tasinir
(atomik). Boylece:
  - kapatirsan inen yillar diskte kalir, ertesi gun kaldigi yerden devam eder
  - yarim yazilmis dosya asla tam sanilmaz (sessizce eksik veriyle backtest
    yapmak, yanlis sonucu dogru sanmaktir)

Enstrumanin baslangicindan onceki yillar bos isaretlenir (`.empty`), boylece
her kosumda bosuna istek atilmaz.

Calistir:
    python -m intraday.history_fetch --symbols NASDAQ100 XAUUSD --tf 15m --from 2012
    python -m intraday.history_fetch --status
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable

import pandas as pd

from .config import INSTRUMENTS

CACHE = Path(__file__).resolve().parent.parent / "outputs" / "intraday" / "cache" / "history"
COLUMNS = ["open", "high", "low", "close", "volume"]

Fetch = Callable[[str, str, int], pd.DataFrame]


def _chunk_path(cache_dir: Path, symbol: str, tf: str, year: int) -> Path:
    return cache_dir / f"{symbol}_{tf}_{year}.csv"


def _empty_marker(cache_dir: Path, symbol: str, tf: str, year: int) -> Path:
    return cache_dir / f"{symbol}_{tf}_{year}.empty"


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """mt5_io/data.py sozlesmesi: UTC index, tz-NAIVE, float kolonlar."""
    df = df.copy()
    idx = pd.to_datetime(df.index, utc=True).tz_convert(None)
    df.index = idx
    df.index.name = "timestamp"
    df = df[COLUMNS].astype(float).sort_index()
    return df[~df.index.duplicated(keep="first")]


def _write_atomic(df: pd.DataFrame, path: Path) -> None:
    """Once .part'a yaz, sonra yerine tasi.

    Yarim yazilmis CSV'nin tam dosya sanilmasini engeller -- kesinti aninda
    dosya ya tam vardir ya hic yoktur.
    """
    tmp = path.with_suffix(path.suffix + ".part")
    try:
        df.to_csv(tmp)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _dukascopy_year(symbol: str, tf: str, year: int) -> pd.DataFrame:
    from datetime import datetime

    import dukascopy_python as dk

    from .data import _INTERVALS, _duka_const

    duka = INSTRUMENTS[symbol].duka
    if not duka:
        raise ValueError(f"{symbol} dukascopy'de yok (yalnizca broker CFD'si)")
    df = dk.fetch(_duka_const(duka), _INTERVALS[tf], dk.OFFER_SIDE_BID,
                  datetime(year, 1, 1), datetime(year + 1, 1, 1))
    return df if df is not None else pd.DataFrame()


def fetch_history(symbol: str, tf: str, start_year: int, end_year: int,
                  fetch: Fetch | None = None, cache_dir: Path | None = None,
                  bugun: pd.Timestamp | None = None,
                  on_progress: Callable[[str], None] | None = None) -> dict:
    """Yillari sirayla indir; inmis olanlari atla. Kesintiye dayanikli."""
    cache_dir = Path(cache_dir) if cache_dir is not None else CACHE
    cache_dir.mkdir(parents=True, exist_ok=True)
    fetch = fetch or _dukascopy_year
    bugun = bugun if bugun is not None else pd.Timestamp.utcnow().tz_localize(None)
    acik_yil = bugun.year

    inen, atlanan, bos = [], [], []
    for year in range(start_year, end_year + 1):
        path = _chunk_path(cache_dir, symbol, tf, year)
        marker = _empty_marker(cache_dir, symbol, tf, year)
        # Kapanmis yil zaten inmisse dokunma. Icinde bulunulan yil HER kosumda
        # tazelenir: gecen hafta indirilmis dosya bu haftanin barlarini icermez.
        if year < acik_yil and (path.exists() or marker.exists()):
            atlanan.append(year)
            continue

        df = fetch(symbol, tf, year)
        if df is None or df.empty:
            if year < acik_yil:
                marker.write_text("veri yok", encoding="utf-8")
            bos.append(year)
            if on_progress:
                on_progress(f"  {symbol} {tf} {year}: veri yok")
            continue

        df = _normalize(df)
        _write_atomic(df, path)
        inen.append(year)
        if on_progress:
            on_progress(f"  {symbol} {tf} {year}: {len(df):,} bar")

    return {"inen": inen, "atlanan": atlanan, "bos": bos}


def load_history(symbol: str, tf: str, start_year: int | None = None,
                 cache_dir: Path | None = None) -> pd.DataFrame:
    """Inmis yil parcalarini tek cerceveye birlestir."""
    cache_dir = Path(cache_dir) if cache_dir is not None else CACHE
    parcalar = sorted(cache_dir.glob(f"{symbol}_{tf}_*.csv"))
    if start_year is not None:
        parcalar = [p for p in parcalar if int(p.stem.split("_")[-1]) >= start_year]
    if not parcalar:
        raise FileNotFoundError(
            f"{symbol} {tf} icin inmis yil yok: {cache_dir}. Once history_fetch calistir."
        )
    frames = [pd.read_csv(p, parse_dates=["timestamp"]).set_index("timestamp")
              for p in parcalar]
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="first")]
    return df[COLUMNS].astype(float)


def status(symbol: str, tf: str, start_year: int, end_year: int,
           cache_dir: Path | None = None) -> dict:
    """Hangi yillar indi, hangileri bos, hangileri eksik."""
    cache_dir = Path(cache_dir) if cache_dir is not None else CACHE
    inen, bos, eksik = [], [], []
    for year in range(start_year, end_year + 1):
        if _chunk_path(cache_dir, symbol, tf, year).exists():
            inen.append(year)
        elif _empty_marker(cache_dir, symbol, tf, year).exists():
            bos.append(year)
        else:
            eksik.append(year)
    return {"symbol": symbol, "tf": tf, "inen": inen, "bos": bos, "eksik": eksik}


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", nargs="+", default=["NASDAQ100", "SP500", "XAUUSD",
                                                    "EURUSD", "GBPUSD"])
    p.add_argument("--tf", nargs="+", default=["15m"])
    p.add_argument("--from", dest="start", type=int, default=2012)
    p.add_argument("--to", dest="end", type=int, default=pd.Timestamp.utcnow().year)
    p.add_argument("--status", action="store_true", help="sadece durum raporu")
    a = p.parse_args()

    for symbol in a.symbols:
        for tf in a.tf:
            if a.status:
                d = status(symbol, tf, a.start, a.end)
                print(f"{symbol:10} {tf:4} inen={len(d['inen'])} bos={len(d['bos'])} "
                      f"eksik={d['eksik']}")
                continue
            print(f"[{symbol} {tf}] {a.start}-{a.end}", flush=True)
            try:
                out = fetch_history(symbol, tf, a.start, a.end,
                                    on_progress=lambda m: print(m, flush=True))
                print(f"  -> inen={len(out['inen'])} atlanan={len(out['atlanan'])} "
                      f"bos={len(out['bos'])}", flush=True)
            except Exception as e:
                print(f"  [HATA] {symbol} {tf}: {e}", flush=True)


if __name__ == "__main__":
    main()
