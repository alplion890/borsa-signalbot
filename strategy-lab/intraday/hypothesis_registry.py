"""Hipotez ON-KAYIT defteri -- iki arastirmacinin ortak butcesi.

NEDEN VAR: arastirma rayinda artik iki taraf calisiyor (Claude + Hermes).
Ikisi ayri ayri "ayda 2 hipotez" uretirse ayda 4 olur ve DSR esigi ona gore
yukselir -- yani butce sessizce iki katina cikar. Bu defter butceyi ORTAK
tutar: ayda en fazla 2, kim yazarsa yazsin.

Ikinci isi: hipotezi testten ONCE yazmaya zorlamak. Bu projede sahte edge uc
kez sonuca bakip kural secmekten cikti. Bir hipotez buraya yazilmadan
kosulursa, sonucu adopte edilemez -- kural bu.

Ucuncu isi: DSR icin TAM deneme sayisini tutmak. Taranan her kombinasyon
sayilir, sadece finalist degil (bkz `search_budget.py`).

Calistir:
    python -m intraday.hypothesis_registry            # durum
    python -m intraday.hypothesis_registry --butce    # kalan deneme butcesi
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

REGISTRY = Path(__file__).resolve().parent / "hypotheses.json"

AYLIK_TAVAN = 2          # iki arastirmacinin TOPLAMI
ZORUNLU_ALANLAR = {
    "id",            # kisa slug
    "tarih",         # YYYY-MM-DD, ON-KAYIT tarihi (test tarihinden once)
    "yazan",         # claude | hermes | alparslan
    "neden_var",     # YAPISAL sebep -- "backtest iyi cikti" gecerli degil
    "enstruman",
    "tutus",         # beklenen tutus suresi (bar/saat/gun)
    "min_n",         # adopte icin gereken minimum islem
    "deneme_sayisi", # taranacak TAM kombinasyon sayisi (DSR'ye girer)
    "durum",         # kayitli | kosuldu | elendi | adopte
}
GECERLI_DURUM = {"kayitli", "kosuldu", "elendi", "adopte"}


def load(path: Path | None = None) -> list[dict]:
    p = Path(path) if path is not None else REGISTRY
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def save(kayitlar: list[dict], path: Path | None = None) -> None:
    p = Path(path) if path is not None else REGISTRY
    p.write_text(json.dumps(kayitlar, indent=2, ensure_ascii=False), encoding="utf-8")


def ay_anahtari(tarih: str) -> str:
    return tarih[:7]


def aylik_sayim(kayitlar: list[dict]) -> Counter:
    return Counter(ay_anahtari(k["tarih"]) for k in kayitlar)


def toplam_deneme(kayitlar: list[dict]) -> int:
    """DSR'ye girecek toplam deneme sayisi -- elenenler DAHIL.

    Elenen hipotezi saymamak, coklu-karsilastirma duzeltmesini kandirmaktir:
    "10 fikir denedim, 9'u tutmadi, 10.'su harika" ile "1 fikir denedim ve
    harika" ayni sey degil.
    """
    return sum(int(k.get("deneme_sayisi", 0)) for k in kayitlar)


def kapasite_var_mi(kayitlar: list[dict], tarih: str | None = None) -> tuple[bool, str]:
    t = tarih or date.today().isoformat()
    ay = ay_anahtari(t)
    mevcut = aylik_sayim(kayitlar).get(ay, 0)
    if mevcut >= AYLIK_TAVAN:
        yazanlar = ", ".join(k["yazan"] for k in kayitlar if ay_anahtari(k["tarih"]) == ay)
        return False, f"{ay} dolu: {mevcut}/{AYLIK_TAVAN} ({yazanlar})"
    return True, f"{ay}: {mevcut}/{AYLIK_TAVAN} kullanildi"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--butce", action="store_true")
    a = p.parse_args()

    kayitlar = load()
    if not kayitlar:
        print("Kayit yok. Ilk hipotez on-kaydi bekleniyor.")
        return

    print(f"{'id':28} {'tarih':11} {'yazan':9} {'durum':9} {'deneme':>7}")
    for k in sorted(kayitlar, key=lambda x: x["tarih"]):
        print(f"{k['id']:28} {k['tarih']:11} {k['yazan']:9} "
              f"{k['durum']:9} {k.get('deneme_sayisi', 0):>7}")

    var, mesaj = kapasite_var_mi(kayitlar)
    print(f"\nAylik kapasite: {mesaj}" + ("" if var else "  -- YENI HIPOTEZ ACILAMAZ"))
    if a.butce:
        print(f"DSR'ye girecek toplam deneme: {toplam_deneme(kayitlar):,}")


if __name__ == "__main__":
    main()
