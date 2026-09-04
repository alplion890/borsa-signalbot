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

NEDEN ADAY KAYDI (durum='aday') -- Hermes denetimi 2026-08-24:
Sadece ACILAN islemleri kaydetmek SECICILIGI olculemez birakir. "Bakip
gectiklerim" yazilmazsa, 20 islem sonunda "iyi setup seciyor muyum" sorusu
cevapsiz kalir. Aday once yazilir; tetiklenirse islem olur, tetiklenmezse
'pas' olur. Secicilik = pas / (pas + alinan).

KATMAN KAPISI (>=3/4, protokolde taahhut edildi):
narrative / hacim / trend / destek. Uc tanesi dolmadan setup aranmaz.
Kural KODDA zorlanir -- hatirlanmasi gereken kural, hatirlanmayan kuraldir.

DURMA KURALI (2026-08-23, ilk islemden ONCE taahhut edildi):
    n >= 20 ve exp_R < 0 ise defter DURUR.
    Kural kodda: `signalbot/test_diskresyoner_tripwire.py`.

Hesap: Maven demo hesabi (mekanik forward ile ayni hesap, AYRI defter).

Calistir:
    python -m intraday.forward_ea.diskresyoner --durum
    python -m intraday.forward_ea.diskresyoner --aday \
        --sembol US100 --yon short --tetik 25000 --stop 25120 \
        --katmanlar narrative,hacim,trend --narrative ai_dalgasi_soguma --tf 1H \
        --tez "makro haber negatif, fiyat 200EMA ustunde pahali bolgede" \
        --curuten "200EMA uzerinde gunluk kapanis olursa tez yanlis"
    python -m intraday.forward_ea.diskresyoner --tetikle 1 --giris 25010
    python -m intraday.forward_ea.diskresyoner --pas 1 --sebep "tetige hic gelmedi"
    python -m intraday.forward_ea.diskresyoner --kapat 1 --cikis 24800
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

DEFTER = (Path(__file__).resolve().parent.parent.parent
          / "outputs" / "intraday" / "forward_ea" / "diskresyoner_defter.csv")

MIN_N = 20          # durma kurali esigi -- tripwire testi ile ayni
MIN_TEZ = 20        # karakter; "iyi gorunuyor" tez degildir
MIN_CURUTEN = 15
KATMANLAR = ("narrative", "hacim", "trend", "destek")
# 2026-09-03, kullanici karari: 3/4 -> 2/4. Bu bir GIRIS FILTRESI degisikligidir,
# kayit kurali degil (Hermes denetimi 2026-09-03: ikisini birbirine karistirmak
# yanlisti -- kod ucuncu katman yoksa setup'i REDDEDIYORDU, yani veto).
# Katmanlar deftere yazilmaya devam eder; 20 islem sonunda "2 katmanli girisler
# 4 katmanlilardan kotu muydu" sorusu olculebilir kalir.
MIN_KATMAN = 2

# Trend tablosu 21 sembollük GÖZLEM yüzeyidir; fırsat paydasını sessizce
# genişletmemesi için diskresyoner aday/işlem evreni ayrı ve fail-closed.
# US100, NASDAQ100'ün Maven broker adıdır; yeni bir enstrüman değildir.
ISLEM_EVRENI = ("NASDAQ100", "US100", "XAUUSD", "EURUSD", "GBPUSD")

DURUMLAR = ("aday", "acik", "kapali", "pas")

# --- RISK POLITIKASI (2026-09-03, kullanici karari) --------------------
#
# Diskresyoner ray MEKANIK raydan AYRI risk tasir. `signalbot/risk.py`
# degistirilmedi: mekanik ray dondurulmus ve challenge cap'i orada %3.
# Karisik tutmak, bir rayin karari otekinin lot buyuklugunu degistirmek
# demek olurdu.
#
# TABAN: her islemde GUNCEL bakiyenin yuzdesi (sabit dolar degil). Boylece
# kaybettikce risk kuculur. `risk.py` de ayni mantikta calisiyor.
#
# 2026-09-04: %6 -> %3'e indirildi. Bootstrap (defterin kendi R dagilimi,
# n=65-66, exp_R -0.015, 20.000 yol): %6 gecme %50/patlama %50/medyan 1 islem;
# %3 gecme %57/patlama %43/medyan 3 islem. Kullanici karari: "en az ama en
# yuksek riskli" -- olculu uc tier'dan (1.5/3/6) ortanca, hala agresif ama
# solvency kapisinin haftalik 5 islem hedefini 1 islemde bogmamasi icin.
# Bkz [[Borsa - Risk Politikasi AB]] (mekanik rayin AYRI %3 A/B'si, karistirma).
RISK_PCT = 0.03

