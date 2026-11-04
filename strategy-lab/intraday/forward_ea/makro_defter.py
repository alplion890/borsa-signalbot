"""On-kayitli makro baglam defteri.

Makro yorum mekanik edge degildir. Bu defter beklenti, gerceklesen veri,
piyasa tepkisi, tez ve curuteni olay aninda dondurur; boylece birkac gun sonra
sonuca bakarak hikaye yazmak yerine ileriye donuk olarak olculebilir.
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
DEFTER = (Path(__file__).resolve().parent.parent.parent
          / "outputs" / "intraday" / "forward_ea" / "makro_defter.csv")

KOLONLAR = [
    "id", "durum", "kayit_utc", "olay_utc", "gecerli_utc", "olay",
    "beklenti", "onceki", "gerceklesen", "revizyon", "surpriz_notu",
    "tepki_utc", "tepki_notu", "tez", "curuten", "kapanis_notu",
]


@dataclass(frozen=True)
class MakroKayit:
    id: int
    durum: str
    kayit_utc: str
    olay_utc: str
    gecerli_utc: str
    olay: str
    beklenti: str
    onceki: str
    gerceklesen: str
    revizyon: str
    surpriz_notu: str
    tepki_utc: str
    tepki_notu: str
    tez: str
    curuten: str
    kapanis_notu: str


def _utc(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat()


def _islem_gunu_ekle(baslangic: datetime, gun: int) -> datetime:
    """Hafta sonlarini saymadan gecerlilik sonunu bul.

    Resmi tatiller takvim katmaninda ayrica gorulur; bu defterin sessizce uc
    takvim gunune dusmemesi icin en azindan Cumartesi/Pazar atlanir.
    """
    sonuc = baslangic
    kalan = gun
    while kalan:
        sonuc += timedelta(days=1)
        if sonuc.weekday() < 5:
            kalan -= 1
    return sonuc


def yukle(path: Path | None = None) -> list[MakroKayit]:
    hedef = Path(path) if path is not None else DEFTER
    if not hedef.exists():
        return []
    with hedef.open(encoding="utf-8", newline="") as fh:
        return [MakroKayit(**{k: row.get(k, "") for k in KOLONLAR})
                for row in csv.DictReader(fh)]


def _yaz(kayitlar: list[MakroKayit], path: Path | None = None) -> None:
    hedef = Path(path) if path is not None else DEFTER
    hedef.parent.mkdir(parents=True, exist_ok=True)
    with hedef.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=KOLONLAR)
        writer.writeheader()
        for kayit in kayitlar:
            writer.writerow(asdict(kayit))


def on_kayit(olay: str, olay_zamani: str, beklenti: str, onceki: str,
             tez: str, curuten: str, *, gecerli_gun: int = 3,
             path: Path | None = None, simdi: str | None = None) -> MakroKayit:
    if len(tez.strip()) < 20 or len(curuten.strip()) < 15:
        raise ValueError("tez en az 20, curuten en az 15 karakter olmali")
    if gecerli_gun < 1 or gecerli_gun > 5:
        raise ValueError("gecerli_gun 1-5 arasinda olmali")
    kayitlar = yukle(path)
    kayit_ani = _utc(simdi)
    olay_ani = _utc(olay_zamani)
    yeni = MakroKayit(
        id=max((int(k.id) for k in kayitlar), default=0) + 1,
        durum="bekliyor", kayit_utc=_iso(kayit_ani), olay_utc=_iso(olay_ani),
        gecerli_utc=_iso(_islem_gunu_ekle(olay_ani, gecerli_gun)),
        olay=olay.strip(), beklenti=beklenti.strip(), onceki=onceki.strip(),
        gerceklesen="", revizyon="", surpriz_notu="", tepki_utc="",
        tepki_notu="", tez=tez.strip(), curuten=curuten.strip(),
        kapanis_notu="",
    )
    _yaz([*kayitlar, yeni], path)
    return yeni


def _guncelle(kid: int, degisim: dict[str, str],
              path: Path | None = None) -> MakroKayit:
    kayitlar = yukle(path)
    indeks = next((i for i, k in enumerate(kayitlar) if int(k.id) == kid), None)
    if indeks is None:
        raise ValueError(f"makro kayit bulunamadi: {kid}")
    kayitlar[indeks] = replace(kayitlar[indeks], **degisim)
    _yaz(kayitlar, path)
    return kayitlar[indeks]


def sonuc(kid: int, gerceklesen: str, *, revizyon: str = "",
          surpriz_notu: str = "", path: Path | None = None) -> MakroKayit:
    return _guncelle(kid, {
        "durum": "aktif", "gerceklesen": gerceklesen.strip(),
        "revizyon": revizyon.strip(), "surpriz_notu": surpriz_notu.strip(),
    }, path)


def tepki(kid: int, tepki_notu: str, *, path: Path | None = None,
          simdi: str | None = None) -> MakroKayit:
    if len(tepki_notu.strip()) < 15:
        raise ValueError("tepki_notu en az 15 karakter olmali")
    return _guncelle(kid, {
        "durum": "aktif", "tepki_utc": _iso(_utc(simdi)),
        "tepki_notu": tepki_notu.strip(),
    }, path)


def kapat(kid: int, not_: str, *, path: Path | None = None) -> MakroKayit:
    return _guncelle(kid, {"durum": "kapali", "kapanis_notu": not_.strip()}, path)


def aktif(simdi: datetime | None = None,
          path: Path | None = None) -> MakroKayit | None:
    now = (simdi or datetime.now(UTC)).astimezone(UTC)
    adaylar = [k for k in yukle(path)
               if k.durum in {"bekliyor", "aktif"} and _utc(k.gecerli_utc) >= now]
    return adaylar[-1] if adaylar else None


def telegram_ozeti(simdi: datetime | None = None,
                   path: Path | None = None) -> str:
    kayit = aktif(simdi, path)
    if kayit is None:
        return "Makro tez: aktif on-kayit yok; mobil projede guncel veriyi dogrula"
    asama = "sonuc bekleniyor" if kayit.durum == "bekliyor" else "aktif"
    sonuc_metni = f"; gerceklesen {kayit.gerceklesen}" if kayit.gerceklesen else ""
    return (
        f"Makro tez #{kayit.id}: {kayit.olay} ({asama}){sonuc_metni}; "
        f"gecerli {kayit.gecerli_utc[:10]}'e kadar; LIVE filtresi degil"
    )


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="On-kayitli makro baglam defteri")
    p.add_argument("--durum", action="store_true")
    p.add_argument("--on-kayit", action="store_true")
    p.add_argument("--sonuc", type=int, metavar="ID")
    p.add_argument("--tepki", type=int, metavar="ID")
    p.add_argument("--kapat", type=int, metavar="ID")
    p.add_argument("--olay")
    p.add_argument("--olay-zamani", help="ISO/UTC; ornek 2026-09-16T18:00:00Z")
    p.add_argument("--beklenti", default="")
    p.add_argument("--onceki", default="")
    p.add_argument("--gerceklesen")
    p.add_argument("--revizyon", default="")
    p.add_argument("--surpriz-notu", default="")
    p.add_argument("--tepki-notu")
    p.add_argument("--tez")
    p.add_argument("--curuten")
    p.add_argument("--not", dest="not_")
    p.add_argument("--gecerli-gun", type=int, default=3)
    a = p.parse_args()

    if a.on_kayit:
        eksik = [ad for ad in ("olay", "olay_zamani", "tez", "curuten")
                 if getattr(a, ad) is None]
        if eksik:
            p.error("zorunlu: " + ", ".join("--" + x.replace("_", "-") for x in eksik))
        k = on_kayit(a.olay, a.olay_zamani, a.beklenti, a.onceki,
                     a.tez, a.curuten, gecerli_gun=a.gecerli_gun)
        print(f"MAKRO ON-KAYIT: id={k.id} {k.olay}; gecerli={k.gecerli_utc}")
        return
    if a.sonuc is not None:
        if a.gerceklesen is None:
            p.error("--sonuc icin --gerceklesen gerekli")
        k = sonuc(a.sonuc, a.gerceklesen, revizyon=a.revizyon,
                  surpriz_notu=a.surpriz_notu)
        print(f"MAKRO SONUC: id={k.id} gerceklesen={k.gerceklesen}")
        return
    if a.tepki is not None:
        if a.tepki_notu is None:
            p.error("--tepki icin --tepki-notu gerekli")
        k = tepki(a.tepki, a.tepki_notu)
        print(f"MAKRO TEPKI: id={k.id} {k.tepki_notu}")
        return
    if a.kapat is not None:
        if a.not_ is None:
            p.error("--kapat icin --not gerekli")
        k = kapat(a.kapat, a.not_)
        print(f"MAKRO KAPANDI: id={k.id} {k.kapanis_notu}")
        return
    if a.durum:
        print(telegram_ozeti())
        for k in yukle()[-5:]:
            print(f"  #{k.id} {k.durum}: {k.olay} | tez={k.tez}")
        return
    p.print_help()


if __name__ == "__main__":
    main()
