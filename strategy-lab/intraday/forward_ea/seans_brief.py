"""Diskresyoner seans brifingi -- SADECE OLGU, YORUM YOK.

NEDEN VAR: diskresyoner deneyde yorumu kullanici yapiyor ("sen bana olaylari
soyle, ben yorumlarim" -- 2026-08-24 karari). Bu script o ayrimi korumak icin
var: hangi olayi gostermek de bir secimdir, o yuzden alanlar HER GUN AYNI ve
SABIT -- bugun ilginc bulduguma gore degil. Hicbir alan "guclu/zayif",
"yuksek/dusuk", "pozitif/negatif" gibi yorum sifati kullanmiyor; sadece
sayi, yuzdelik ve tarih basiyor. Yorumlayan taraf kullanici.

NE GOSTERIR (sabit alan seti, her sembol icin ayni):
  - takvim: bugun + bu hafta FOMC/CPI/NFP (dis kaynakli, on-kayitli takvim)
  - fiyat: son kapanis, dun/bugun araligi
  - 200EMA'ya uzaklik (puan ve %) -- ham sayi, "ustunde/pahali" demiyor
  - ATR(14) yuzdelik dilimi (son 100 gun icinde nerede) -- SON KAPALI gunden
  - hacim yuzdelik dilimi (son 20 gun icinde nerede) -- SON KAPALI gunden
  - son 60 gunde donus yapmis seviyeler (swing high/low, tarihli)
  - seans: hangi seans acik, kapanisa kac saat

Calistir (MT5 venv, dukascopy_python gerekli):
    python -m intraday.forward_ea.seans_brief
    python -m intraday.forward_ea.seans_brief --tazele   # 2026 yilini once guncelle
    python -m intraday.forward_ea.seans_brief --semboller NASDAQ100 XAUUSD
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable
from zoneinfo import ZoneInfo

import pandas as pd

from ..event_calendar import MacroEvent, all_events
from ..history_fetch import fetch_history, load_history
from ..indicators import atr, ema, swing_high, swing_low

TR = ZoneInfo("Europe/Istanbul")
UTC = timezone.utc

VARSAYILAN_SEMBOLLER = [
    ("NASDAQ100", "15m"),
    ("XAUUSD", "5m"),
    ("EURUSD", "5m"),
    ("GBPUSD", "5m"),
]

SEANSLAR = [  # (ad, baslangic_utc_saat, bitis_utc_saat)
    ("Tokyo", 0, 9),
    ("Londra", 7, 16),
    ("New York", 13, 21),
]

ATR_PENCERE = 100
HACIM_PENCERE = 20
SWING_GUN = 60


@dataclass(frozen=True)
class SembolOlgusu:
    sembol: str
    son_kapanis: float
    son_bar_utc: str
    dun_yuksek: float
    dun_dusuk: float
    bugun_yuksek: float
    bugun_dusuk: float
    ema200: float
    ema200_uzaklik_puan: float
    ema200_uzaklik_yuzde: float
    # ATR/hacim SON KAPALI GUNDEN gelir; bugunun yarim bari disarida.
    atr_bugun: float
    atr_yuzdelik: float
    hacim_bugun: float
    hacim_yuzdelik: float
    donus_seviyeleri: list[tuple[str, float, str]]  # (tarih, fiyat, tip)


def _gunluk(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("1D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last",
         "volume": "sum"}
    ).dropna(subset=["close"])


def _yuzdelik(seri: pd.Series, pencere: int) -> float:
    """Son degerin, son `pencere` gozlem icindeki yuzdelik sirasi (0-100)."""
    son_n = seri.dropna().iloc[-pencere:]
    if len(son_n) < 2:
        return float("nan")
    return 100.0 * (son_n < son_n.iloc[-1]).sum() / (len(son_n) - 1)


def _donus_seviyeleri(gunluk_df: pd.DataFrame, gun: int) -> list[tuple[str, float, str]]:
    pencere = gunluk_df.iloc[-gun:]
    if len(pencere) < 10:
        return []
    sh = swing_high(pencere, left=2, right=2)
    sl = swing_low(pencere, left=2, right=2)
    seviyeler: dict[str, tuple[float, str]] = {}
    for seri, tip in ((sh, "direnc"), (sl, "destek")):
        degisim = seri[seri.diff().fillna(1) != 0]
        for ts, deger in degisim.items():
            if pd.notna(deger):
                seviyeler[f"{ts.date()}_{tip}"] = (float(deger), tip)
    sirali = sorted(seviyeler.items(), key=lambda kv: kv[0])[-8:]
    return [(k.split("_")[0], v[0], v[1]) for k, v in sirali]


def _yerel_veri(sembol: str, tf: str, tazele: bool) -> pd.DataFrame:
    """PC yolu: dukascopy cache."""
    if tazele:
        fetch_history(sembol, tf, date.today().year, date.today().year)
    return load_history(sembol, tf, start_year=date.today().year - 1)


def sembol_olgusu(sembol: str, tf: str, tazele: bool = False,
                  veri: Callable[[str, str], pd.DataFrame] | None = None,
                  gunluk_veri: Callable[[str], pd.DataFrame] | None = None,
                  ) -> SembolOlgusu:
    """Sabit alan seti. Feed DISARIDAN verilebilir.

    NEDEN ENJEKSIYON (2026-09-01): telefon brifingi GitHub Actions'ta uretiliyor
    ve orada dukascopy yok. Ikinci bir olgu ureticisi yazmak bu projenin tekrar
    eden hata sinifi olurdu (whitelist iki kopya, defterin bes okuyucusu, iki
    eslestirici). Alan seti tek yerde kaliyor; degisen yalnizca veri kaynagi.

    NEDEN AYRI GUNLUK FEED: EMA200 ve ATR'nin 100 gunluk yuzdeligi 200+ gunluk
    bar ister. Intraday seriyi resample etmek PC'de yetiyor (dukascopy 2 yil
    veriyor) ama yfinance 15m'i en fazla 60 gun donduruyor -- yani bulutta
    "EMA200" aslinda 60 barla hesaplanip sessizce yanlis basiliyordu.
    """
    df = veri(sembol, tf) if veri is not None else _yerel_veri(sembol, tf, tazele)
    if df.empty:
        raise RuntimeError(f"{sembol} {tf}: veri bos")

    gunluk = _gunluk(gunluk_veri(sembol)) if gunluk_veri is not None else _gunluk(df)
    bugun_utc = pd.Timestamp.now(UTC).tz_localize(None).normalize()
    dun = gunluk[gunluk.index < bugun_utc]
    bugun_bar = gunluk[gunluk.index >= bugun_utc]

    # KISMI GUN DISARIDA (2026-09-01'de bulundu): bugunun gunluk bari daha
    # kapanmadi. ATR/hacim/EMA'yi onun uzerinden hesaplamak sistematik olarak
    # DUSUK gosteriyordu -- NASDAQ "ATR 100 gunun %0. yuzdeligi" basiyordu,
    # cunku yarim gunun araligi elbette en dar. Yorum degil OLGU basmak
    # iddiasindaki bir dosyada bu sessiz bir yalan.
    # Bugunun ham araligi (bugun_yuksek/dusuk) ayri alan olarak duruyor.
    tam = dun if len(dun) >= 2 else gunluk
    ema200 = ema(tam["close"], 200)
    a = atr(tam, 14)
    son_kapanis = float(df["close"].iloc[-1])

    return SembolOlgusu(
        sembol=sembol,
        son_kapanis=son_kapanis,
        son_bar_utc=str(df.index[-1]),
        dun_yuksek=float(dun["high"].iloc[-1]) if len(dun) else float("nan"),
        dun_dusuk=float(dun["low"].iloc[-1]) if len(dun) else float("nan"),
        bugun_yuksek=float(bugun_bar["high"].iloc[-1]) if len(bugun_bar) else float("nan"),
        bugun_dusuk=float(bugun_bar["low"].iloc[-1]) if len(bugun_bar) else float("nan"),
        ema200=float(ema200.iloc[-1]),
        ema200_uzaklik_puan=son_kapanis - float(ema200.iloc[-1]),
        ema200_uzaklik_yuzde=100 * (son_kapanis - float(ema200.iloc[-1])) / float(ema200.iloc[-1]),
        atr_bugun=float(a.iloc[-1]),
        atr_yuzdelik=_yuzdelik(a, ATR_PENCERE),
        hacim_bugun=float(tam["volume"].iloc[-1]),
        hacim_yuzdelik=_yuzdelik(tam["volume"], HACIM_PENCERE),
        donus_seviyeleri=_donus_seviyeleri(tam, SWING_GUN),
    )


def _tr(t: datetime) -> str:
    return t.astimezone(TR).strftime("%Y-%m-%d %H:%M TR")


def takvim_olgusu() -> tuple[list[MacroEvent], list[MacroEvent]]:
    bugun = date.today()
    hafta_sonu = bugun + timedelta(days=7)
    hepsi = all_events()
    bugunku = [e for e in hepsi if e.gun == bugun]
    haftaki = [e for e in hepsi if bugun < e.gun <= hafta_sonu]
    return bugunku, haftaki


def seans_olgusu(simdi_utc: datetime) -> list[tuple[str, bool, float]]:
    saat = simdi_utc.hour + simdi_utc.minute / 60
    sonuc = []
    for ad, bas, bit in SEANSLAR:
        acik = (bas <= saat < bit) if bas <= bit else (saat >= bas or saat < bit)
        kalan = ((bit - saat) % 24) if acik else ((bas - saat) % 24)
        sonuc.append((ad, acik, kalan))
    return sonuc


def yazdir(semboller: list[tuple[str, str]], tazele: bool) -> None:
    simdi_utc = datetime.now(UTC)
    print("=" * 78)
    print(f"  DISKRESYONER SEANS BRIFINGI -- {_tr(simdi_utc)}  (olgu, yorum yok)")
    print("=" * 78)

    print("\n[TAKVIM]")
    bugunku, haftaki = takvim_olgusu()
    if bugunku:
        for e in bugunku:
            erken = "  <-- ERKEN ACIKLAMA, standart saatten farkli" if e.erken_aciklama else ""
            print(f"  BUGUN  {e.tip:6} duyuru {e.aciklama_et.strftime('%H:%M')} ET{erken}")
    else:
        print("  Bugun FOMC/CPI/NFP yok.")
    if haftaki:
        print("  Bu hafta (bugun haric):")
        for e in haftaki[:6]:
            print(f"    {e.gun}  {e.tip}")
    else:
        print("  Onumuzdeki 7 gunde FOMC/CPI/NFP yok.")

    print("\n[SEANS]")
    for ad, acik, kalan in seans_olgusu(simdi_utc):
        print(f"  {ad:10} {'ACIK ' if acik else 'kapali'}  "
              f"{'kapanisa' if acik else 'acilisa'} {kalan:.1f} saat")

    for sembol, tf in semboller:
        print(f"\n[{sembol} {tf}]")
        try:
            o = sembol_olgusu(sembol, tf, tazele)
        except Exception as e:
            print(f"  VERI YOK: {type(e).__name__}: {e}")
            continue
        print(f"  son kapanis        : {o.son_kapanis:.5g}  (bar: {o.son_bar_utc} UTC)")
        print(f"  dun araligi        : {o.dun_dusuk:.5g} -> {o.dun_yuksek:.5g}")
        if o.bugun_dusuk == o.bugun_dusuk:  # NaN degil
            print(f"  bugun araligi      : {o.bugun_dusuk:.5g} -> {o.bugun_yuksek:.5g}")
        else:
            print("  bugun araligi      : henuz bar yok (cache guncel degil, --tazele dene)")
        print(f"  200EMA (gunluk)    : {o.ema200:.5g}  (uzaklik {o.ema200_uzaklik_puan:+.5g} "
              f"/ %{o.ema200_uzaklik_yuzde:+.2f})")
        print(f"  ATR(14) son kapali : {o.atr_bugun:.5g}  ({ATR_PENCERE} gunun "
              f"%{o.atr_yuzdelik:.0f}. yuzdeligi)")
        print(f"  hacim (son kapali) : {o.hacim_bugun:,.0f}  ({HACIM_PENCERE} gunun "
              f"%{o.hacim_yuzdelik:.0f}. yuzdeligi)")
        print(f"  donus seviyeleri (son {SWING_GUN} gun):")
        if o.donus_seviyeleri:
            for tarih, fiyat, tip in o.donus_seviyeleri:
                print(f"    {tarih}  {fiyat:.5g}  ({tip})")
        else:
            print("    yeterli veri yok")

    print("\n" + "=" * 78)
    print("  Yorum yok. Katman kapisi (>=3/4) icin: intraday/forward_ea/diskresyoner.py")
    print("=" * 78)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="Diskresyoner seans brifingi")
    p.add_argument("--semboller", nargs="+", default=None,
                    help="ornek: NASDAQ100 XAUUSD (varsayilan tf'leri kullanir)")
    p.add_argument("--tazele", action="store_true",
                    help="calistirmadan once bu yilin barlarini dukascopy'den guncelle")
    a = p.parse_args()

    if a.semboller:
        varsayilan_tf = dict(VARSAYILAN_SEMBOLLER)
        semboller = [(s, varsayilan_tf.get(s, "5m")) for s in a.semboller]
    else:
        semboller = VARSAYILAN_SEMBOLLER

    yazdir(semboller, a.tazele)


if __name__ == "__main__":
    main()