# Maven challenge: 5000 baslangic, 4500 breach. Tampon 500 dolar.
BREACH_BAKIYE = 4500.0
# %3 = ~150 dolar. Tampon 500 dolar = 3.33R. Guvenlik payi: tamponun tamami
# kumar edilmesin.
GUVENLIK_TAMPONU = 100.0


def risk_dolar(bakiye: float, risk_pct: float = RISK_PCT) -> float:
    """Guncel bakiyeye gore planlanan dolar riski."""
    return round(bakiye * risk_pct, 2)


def solvency_kapisi(bakiye: float, risk_usd: float) -> None:
    """Planlanan stop kaybi, breach'e kalan tamponu ASAMAZ.

    NEDEN POST-HOC DEGIL (Hermes denetimi 2026-09-03): bu kural ilk %6'lik
    islemden ONCE yaziliyor. Post-hoc olan, kayiplari gordukten sonra esigi
    sonuca gore secmektir.

    Aritmetik: %6 ~ 300 dolar risk, breach'e tampon 500 dolar = 1.67R. Bir tam
    stop sonrasi ~200 dolar kalir; ayni yuzdeyle ikinci islem breach sinirini
    asar. Yani durma kurali (n>=20 ve exp_R<0) devreye girmeden hesap bitebilir
    -- o kural EDGE olcer, hayatta kalmayi garanti etmez.
    """
    tampon = bakiye - BREACH_BAKIYE - GUVENLIK_TAMPONU
    if tampon <= 0:
        raise ValueError(
            f"SOLVENCY: bakiye {bakiye:.2f}, breach {BREACH_BAKIYE:.0f}, "
            f"guvenlik payi {GUVENLIK_TAMPONU:.0f} -> kullanilabilir tampon yok. "
            "Yeni islem acilmaz.")
    if risk_usd > tampon:
        raise ValueError(
            f"SOLVENCY: planlanan risk {risk_usd:.2f} USD, kullanilabilir "
            f"tampon {tampon:.2f} USD. Riski dusur ya da islem acma. "
            f"(bakiye {bakiye:.2f}, breach {BREACH_BAKIYE:.0f}, "
            f"guvenlik payi {GUVENLIK_TAMPONU:.0f})")

KOLONLAR = [
    # `kayit_utc`: satirin fiilen YAZILDIGI an. `acilis_utc` islemin acildigi an.
    # Ikisi ayri (2026-09-03): kullanici telefondan islem acip kaydi sonra
    # veriyor. Yasaklamak yerine OLCUYORUZ -- gecikme buyudukce tez, aradaki
    # fiyat hareketinden etkilenmis olabilir. 20 islem sonunda "gecikmeli
    # kayitlar farkli mi" sorusu cevaplanabilir kalsin.
    "id", "durum", "aday_utc", "acilis_utc", "kayit_utc", "kapanis_utc",
    "sembol", "yon", "timeframe", "narrative", "katmanlar",
    "tetik", "giris", "stop", "hedef", "cikis", "r",
    # GERCEKLESEN RISK (2026-09-03): R tek basina yetmiyor -- ayni R farkli
    # bakiyede farkli dolar demek. Girisdeki bakiye, planlanan yuzde ve dolar
    # riski yazilmadan "%6 ile ne oldu" sorusu sonradan cevaplanamaz.
    "bakiye", "risk_pct", "risk_usd",
    "tez", "curuten", "pas_sebebi", "sonuc_notu",
]


@dataclass(frozen=True)
class Kayit:
    id: int
    durum: str
    aday_utc: str
    acilis_utc: str
    kayit_utc: str
    kapanis_utc: str
    sembol: str
    yon: str
    timeframe: str
    narrative: str
    katmanlar: str
    tetik: float | None
    giris: float | None
    stop: float
    hedef: float | None
    cikis: float | None
    r: float | None
    bakiye: float | None
    risk_pct: float | None
    risk_usd: float | None
    tez: str
    curuten: str
    pas_sebebi: str
    sonuc_notu: str

    @property
    def katman_sayisi(self) -> int:
        return len([k for k in self.katmanlar.split(",") if k.strip()])

    @property
    def kayit_gecikmesi_dk(self) -> float | None:
        """Islem acildiktan KAC DAKIKA sonra deftere yazildi.

        0 = on-kayit (kayit once, islem sonra). Buyuk deger = islem acikken
        yazilmis; tez aradaki fiyat hareketinden etkilenmis OLABILIR. Bu bir
        yasak degil, olculen bir alan.
        """
        if not self.acilis_utc or not self.kayit_utc:
            return None
        from datetime import datetime
        bicim = "%Y-%m-%d %H:%M:%S"
        try:
            acilis = datetime.strptime(self.acilis_utc[:19], bicim)
            kayit = datetime.strptime(self.kayit_utc[:19], bicim)
        except ValueError:
            return None
        return round((kayit - acilis).total_seconds() / 60, 1)


