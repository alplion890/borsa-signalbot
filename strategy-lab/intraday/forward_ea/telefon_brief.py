"""Telefon brifingi -- ayni olgular, markdown olarak, GitHub Actions'ta.

NEDEN VAR (2026-09-01): kullanici surekli PC basinda olamiyor. Diskresyoner
ray birincil ray oldugu icin, PC'ye bagli kalmasi rayin fiilen calismamasi
demek. Bu script `TELEFON/BRIEF.md` uretiyor; telefondaki Claude o dosyayi
okuyup kullaniciya SESLI aktarabiliyor.

NE DEGISMEDI: alan seti. `seans_brief.sembol_olgusu()` cagriliyor, ikinci bir
olgu ureticisi YAZILMADI. Degisen tek sey veri kaynagi: PC'de dukascopy,
bulutta `cloud_feed` (yfinance/Binance). Feed farki 2026-08-28'de olculdu ve
ihmal edilebilir cikti (NASDAQ -0.09 puan, bkz [[Borsa - Feed Parity]]).

NE DEGISMEYECEK: yorum yok. Bu dosya "guclu/zayif", "pahali/ucuz",
"al/sat" gibi tek bir sifat bile basmaz -- `test_telefon_brief` bunu kilitler.
Sifat basarsa telefondaki Claude onu tekrarlar ve yorumu makine yapmis olur;
diskresyoner deneyin butun anlami yorumun KULLANICIDA olmasi.

Calistir:
    python -m intraday.forward_ea.telefon_brief          # TELEFON/BRIEF.md yazar
    python -m intraday.forward_ea.telefon_brief --stdout # ekrana bas
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from ..elenenler import KATALOG, STATULER, veto_mu
from ..signalbot.risk import live_module_names
from . import diskresyoner, trend_katmani
from .ledger import birlesik_forward
from .seans_brief import (
    ATR_PENCERE,
    HACIM_PENCERE,
    SWING_GUN,
    TR,
    UTC,
    VARSAYILAN_SEMBOLLER,
    seans_olgusu,
    sembol_olgusu,
    takvim_olgusu,
)

CIKTI = Path(__file__).resolve().parent.parent.parent.parent / "TELEFON" / "BRIEF.md"

# `signalbot/test_demotion_tripwire.py` ile AYNI esik. Iki yerde sayi tutmak
# bu projedeki tekrar eden hata; buraya tasindiginda oradan import edilecek.
MIN_N = 25


def _bulut_veri(sembol: str, tf: str) -> pd.DataFrame:
    """Intraday barlar -- yalniz 'son kapanis' ve 'bugun araligi' icin."""
    from .cloud_feed import ohlcv
    return ohlcv(sembol, tf, days=5)


def _bulut_gunluk(sembol: str) -> pd.DataFrame:
    """Gunluk barlar -- EMA200 / ATR yuzdeligi / donus seviyeleri icin.

    Intraday seriden resample EDILMEZ: yfinance 15m'i 60 gun veriyor, EMA200
    o pencereye sigmaz ve sayi sessizce yanlis cikar (2026-09-01'de goruldu).
    """
    from .cloud_feed import ohlcv
    return ohlcv(sembol, "1d", days=500)


def _mekanik_durum() -> list[str]:
    """Canli modullerin forward durumu + dusurme esigine kalan islem."""
    satirlar = []
    try:
        d = birlesik_forward(include_candidates=False)
    except Exception as e:  # kanit kapisi fail-closed: sebebi yaz, uydurma
        return [f"- DEFTER OKUNAMADI: {type(e).__name__}: {e}"]
    for modul in sorted(live_module_names()):
        alt = d[d["module"] == modul]
        n = len(alt)
        if n == 0:
            satirlar.append(f"- **{modul}**: forward islem yok")
            continue
        exp_r = float(alt["r"].mean())
        kalan = max(0, MIN_N - n)
        esik = "esikte" if kalan == 0 else f"esige {kalan} islem"
        satirlar.append(f"- **{modul}**: n={n}, exp_R={exp_r:+.3f}, {esik}")
    return satirlar


def _diskresyoner_durum() -> list[str]:
    try:
        o = diskresyoner.ozet()
    except Exception as e:
        return [f"- DEFTER OKUNAMADI: {type(e).__name__}: {e}"]
    satirlar = [f"- acik aday: {o['aday_acik']}, pas: {o['pas']}, "
                f"secicilik: %{o['secicilik']:.0f}"
                if o["secicilik"] == o["secicilik"] else
                f"- acik aday: {o['aday_acik']}, pas: {o['pas']}"]
    if not o["n"]:
        satirlar.append("- Kapanmis islem yok (defter bos).")
        return satirlar
    satirlar.append(f"- n={o['n']}, exp_R={o['exp_R']:+.3f}, "
                    f"toplam {o['toplam_R']:+.2f}R, WR %{o['wr']:.0f}")
    if o["durma_tetik"]:
        satirlar.append("- **DURMA KURALI TETIKLENDI** (n>=20 ve exp_R<0): "
                        "yeni diskresyoner islem YOK.")
    return satirlar


def _katalog_satirlari() -> list[str]:
    satirlar = []
    for statu, (baslik, _) in STATULER.items():
        grup = [x for x in KATALOG if x.statu == statu]
        if not grup:
            continue
        veto = "VETO" if veto_mu(statu) else "veto DEGIL"
        satirlar.append(f"\n**{baslik}** ({veto})\n")
        for x in grup:
            satir = f"- `{x.id}` — {x.baslik}"
            if x.kapsam:
                satir += f"\n  - kapsam: {x.kapsam}"
            satirlar.append(satir)
    return satirlar


def _sembol_satirlari(semboller: list[tuple[str, str]]) -> list[str]:
    satirlar = []
    for sembol, tf in semboller:
        satirlar.append(f"\n### {sembol} ({tf})\n")
        try:
            o = sembol_olgusu(sembol, tf, veri=_bulut_veri,
                              gunluk_veri=_bulut_gunluk)
        except Exception as e:
            satirlar.append(f"- VERI YOK: {type(e).__name__}: {e}")
            continue
        satirlar += [
            f"- son kapanis: {o.son_kapanis:.5g}  (bar {o.son_bar_utc} UTC)",
            f"- dun araligi: {o.dun_dusuk:.5g} → {o.dun_yuksek:.5g}",
        ]
        if o.bugun_dusuk == o.bugun_dusuk:  # NaN degil
            satirlar.append(
                f"- bugun araligi: {o.bugun_dusuk:.5g} → {o.bugun_yuksek:.5g}")
        else:
            satirlar.append("- bugun araligi: henuz bar yok")
        satirlar += [
            f"- 200EMA (gunluk): {o.ema200:.5g}  "
            f"(uzaklik {o.ema200_uzaklik_puan:+.5g} / %{o.ema200_uzaklik_yuzde:+.2f})",
            f"- ATR(14) son kapali gun: {o.atr_bugun:.5g}  "
            f"({ATR_PENCERE} gunun %{o.atr_yuzdelik:.0f}. yuzdeligi)",
            (f"- hacim (son kapali gun): {o.hacim_bugun:,.0f}  "
             f"({HACIM_PENCERE} gunun %{o.hacim_yuzdelik:.0f}. yuzdeligi)")
            if o.hacim_bugun == o.hacim_bugun else
            "- hacim: BU FEED HACIM VERMIYOR (spot FX) -- hacim katmani "
            "brifingten doldurulamaz",
            f"- donus seviyeleri (son {SWING_GUN} gun):",
        ]
        if o.donus_seviyeleri:
            for tarih, fiyat, tip in o.donus_seviyeleri:
                satirlar.append(f"  - {tarih}  {fiyat:.5g}  ({tip})")
        else:
            satirlar.append("  - yeterli veri yok")
    return satirlar


def brief_metni(semboller: list[tuple[str, str]] | None = None,
                simdi_utc: datetime | None = None) -> str:
    """Markdown brifing. YALNIZ olgu -- sifat yok, tavsiye yok."""
    semboller = semboller or VARSAYILAN_SEMBOLLER
    simdi = simdi_utc or datetime.now(UTC)
    tr = simdi.astimezone(TR).strftime("%Y-%m-%d %H:%M")

    p = [
        "# Seans brifingi (olgu)",
        "",
        f"Uretim: **{tr} TR** / {simdi.strftime('%Y-%m-%d %H:%M')} UTC  ",
        "Kaynak: bulut feed (yfinance/Binance). Otomatik uretilir; "
        "yalniz olcum basar.",
        "",
        "> **Fiyatlar endeks kotasyonu, broker fiyati DEGIL.** ^NDX ile "
        "MavenTrade US100 arasinda olculmus basis ~-170 puan (2026-08-24). "
        "Buradaki seviyeleri dogrudan emir fiyati olarak kullanma; "
        "terminaldeki fiyatla farki kendin hesapla.",
        "",
        "## Sistem durumu",
        "",
        "### Mekanik ray (dondurulmus -- yeni modul/parametre yok)",
        "",
    ]
    p += _mekanik_durum()
    p += ["", "### Diskresyoner ray (birincil)", ""]
    p += _diskresyoner_durum()

    p += ["", "## Takvim", ""]
    bugunku, haftaki = takvim_olgusu()
    if bugunku:
        for e in bugunku:
            erken = " (ERKEN ACIKLAMA)" if e.erken_aciklama else ""
            p.append(f"- BUGUN {e.tip} duyuru "
                     f"{e.aciklama_et.strftime('%H:%M')} ET{erken}")
    else:
        p.append("- Bugun FOMC/CPI/NFP yok.")
    if haftaki:
        for e in haftaki[:6]:
            p.append(f"- {e.gun}  {e.tip}")
    else:
        p.append("- Onumuzdeki 7 gunde FOMC/CPI/NFP yok.")

    p += ["", "## Seans", ""]
    for ad, acik, kalan in seans_olgusu(simdi):
        durum = "ACIK" if acik else "kapali"
        ne = "kapanisa" if acik else "acilisa"
        p.append(f"- {ad}: {durum}, {ne} {kalan:.1f} saat")

    p += ["", "## Semboller", ""]
    p += _sembol_satirlari(semboller)

    if semboller:
        # Trend katmani: SABIT tanim, evrenin tamami, siralama var ama eleme
        # yok. Modele "trend olan pariteleri bul" diye sormak, olculmemis bir
        # secim katmani eklemek olurdu (bkz trend_katmani docstring).
        try:
            p += trend_katmani.markdown(
                trend_katmani.tara(trend_katmani._bulut_gunluk))
        except Exception as e:
            p += ["", "## Trend katmani", "",
                  f"- URETILEMEDI: {type(e).__name__}: {e}"]

    p += ["", "## Olculmus fikirler katalogu", "",
          "Tez kontrolu icin. Statuye bak: veto YALNIZ rejected/retired."]
    p += _katalog_satirlari()

    p += ["", "---", "",
          "Bu dosyayi okuyan asistan icin kural seti: `TELEFON/SISTEM.md`."]
    return "\n".join(p) + "\n"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Telefon brifingi (markdown)")
    ap.add_argument("--stdout", action="store_true", help="dosyaya yazma, ekrana bas")
    ap.add_argument("--cikti", default=None, help="hedef dosya")
    a = ap.parse_args()

    metin = brief_metni()
    if a.stdout:
        print(metin)
        return
    hedef = Path(a.cikti) if a.cikti else CIKTI
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(metin, encoding="utf-8")
    print(f"yazildi: {hedef}  ({len(metin)} karakter)")


if __name__ == "__main__":
    main()
