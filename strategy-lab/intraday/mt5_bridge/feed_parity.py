"""signalbot feed'i ile MT5 broker feed'i arasindaki fiyat farki.

NEDEN: Telegram sinyali signalbot'un yfinance serisinden uretiliyor, ama emir
MT5'te broker'in kendi enstrumanina giriliyor. Iki seri AYNI DEGIL.

DIKKAT -- signalbot cogu enstrumanda VADELI kullaniyor (bkz signalbot/symbols.py):
    NASDAQ100 -> NQ=F   (vadeli)  vs MT5 US100  (nakit endeks CFD'si)
    XAUUSD    -> GC=F   (vadeli)  vs MT5 XAUUSD (spot)
    SP500     -> ES=F   (vadeli)  vs MT5 US500  (nakit endeks CFD'si)
    EURUSD/GBPUSD -> spot vs spot (fark kucuk beklenir)
Vadeli ile nakit arasinda tasima maliyeti kaynakli yapisal bir baz farki olur
ve vade yaklastikca kapanir. symbols.py'nin kendi yorumu bunu zaten isaret
ediyordu: "Kontrat-vade/baz farki, gercek piyasa hareketi gibi gorunebiliyor."

Sabit basis ZARARSIZDIR: dedektor seviyeleri de ayni seriden hesapliyor, hepsi
birlikte kayar. TEHLIKELI OLAN basis'in oynakligi -- cunku sinyal fiyati ile
girilen fiyat arasindaki farki O yaratir ve dogrudan R'den yer.

Bu yuzden olculen sey basis'in kendisi degil, basis'in ARTIK OYNAKLIGI:
gunluk medyan cikarilir, kalan gurultu R cinsine cevrilir.

Kullanim (MT5 terminali acik + Maven hesabinda login olmali):
    python -m intraday.mt5_bridge.feed_parity                 # tum semboller
    python -m intraday.mt5_bridge.feed_parity XAUUSD EURUSD   # secili
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..signalbot import free_data
from ..signalbot.symbols import resolve
from . import mt5_io

TF = "5m"
DAYS = 30
LEDGER = "outputs/intraday/forward_ea/forward_ledger.csv"
# Olculecek semboller. BTC yok: iki taraf da ayni Binance serisini kullanmiyor
# (signalbot Binance spot, MT5 BTCUSD CFD) ama BTC zaten Telegram'a cikmiyor.
SYMBOLS = ("NASDAQ100", "XAUUSD", "EURUSD", "GBPUSD")


def _median_stop_distance(symbol_key: str,
                          path: str = LEDGER) -> float | None:
    """Defterde bu SEMBOLE ait islemlerin medyan stop mesafesi (fiyat puani).

    R'yi puana cevirmek icin gerekli: 1R = |entry - sl|. Modul adina degil
    sembole bakar -- ayni sembolde birden fazla modul olabilir ve stop
    mesafesi modulden cok enstrumanin oynakligiyla belirlenir.
    """
    try:
        df = pd.read_csv(path)
    except OSError:
        return None
    sub = df[df["symbol"] == symbol_key]
    if sub.empty:
        return None
    return float((sub["entry"] - sub["sl"]).abs().median())


def load_pair(symbol_key: str, days: int = DAYS, tf: str = TF) -> pd.DataFrame:
    """Iki feed'i ortak zaman damgalarinda hizala (UTC, tz-naive)."""
    yf_df = free_data.ohlcv(symbol_key, tf, days=days)
    if yf_df.empty:
        raise RuntimeError(f"{symbol_key}: signalbot feed'i bos geldi.")
    yf_close = yf_df["close"]
    yf_close.index = pd.DatetimeIndex(yf_close.index).tz_convert("UTC").tz_localize(None)

    mt5_df = mt5_io.ohlcv(symbol_key, tf, days=days)
    mt5_close = mt5_df["close"]
    idx = pd.DatetimeIndex(mt5_close.index)
    if idx.tz is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)
    mt5_close = mt5_close.set_axis(idx)

    pair = pd.concat({"yf": yf_close, "mt5": mt5_close}, axis=1).dropna()
    if pair.empty:
        raise RuntimeError("Iki feed'in ortak zaman damgasi yok "
                           "(saat dilimi veya seans uyusmazligi).")
    return pair