def _f(x):
    return float(x) if x not in ("", None) else None


def _satir_to_kayit(s: dict) -> Kayit:
    return Kayit(
        id=int(s["id"]), durum=s.get("durum", "acik"),
        aday_utc=s.get("aday_utc", ""), acilis_utc=s.get("acilis_utc", ""),
        kayit_utc=s.get("kayit_utc", ""), kapanis_utc=s.get("kapanis_utc", ""), sembol=s["sembol"], yon=s["yon"],
        timeframe=s.get("timeframe", ""), narrative=s.get("narrative", ""),
        katmanlar=s.get("katmanlar", ""), tetik=_f(s.get("tetik")),
        giris=_f(s.get("giris")), stop=float(s["stop"]), hedef=_f(s.get("hedef")),
        cikis=_f(s.get("cikis")), r=_f(s.get("r")),
        bakiye=_f(s.get("bakiye")), risk_pct=_f(s.get("risk_pct")),
        risk_usd=_f(s.get("risk_usd")), tez=s["tez"],
        curuten=s["curuten"], pas_sebebi=s.get("pas_sebebi", ""),
        sonuc_notu=s.get("sonuc_notu", ""),
    )


def yukle(path: Path | None = None) -> list[Kayit]:
    p = Path(path) if path is not None else DEFTER
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        return [_satir_to_kayit(s) for s in csv.DictReader(fh)]


def _yaz(kayitlar: list[Kayit], path: Path | None = None) -> None:
    p = Path(path) if path is not None else DEFTER
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=KOLONLAR)
        w.writeheader()
        for k in kayitlar:
            d = {c: getattr(k, c) for c in KOLONLAR}
            for sayisal in ("tetik", "giris", "hedef", "cikis", "r"):
                if d[sayisal] is None:
                    d[sayisal] = ""
            if d["r"] != "":
                d["r"] = round(float(d["r"]), 4)
            w.writerow(d)


def _simdi(x: str | None) -> str:
    return x or datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dogrula(yon: str, tez: str, curuten: str, katmanlar: str,
             stop: float, ref: float) -> tuple[str, str]:
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
    secilen = [k.strip() for k in katmanlar.split(",") if k.strip()]
    bilinmeyen = [k for k in secilen if k not in KATMANLAR]
    if bilinmeyen:
        raise ValueError(f"bilinmeyen katman: {bilinmeyen}. Gecerli: {list(KATMANLAR)}")
    if len(set(secilen)) < MIN_KATMAN:
        raise ValueError(
            f"katman kapisi: en az {MIN_KATMAN}/4 gerekli, verilen "
            f"{len(set(secilen))} ({secilen}). Protokol taahhudu -- kapi "
            "dolmadan setup aranmaz."
        )
    if yon == "long" and stop >= ref:
        raise ValueError("long islemde stop giris/tetikten kucuk olmali")
    if yon == "short" and stop <= ref:
        raise ValueError("short islemde stop giris/tetikten buyuk olmali")
    return yon, ",".join(dict.fromkeys(secilen))


def _dogrula_sembol(sembol: str) -> str:
    temiz = sembol.strip().upper()
    if temiz not in ISLEM_EVRENI:
        raise ValueError(
            f"{temiz!r} diskresyoner islem evreni disinda. Trend tablosu "
            "gozlem evrenidir; yeni sembol icin once yeni on-kayitli donem ac.")
    return temiz


def _yeni_id(kayitlar: list[Kayit]) -> int:
    return max((k.id for k in kayitlar), default=0) + 1


def _acik_kontrol(kayitlar: list[Kayit]) -> None:
    acik = next((k for k in kayitlar if k.durum == "acik"), None)
    if acik:
        raise ValueError(
            f"Zaten acik islem var (id={acik.id}, {acik.sembol}). Maven slot "
            "kisiti: ayni anda tek islem. Once onu kapat."
        )


