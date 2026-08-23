"""Makro olay takvimi -- `macro_day_drift_nq` hipotezinin olay kaynagi.

NEDEN AYRI DOSYA: olay tarihleri sinyalin girdisi, stratejinin parcasi degil.
Ayri tutulunca (a) kaynak denetlenebilir, (b) tarih listesi degisirse strateji
kodu degismez, (c) ayni takvim baska hipotezlerde de kullanilabilir.

LOOK-AHEAD YOK: FOMC takvimi toplantidan aylar once ilan edilir, CPI/NFP
takvimi BLS tarafindan bir yil onceden yayinlanir. Yani bu tarihler islem
gununde ONCEDEN bilinebilir bilgidir.

KAYNAK (hepsi resmi, ucretsiz, 2026-08-24'te cekildi):
    federalreserve.gov/monetarypolicy/fomchistorical{yil}.htm   (2012-2020)
    federalreserve.gov/monetarypolicy/fomccalendars.htm         (2021-2026)

DUYURU SAATI -- DIKKAT, GECMISTE DEGISTI:
    2013-03-13 duyurusuyla (monetary20130313a.htm) TUM duzenli toplantilarin
    karar metni 14:00 ET'ye sabitlendi. ONCESINDE ikili bir duzen vardi:
      - basin toplantili toplantilar: metin ~12:30 ET (2012-01-25'te 12:20)
      - basin toplantisiz toplantilar: metin 14:15 ET
    Bu, "duyurudan 5dk once cik" kuralini 2012 ve 2013 baslarinda KIRAR:
    13:55 ET cikis, 12:30'da aciklanmis bir karardan SONRA olur -- yani
    pozisyon duyuruyu tasimis olur. Bu tarihler `erken_aciklama` olarak
    isaretli; strateji kodu bunlari ya dislamali ya da kendi saatini
    kullanmali. Sessizce 14:00 varsaymak look-ahead degil ama MEKANIZMA
    ihlalidir (fat-tail'e bilerek girmemek ana varsayimdi).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, time
from pathlib import Path

# ----------------------------------------------------------------------------
# FOMC -- duzenli toplantilar. Tarih = KARARIN aciklandigi gun (son gun).
# Plansiz konferans gorusmeleri (2013-10-16, 2014-03-04, 2019-10-04,
# 2020-03-02, 2020-03-15) DISARIDA: onceden ilan edilmemislerdi, yani
# islem gununde bilinemezlerdi -> look-ahead olurdu.
# ----------------------------------------------------------------------------

_FOMC_14_00 = [  # 14:00 ET rejimi (2013-03-13 duyurusundan itibaren)
    # 2013
    "2013-03-20", "2013-05-01", "2013-06-19", "2013-07-31", "2013-09-18",
    "2013-10-30", "2013-12-18",
    # 2014
    "2014-01-29", "2014-03-19", "2014-04-30", "2014-06-18", "2014-07-30",
    "2014-09-17", "2014-10-29", "2014-12-17",
    # 2015
    "2015-01-28", "2015-03-18", "2015-04-29", "2015-06-17", "2015-07-29",
    "2015-09-17", "2015-10-28", "2015-12-16",
    # 2016
    "2016-01-27", "2016-03-16", "2016-04-27", "2016-06-15", "2016-07-27",
    "2016-09-21", "2016-11-02", "2016-12-14",
    # 2017
    "2017-02-01", "2017-03-15", "2017-05-03", "2017-06-14", "2017-07-26",
    "2017-09-20", "2017-11-01", "2017-12-13",
    # 2018
    "2018-01-31", "2018-03-21", "2018-05-02", "2018-06-13", "2018-08-01",
    "2018-09-26", "2018-11-08", "2018-12-19",
    # 2019
    "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19", "2019-07-31",
    "2019-09-18", "2019-10-30", "2019-12-11",
    # 2020 (plansiz mart toplantilari haric)
    "2020-01-29", "2020-04-29", "2020-06-10", "2020-07-29", "2020-09-16",
    "2020-11-05", "2020-12-16",
    # 2021
    "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28",
    "2021-09-22", "2021-11-03", "2021-12-15",
    # 2022
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27",
    "2022-09-21", "2022-11-02", "2022-12-14",
    # 2023
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26",
    "2023-09-20", "2023-11-01", "2023-12-13",
    # 2024
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31",
    "2024-09-18", "2024-11-07", "2024-12-18",
    # 2025
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30",
    "2025-09-17", "2025-10-29", "2025-12-10",
    # 2026
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29",
    # 2026-09-16, 2026-10-28, 2026-12-09 -- veri sonrasi, listede tutuluyor
    "2026-09-16", "2026-10-28", "2026-12-09",
]

# ESKI REJIM: basin toplantili toplantilar, metin ~12:30 ET.
# 2012'de basin toplantisi Ocak/Nisan/Haziran/Eylul ve Aralik'ta yapildi.
_FOMC_12_30 = [
    "2012-01-25", "2012-04-25", "2012-06-20", "2012-09-13", "2012-12-12",
]

# ESKI REJIM: basin toplantisiz toplantilar, metin 14:15 ET.
_FOMC_14_15 = [
    "2012-03-13", "2012-08-01", "2012-10-24",
    "2013-01-30",
]


@dataclass(frozen=True)
class MacroEvent:
    gun: date
    tip: str          # "FOMC" | "CPI" | "NFP"
    aciklama_et: time  # duyurunun ET saati
    erken_aciklama: bool = False  # True -> 14:00 varsayimi bu gun GECERSIZ


def _mk(gunler: list[str], tip: str, saat: time, erken: bool = False):
    return [MacroEvent(date.fromisoformat(g), tip, saat, erken) for g in gunler]


def fomc_events() -> list[MacroEvent]:
    """Duzenli FOMC karar gunleri, gercek duyuru saatiyle."""
    olaylar = (
        _mk(_FOMC_14_00, "FOMC", time(14, 0))
        + _mk(_FOMC_12_30, "FOMC", time(12, 30), erken=True)
        + _mk(_FOMC_14_15, "FOMC", time(14, 15), erken=True)
    )
    return sorted(olaylar, key=lambda e: e.gun)


_BLS_ONBELLEK = Path(__file__).resolve().parent / "event_dates_bls.json"
BLS_SAAT = time(8, 30)  # CPI ve Employment Situation ikisi de 08:30 ET


def _bls_yukle() -> dict:
    if not _BLS_ONBELLEK.exists():
        raise FileNotFoundError(
            f"{_BLS_ONBELLEK} yok. Once `python -m intraday.event_calendar_fetch` "
            "calistir (FRED_API_KEY gerekir)."
        )
    return json.loads(_BLS_ONBELLEK.read_text(encoding="utf-8"))


def cpi_events() -> list[MacroEvent]:
    """CPI yayin gunleri (FRED onbellegi, revizyonlar elenmis)."""
    return _mk(_bls_yukle()["CPI"], "CPI", BLS_SAAT)


def nfp_events() -> list[MacroEvent]:
    """NFP (Employment Situation) yayin gunleri (FRED onbellegi)."""
    return _mk(_bls_yukle()["NFP"], "NFP", BLS_SAAT)


def all_events() -> list[MacroEvent]:
    """Tum makro olaylar, tarihe gore sirali.

    ON-KAYIT KURALI (hypotheses.json / macro_day_drift_nq): CPI ve NFP ayni
    gune duserse gun CPI sayilir, NFP islemi ATLANIR. Kural testte kilitli.
    """
    cpi_gunleri = {e.gun for e in cpi_events()}
    olaylar = fomc_events() + cpi_events() + [
        e for e in nfp_events() if e.gun not in cpi_gunleri
    ]
    return sorted(olaylar, key=lambda e: (e.gun, e.tip))


def main() -> None:
    olaylar = fomc_events()
    erken = [e for e in olaylar if e.erken_aciklama]
    print(f"FOMC duzenli karar gunu: {len(olaylar)} "
          f"({olaylar[0].gun} -> {olaylar[-1].gun})")
    print(f"  14:00 ET rejimi : {len(olaylar) - len(erken)}")
    print(f"  ERKEN aciklama  : {len(erken)}  <- 13:55 cikis kurali bu gunlerde KIRIK")
    for e in erken:
        print(f"    {e.gun}  {e.aciklama_et.strftime('%H:%M')} ET")

    try:
        hepsi = all_events()
    except FileNotFoundError as e:
        print(f"\nCPI/NFP: {e}")
        return
    from collections import Counter
    sayim = Counter(o.tip for o in hepsi)
    print(f"\nTum olaylar: {len(hepsi)}  ({hepsi[0].gun} -> {hepsi[-1].gun})")
    for tip, n in sorted(sayim.items()):
        print(f"  {tip:5} {n}")
    cakisma = len(cpi_events()) + len(nfp_events()) + len(fomc_events()) - len(hepsi)
    print(f"  (CPI ile ayni gune dusup atlanan NFP: {cakisma})")


if __name__ == "__main__":
    main()
