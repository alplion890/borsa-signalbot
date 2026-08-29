"""ELENENLER KATALOGU -- olculmus ve elenmis fikirlerin donmus listesi.

NE ISE YARAR: diskresyoner seansta, islem acmadan once "benim tezim zaten
elenmis bir sey mi?" sorusunu cevaplar. Sinyal degil VETO araci.

NEDEN VETO, NEDEN SINYAL DEGIL (2026-08-28 karari):
"Calismiyor" ile "tersi calisir" ayni sey degildir.
  - exp_R ~ 0 (edge yok)  -> tersini almak da ~0 verir, ustune iki kez spread
  - exp_R << 0 (guvenilir kaybettirir) -> tersi ISE YARAYABILIR
Bizim elenenlerimizin neredeyse hepsi birinci turden. Ustelik R'nin isaretini
cevirerek ters stratejinin sonucunu HESAPLAYAMAZSIN: stop ve hedef asimetrik
yerlestirilir, -1R'de stop yiyen islem ters cevrilince +1R vermez. Tersini
bilmek yeniden backtest ister -- yani yeni hipotez, yani butce.

Bu yuzden katalog yalnizca "bunu alma" der, "tersini al" demez.

KATALOG DONMUSTUR. Seans sirasinda "su saatte bu desen ne yapmis" diye canli
sorgu YAPILMAZ -- o, on-kayitsiz hipotez testidir ve bu projedeki dort sahte
edge tam o dusunce biciminden cikti. Yeni madde eklemek icin once olcum,
sonra kayit; sirasi boyle.

Calistir:
    python -m intraday.elenenler                 # tum katalog
    python -m intraday.elenenler --kontrol fvg   # tez kontrolu
    python -m intraday.elenenler --yapi          # elenmemis yapisal bulgular
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Elenen:
    """Olculmus ve elenmis bir fikir. Her alan bir olcume dayanir."""
    id: str
    baslik: str
    iddia: str        # cazip gorunen sey -- neden birinin aklina gelir
    olcum: str        # ne olculdu, hangi sayiyla
    neden: str        # neden bu sayi fikri eler
    tarih: str
    kaynak: str
    anahtarlar: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Yapi:
    """Elenmemis YAPISAL bulgu -- ama tek basina edge DEGIL, baglam."""
    baslik: str
    olcum: str
    uyari: str
    tarih: str
    kaynak: str
    anahtarlar: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# ELENENLER -- her madde bir olcume dayanir, "bence" yok
# ---------------------------------------------------------------------------

KATALOG: tuple[Elenen, ...] = (
    Elenen(
        id="fvg_doldurma",
        baslik="FVG (fair value gap) doldurulur",
        iddia="Ucgen bosluk aciliyorsa fiyat geri donup doldurur, girisi buna gore kur.",
        olcum="10 paritede doldurma orani ~%84 -- AMA yayilim 2-6, yani "
              "NASDAQ da AUDUSD da ayni orani veriyor.",
        neden="Bir metrik karakter olcuyorsa pariteler AYRISMALI. Ayrismiyorsa "
              "piyasayi degil metrigin kendi geometrisini olcuyorsun. %84 dogru "
              "ama bilgi tasimiyor: her yerde ayni oldugu icin secim yapamazsin.",
        tarih="2026-07-11",
        kaynak="liquidity_profiler.py + [[Borsa - Likidite Karakter Haritasi]]",
        anahtarlar=("fvg", "fair value gap", "bosluk", "imbalance", "ict", "smc"),
    ),
    Elenen(
        id="ema_vwap_sicrama",
        baslik="EMA20 / EMA50 / VWAP'tan sicrama",
        iddia="Trend yonunde fiyat EMA20'ye veya VWAP'a dusunce sicrar, oradan al.",
        olcum="10 paritenin HEPSI: EMA20 ~%57, EMA50 ~%42, VWAP ~%54 sicrama. "
              "Parite-ozel karakter YOK.",
        neden="Evrensel gurultu. %57 sicrama tek basina edge degil -- honest "
              "engine'de PnL cikmiyor; maliyet dusunce sifira iniyor.",
        tarih="2026-07-11",
        kaynak="liquidity_profiler.py + [[Borsa - Likidite Karakter Haritasi]]",
        anahtarlar=("ema", "ema20", "ema50", "vwap", "sicrama", "bounce", "ortalama"),
    ),
    Elenen(
        id="equal_high_low_raid",
        baslik="Equal high/low avlandiktan sonra donus",
        iddia="Cift tepe/dip alinirsa likidite suprulmustur, fiyat doner.",
        olcum="Raid sonrasi donus orani ~%50, yayilim dusuk.",
        neden="Yazi-tura. Maliyet dusunce negatif.",
        tarih="2026-07-11",
        kaynak="liquidity_profiler.py + [[Borsa - Likidite Karakter Haritasi]]",
        anahtarlar=("equal high", "equal low", "cift tepe", "cift dip", "raid",
                    "likidite", "sweep", "supurme"),
    ),
    Elenen(
        id="ny_londra_surdurme",
        baslik="NY seansi Londra yonunu surdurur",
        iddia="Londra yonu belirler, NY devam ettirir; NY acilisinda o yone gir.",
        olcum="Surdurme orani ~%50.",
        neden="Yazi-tura.",
        tarih="2026-07-11",
        kaynak="liquidity_profiler.py + [[Borsa - Likidite Karakter Haritasi]]",
        anahtarlar=("ny", "londra", "seans", "surdurme", "continuation", "devam"),
    ),
    Elenen(
        id="prevday_continuation",
        baslik="Dun yukari kapadiysa once PDH vurulur",
        iddia="Onceki gunun yonu bugune bias verir; %75 oranla dogruluyordu.",
        olcum="%75 cikti AMA GEOMETRIK KONTAMINE: dun yukari kapayinca fiyat "
              "zaten PDH'ye yakin aciliyor, mekanik olarak once onu vuruyor.",
        neden="Olcumun kendisi hatali kurulmustu -- 'smart money devami' degil "
              "acilis mesafesi olculuyordu. Metrik cope atildi.",
        tarih="2026-07-11",
        kaynak="liquidity_profiler.py + [[Borsa - Likidite Karakter Haritasi]]",
        anahtarlar=("pdh", "pdl", "onceki gun", "prevday", "dun", "bias"),
    ),
    Elenen(
        id="inside_day_kirilim",
        baslik="Inside day sonrasi kirilim (Kathy Lien)",
        iddia="Inside day olusursa %84.92 ihtimalle high veya low kirilir.",
        olcum="PRIOR_DAY_HL kurulumu: 176 islem, exp_R -0.009. "
              "Sabit 1.5R baseline: 286 islem, exp_R +0.099. "
              "4 enstruman x 15 konfig = 45 hucre, neredeyse tamami negatif.",
        neden="Klasik baz-oran yanilgisi: %84.92 zaten her gunun taban orani, "
              "inside day'e ozgu degil. Iddia edilen seviye baseline'dan KOTU.",
        tarih="2026-07-20",
        kaynak="inside_day_lab.py + [[Borsa - Inside Day Sahte Edge]]",
        anahtarlar=("inside day", "ic gun", "kirilim", "breakout", "kathy lien"),
    ),
    Elenen(
        id="btc_absorption",
        baslik="BTC absorption modulu",
        iddia="Backtest'te pozitifti (+0.073), kripto 7/24 oldugu icin frekans yuksek.",
        olcum="Forward: exp_R -0.326, n=24, WR %29. Backtest'in TERSI.",
        neden="Bu projedeki en net backtest-forward ayrismasi. Sinyallerine "
              "islem ACILMAMALI.",
        tarih="2026-08-06 (forward guncel 2026-08-28)",
        kaynak="forward_ledger.csv + [[Borsa - Forward EA Durumu]]",
        anahtarlar=("btc", "bitcoin", "kripto", "absorption", "crypto"),
    ),
    Elenen(
        id="fomc_oncesi_drift",
        baslik="FOMC duyurusu oncesi long (15-30 dk pencere)",
        iddia="Lucca-Moench (JF 2015) pre-FOMC drift: duyuru oncesi getiri anormal yuksek.",
        olcum="116 FOMC olayi, 2 enstruman x 2 giris varyanti. Havuz PSR 0.9198 "
              "gorunuyordu AMA 464 'gozlem' ayni 116 olayin 4 kez olculmus haliydi "
              "(bacak korelasyonu 0.47-0.82). Olay bazina: PSR 0.8031, t=0.845.",
        neden="Havuz istatistigi gecersizdi -- ortusen bacaklari bagimsiz saymak "
              "n'i sisiriyor, PSR sqrt(n) ile olcekleniyor. "
              "NOT: bu Lucca-Moench'i CURUTMEZ; onlar 24 SAATLIK pencereyi olctu, "
              "biz 15-30 dakikayi. Farkli soru.",
        tarih="2026-08-24",
        kaynak="macro_day_lab.py + [[Borsa - Makro Gun Kitabi Hipotezi]]",
        anahtarlar=("fomc", "fed", "faiz", "duyuru", "drift", "makro", "pre-fomc"),
    ),
    Elenen(
        id="sweep_cok_endeks",
        baslik="SWEEP'i 7 endekse yayarak kari katlamak",
        iddia="Havuz exp_R +0.194 (n=118) -- ayni kurali cok enstrumanda kos, kar katlanir.",
        olcum="Ayni-anda-tek-islem (slot) kisiti uygulaninca exp_R -0.062'ye dusuyor.",
        neden="Slot ilk gelen sinyale gidiyor, EN IYI sembole degil. Havuz "
              "ortalamasi bu kisiti saymiyor. Portfoyde degisiklik yapilmadi.",
        tarih="2026-08-14",
        kaynak="portfolio_ab + [[Borsa - Portfoy Kompozisyonu ve Slot Kisiti]]",
        anahtarlar=("sweep", "cok enstruman", "breadth", "genisleme", "portfoy",
                    "slot", "endeks"),
    ),
    Elenen(
        id="donchian_xau",
        baslik="Donchian kanal kirilimi, XAUUSD 1H (turtle)",
        iddia="Klasik turtle N=20/55 kanal kirilimi, altinda NASDAQ'tan bagimsiz kitap.",
        olcum="2012-2026: N=20 exp_R +0.085 (848 islem, PSR 0.976), "
              "N=55 +0.078 (531 islem, PSR 0.946). Korelasyon/maliyet kapilari gecti. "
              "Yil-yil 9/15 ve 11/15 pozitif.",
        neden="ADOPTE EDILMEDI: SR ~0.08, mevcut forward kitabin altinda. "
              "Ayrica N=20 karinin yarisi 2014+2017 iki yildan geliyor. "
              "Elenmis degil ama 'kullanilabilir' de degil.",
        tarih="2026-08-23 (Hermes denetimi 08-24)",
        kaynak="donchian_xau_lab.py + [[Borsa - Donchian XAUUSD 1H Hipotezi]]",
        anahtarlar=("donchian", "turtle", "kanal", "channel", "kirilim", "altin",
                    "xauusd"),
    ),
    Elenen(
        id="gold_ny_orb",
        baslik="GOLD NY ORB modulu",
        iddia="Altinda NY acilis range kirilimi; portfoyde aylardir duruyordu.",
        olcum="Forward exp_R -0.411, n=9, t=-2.05 -- defterdeki TEK |t|>2 sonuc "
              "ve negatif tarafta. 2026-07-09'dan beri sifir sinyal (ATR filtresi "
              "kurulumlarin ~%88'ini kesiyor).",
        neden="Emekli edildi 2026-08-28. 50 gundur ne dogrulanabilir ne curutulebilir "
              "durumdaydi.",
        tarih="2026-08-28",
        kaynak="modules.py + [[Borsa - Uc Rayli Son Duzen]]",
        anahtarlar=("gold", "altin", "orb", "ny orb", "acilis range"),
    ),
    Elenen(
        id="ic_bar_bazli",
        baslik="Bar-bazli IC (Information Coefficient) ile bekleme suresini kisaltmak",
        iddia="Islem yerine BAR sayarsak 350.000 gozlem olur, kanit aylar icinde gelir.",
        olcum="Sinyal yogunlugu olculdu: NQ_ORB 956.183 barin 2.104'unde sinyal "
              "veriyor (%0.220), SWEEP_CORE %0.214. Barlarin %99.78'inde tahmin YOK.",
        neden="IC her barda bir forecast ister; bizim moduller olay-tetiklemeli. "
              "Ayrica o 2.104 sinyal zaten elimizdeki BACKTEST verisi -- darbogaz "
              "olcum hassasiyeti degil ornek-disi gecerlilik. Ucuncusu: IC yon "
              "korelasyonu olcer, SWEEP %33 isabetle +0.804 kazaniyor (odeme "
              "asimetrisi) -- IC on-filtresi tam da karli modulu elerdi.",
        tarih="2026-08-24",
        kaynak="[[Borsa - Profesyonel Quant Playbook Karsilastirmasi]]",
        anahtarlar=("ic", "information coefficient", "rank ic", "bar bazli",
                    "bekleme", "hizlandirma"),
    ),
    Elenen(
        id="sunucu_kiralama",
        baslik="Sunucu kiralayip daha cok strateji taramak",
        iddia="Daha fazla islem gucu = daha fazla hipotez = edge bulma sansi artar.",
        olcum="3 yillik veri istatistiksel olarak ~37 hipotez finanse ediyor; "
              "14 yilla gercek butce 1-3'e dusuyor (SR dustugu icin). "
              "256 cekirdek bu butceyi yarim saniyede tuketir.",
        neden="Darbogaz islem gucu degil VERI. Sunucu hicbir sey hizlandirmiyor, "
              "sadece butceyi daha hizli yakiyor.",
        tarih="2026-08-21",
        kaynak="search_budget.py + [[Borsa - Arama Butcesi ve Veri Uzunlugu]]",
        anahtarlar=("sunucu", "server", "kiralama", "islem gucu", "tarama",
                    "compute", "gpu"),
    ),
)


# ---------------------------------------------------------------------------
# ELENMEYEN YAPISAL BULGULAR -- baglam olarak kullanilabilir, EDGE DEGIL
# ---------------------------------------------------------------------------

YAPILAR: tuple[Yapi, ...] = (
    Yapi(
        baslik="NASDAQ uclarini NY seansinda yogunlastiriyor",
        olcum="Gunun high'i NY'de: NASDAQ %59 vs AUDUSD %37 (yayilim 22). "
              "Asya range supurme: NASDAQ %84 vs AUDUSD %62 (yayilim 23).",
        uyari="Yayilim >10 oldugu icin GERCEK karakter (artefakt degil). AMA bu "
              "bir giris kurali degil, baglam: NQ_ORB'un neden calistigi bununla "
              "aciklaniyor ve o zaten somuruluyor. Tek basina islem gerekcesi degil.",
        tarih="2026-07-11",
        kaynak="liquidity_profiler.py + [[Borsa - Likidite Karakter Haritasi]]",
        anahtarlar=("nasdaq", "nq", "ny", "seans", "yogunlasma"),
    ),
    Yapi(
        baslik="FX pariteleri uclarini seanslara yayiyor",
        olcum="Ayni olcumlerin FX tarafi: AUDUSD gunun high'ini NY'de yapma "
              "orani %37 (NASDAQ %59), Asya range supurme %62 (NASDAQ %84).",
        uyari="Yapisal olarak daha rangeci -- FX'te trend/kirilim sablonlarinin "
              "neden surekli oldugunu aciklar. Yine baglam, kural degil.",
        tarih="2026-07-11",
        kaynak="liquidity_profiler.py + [[Borsa - Likidite Karakter Haritasi]]",
        anahtarlar=("fx", "eurusd", "gbpusd", "parite", "range"),
    ),
)


def ara(sorgu: str) -> tuple[list[Elenen], list[Yapi]]:
    """Anahtar kelimeye gore katalogda ara. Basit substring -- kasitli."""
    q = sorgu.lower().strip()
    e = [x for x in KATALOG
         if q in x.baslik.lower() or q in x.iddia.lower()
         or any(q in a or a in q for a in x.anahtarlar)]
    y = [x for x in YAPILAR
         if q in x.baslik.lower() or any(q in a or a in q for a in x.anahtarlar)]
    return e, y


def _yaz_elenen(x: Elenen) -> None:
    print(f"\n  [{x.id}]  {x.baslik}")
    print(f"    iddia  : {x.iddia}")
    print(f"    olcum  : {x.olcum}")
    print(f"    neden  : {x.neden}")
    print(f"    kaynak : {x.kaynak}  ({x.tarih})")


def _yaz_yapi(x: Yapi) -> None:
    print(f"\n  {x.baslik}")
    print(f"    olcum  : {x.olcum}")
    print(f"    UYARI  : {x.uyari}")
    print(f"    kaynak : {x.kaynak}  ({x.tarih})")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="Elenenler katalogu (VETO araci)")
    p.add_argument("--kontrol", metavar="TEZ", help="tezini kontrol et")
    p.add_argument("--yapi", action="store_true", help="yapisal bulgular")
    a = p.parse_args()

    if a.kontrol:
        e, y = ara(a.kontrol)
        if not e and not y:
            print(f"\n'{a.kontrol}' katalogda YOK.")
            print("  Bu 'calisir' demek DEGIL -- sadece 'olculmemis' demek.")
            print("  Tezini diskresyoner deftere yaz, curuten alanini doldur.")
            return
        if e:
            print(f"\n{'='*70}\n  ELENMIS -- BU TEZI KULLANMA\n{'='*70}")
            for x in e:
                _yaz_elenen(x)
            print(f"\n  NOT: 'elenmis' TERSI CALISIR demek degil. Bkz modul docstring.")
        if y:
            print(f"\n{'='*70}\n  YAPISAL BULGU (baglam, giris kurali degil)\n{'='*70}")
            for x in y:
                _yaz_yapi(x)
        return

    if a.yapi:
        print(f"\n{'='*70}\n  ELENMEYEN YAPISAL BULGULAR\n{'='*70}")
        for x in YAPILAR:
            _yaz_yapi(x)
        return

    print(f"\n{'='*70}")
    print(f"  ELENENLER KATALOGU -- {len(KATALOG)} madde (donmus liste)")
    print(f"{'='*70}")
    for x in KATALOG:
        _yaz_elenen(x)
    print(f"\n{'='*70}")
    print("  Yapisal bulgular icin: --yapi   |   Tez kontrolu: --kontrol <kelime>")
    print("  'Elenmis' = bunu alma. TERSINI AL demek DEGIL (bkz docstring).")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