def _risk_kapisi(bakiye: float | None, risk_pct: float) -> float | None:
    """Bakiye verildiyse riski hesapla ve solvency kapisindan gecir.

    Bakiye verilmediyse kayit yine yazilir (eski satirlarla uyum) ama gerceklesen
    risk alanlari bos kalir -- o zaman "%6 ile ne oldu" sorusu o satir icin
    cevaplanamaz. CLI bakiyeyi MT5'ten okuyup gecirir.
    """
    if bakiye is None:
        return None
    risk_usd = risk_dolar(bakiye, risk_pct)
    solvency_kapisi(bakiye, risk_usd)
    return risk_usd


def aday(sembol: str, yon: str, tetik: float, stop: float, tez: str, curuten: str,
         katmanlar: str, narrative: str = "", timeframe: str = "",
         hedef: float | None = None, path: Path | None = None,
         simdi: str | None = None, bakiye: float | None = None,
         risk_pct: float = RISK_PCT) -> Kayit:
    """Setup adayi kaydet -- HENUZ islem degil. Seciciligi olcmek icin."""
    sembol = _dogrula_sembol(sembol)
    yon, kat = _dogrula(yon, tez, curuten, katmanlar, stop, tetik)
    risk_usd = _risk_kapisi(bakiye, risk_pct)
    kayitlar = yukle(path)
    yeni = Kayit(
        id=_yeni_id(kayitlar), durum="aday", aday_utc=_simdi(simdi),
        acilis_utc="", kayit_utc=_simdi(simdi), kapanis_utc="", sembol=sembol, yon=yon,
        timeframe=timeframe, narrative=narrative, katmanlar=kat,
        tetik=tetik, giris=None, stop=stop, hedef=hedef, cikis=None, r=None,
        bakiye=bakiye, risk_pct=risk_pct if bakiye else None, risk_usd=risk_usd,
        tez=tez.strip(), curuten=curuten.strip(), pas_sebebi="", sonuc_notu="",
    )
    _yaz(kayitlar + [yeni], path)
    return yeni


def ac(sembol: str, yon: str, giris: float, stop: float, tez: str, curuten: str,
       katmanlar: str, narrative: str = "", timeframe: str = "",
       hedef: float | None = None, path: Path | None = None,
       simdi: str | None = None, bakiye: float | None = None,
       risk_pct: float = RISK_PCT, acilis: str | None = None) -> Kayit:
    """Dogrudan islem ac (aday asamasindan gecmeden).

    `acilis`: islemin GERCEKTEN acildigi an (telefondan acilip sonra
    kaydedildiyse gecmis bir zaman). Verilmezse kayit ani kullanilir.
    Kayit ani her halukarda ayri yazilir; ikisi arasindaki fark olculur.
    """
    sembol = _dogrula_sembol(sembol)
    yon, kat = _dogrula(yon, tez, curuten, katmanlar, stop, giris)
    risk_usd = _risk_kapisi(bakiye, risk_pct)
    kayitlar = yukle(path)
    _acik_kontrol(kayitlar)
    yeni = Kayit(
        id=_yeni_id(kayitlar), durum="acik", aday_utc="",
        acilis_utc=_simdi(acilis or simdi), kayit_utc=_simdi(simdi),
        kapanis_utc="", sembol=sembol, yon=yon, timeframe=timeframe,
        narrative=narrative, katmanlar=kat, tetik=None, giris=giris, stop=stop,
        hedef=hedef, cikis=None, r=None,
        bakiye=bakiye, risk_pct=risk_pct if bakiye else None, risk_usd=risk_usd,
        tez=tez.strip(), curuten=curuten.strip(),
        pas_sebebi="", sonuc_notu="",
    )
    _yaz(kayitlar + [yeni], path)
    return yeni


def _bul(kayitlar: list[Kayit], kid: int, beklenen: str) -> int:
    idx = next((i for i, k in enumerate(kayitlar) if k.id == kid), None)
    if idx is None:
        raise ValueError(f"id={kid} bulunamadi")
    if kayitlar[idx].durum != beklenen:
        raise ValueError(f"id={kid} durumu '{kayitlar[idx].durum}', "
                         f"'{beklenen}' bekleniyordu")
    return idx


