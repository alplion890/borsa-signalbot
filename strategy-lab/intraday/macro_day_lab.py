"""MACRO_DAY_DRIFT_NQ -- on-kayitli hipotez (hypotheses.json, id=macro_day_drift_nq).

NE: FOMC karar gununde, KARAR ACIKLANMADAN once long. Cikis duyurudan hemen
once -- spike'a bilerek girilmez.

NEDEN (Hermes'in on-kaydindan): Lucca-Moench (JF 2015) "pre-FOMC announcement
drift" -- duyuru oncesi hisse getirisi anormal yuksek, belirsizlik primi
duyuruyla cozuluyor. Takvim onceden bilinir, sinyal look-ahead'siz kurulur.

GRID (Hermes 2026-08-24 revizyonu, 12 -> 4):
    2 enstruman (NASDAQ100, SP500) x FOMC x 2 giris varyanti = 4 kombinasyon.
    CPI/NFP bu kayitta TARANMAZ (ayri kayitla, bu sonucu gormeden yazilacak).
    Duyurudan SONRA giris varyanti taranmaz -- kisa devre olurdu.

ZAMANLAMA (15m bar, index = bar ACILISI, UTC):
    Duyuru 15m izgarasina oturuyor (12:30 / 14:00 / 14:15 ET hepsi tam bar).
    p = duyuruyu ICEREN bar. p-1 barinin KAPANISI = duyuru ani, spike bir
    sonraki barda -> p-1 kapanisi son temiz duyuru-oncesi fiyat.

      varyant "1bar": sinyal p-2  -> giris p-2 kapanisi (duyuru-15dk)
                                     cikis p-1 kapanisi (duyuru ani)
      varyant "2bar": sinyal p-3  -> giris p-3 kapanisi (duyuru-30dk)
                                     cikis p-1 kapanisi (duyuru ani)

    SAPMA (kayitla fark, bilerek): on-kayit "cikis = duyuru-5dk" diyor.
    15m granularitesinde 13:55 diye bir bar siniri YOK. En yakin temiz cikis
    p-1 kapanisi, yani duyuru-0dk. Bunun duyuru-oncesi oldugu veriyle
    dogrulandi: 2024-09-18'de p-1 bari 19430-19464 araliginda, spike (19652)
    p barinda. Pozisyon spike'i TASIMIYOR -- mekanizma korunuyor.

STOP/HEDEF: stop = giris - 0.5*ATR(14, GUNLUK, onceki gun), RR 1.0,
    vurulmazsa pencere sonunda zaman-cikisi.

Calistir:
    python -m intraday.macro_day_lab
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import pandas as pd

from .config import INSTRUMENTS
from .event_calendar import fomc_events
from .history_fetch import load_history
from .honest_engine import simulate_trades
from .indicators import atr
from .overfit_stats import sharpe

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

SEMBOLLER = ("NASDAQ100", "SP500")
TF = "15m"
ATR_GUN = 14
STOP_ATR_CARPAN = 0.5
RR = 1.0
BASLANGIC_YIL = 2012

# varyant adi -> (sinyalin duyuru barina gore ofseti, max_hold)
VARYANTLAR = {"1bar": (-2, 1), "2bar": (-3, 2)}


@dataclass(frozen=True)
class Sonuc:
    sembol: str
    varyant: str
    r: pd.Series


def gunluk_atr(df: pd.DataFrame) -> pd.Series:
    """Onceki gunun ATR(14)'u, her 15m bara yayilmis.

    shift(1): islem gunune ait ATR o gun kapanmadan bilinemez.
    """
    gun = df.resample("1D").agg({"open": "first", "high": "max",
                                 "low": "min", "close": "last"}).dropna()
    a = atr(gun, ATR_GUN).shift(1)
    return pd.Series(df.index.normalize(), index=df.index).map(a)


def _duyuru_utc(gun, saat_et) -> pd.Timestamp:
    """ET tarih+saat -> naive UTC (veri index'i naive UTC)."""
    yerel = pd.Timestamp.combine(gun, saat_et).tz_localize(ET)
    return yerel.tz_convert(UTC).tz_localize(None)


def sinyal_kur(df: pd.DataFrame, ofset: int) -> pd.Series:
    """Her FOMC gunu icin tek long sinyali; duyuru barina gore `ofset`."""
    sinyal = pd.Series(False, index=df.index)
    bulunan = 0
    for e in fomc_events():
        t = _duyuru_utc(e.gun, e.aciklama_et)
        loc = df.index.get_indexer([t])[0]
        if loc == -1:                      # o bar veride yok (tatil/bosluk)
            continue
        i = loc + ofset
        if i < 0:
            continue
        sinyal.iloc[i] = True
        bulunan += 1
    if not bulunan:
        raise RuntimeError("Hicbir FOMC bari veride bulunamadi -- zaman dilimi hatasi?")
    return sinyal


def kos(sembol: str, varyant: str, df: pd.DataFrame) -> pd.Series:
    ofset, max_hold = VARYANTLAR[varyant]
    le = sinyal_kur(df, ofset)
    se = pd.Series(False, index=df.index)          # YALNIZ LONG (on-kayit)

    a = gunluk_atr(df)
    giris = df["close"]
    risk = STOP_ATR_CARPAN * a
    long_sl = (giris - risk).where(le)
    long_tp = (giris + RR * risk).where(le)
    bos = pd.Series(float("nan"), index=df.index)

    return simulate_trades(df, le, se, long_sl, long_tp, bos, bos,
                           INSTRUMENTS[sembol],
                           min_rr=RR - 0.01, max_rr=RR, max_hold=max_hold)


def ozet(r: pd.Series) -> dict:
    if not len(r):
        return {"islem": 0, "toplam_R": 0.0, "exp_R": float("nan"),
                "SR": float("nan")}
    return {"islem": len(r), "toplam_R": float(r.sum()),
            "exp_R": float(r.mean()),
            "SR": sharpe(r) if len(r) > 1 else float("nan")}


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    sonuclar: list[Sonuc] = []
    for sembol in SEMBOLLER:
        df = load_history(sembol, TF, start_year=BASLANGIC_YIL)
        print(f"\n{sembol} {TF}: {len(df):,} bar  "
              f"{df.index[0].date()} -> {df.index[-1].date()}")
        for varyant in VARYANTLAR:
            r = kos(sembol, varyant, df)
            o = ozet(r)
            print(f"  {varyant:5} islem={o['islem']:4}  toplam_R={o['toplam_R']:+8.2f}  "
                  f"exp_R={o['exp_R']:+.4f}  SR={o['SR']:+.4f}")
            sonuclar.append(Sonuc(sembol, varyant, r))

    havuz = pd.concat([s.r for s in sonuclar]).sort_index()
    o = ozet(havuz)
    print(f"\nHAVUZ (4 kombinasyon): islem={o['islem']}  "
          f"toplam_R={o['toplam_R']:+.2f}  exp_R={o['exp_R']:+.4f}  SR={o['SR']:+.4f}")

    yil = havuz.groupby(havuz.index.year).agg(["size", "sum", "mean"])
    yil.columns = ["islem", "toplam_R", "exp_R"]
    print("\nYIL YIL (havuz):")
    print(yil.to_string(float_format=lambda x: f"{x:+.3f}"))
    print(f"\nPozitif yil: {(yil['toplam_R'] > 0).sum()}/{len(yil)}")

    return sonuclar, havuz


if __name__ == "__main__":
    main()
