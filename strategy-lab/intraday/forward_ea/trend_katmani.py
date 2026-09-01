"""Trend katmani -- SABIT tanim, SABIT evren, her gun ayni hesap.

NEDEN VAR (2026-09-01): kullanici telefondan "trend haline gelmis pariteleri
bul" diye sormak istedi. Bunu bir dil modeline sordurmak, bu projede zaten
kapatilmis bir kapiyi acardi: model kendi "trend" tanimini uydurur, kendi
listesini secer ve sana FILTRELENMIS bir evren gosterir. Olculmemis bir sinyal
kaynagi 2026-08-01'de tam bu yuzden kapatildi; `elenenler` katalogunda
`sunucu_kiralama` maddesi de ayni seyi soyluyor -- darbogaz tarama gucu degil.

Farki soyle koymak lazim: model taramasi "bugun sana ne gostereyim" diye karar
verir. Kodlanmis tanim her gun AYNI soruyu sorar ve cevap ne cikarsa onu basar,
kotu olsa bile. Ikincisi on-kayitlidir, birincisi degildir.

TANIM (2026-09-01'de, sonuca BAKILMADAN sabitlendi -- degistirmek yeni karar
gerektirir ve gerekcesi yazilir):
  - gunluk kapanisin 200EMA'ya gore konumu (ustunde/altinda) ve % uzakligi
  - ADX(14), gunluk, Wilder -- kapanmamis bar shift'li
  - 20 ve 50 gunluk yuzde degisim
  - siralama: 20 gunluk degisime gore, buyukten kucuge

Siralama bir SECIM DEGIL: evrenin tamami listeleniyor, yalnizca sirasi
belirleniyor. Eleme yapilsaydi (ornegin "ADX>25 olanlari goster") o zaman esik
bir hipotez olurdu ve olculmesi gerekirdi.

ISLEM EVRENI DEGISMEDI. Bu liste yalnizca OLGU gosterir. Portfoy, slot kisiti
ve modul kumesi aynen duruyor; `sweep_cok_endeks` maddesi (cok enstrumana
yayilma) katalogda hala `rejected`. Buradaki bir sembolde islem acmak, o
sembolun uzerinde calisan bir modul oldugu anlamina GELMEZ -- diskresyoner
rayda karar kullanicinindir ve ayni protokolden gecer.

Calistir:
    python -m intraday.forward_ea.trend_katmani
"""
from __future__ import annotations

import sys

import pandas as pd

from ..indicators import adx, ema

# Evren: kullanici karari (2026-09-01), portfoyun otesinde genis bakis.
# Gruplar yalnizca okunurluk icin; hesap hepsinde ayni.
EVREN: tuple[tuple[str, str], ...] = (
    ("NASDAQ100", "endeks"),
    ("SP500", "endeks"),
    ("US30", "endeks"),
    ("US2000", "endeks"),
    ("GER40", "endeks"),
    ("UK100", "endeks"),
    ("FRA40", "endeks"),
    ("JAP225", "endeks"),
    ("EURUSD", "fx"),
    ("GBPUSD", "fx"),
    ("USDJPY", "fx"),
    ("AUDUSD", "fx"),
    ("USDCAD", "fx"),
    ("USDCHF", "fx"),
    ("NZDUSD", "fx"),
    ("EURJPY", "fx"),
    ("GBPJPY", "fx"),
    ("XAUUSD", "emtia"),
    ("XAGUSD", "emtia"),
    ("WTI", "emtia"),
    ("BTCUSDT", "kripto"),
)

EMA_UZUN = 200
ADX_PENCERE = 14
GETIRI_PENCERELERI = (20, 50)
GUN = 400  # 200EMA icin yeterli gecmis


def _getiri(kapanis: pd.Series, gun: int) -> float:
    if len(kapanis) <= gun:
        return float("nan")
    onceki = float(kapanis.iloc[-gun - 1])
    if onceki == 0:
        return float("nan")
    return 100.0 * (float(kapanis.iloc[-1]) - onceki) / onceki


def sembol_satiri(sembol: str, grup: str, gunluk: pd.DataFrame) -> dict:
    """Tek sembolun sabit alanlari. Sifat yok, esik yok, eleme yok."""
    kapanis = gunluk["close"].dropna()
    if len(kapanis) < EMA_UZUN:
        return {"sembol": sembol, "grup": grup, "veri": False}
    e = float(ema(kapanis, EMA_UZUN).iloc[-1])
    son = float(kapanis.iloc[-1])
    a = adx(gunluk, ADX_PENCERE).iloc[-1]
    return {
        "sembol": sembol,
        "grup": grup,
        "veri": True,
        "kapanis": son,
        "ema200": e,
        # "ustunde/altinda" bir OLGU: fiyatin ortalamaya gore konumu.
        # "pahali/ucuz" olsaydi yorum olurdu.
        "ema200_konum": "ustunde" if son > e else "altinda",
        "ema200_uzaklik_yuzde": 100.0 * (son - e) / e if e else float("nan"),
        "adx": float(a) if pd.notna(a) else float("nan"),
        **{f"getiri_{g}g": _getiri(kapanis, g) for g in GETIRI_PENCERELERI},
    }


def tara(gunluk_veri) -> list[dict]:
    """Evrenin tamami; siralama 20 gunluk degisime gore, buyukten kucuge."""
    satirlar = []
    for sembol, grup in EVREN:
        try:
            gunluk = gunluk_veri(sembol)
        except Exception as e:
            satirlar.append({"sembol": sembol, "grup": grup, "veri": False,
                             "hata": f"{type(e).__name__}"})
            continue
        satirlar.append(sembol_satiri(sembol, grup, gunluk))

    def _anahtar(s: dict) -> float:
        d = s.get("getiri_20g", float("nan"))
        return d if d == d else float("-inf")  # veri yoksa sona

    return sorted(satirlar, key=_anahtar, reverse=True)


def markdown(satirlar: list[dict]) -> list[str]:
    p = [
        "",
        f"## Trend katmani (sabit tanim, {len(EVREN)} sembol)",
        "",
        f"200EMA konumu + ADX({ADX_PENCERE}) + {GETIRI_PENCERELERI[0]}/"
        f"{GETIRI_PENCERELERI[1]} gunluk degisim, gunluk barlardan. Evrenin "
        "TAMAMI listeleniyor; siralama 20 gunluk degisime gore. Eleme yok, "
        "esik yok, yorum yok.",
        "",
        "**Bu liste islem evreni DEGIL.** Portfoy ve modul kumesi degismedi; "
        "burada bir sembolun gorunmesi orada calisan bir modul oldugu anlamina "
        "gelmez.",
        "",
        "| sembol | grup | 200EMA | uzaklik | ADX | 20g | 50g |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in satirlar:
        if not s.get("veri"):
            p.append(f"| {s['sembol']} | {s['grup']} | VERI YOK | | | | |")
            continue
        p.append(
            f"| {s['sembol']} | {s['grup']} | {s['ema200_konum']} | "
            f"%{s['ema200_uzaklik_yuzde']:+.1f} | {s['adx']:.1f} | "
            f"%{s['getiri_20g']:+.1f} | %{s['getiri_50g']:+.1f} |"
        )
    return p


def _bulut_gunluk(sembol: str) -> pd.DataFrame:
    from .cloud_feed import ohlcv
    return ohlcv(sembol, "1d", days=GUN)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("\n".join(markdown(tara(_bulut_gunluk))))


if __name__ == "__main__":
    main()