def tetikle(kid: int, giris: float, path: Path | None = None,
            simdi: str | None = None, acilis: str | None = None) -> Kayit:
    """Aday tetiklendi -> acik islem.

    `acilis`: gercek tetiklenme ani (sonradan kaydediliyorsa gecmis zaman).
    """
    kayitlar = yukle(path)
    idx = _bul(kayitlar, kid, "aday")
    _acik_kontrol(kayitlar)
    k = kayitlar[idx]
    if k.yon == "long" and k.stop >= giris:
        raise ValueError("long islemde stop giristen kucuk olmali")
    if k.yon == "short" and k.stop <= giris:
        raise ValueError("short islemde stop giristen buyuk olmali")
    kayitlar[idx] = replace(k, durum="acik", giris=giris,
                            acilis_utc=_simdi(acilis or simdi),
                            kayit_utc=_simdi(simdi))
    _yaz(kayitlar, path)
    return kayitlar[idx]


def pas(kid: int, sebep: str, path: Path | None = None,
        simdi: str | None = None) -> Kayit:
    """Aday islem olmadi. Secicilik metrigi bu kayitlardan cikar."""
    if len(sebep.strip()) < 5:
        raise ValueError("pas sebebi yazilmali -- neden girmedigin de veridir")
    kayitlar = yukle(path)
    idx = _bul(kayitlar, kid, "aday")
    kayitlar[idx] = replace(kayitlar[idx], durum="pas", pas_sebebi=sebep.strip(),
                            kapanis_utc=_simdi(simdi))
    _yaz(kayitlar, path)
    return kayitlar[idx]


def kapat(kid: int, cikis: float, not_: str = "", path: Path | None = None,
          simdi: str | None = None) -> Kayit:
    """Islemi kapat, R'yi stop mesafesine gore hesapla."""
    kayitlar = yukle(path)
    idx = _bul(kayitlar, kid, "acik")
    k = kayitlar[idx]
    risk = abs(k.giris - k.stop)
    if risk <= 0:
        raise ValueError("risk mesafesi sifir")
    hareket = (cikis - k.giris) if k.yon == "long" else (k.giris - cikis)
    kayitlar[idx] = replace(k, durum="kapali", kapanis_utc=_simdi(simdi),
                            cikis=cikis, r=hareket / risk, sonuc_notu=not_)
    _yaz(kayitlar, path)
    return kayitlar[idx]


