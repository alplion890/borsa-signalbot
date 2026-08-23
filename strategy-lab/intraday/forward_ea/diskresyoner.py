"""Diskresyoner (elle yorumlu) islem defteri -- mekanik defterden AYRI.

NEDEN AYRI DOSYA: mekanik moduller ile elle acilan islemler ayni deftere
girerse ikisi de olculemez hale gelir. Modulun exp_R'si insan kararlariyla
kirlenir, insan karari da modul sinyalleriyle. AI scout 2026-08-01'de tam bu
gerekceyle kapatilmisti ("olculmemis bir sinyal kaynagi eklemek olcumu
zorlastirir"). Ayri defter o gerekceyi ihlal etmeden diskresyoner denemeye
izin verir.

NEDEN "TEZ" VE "CURUTEN" ALANLARI ZORUNLU:
Diskresyoner islem backtest edilemez. Geriye kalan tek dogrulama bicimi
ON-KAYITLI islem gunlugu: girmeden ONCE tezi yazmak. "Curuten" alani
(bu tezi ne yanlislar) daha da onemli -- onsuz her sonuc sonradan
aciklanabilir hale gelir ve defter hicbir sey ogretmez.

Bu projede ayni hata uc kez oldu: sonuca bakip kural secmek. Burada sonuca
bakip GEREKCE secmeyi engelleyen sey bu iki alan.

DURMA KURALI (2026-08-23, ilk islemden ONCE taahhut edildi):
    n >= 20 ve exp_R < 0 ise defter DURUR.
    Kural kodda: `signalbot/test_diskresyoner_tripwire.py`.

Hesap: Maven demo hesabi (mekanik forward ile ayni hesap, AYRI defter).

Calistir:
    python -m intraday.forward_ea.diskresyoner --durum
    python -m intraday.forward_ea.diskresyoner --ac \
        --sembol US100 --yon short --giris 25000 --stop 25120 \
        --tez "makro haber negatif, fiyat 200EMA ustunde pahali bolgede" \
        --curuten "200EMA uzerinde gunluk kapanis olursa tez yanlis"
    python -m intraday.forward_ea.diskresyoner --kapat 3 --cikis 24800
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFTER = (Path(__file__).resolve().parent.parent.parent
          / "outputs" / "intraday" / "forward_ea" / "diskresyoner_defter.csv")

MIN_N = 20          # durma kurali esigi -- tripwire testi ile ayni
MIN_TEZ = 20        # karakter; "iyi gorunuyor" tez degildir
MIN_CURUTEN = 15

KOLONLAR = [
    "id", "acilis_utc", "kapanis_utc", "sembol", "yon",
    "giris", "stop", "hedef", "cikis", "r",
    "tez", "curuten", "sonuc_notu",
]


@dataclass(frozen=True)
class Islem:
    id: int
    acilis_utc: str
    kapanis_utc: str
    sembol: str
    yon: str
    giris: float
    stop: float
    hedef: float | None
    cikis: float | None
    r: float | None
    tez: str
    curuten: str
    sonuc_notu: str

    @property
    def acik(self) -> bool:
        return not self.kapanis_utc


def _satir_to_islem(s: dict) -> Islem:
    def f(x):
        return float(x) if x not in ("", None) else None
    return Islem(
        id=int(s["id"]), acilis_utc=s["acilis_utc"], kapanis_utc=s["kapanis_utc"],
        sembol=s["sembol"], yon=s["yon"], giris=float(s["giris"]),
        stop=float(s["stop"]), hedef=f(s["hedef"]), cikis=f(s["cikis"]),
        r=f(s["r"]), tez=s["tez"], curuten=s["curuten"],
        sonuc_notu=s.get("sonuc_notu", ""),
    )


def yukle(path: Path | None = None) -> list[Islem]:
    p = Path(path) if path is not None else DEFTER
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        return [_satir_to_islem(s) for s in csv.DictReader(fh)]


def _yaz(islemler: list[Islem], path: Path | None = None) -> None:
    p = Path(path) if path is not None else DEFTER
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=KOLONLAR)
        w.writeheader()
        for i in islemler:
            w.writerow({
                "id": i.id, "acilis_utc": i.acilis_utc, "kapanis_utc": i.kapanis_utc,
                "sembol": i.sembol, "yon": i.yon, "giris": i.giris, "stop": i.stop,
                "hedef": "" if i.hedef is None else i.hedef,
                "cikis": "" if i.cikis is None else i.cikis,
                "r": "" if i.r is None else round(i.r, 4),
                "tez": i.tez, "curuten": i.curuten, "sonuc_notu": i.sonuc_notu,
            })


def ac(sembol: str, yon: str, giris: float, stop: float, tez: str, curuten: str,
       hedef: float | None = None, path: Path | None = None,
       simdi: str | None = None) -> Islem:
    """Yeni diskresyoner islem ac. Tez ve curuten ZORUNLU."""
    yon = yon.lower()
    if yon not in ("long", "short"):
        raise ValueError(f"yon 'long' veya 'short' olmali, verilen: {yon!r}")
    if len(tez.strip()) < MIN_TEZ:
        raise ValueError(
            f"tez en az {MIN_TEZ} karakter olmali. Girmeden once NEDEN girdigini "
            "yazmak bu defterin tek dogrulama mekanizmasi."
        )
    if len(curuten.strip()) < MIN_CURUTEN:
        raise ValueError(
            f"'curuten' en az {MIN_CURUTEN} karakter olmali. Tezi NE yanlislar? "
            "Bu alan olmadan her sonuc sonradan aciklanabilir ve defter "
            "hicbir sey ogretmez."
        )
    if yon == "long" and stop >= giris:
        raise ValueError("long islemde stop giristen kucuk olmali")
    if yon == "short" and stop <= giris:
        raise ValueError("short islemde stop giristen buyuk olmali")

    islemler = yukle(path)
    if any(i.acik for i in islemler):
        acik = next(i for i in islemler if i.acik)
        raise ValueError(
            f"Zaten acik islem var (id={acik.id}, {acik.sembol}). Maven slot "
            "kisiti: ayni anda tek islem. Once onu kapat."
        )
    yeni = Islem(
        id=max((i.id for i in islemler), default=0) + 1,
        acilis_utc=simdi or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        kapanis_utc="", sembol=sembol, yon=yon, giris=giris, stop=stop,
        hedef=hedef, cikis=None, r=None, tez=tez.strip(),
        curuten=curuten.strip(), sonuc_notu="",
    )
    _yaz(islemler + [yeni], path)
    return yeni


def kapat(islem_id: int, cikis: float, not_: str = "",
          path: Path | None = None, simdi: str | None = None) -> Islem:
    """Islemi kapat, R'yi stop mesafesine gore hesapla."""
    islemler = yukle(path)
    idx = next((k for k, i in enumerate(islemler) if i.id == islem_id), None)
    if idx is None:
        raise ValueError(f"id={islem_id} bulunamadi")
    i = islemler[idx]
    if not i.acik:
        raise ValueError(f"id={islem_id} zaten kapali")

    risk = abs(i.giris - i.stop)
    if risk <= 0:
        raise ValueError("risk mesafesi sifir")
    hareket = (cikis - i.giris) if i.yon == "long" else (i.giris - cikis)
    kapali = Islem(
        id=i.id, acilis_utc=i.acilis_utc,
        kapanis_utc=simdi or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        sembol=i.sembol, yon=i.yon, giris=i.giris, stop=i.stop, hedef=i.hedef,
        cikis=cikis, r=hareket / risk, tez=i.tez, curuten=i.curuten,
        sonuc_notu=not_,
    )
    islemler[idx] = kapali
    _yaz(islemler, path)
    return kapali