def report(symbol_key: str, days: int = DAYS, tf: str = TF) -> dict:
    pair = load_pair(symbol_key, days, tf)
    basis = pair["mt5"] - pair["yf"]
    # Sabit/yavas suruklenen kismi cikar: gunluk medyan basis.
    daily = basis.groupby(basis.index.normalize()).transform("median")
    residual = basis - daily

    yf_ret = pair["yf"].pct_change()
    mt5_ret = pair["mt5"].pct_change()
    both = pd.concat([yf_ret, mt5_ret], axis=1).dropna()

    stop = _median_stop_distance(symbol_key)
    out = {
        "sembol": symbol_key,
        "signalbot_ticker": resolve(symbol_key).ticker,
        "mt5_sembol": mt5_io.SYMBOL_MAP.get(symbol_key, symbol_key),
        "ortak_bar": len(pair),
        "pencere": f"{pair.index.min()} -> {pair.index.max()}",
        "basis_ortalama": float(basis.mean()),
        "basis_std": float(basis.std(ddof=1)),
        "basis_gun_ici_surukleme": float(daily.groupby(daily.index.normalize())
                                         .first().diff().abs().mean()),
        "artik_std_puan": float(residual.std(ddof=1)),
        "artik_p95_puan": float(residual.abs().quantile(0.95)),
        "getiri_korelasyonu": float(both.iloc[:, 0].corr(both.iloc[:, 1])),
        "medyan_stop_puan": stop,
    }
    if stop:
        out["artik_std_R"] = out["artik_std_puan"] / stop
        out["artik_p95_R"] = out["artik_p95_puan"] / stop
    return out


def _print_one(res: dict) -> None:
    print(f"\n=== {res['sembol']}: {res['signalbot_ticker']} (signalbot) "
          f"vs {res['mt5_sembol']} (MT5)")
    print(f"  ortak bar      : {res['ortak_bar']}  [{res['pencere']}]")
    print(f"  getiri koresp. : {res['getiri_korelasyonu']:.4f}")
    print(f"  basis ortalama : {res['basis_ortalama']:+.4f} "
          f"(std {res['basis_std']:.4f})")
    print(f"  gunluk kayma   : {res['basis_gun_ici_surukleme']:.4f}")
    print(f"  ARTIK gurultu  : std {res['artik_std_puan']:.4f}, "
          f"p95 {res['artik_p95_puan']:.4f}")
    if res.get("medyan_stop_puan"):
        print(f"  medyan stop    : {res['medyan_stop_puan']:.4f} (defterden)")
        print(f"  => ARTIK std   : {res['artik_std_R']:.3f} R")
        print(f"  => ARTIK p95   : {res['artik_p95_R']:.3f} R")
    else:
        print("  medyan stop    : defterde bu sembolde islem yok -> R'ye "
              "cevrilemedi")


def main(argv: list[str] | None = None) -> None:
    import sys

    keys = list(argv if argv is not None else sys.argv[1:]) or list(SYMBOLS)
    rows = []
    # Tek oturum: her sembol icin ayri initialize/shutdown terminali yorar.
    with mt5_io.session():
        for key in keys:
            try:
                rows.append(report(key))
            except Exception as exc:                      # noqa: BLE001
                print(f"\n=== {key}: OLCULEMEDI -- {exc}")
    for res in rows:
        _print_one(res)
    if rows:
        print("\n--- ozet (artik gurultu, R) ---")
        for res in rows:
            r = res.get("artik_p95_R")
            print(f"  {res['sembol']:10s} basis {res['basis_ortalama']:+10.4f}"
                  f"   p95 artik {'-' if r is None else f'{r:.3f} R'}")


if __name__ == "__main__":
    main()