def ozet(path: Path | None = None) -> dict:
    kayitlar = yukle(path)
    kapali = [k for k in kayitlar if k.durum == "kapali" and k.r is not None]
    pas_sayisi = sum(1 for k in kayitlar if k.durum == "pas")
    alinan = len(kapali) + sum(1 for k in kayitlar if k.durum == "acik")
    bakilan = alinan + pas_sayisi
    n = len(kapali)
    gecikmeler = [k.kayit_gecikmesi_dk for k in kayitlar
                  if k.kayit_gecikmesi_dk is not None]
    temel = {
        "n": n, "pas": pas_sayisi,
        "kayit_gecikme_medyan_dk": (
            sorted(gecikmeler)[len(gecikmeler) // 2] if gecikmeler else None),
        "aday_acik": sum(1 for k in kayitlar if k.durum == "aday"),
        "secicilik": (100 * pas_sayisi / bakilan) if bakilan else float("nan"),
    }
    if not n:
        return {**temel, "exp_R": float("nan"), "toplam_R": 0.0, "kazanan": 0,
                "wr": float("nan"), "durma_tetik": False}
    rlar = [k.r for k in kapali]
    exp_r = sum(rlar) / n
    kazanan = sum(1 for r in rlar if r > 0)
    return {**temel, "exp_R": exp_r, "toplam_R": sum(rlar), "kazanan": kazanan,
            "wr": 100 * kazanan / n, "durma_tetik": n >= MIN_N and exp_r < 0}


def _mt5_bakiye() -> float | None:
    """Bakiyeyi MT5'ten oku. Terminal kapaliysa None -- uydurma yok.

    Lazy import: `telefon_brief` bu modulu bulutta import ediyor ve orada MT5
    yok (`test_cloud_deps`).
    """
    try:
        import MetaTrader5 as mt5
    except Exception:
        return None
    try:
        if not mt5.initialize():
            return None
        hesap = mt5.account_info()
        return float(hesap.balance) if hesap else None
    except Exception:
        return None
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="Diskresyoner islem defteri")
    p.add_argument("--durum", action="store_true")
    p.add_argument("--aday", action="store_true")
    p.add_argument("--ac", action="store_true")
    p.add_argument("--tetikle", type=int, metavar="ID")
    p.add_argument("--pas", type=int, metavar="ID")
    p.add_argument("--kapat", type=int, metavar="ID")
    p.add_argument("--sembol")
    p.add_argument("--yon")
    p.add_argument("--tetik", type=float)
    p.add_argument("--giris", type=float)
    p.add_argument("--stop", type=float)
    p.add_argument("--hedef", type=float)
    p.add_argument("--cikis", type=float)
    p.add_argument("--katmanlar", help="virgullu: " + ",".join(KATMANLAR))
    p.add_argument("--narrative", default="")
    p.add_argument("--tf", default="")
    p.add_argument("--tez")
    p.add_argument("--curuten")
    p.add_argument("--sebep")
    p.add_argument("--not", dest="not_")
    p.add_argument("--acilis", default=None,
                   help="islemin GERCEK acilis ani (UTC, 'YYYY-MM-DD HH:MM'); "
                        "telefondan acip sonra kaydediyorsan ver")
    p.add_argument("--bakiye", type=float, default=None,
                   help="giristeki hesap bakiyesi; verilmezse MT5'ten okunur")
    p.add_argument("--risk-pct", type=float, default=RISK_PCT,
                   dest="risk_pct", help=f"varsayilan {RISK_PCT}")
    a = p.parse_args()

    if a.aday or a.ac:
        ref_ad = "tetik" if a.aday else "giris"
        eksik = [k for k in ("sembol", "yon", ref_ad, "stop", "tez", "curuten",
                             "katmanlar") if getattr(a, k) is None]
        if eksik:
            p.error("zorunlu: " + ", ".join("--" + k for k in eksik))
        fn = aday if a.aday else ac
        ref = a.tetik if a.aday else a.giris
        bakiye = a.bakiye if a.bakiye is not None else _mt5_bakiye()
        if bakiye is None:
            print("  UYARI: bakiye okunamadi; risk alanlari bos kalacak ve "
                  "solvency kapisi CALISMAYACAK. --bakiye ile ver.")
        ek = {"acilis": a.acilis} if (a.ac and a.acilis) else {}
        k = fn(a.sembol, a.yon, ref, a.stop, a.tez, a.curuten, a.katmanlar,
               a.narrative, a.tf, a.hedef, bakiye=bakiye, risk_pct=a.risk_pct,
               **ek)
        print(f"{k.durum.upper()}: id={k.id} {k.sembol} {k.yon} "
              f"{ref_ad}={ref} stop={k.stop} katman={k.katman_sayisi}/"
              f"{len(KATMANLAR)}")
        if k.risk_usd is not None:
            tampon = k.bakiye - BREACH_BAKIYE - GUVENLIK_TAMPONU
            print(f"  risk    : %{k.risk_pct*100:.1f} = {k.risk_usd:.2f} USD "
                  f"(bakiye {k.bakiye:.2f}, breach'e kullanilabilir {tampon:.2f})")
        print(f"  tez     : {k.tez}")
        print(f"  curuten : {k.curuten}")
        return

    if a.tetikle is not None:
        if a.giris is None:
            p.error("--tetikle icin --giris gerekli")
        k = tetikle(a.tetikle, a.giris, acilis=a.acilis)
        print(f"ACILDI: id={k.id} giris={k.giris} stop={k.stop}")
    elif a.pas is not None:
        if not a.sebep:
            p.error("--pas icin --sebep gerekli")
        k = pas(a.pas, a.sebep)
        print(f"PAS: id={k.id} -- {k.pas_sebebi}")
    elif a.kapat is not None:
        if a.cikis is None:
            p.error("--kapat icin --cikis gerekli")
        k = kapat(a.kapat, a.cikis, a.not_ or "")
        print(f"KAPANDI: id={k.id} cikis={k.cikis} R={k.r:+.3f}")

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
    if o["pas"] or o["aday_acik"]:
        print(f"  Pas gecilen: {o['pas']}  |  secicilik: %{o['secicilik']:.0f}"
              f"  |  bekleyen aday: {o['aday_acik']}")
    for k in yukle():
        if k.durum == "aday":
            print(f"  ADAY: id={k.id} {k.sembol} {k.yon} tetik={k.tetik} "
                  f"stop={k.stop}")
        elif k.durum == "acik":
            print(f"  ACIK: id={k.id} {k.sembol} {k.yon} giris={k.giris} "
                  f"stop={k.stop}")


if __name__ == "__main__":
    main()