def ozet(path: Path | None = None) -> dict:
    kapali = [i for i in yukle(path) if not i.acik and i.r is not None]
    n = len(kapali)
    if not n:
        return {"n": 0, "exp_R": float("nan"), "toplam_R": 0.0,
                "kazanan": 0, "wr": float("nan"), "durma_tetik": False}
    rlar = [i.r for i in kapali]
    exp_r = sum(rlar) / n
    kazanan = sum(1 for r in rlar if r > 0)
    return {"n": n, "exp_R": exp_r, "toplam_R": sum(rlar), "kazanan": kazanan,
            "wr": 100 * kazanan / n, "durma_tetik": n >= MIN_N and exp_r < 0}


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="Diskresyoner islem defteri")
    p.add_argument("--durum", action="store_true")
    p.add_argument("--ac", action="store_true")
    p.add_argument("--kapat", type=int, metavar="ID")
    p.add_argument("--sembol"); p.add_argument("--yon")
    p.add_argument("--giris", type=float); p.add_argument("--stop", type=float)
    p.add_argument("--hedef", type=float); p.add_argument("--cikis", type=float)
    p.add_argument("--tez"); p.add_argument("--curuten"); p.add_argument("--not", dest="not_")
    a = p.parse_args()

    if a.ac:
        eksik = [k for k in ("sembol", "yon", "giris", "stop", "tez", "curuten")
                 if getattr(a, k) is None]
        if eksik:
            p.error("--ac icin zorunlu: " + ", ".join("--" + k for k in eksik))
        i = ac(a.sembol, a.yon, a.giris, a.stop, a.tez, a.curuten, a.hedef)
        print(f"Acildi: id={i.id} {i.sembol} {i.yon} giris={i.giris} stop={i.stop}")
        print(f"  tez     : {i.tez}")
        print(f"  curuten : {i.curuten}")
        return

    if a.kapat is not None:
        if a.cikis is None:
            p.error("--kapat icin --cikis gerekli")
        i = kapat(a.kapat, a.cikis, a.not_ or "")
        print(f"Kapandi: id={i.id} cikis={i.cikis} R={i.r:+.3f}")

    o = ozet()
    print(f"\nDISKRESYONER DEFTER  (durma kurali: n>={MIN_N} ve exp_R<0)")
    if not o["n"]:
        print("  Henuz kapanmis islem yok.")
    else:
        print(f"  n={o['n']}  exp_R={o['exp_R']:+.3f}  toplam={o['toplam_R']:+.2f}R  "
              f"WR=%{o['wr']:.1f}")
        kalan = max(0, MIN_N - o["n"])
        print(f"  Esige {kalan} islem kaldi." if kalan else
              ("  ESIK ASILDI -- DURMA TETIKLENDI" if o["durma_tetik"]
               else "  Esik asildi, exp_R>=0, devam."))
    for i in yukle():
        if i.acik:
            print(f"  ACIK: id={i.id} {i.sembol} {i.yon} giris={i.giris} stop={i.stop}")


if __name__ == "__main__":
    main()
