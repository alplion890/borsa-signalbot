"""CPI/NFP yayin tarihlerini FRED'den cek, `event_calendar` icin onbellege yaz.

NEDEN AYRI CALISTIRILIR: FRED API anahtar ister ve ag erisimi gerekir.
Backtest'in her kosumunda ag'a cikmasi hem yavas hem kirilgan olur, hem de
tarih listesi degisirse sonuc sessizce degisir. Bir kez cekilir, JSON'a
yazilir, commit'lenir; sonrasi deterministik.

ANAHTAR: `.env` icinde `FRED_API_KEY=...` (dosya .gitignore'da, PUBLIC repo).

GERCEK AYLIK YAYIN NASIL AYIRT EDILIR (kural onceden sabit, sonuca bakilmadi):
    FRED bir "release" altinda hem duzenli aylik yayini hem yillik revizyon /
    benchmark yayinlarini listeler. Ornek: 2024-02-09 CPI mevsimsel duzeltme
    revizyonu, 2024-02-13 gercek Ocak CPI'i.

    Ayirt etme kurali MEKANIK: o tarihte manset serinin (CPIAUCSL / PAYEMS)
    EN SON gozlem ayi, bir onceki yayin tarihindekine gore ILERLEDIYSE bu
    gercek aylik yayindir. Ilerlemediyse revizyondur ve atlanir.

    Bu kural getiriye bakmadan secildi. Alternatifi ("ayni ayda iki tarih
    varsa ikincisini al") CPI'de dogru, NFP'de YANLIS sonuc veriyordu --
    yani gozle secilen bir kural olacakti. Bu projede sahte edge tam olarak
    boyle uretiliyor.

YAYIN SAATI: CPI ve Employment Situation ikisi de 08:30 ET (BLS standardi).

Calistir:
    python -m intraday.event_calendar_fetch
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
ONBELLEK = Path(__file__).resolve().parent / "event_dates_bls.json"

RELEASES = {
    "CPI": {"release_id": 10, "series_id": "CPIAUCSL"},
    "NFP": {"release_id": 50, "series_id": "PAYEMS"},
}
BASLANGIC = "2012-01-01"
BITIS = "2026-12-31"


def _anahtar() -> str:
    k = os.environ.get("FRED_API_KEY")
    if k:
        return k.strip()
    env = REPO / ".env"
    if env.exists():
        for satir in env.read_text(encoding="utf-8").splitlines():
            if satir.startswith("FRED_API_KEY="):
                return satir.split("=", 1)[1].strip()
    raise SystemExit(
        "FRED_API_KEY yok. .env dosyasina 'FRED_API_KEY=...' ekle "
        "(anahtar: fredaccount.stlouisfed.org/apikey)."
    )


def _get(yol: str, anahtar: str, **params) -> dict:
    p = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://api.stlouisfed.org/fred/{yol}?api_key={anahtar}&file_type=json&{p}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def yayin_tarihleri(anahtar: str, release_id: int) -> list[str]:
    d = _get("release/dates", anahtar, release_id=release_id,
             realtime_start=BASLANGIC, realtime_end=BITIS, limit=1000,
             include_release_dates_with_no_data="true")
    return [x["date"] for x in d["release_dates"]]


def son_gozlem_ayi(anahtar: str, series_id: str, tarih: str) -> str | None:
    """`tarih` gununde serinin bilinen EN SON gozlem ayi (o gunun vintage'i)."""
    d = _get("series/observations", anahtar, series_id=series_id,
             realtime_start=tarih, realtime_end=tarih,
             sort_order="desc", limit=1)
    obs = d["observations"]
    return obs[0]["date"] if obs else None


def gercek_aylik_yayinlar(anahtar: str, ad: str) -> list[str]:
    """Gecmis yayinlari vintage ile dogrula; GELECEK yayinlari oldugu gibi al.

    FRED bugunden sonraki bir tarihi vintage olarak kabul etmez (400). Gelecek
    yayinlar zaten takvimde ilan edilmis ve revizyon degil -- dogrulanacak bir
    gozmelem gecmisi yok. Backtest sadece gecmisi kullanir, o yuzden bu
    tarihlerin dogrulanmamis olmasi olcumu etkilemez.
    """
    from datetime import date as _date

    cfg = RELEASES[ad]
    tarihler = yayin_tarihleri(anahtar, cfg["release_id"])
    bugun = _date.today().isoformat()
    tutulan: list[str] = []
    onceki_ay: str | None = None
    for i, t in enumerate(tarihler, 1):
        if t > bugun:
            tutulan.append(t)
            print(f"  [{ad}] {i}/{len(tarihler)} {t} GELECEK -> dogrulanmadan tutuldu",
                  file=sys.stderr)
            continue
        ay = son_gozlem_ayi(anahtar, cfg["series_id"], t)
        if ay is not None and (onceki_ay is None or ay > onceki_ay):
            tutulan.append(t)
            onceki_ay = ay
        print(f"  [{ad}] {i}/{len(tarihler)} {t} son_gozlem={ay} "
              f"{'TUT' if tutulan and tutulan[-1] == t else 'atla'}",
              file=sys.stderr)
        time.sleep(0.12)  # FRED'e nazik ol
    return tutulan


def main() -> None:
    anahtar = _anahtar()
    cikti = {"kaynak": "FRED api.stlouisfed.org", "aralik": [BASLANGIC, BITIS],
             "yayin_saati_et": "08:30",
             "kural": "manset serinin son gozlem ayini ilerleten yayin = gercek aylik yayin"}
    for ad in RELEASES:
        g = gercek_aylik_yayinlar(anahtar, ad)
        cikti[ad] = g
        print(f"{ad}: {len(g)} gercek aylik yayin ({g[0]} -> {g[-1]})")
    ONBELLEK.write_text(json.dumps(cikti, indent=1), encoding="utf-8")
    print(f"Yazildi: {ONBELLEK}")


if __name__ == "__main__":
    main()
