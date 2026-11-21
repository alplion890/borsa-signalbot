"""OLCULMUS FIKIRLER KATALOGU -- donmus liste, statulu.

NE ISE YARAR: diskresyoner seansta, islem acmadan once "benim tezim zaten
olculmus mu, ne cikmis?" sorusunu cevaplar. Sinyal uretmez.

STATU SART (Hermes denetimi 2026-08-29): katalogun hepsi "kullanma" degil.
  rejected            -> olculdu, sonuc fikri eliyor            (VETO)
  standalone_rejected -> tek basina edge degil; baglam olabilir  (veto DEGIL)
  not_adopted         -> pozitif ama kitabin altinda, secilmedi  (veto DEGIL)
  retired             -> uretimden cikarildi                     (VETO)
Ayrica `kapsam` alani, calisan bir modulle isim cakismasini keser: "sweep"
sorgusu calisan SWEEP_CORE'u, "orb" sorgusu emekli NQ_ORB gecmisini yanlis
yorumlayamaz.

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


# ---------------------------------------------------------------------------
# STATU -- hepsi "kullanma" DEGIL (Hermes denetimi 2026-08-29)
#
# Ilk surumde her madde tek basliga giriyordu: "ELENMIS -- BU TEZI KULLANMA".
# Uc kategori hatasi uretiyordu:
#   - Donchian maddesi metninde "elenmis degil" yaziyor ama veto gibi cikiyordu
#   - "tek basina edge degil" (FVG/EMA/VWAP) ile "olcum negatif" ayni sayiliyordu;
#     confluence olarak bakmak ile giris kurali yapmak farkli sorulardir
#   - emekli GOLD ORB, calisan NQ ORB'u da kapsiyormus gibi gorunuyordu
# ---------------------------------------------------------------------------

STATULER: dict[str, tuple[str, str]] = {
    "rejected": ("ELENMIS -- BU TEZI KULLANMA",
                 "Olculdu, sonuc fikri eliyor."),
    "standalone_rejected": ("TEK BASINA EDGE DEGIL -- giris kurali yapma",
                            "Olculdu: yalniz basina PnL uretmiyor. Baska bir "
                            "gerekcenin yaninda BAGLAM olarak bakilabilir; "
                            "tek basina giris sebebi degildir."),
    "not_adopted": ("ADOPTE EDILMEDI -- veto DEGIL",
                    "Olcum pozitif ama mevcut kitabin altinda kaldi. "
                    "Yasak degil; secilmedi."),
    "retired": ("EMEKLI EDILDI -- yeniden acmak icin yeni gerekce gerekir",
                "Uretimden cikarildi; gecmis kayitlar defterde duruyor."),
}


# Hangi statuler VETO -- TEK KAYNAK. Once bu ayrim uc yerde ayri ayri
# hesaplaniyordu (CLI baslik metni, telefon brifingi, testler); ucu ayrisinca
# katalog bir yerde "yasak" oteki yerde "secilmedi" diyebilirdi.
VETO_STATULERI = ("rejected", "retired")


def veto_mu(statu: str) -> bool:
    return statu in VETO_STATULERI


@dataclass(frozen=True)
class Elenen:
    """Olculmus bir fikir ve STATUSU. Her alan bir olcume dayanir."""
    id: str
    statu: str        # STATULER anahtari -- "elenmis" tek bir sey degil
    baslik: str
    iddia: str        # cazip gorunen sey -- neden birinin aklina gelir
    olcum: str        # ne olculdu, hangi sayiyla
    neden: str        # neden bu sayi bu statuyu veriyor
    tarih: str
    kaynak: str
    anahtarlar: tuple[str, ...] = field(default_factory=tuple)
    # Calisan bir modulle isim cakismasi varsa kapsam BURADA daraltilir;
    # yoksa `--kontrol sweep` calisan SWEEP_CORE'u da veto etmis gibi olur.
    kapsam: str = ""

    def __post_init__(self) -> None:
        if self.statu not in STATULER:
            raise ValueError(f"{self.id}: bilinmeyen statu {self.statu!r}")


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
        id="eur_gbp_london_retired", statu="retired",
        baslik="EUR_LONDON_FADE_EMA / GBP_LONDON_STRONG_TREND",
        iddia="Mevcut London kurallari aktif PAPER forward olcumune devam etsin.",
        olcum="EUR 7 Agustos-24 Eylul mevcut config n=14, +3.812R; GBP "
              "29 Eylul birlesik n=23, -8.379R. Uzun tarih EUR/GBP negatiftir.",
        neden="Kullanici seyrek sinyal ve zayif uzun-donem kaniti nedeniyle "
              "2026-09-30'da rafa kaldirdi. EUR forward negatif diye elenmedi.",
        tarih="2026-09-30", kaynak="[[Borsa - EUR GBP London Emeklilik Karari 2026-09-30]]",
        anahtarlar=("EUR_LONDON_FADE_EMA", "GBP_LONDON_STRONG_TREND", "london"),
        kapsam="Yalniz bu iki mekanik London surumu; SWEEP_CORE ve EUR/GBP paritelerini veya "
               "baska diskresyoner tezleri genel olarak veto etmez.",
    ),
    Elenen(
        id="fvg_doldurma",
        statu="standalone_rejected",
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
        kapsam=("Giris kurali olarak. Diskresyoner seansta baska bir gerekcenin "
                "yaninda baglam diye bakmak yasak degil; tek basina tez olamaz."),
    ),
    Elenen(
        id="ema_vwap_sicrama",
        statu="standalone_rejected",
        baslik="EMA20 / EMA50 / VWAP'tan sicrama",
        iddia="Trend yonunde fiyat EMA20'ye veya VWAP'a dusunce sicrar, oradan al.",
        olcum="10 paritenin HEPSI: EMA20 ~%57, EMA50 ~%42, VWAP ~%54 sicrama. "
              "Parite-ozel karakter YOK.",
        neden="Evrensel gurultu. %57 sicrama tek basina edge degil -- honest "
              "engine'de PnL cikmiyor; maliyet dusunce sifira iniyor.",
        tarih="2026-07-11",
        kaynak="liquidity_profiler.py + [[Borsa - Likidite Karakter Haritasi]]",
        anahtarlar=("ema", "ema20", "ema50", "vwap", "sicrama", "bounce", "ortalama"),
        kapsam=("Giris kurali olarak. Confluence/baglam kullanimi ayri soru -- "
                "olculen sey 'tek basina sicrama al' idi."),
    ),
    Elenen(
        id="equal_high_low_raid",
        statu="rejected",
        baslik="Equal high/low avlandiktan sonra donus",
        iddia="Cift tepe/dip alinirsa likidite suprulmustur, fiyat doner.",
        olcum="Raid sonrasi donus orani ~%50, yayilim dusuk.",
        neden="Yazi-tura. Maliyet dusunce negatif.",
        tarih="2026-07-11",
        kaynak="liquidity_profiler.py + [[Borsa - Likidite Karakter Haritasi]]",
        anahtarlar=("equal high", "equal low", "cift tepe", "cift dip", "raid",
                    "likidite", "sweep", "supurme"),
        kapsam=("'raid/sweep DONUSU' tezine dair. Calisan SWEEP_CORE ayri bir sey "
                "olcuyor (NASDAQ 15m, ADX rejimi + VWAP konumu) ve forward "
                "defterinde duruyor -- bu madde onu veto ETMEZ."),
    ),
    Elenen(
        id="ny_londra_surdurme",
        statu="rejected",
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
        statu="rejected",
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
        statu="rejected",
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
        statu="rejected",
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
        statu="rejected",
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
        kapsam=("15-30 dakikalik pencere. Lucca-Moench 24 SAATLIK pencereyi olcer; "
                "o soru burada CURUTULMEDI, sorulmadi bile."),
    ),
    Elenen(
        id="sweep_cok_endeks",
        statu="rejected",
        baslik="SWEEP'i 7 endekse yayarak kari katlamak",
        iddia="Havuz exp_R +0.194 (n=118) -- ayni kurali cok enstrumanda kos, kar katlanir.",
        olcum="Ayni-anda-tek-islem (slot) kisiti uygulaninca exp_R -0.062'ye dusuyor. "
              "2026-11-18 slot KISITSIZ 14y yeniden test (on-kayit cd76805, olculmus Maven maliyeti): "
              "SP500 -0.865R, US30 -0.148, US2000 -0.076, UK100 -0.113, FRA40 -0.205, JAP225 -0.162; "
              "6/6 gecmedi (NQ kontrol 2022+ +0.718 yeniden uretildi).",
        neden="Slot ilk gelen sinyale gidiyor, EN IYI sembole degil. Havuz "
              "ortalamasi bu kisiti saymiyor. Slot kaldirilinca da diger endeksler "
              "14 yilda olculmus maliyetle negatif. Portfoyde degisiklik yapilmadi.",
        tarih="2026-08-14",
        kaynak="portfolio_ab + [[Borsa - Portfoy Kompozisyonu ve Slot Kisiti]]",
        anahtarlar=("sweep", "cok enstruman", "breadth", "genisleme", "portfoy",
                    "slot", "endeks"),
        kapsam=("Veto YALNIZCA 'ayni kurali 7 endekse yay' genislemesine. Tek- "
                "enstruman SWEEP_CORE_AVOID_MID_VWAP portfoyde kaldi; "
                "guncel olcumu sistem durumu bolumundedir."),
    ),
    Elenen(
        id="donchian_xau",
        statu="not_adopted",
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
        kapsam=("XAUUSD 1H turtle kanali. Yasak degil: olculdu, pozitif cikti, "
                "mevcut kitabin altinda kaldigi icin secilmedi."),
    ),
    Elenen(
        id="gold_ny_orb",
        statu="retired",
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
        kapsam=("XAUUSD 5m ORB modulune. NQ_ORB_STRONG_TREND ayri moduldu; "
                "2026-09-11'de negatif forward sonucuyla tarama/Telegram "
                "listesinden cikarildi. 'ORB' kelimesi SWEEP_CORE'u vetolamaz."),
    ),
    Elenen(
        id="ic_bar_bazli",
        statu="rejected",
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
        statu="rejected",
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
    Elenen(
        id="rsiband_supertrend_video",
        statu="rejected",
        baslik="YouTube 'ucretsiz al-sat sistemi': RSI Bands + Supertrend + RSI/TDI, Heikin Ashi",
        iddia="Tum zaman dilimlerinde, kripto ve forexte calisir; HA bant disina sarkar -> "
              "RSI kesisimi -> ilk Supertrend buy/sell, hedef karsi bant (sayi verilmedi).",
        olcum="On-kayitli test, 11 seri (BTC 15m/1h/4h, EUR/GBP/XAU/NQ 15m/1h), 3 yil: "
              "hepsi exp_R<0 (BTC 15m -0.167 n=2001, 1h -0.162, 4h -0.064). "
              "Maliyetsiz bile ~0 (BTC 15m -0.005). WR ~%47-51, ort. kazanc ~0.9R.",
        neden="Sinyal bilgi tasimiyor: maliyet oncesi yazi-tura, maliyet sonrasi net kayip. "
              "Video ornekleri secilmis grafik + broker/sinyal grubu reklami.",
        tarih="2026-11-07",
        kaynak="rsiband_st_video_lab.py + HANDOFF/rsiband_supertrend_video_onkayit_2026-11-07.md "
               "+ [[Borsa - RSI Bands Supertrend Video Testi 2026-11-07]]",
        anahtarlar=("supertrend", "rsi band", "rsi bands", "heikin", "heikin ashi", "tdi",
                    "rsi", "kripton", "youtube", "al-sat sistemi"),
    ),
    Elenen(
        id="mnq_orb_15m_half_r_video",
        statu="rejected",
        baslik="Instagram '$20K/ay' MNQ ORB: 9:15-9:30 NY mumu, 15m kapanis kirilimi, hedef 0.5R",
        iddia="TradingView: 714 islem, WR %72, 2026'da WR %80 PF 2.06; 20 prop hesapla ~$17K/ay.",
        olcum="On-kayitli test, NQ 15m 2021-06..2026-06: n=1288, exp_R -0.079, WR %65.7, "
              "her yil negatif; 2012+ n=3578 exp_R -0.158. Maliyetsiz bile -0.014 "
              "(0.5R'de basabas WR %66.7).",
        neden="Yuksek WR, kucuk hedefin dogal sonucu; basabas WR'nin altinda. "
              "'5 rejim filtresi uret, en iyisini sec' = post-hoc filtre; ayarlar gizli.",
        tarih="2026-11-10",
        kaynak="mnq_orb_video_lab.py + HANDOFF/mnq_orb_15m_halfR_video_onkayit_2026-11-10.md "
               "+ [[Borsa - MNQ ORB 0.5R Video Testi 2026-11-10]]",
        kapsam="Yalniz bu kural: 9:15 NY tek 15m mum araligi + 0.5R hedef + kirilim mumu stopu. "
               "Canli SWEEP_CORE_AVOID_MID_VWAP ve bizim CAND_RT_NQ_ORB ayri kurallardir, "
               "bu madde onlari vetolamaz.",
        anahtarlar=("orb", "opening range", "0.5r", "yarim r", "mnq", "9:15", "theagent",
                    "instagram", "win rate", "20k"),
    ),
    Elenen(
        id="naked_poc_minor_video",
        statu="rejected",
        baslik="Canli yayin 'prop firm sistemi': D-sekilli naked POC'a ilk temas, FX minor (seviye kismi)",
        iddia="Dokunulmamis POC'a ilk temas + sentetik footprint onayi; 1-1.5R'de WR %70-75 (sayi/rapor yok).",
        olcum="On-kayitli test, Maven MT5 M15 2023-01..2026-11, 8 minor: birlesik n=2522, 1.5R exp_R -0.300, "
              "WR %40.6 (abartili varsayim); Maven olculmus maliyetle (spread+kayma) -0.128; maliyetsiz +0.005 "
              "(WR %40.8 = basabas %40). 8/8 parite negatif, iki yari negatif.",
        neden="Seviye tek basina bilgi tasimiyor: maliyetsiz yazi-tura, dar stop yuzunden maliyet sonrasi agir kayip. "
              "Footprint onayi (kapali program, ATAS gecmis veri vermiyor) OLCULEMEDI -- bu madde onu kapsamaz.",
        tarih="2026-11-11",
        kaynak="naked_poc_video_lab.py + HANDOFF/naked_poc_minor_video_onkayit_2026-11-11.md "
               "+ [[Borsa - Naked POC Minor Video Testi 2026-11-11]]",
        kapsam="Yalniz FX minorde gunluk naked POC ilk temas kurali. Canli SWEEP_CORE_AVOID_MID_VWAP "
               "ve diger moduller ayri kurallardir, bu madde onlari vetolamaz.",
        anahtarlar=("poc", "point of control", "naked poc", "volume profile", "hacim profili",
                    "minor", "minör", "ziya", "footprint", "sentetik"),
    ),
    Elenen(
        id="meta_label_regime_filter",
        statu="rejected",
        baslik="Meta-label: kaybeden sinyali giris anindaki piyasa kosuluyla ayiklamak",
        iddia="Edge gecmiste hangi kosulda (oynaklik, hacimli mum, testere, haber gunu, trend) kaybettiyse "
              "o kosulda sinyali gecersek zayif/negatif edge pozitife doner.",
        olcum="On-kayitli, IS 2012-2021 / OOS 2022+, Maven olculmus maliyet. 5 modul x 9 ozellik (atr_rank, "
              "adx, eff20, rel_vol, bar_atr, event_day, hour, gap, with_trend) tek-kural + 5 lojistik model "
              "= 50 hipotez: 0 gecti (Holm p hepsi >=0.55). Hicbir kural IS'te keep exp_R'yi pozitife "
              "cevirmedi. En yakin: SWEEP 'en guclu ADX tercilinde gecme' OOS +1.09 vs +0.72, ham p 0.012, "
              "Holm 0.55.",
        neden="Giris aninda bilinen bu kosullar kaybeden ve kazanan sinyalleri ayirmiyor; ayni grafik "
              "bilgisiyle goz filtresinin de ayirmasi icin dayanak yok. Plansiz haber (savas vb.) olculemedi.",
        tarih="2026-11-16",
        kaynak="meta_label_lab.py + HANDOFF/meta_label_onkayit_2026-11-16.md",
        kapsam="Yalniz bu 9 ozellikle sinyal ayiklama. Modullerin kendisini vetolamaz; SWEEP-ADX ipucu "
               "yeni on-kayitla tek hipotez olarak sinanabilir.",
        anahtarlar=("meta-label", "meta label", "rejim filtresi", "testere", "volatil", "hacimli mum",
                    "haber gunu", "adx filtresi"),
    ),
    Elenen(
        id="baltussen_last30_momentum",
        statu="rejected",
        baslik="Baltussen et al. 2021 son-30-dakika momentumu (rROD) NQ ve XAU",
        iddia="JFE 2021: onceki kapanistan T-30dk getirisinin isaretiyle son 30 dk; 1974-2020 vadelilerde Sharpe 0.87-1.73.",
        olcum="On-kayitli, Dukascopy 5m 2012-2026, Maven olculmus maliyet. NQ n=3639: maliyetsiz +0.75bp "
              "(2022+ -0.39), olculmus -1.46bp/islem, yillik -%3.7. XAU n=3719: maliyetsiz +0.56bp, olculmus "
              "-2.14bp, yillik -%5.4. Iki enstruman da 2022+ maliyetsiz bile negatif.",
        neden="Brut etki CFD spread'inden kucuk ve 2022 sonrasi kaybolmus; gunluk tek 30 dk islem maliyeti tasiyamiyor.",
        tarih="2026-11-17",
        kaynak="last30_momentum.py + HANDOFF/baltussen_son30dk_onkayit_2026-11-17.md",
        kapsam="Yalniz rROD son-30dk kurali, gamma filtresi yok. Canli SWEEP_CORE_AVOID_MID_VWAP, "
               "CAND_EMA12_FIRST5M ve Noise Band ayri kurallardir, bu madde onlari vetolamaz.",
        anahtarlar=("baltussen", "son 30 dakika", "last half hour", "intraday momentum", "rrod", "gamma hedging"),
    ),
    Elenen(
        id="uydu_cushing_petrol",
        statu="rejected",
        baslik="Uydu (Sentinel-2) ile Cushing petrol stoku tahmini -> WTI Pzt-Crs islemi",
        iddia="Video: yuzen cati golgesiyle Cushing stok yonu %63.48 isabet (512 hafta); EIA aciklamasindan once bilinir.",
        olcum="On-kayitli kahin testi 2017-2026, EIA gercek verisi onceden biliniyormus gibi. Naif 'gecen haftanin "
              "yonu' Cushing isabeti %65.9 (videodan yuksek). Kusursuz Cushing bilgisiyle bile WTI Pzt acilis->Crs "
              "kapanis: n513 isabet %51.1, t +0.83 (2020 haric t +0.23). ABD toplam stok kahini t +2.81 ama "
              "2022+ t +0.49, isabet %51.4.",
        neden="Uydu tahmini naif kaliciliktan kotu; ustelik Cushing'i kusursuz bilmek bile fiyat yonu vermiyor. "
              "Toplam stok bilgisi 2022 sonrasi fiyata yansimis gorunuyor. Petrol icin Maven maliyeti olculmedi.",
        tarih="2026-11-17",
        kaynak="HANDOFF/uydu_petrol_kahin_onkayit_2026-11-17.md + scratchpad oil_oracle.py (EIA LeafHandler + Yahoo CL=F)",
        kapsam="Yalniz Cushing stok -> WTI haftalik yon. Canli SWEEP_CORE_AVOID_MID_VWAP ve diger uydu "
               "kullanimlari (tarim NDVI, NO2, dogalgaz hava) bu maddenin disinda.",
        anahtarlar=("uydu", "satellite", "sentinel", "cushing", "petrol stok", "eia", "alternatif veri"),
    ),
    Elenen(
        id="dogalgaz_hava_depolama",
        statu="rejected",
        baslik="Dogalgaz: hava (HDD/CDD) ve depolama surprizi -> UNG/NG haftalik yon",
        iddia="Hava gaz talebini belirler; hava veya depolama onceden bilinirse Persembe EIA raporu oncesi yon alinir.",
        olcum="On-kayitli kahin testi 2011-2026, UNG. Kusursuz haftalik hava bilgisi: t -0.45, isabet %49.1. "
              "Kusursuz depolama surprizi (5 yil ort. gore): +46.7bp/hafta t +2.33 (2022+ t +1.05); isabet naif "
              "duzeye (%64.6) inince ort +13.9bp, 5. yuzdelik -18.4bp. Gercek naif kalicilik (H3): t +0.62, "
              "2022+ ~0, 5bp maliyette ~0.",
        neden="Hava fiyata yansimis; depolama bilgisi yalniz ~%90+ isaret isabetiyle anlamli olur. Yeralti "
              "depolamasi uydudan gorulmez, ucretsiz yoldan bu isabet saglanamiyor. Maliyet olculmedi.",
        tarih="2026-11-17",
        kaynak="HANDOFF/dogalgaz_hava_kahin_onkayit_2026-11-17.md + HANDOFF/dogalgaz_hava_ng_oracle.py",
        kapsam="Yalniz haftalik hava/depolama -> UNG/NG yon. Canli SWEEP_CORE_AVOID_MID_VWAP ve boru hatti "
               "akis verisiyle (EBB) depolama tahmini bu maddenin disinda.",
        anahtarlar=("dogalgaz", "doğalgaz", "natgas", "natural gas", "hdd", "cdd", "derece gun", "depolama",
                    "ung", "hava durumu"),
    ),
    Elenen(
        id="noise_band_sp500_us30_us2000",
        statu="rejected",
        baslik="Noise Band (Zarattini 2024) NQ disi endeksler: SP500, US30, US2000",
        iddia="NQ'da 14 yil gecen Noise Band kurali ayni parametrelerle diger ABD endekslerinde de calisir, islem sayisini artirir.",
        olcum="On-kayitli (6537c91), degistirilmemis simulate, Dukascopy 5m, Maven olculmus maliyet, Bonferroni 3 test. "
              "SP500 2012-26: maliyetsiz +2.37bp/gun CI>0 ama olculmus -0.63bp, NQ ile gunluk korelasyon 0.68, "
              "ayni yon %92. US30 2012-26: maliyetsiz +0.90bp CI 0'i kapsiyor, olculmus -0.02bp, 2022+ -0.79. "
              "US2000 2018-11..2026 (Dukascopy daha eskisi yok): maliyetsiz bile -2.09bp/gun.",
        neden="Brut etki yalniz NQ ve SP500'de; SP500'de olculmus spread siliyor ve NQ'nun kopyasi. US30 zayif, "
              "US2000 ters. Kural ek bagimsiz islem uretmiyor.",
        tarih="2026-11-17",
        kaynak="noise_band_cross.py + HANDOFF/noise_band_capraz_endeks_onkayit_2026-11-17.md",
        kapsam="Yalniz SP500/US30/US2000 Noise Band. NQ Noise Band (14y gecti) ve canli "
               "SWEEP_CORE_AVOID_MID_VWAP bu maddenin disinda.",
        anahtarlar=("noise band sp500", "noise band us30", "noise band us2000", "noise band dow", "noise band russell",
                    "zarattini sp500", "beat the market spy"),
    ),
    Elenen(
        id="ema12_first5m_nq_14y",
        statu="rejected",
        baslik="NQ EMA12 ilk 5 dk (CAND_EMA12_FIRST5M) 14 yil olculmus maliyet",
        iddia="NY 09:30 5m mumu EMA12 ustu/alti -> yon; stop mum araligi, hedef yok, 6 saat. Acilis momentumu.",
        olcum="On-kayitli (5400829), Dukascopy 5m 2012-2026, n=3776, ayda ~21, WR %28. Maliyetsiz +0.138R CI>0; "
              "olculmus merkez +0.036R CI [-0.028, +0.103] (2022+ +0.064); 2x maliyet -0.066R. En uzun kayip "
              "serisi 20. Not: on-kayitli ham sonuc +0.020R, 7 sifir-aralikli veri artefakti mumu (-709R tek islem) "
              "dahil; artefaktsiz satir yukarida.",
        neden="Brut etki var ama medyan stop ~22 puan dar; olculmus spread islem basina ~0.09R yiyor, "
              "geriye anlamli olmayan pozitif kaliyor. Forward n=7 +1.28R kanit degil.",
        tarih="2026-11-17",
        kaynak="ema12_first5m_14y.py + HANDOFF/ema12_ilk5dk_14y_onkayit_2026-11-17.md",
        kapsam="Yalniz bu kuralin LIVE adayligi. Maven sessiz PAPER olcumu kullanici karariyla surer. "
               "Canli SWEEP_CORE_AVOID_MID_VWAP ve NQ Noise Band bu maddenin disinda.",
        anahtarlar=("ema12", "ilk 5 dakika", "first 5m", "first candle", "acilis mumu", "opening momentum"),
    ),
    Elenen(
        id="btc_22utc_2h_long",
        statu="rejected",
        baslik="BTC 22:00 UTC 2 saat long (Quantpedia strateji sayfasi surumu)",
        iddia="Padysak-Vojtko/Quantpedia: 22:00 UTC long, 2 saat; 2015-2022 yillik ~%33.",
        olcum="On-kayitli (04d8fca), Binance 1h 2017-08..2026-11, n=3376, Maven BTCUSD olculmus maliyet. "
              "Maliyetsiz +2.54bp/gun CI 0'i kapsiyor; olculmus -0.56bp, 2022-03+ -2.24bp.",
        neden="Bir saat kaymis pencere (22-24 UTC) etkiyi tasimiyor; ayni on-kayittaki 21-23 UTC surumu ayri degerlendirildi.",
        tarih="2026-11-17",
        kaynak="fx_fix_btc_hours.py + HANDOFF/fx_fix_btc_saat_onkayit_2026-11-17.md",
        kapsam="Yalniz 22:00-00:00 UTC penceresi. 21:00-23:00 UTC (H6), canli SWEEP_CORE_AVOID_MID_VWAP "
               "ve NQ Noise Band bu maddenin disinda.",
        anahtarlar=("btc 22 utc", "bitcoin 22:00", "btc gece saati 22"),
    ),
    Elenen(
        id="fx_fix_reversal_london_tokyo",
        statu="rejected",
        baslik="FX fix donusu: Londra 16:00 ve Tokyo 09:55 oncesi USD long / sonrasi USD short (6 parite sepeti)",
        iddia="Krohn-Mueller-Whelan JF 2024: dolar fix oncesi yukselir, sonrasi duser.",
        olcum="On-kayitli (04d8fca), Dukascopy 5m 2012-2026, n~3860 gun, Maven olculmus maliyet. Londra: maliyetsiz "
              "+0.02/+0.03bp (etki yok), olculmus -0.71bp. Tokyo: maliyetsiz +0.64/+0.55bp CI>0 (etki gercek), "
              "olculmus -0.10/-0.18bp, 2x negatif.",
        neden="Londra 16:00'da 1 saatlik pencerede etki yok; Tokyo'da brut etki var ama sepet maliyeti (~0.7bp gidis-donus) "
              "etkiden buyuk.",
        tarih="2026-11-18",
        kaynak="fx_fix_btc_hours.py + HANDOFF/fx_fix_btc_saat_onkayit_2026-11-17.md",
        kapsam="Yalniz 1 saatlik pre/post pencereler, 6 USD paritesi. Canli SWEEP_CORE_AVOID_MID_VWAP, NQ Noise Band "
               "ve BTC 21-23 UTC bu maddenin disinda.",
        anahtarlar=("fx fix", "wm reuters", "london fix", "tokyo fix", "fix reversal", "usd fix"),
    ),
    Elenen(
        id="gao_itsm_first30_last30",
        statu="rejected",
        baslik="Gun ici zaman serisi momentumu: ilk 30 dk yonu -> son 30 dk (Gao-Han-Li-Zhou), 8 piyasa",
        iddia="Gao-Han-Li-Zhou JFE 2018 + Li-Sakkas-Urquhart JFM 2022 (16 gelismis piyasa): ilk yarim saat "
              "getirisi son yarim saati ongorur.",
        olcum="2026-09-21 (intraday_momentum_research_lab): NQ -0.038R, Gold -0.072R, EUR -0.121R, GBP -0.172R, "
              "tum varyantlar negatif. 2026-11-18 on-kayitli (fe57dc4) ABD disi endeksler, Dukascopy 5m 2012-2026: "
              "maliyetsiz UK100 +0.03bp, FRA40 -0.26bp, JAP225 +0.10bp, GER40 +0.70bp (2022+ +0.10bp); olculmus "
              "UK100 -1.45, FRA40 -2.31, JAP225 -3.05bp. GER40 maliyeti olculmedi.",
        neden="Brut etki 8 piyasanin hicbirinde CFD maliyetini karsilamiyor; GER40 2022+ brut +0.1bp her pozitif "
              "maliyette negatif.",
        tarih="2026-11-18",
        kaynak="kaynak_adaylari.py (A1) + intraday_momentum_research_lab.py + HANDOFF/kaynak_adaylari_onkayit_2026-11-18.md",
        kapsam="Yalniz ilk-30dk isaretiyle son-30dk kurali. Baltussen rROD ayri madde. Canli SWEEP_CORE_AVOID_MID_VWAP, "
               "NQ Noise Band ve CAND_EMA12_FIRST5M bu maddenin disinda.",
        anahtarlar=("itsm", "intraday time series momentum", "ilk 30", "first half hour", "gao han",
                    "son yarim saat", "last half hour"),
    ),
    Elenen(
        id="opex_week_long",
        statu="rejected",
        baslik="Opsiyon vadesi haftasi long (3. Cuma haftasi), SP500 ve NQ",
        iddia="Stivers-Sun JBF 2013: OE haftasi getirisi diger haftalardan yuksek (delta-hedge geri sarma).",
        olcum="On-kayitli (fe57dc4), 2012-2026, n=178 hafta. Olculmus: SP500 +5.7bp/hafta, NQ +13.8bp; AMA diger "
              "haftalar SP500 +29.5, NQ +40.2bp -> OE haftasi farki -20.5 / -24.1bp. 2022+ SP500 -14.6, NQ -22.4bp.",
        neden="OE haftasi diger haftalardan KOTU; gorunen pozitiflik endeks drift'i (baz oran). 2022+ negatif.",
        tarih="2026-11-18",
        kaynak="kaynak_adaylari.py (A2) + HANDOFF/kaynak_adaylari_onkayit_2026-11-18.md",
        kapsam="Yalniz takvim kurali. Canli SWEEP_CORE_AVOID_MID_VWAP, NQ Noise Band ve CAND_EMA12_FIRST5M bu maddenin disinda.",
        anahtarlar=("opex", "option expiration", "opsiyon vadesi", "third friday", "3. cuma", "expiration week"),
    ),
    Elenen(
        id="turn_of_month_plus1",
        statu="rejected",
        baslik="Ay donumu +1 gunu: ayin son gunu kapanis -> ertesi gun kapanis long, SP500 ve NQ",
        iddia="Carchano-Pardo 2011: S&P futures'ta maliyetten sonra kalici tek takvim etkisi.",
        olcum="On-kayitli (fe57dc4), 2012-2026, n=178. Olculmus SP500 +7.6bp (diger gunler +5.0), NQ +14.0bp "
              "(diger +7.0); Bonferroni CI SP500 [-9.7, 24.9], NQ [-7.1, 35.5]. 2022+ SP500 +3.8, NQ +4.2bp.",
        neden="Isaret dogru ve baz orandan iyi ama 178 islemle sifirdan ayrilmiyor; ayda 1 islem kaniti "
              "yillarca hizlandirmaz.",
        tarih="2026-11-18",
        kaynak="kaynak_adaylari.py (A3) + HANDOFF/kaynak_adaylari_onkayit_2026-11-18.md",
        kapsam="Yalniz takvim kurali. Canli SWEEP_CORE_AVOID_MID_VWAP, NQ Noise Band ve CAND_EMA12_FIRST5M bu maddenin disinda.",
        anahtarlar=("turn of month", "turn-of-month", "ay donumu", "tom", "month end", "ay sonu"),
    ),
    Elenen(
        id="btc_nyse_overnight_long",
        statu="rejected",
        baslik="BTC NYSE kapaliyken long (16:00 ET -> sonraki NYSE gunu 10:00 ET)",
        iddia="Quantpedia (Dujava 2024): 2021 sonrasi BTC getirisi gece/hafta sonu seanslarinda.",
        olcum="On-kayitli (fe57dc4), Binance 1h 2017-08..2026-11, n=2319. Olculmus +15.4bp/islem, CI [0.7, 30.5], "
              "2017-21 +23.9 / 2022+ +7.8, 2x +12.3 -> istatistik GECTI. Gunduz 10-16 ET ayni donem negatif. "
              "Ikame sarti: NB0.75 + esit std olcek (0.101x) Maven BNPL 2022+ equity: ihlal %67 (H6 ile %33), "
              "cekim $154 vs $99. Gun ici en kotu -%37 (1x). Swap olculmedi.",
        neden="On-kayitli ikame sarti saglanmadi (Maven funded ihlal H6'nin iki kati); H6 21-23 UTC ile ayni etki "
              "(korelasyon 0.25). Maven swap olcumu (2026-11-18, MT5): BTCUSD swap_mode 6 = -%30/yil, her 00:00 UTC "
              "rollover'da; ortalama 1.45 rollover/islem -> swapli net +3.3bp, CI [-11.4, 18.4], 2022+ -4.4bp: GECMEZ.",
        tarih="2026-11-18",
        kaynak="kaynak_adaylari.py (A4) + HANDOFF/kaynak_adaylari_onkayit_2026-11-18.md",
        kapsam="Yalniz gece/hafta sonu tasiyan BTC long. BTC 21-23 UTC (H6) 00:00 UTC rollover'i gecmedigi icin bu "
               "maddenin disinda. Kripto swap'i belirgin dusuk bir firmada yeniden olculebilir.",
        anahtarlar=("btc overnight", "btc gece", "bitcoin overnight", "nyse kapali", "weekend btc"),
    ),
    Elenen(
        id="seffaf_kaynak_b1_b6",
        statu="rejected",
        baslik="Seffaf kaynak adaylari B1, B3-B6 (NB overlay, MQL5 altin EA'lari, Turtle Soup, Oops)",
        iddia="Akademik/MQL5 CodeBase/Raschke/Williams kaynaklarinda kurali acik stratejiler; "
              "NB'ye 5dk geri cekilme overlay'i girisi iyilestirir.",
        olcum="On-kayit 8db3103 (+560aaa7), 2012-2026, olculmus Maven maliyeti, Bonferroni 0.05/9. bp/islem "
              "maliyetsiz/merkez/2x, CI, <2022/2022+: B1 fark +0.5/+0.5/+0.5 [-0.2,1.2] +0.8/-0.1; "
              "B3 XAU H1 +52.6/+49.9/+47.2 [-26,235] +7.3/+161 (n=228); B4 XAU M30 +4.0/+1.3/-1.4 [-3.3,6.0]; "
              "B5 NQ +4.2 [-16,25], XAU +5.9 [-14,28]; B6 NQ +1.6 [-5.9,9.2], XAU -17.1 [-44,5.7]. 7/7 GECMEDI.",
        neden="Hicbirinde CI alt siniri > 0 degil; B3'un ortalamasi 2022+ altin trendinden geliyor "
              "(<2022 +7.3bp), B4 ve B6 NQ 2x maliyette negatif.",
        tarih="2026-11-18",
        kaynak="seffaf_adaylari.py + HANDOFF/seffaf_kaynak_adaylari_onkayit_2026-11-18.md",
        kapsam="Yalniz on-kayitta sabitlenen parametreler. B2 (BTC Donchian topluluk) ve B7 (IBS NQ) GECTI, "
               "bu maddenin disinda. Canli SWEEP ve NOISE_BAND modulleri (overlay'siz NB) etkilenmez. "
               "Turtle Soup/Oops icin farkli tutma suresi yeni on-kayit ister.",
        anahtarlar=("turtle soup", "williams oops", "oops", "gold trend breakout", "ema trend cross",
                    "pullback overlay", "noise band overlay", "mql5 codebase"),
    ),
    Elenen(
        id="edge5k_c1_c8",
        statu="rejected",
        baslik="Derin tarama adaylari C1-C8 (ay sonu rebalans, tatil oncesi, 3. Cuma settlement, VIX contango, "
               "VIX filtresi NB, kucuk bosluk doldurma, bosluk fade, altin Asya long)",
        iddia="NBER 33554 ay sonu rebalans; Ariel tatil oncesi; Terstegge-Whelan 3. Cuma; VIX vade yapisi; "
              "tradingstats bosluk doldurma; WGC altin Asya saatleri.",
        olcum="On-kayit b3bf8ef, 2012-2026, olculmus Maven maliyeti (2026-11-12), Bonferroni 0.05/16. "
              "bp/islem maliyetsiz/merkez/2x [CI]: C1 SP +20/+17/+14 [-24,60] NQ +11/+9/+7 (11.7/yil, swap'li); "
              "C2 SP +12/+9/+6 [-10,27] NQ +14/+12/+10 (9.3/yil); C3 4 test merkez -3..-5; "
              "C4 SP -1.2 NQ +0.7, sinyalsiz gunler daha iyi (12.8/18.1bp) kosul FAIL; C5 filtre degeri -8.1 "
              "(atlanan NB islemleri karli); C6 NQ -0.6/-2.8/-5.0 [-4.0,-1.6] SP -3.3; C7 NQ -2.6 SP -3.1; "
              "C8 XAU +1.2/-1.5/-4.2. 16/16 GECMEDI.",
        neden="Hicbirinde CI alt siniri > 0 degil. C1/C2 pozitif ama seyrek ve gurultu icinde; gun ici sik "
              "olanlar (C4, C6, C7, C8) maliyet oncesi ~0, sonrasi negatif.",
        tarih="2026-11-20",
        kaynak="edge5k_adaylari.py + HANDOFF/edge5k_adaylari_onkayit_2026-11-20.md",
        kapsam="Yalniz on-kayitta sabitlenen kurallar. C1/C2'nin farkli pencere/enstruman hali yeni on-kayit "
               "ister; sonuca bakip pencere degistirmek yasak.",
        anahtarlar=("ay sonu", "month end", "rebalans", "rebalance", "tatil", "holiday", "pre-holiday",
                    "settlement", "ucuncu cuma", "third friday", "vix", "contango", "backwardation",
                    "gap fill", "bosluk", "gap fade", "asya", "asia", "altin asya"),
    ),
    Elenen(
        id="melvin_prins_month_end_fx",
        statu="rejected",
        baslik="Melvin-Prins ay sonu FX hedge akisi: son gun 15-16 Londra, goreli hisse getirisinin tersi (EUR/GBP/JPY)",
        iddia="Melvin-Prins JFM 2015 (2004-2012): ayin hisse getirisi yabanci > ABD ise yabanci para fix'ten onceki "
              "saatte duser; katsayi -0.0142 (%10 -> 14bp).",
        olcum="On-kayitli (0d6b456), Dukascopy 5m, 164 ay sonu 2013-01..2026-08 (tamami yayin sonrasi), Maven "
              "olculmus maliyet. Sepet bp/ay maliyetsiz +1.22 / merkez +0.79 / 2x +0.36, se 1.26, p 0.27. "
              "Bloklar 1x +3.4/-3.7/+4.1/+0.1. Egim -0.0049 (makalenin ~1/3'u). Kesif K1 (fix sonrasi donus 16:00->"
              "ertesi 12:00) brut +5.0bp se 2.85 n128 -- karar vermez.",
        neden="Yon makaleyle ayni ama etki ~1/3'e inmis, gurultu icinde; 2018-21 negatif.",
        tarih="2026-11-21",
        kaynak="HANDOFF/scripts_2026-11-21/melvin_prins.py + HANDOFF/melvin_prins_onkayit_2026-11-21.md",
        kapsam="Yalniz on-kayitli 15-16 penceresi ve isaret kurali. K1 fix sonrasi donus test EDILMEDI (kesif); "
               "ayni veride sonuca bakip ana teste cevirmek post-hoc olur, yalniz forward PAPER ile sinanabilir. "
               "Canli SWEEP_CORE_AVOID_MID_VWAP, NQ Noise Band ve BTC 21-23 UTC bu maddenin disinda.",
        anahtarlar=("melvin", "prins", "ay sonu fx", "month end fx", "hedge akisi", "equity hedging",
                    "london fix", "wm fix"),
    ),
    Elenen(
        id="futures_cost_retest_nb_es_ema12",
        statu="rejected",
        baslik="CFD maliyetine yenilen NB ES ve EMA12 NQ'yu CME vadeli maliyetiyle yeniden yargilamak",
        iddia="Futures (MES/MNQ) maliyeti CFD'nin ~1/5'i; brut pozitif bu iki kural vadelide gecer.",
        olcum="On-kayitli (57bf0ba), Databento CME 1m 2012-2026, olculmus bbo-1m spread + $0.61/yon komisyon, puan "
              "olarak gecmise tasindi. NB ES merkez +0.88bp/gun Bonf CI [-0.49,+2.26], 2x -0.81. EMA12 NQ merkez "
              "+0.032R CI [-0.044,+0.105], 2012-21 -0.006, 2x -0.052. 2010-11 gorulmemis: NB ES +0.82, EMA12 -0.199R.",
        neden="Puan maliyeti sabit; dusuk fiyatli eski yillarda oransal maliyet yuksek. Iki kural da merkezde CI 0'i "
              "kapsiyor, 2x negatif. 2022+ pozitif dilim post-hoc, karar vermez.",
        tarih="2026-11-21",
        kaynak="HANDOFF/scripts_2026-11-21/futures_cost_retest.py + HANDOFF/futures_maliyet_onkayit_2026-11-21.md",
        kapsam="Yalniz NB ES ve EMA12 NQ'nun vadeli maliyetiyle 2012-2026 testi. NQ Noise Band (CME'de de gecti, "
               "2010-11 negatif) ve canli SWEEP_CORE_AVOID_MID_VWAP, BTC 21-23 UTC bu maddenin disinda.",
        anahtarlar=("futures", "vadeli", "mes", "mnq", "cme maliyet", "futures maliyet", "noise band es",
                    "ema12 futures"),
    ),
    Elenen(
        id="futures_transfer_baltussen_oops",
        statu="rejected",
        baslik="Baltussen son 30 dk ve Williams Oops'u CME vadeli maliyetiyle yeniden yargilamak",
        iddia="CFD maliyetine yenilen bu kurallar futures maliyetiyle pozitif kalir.",
        olcum="On-kayitli (4f78b05), Databento CME 2012-2026, olculmus futures maliyeti. bp/islem merkez: Baltussen NQ "
              "-1.26, ES -1.15 (maliyetsiz +0.46/+0.65); Oops NQ +2.84 CI [-4.15,+9.72] 2010-11 -14.6; Oops ES -0.38.",
        neden="Baltussen brut etkisi futures maliyetinden de kucuk; Oops CI 0'i kapsiyor ve gorulmemis dilimde negatif.",
        tarih="2026-11-21",
        kaynak="HANDOFF/scripts_2026-11-21/futures_transfer_retest.py + HANDOFF/futures_tasima_onkayit_2026-11-21.md",
        kapsam="Yalniz Baltussen son 30 dk (NQ/ES) ve Williams Oops (NQ/ES) futures testi. IBS (B7) NQ/ES, NQ Noise "
               "Band ve canli SWEEP_CORE_AVOID_MID_VWAP, BTC 21-23 UTC bu maddenin disinda.",
        anahtarlar=("baltussen futures", "oops futures", "williams oops", "son 30 dk futures", "futures tasima"),
    ),
    Elenen(
        id="futures_transfer3_sweep_donchian",
        statu="rejected",
        baslik="Sweep NQ, Donchian GC N=20 ve Sweep RTY'yi CME vadeli maliyetiyle yeniden yargilamak",
        iddia="CFD'de maliyetsiz pozitif bu uc kural futures maliyetiyle gecer.",
        olcum="On-kayitli (d4efb82, EK 46233b2), Databento CME, olculmus bbo-1m + $0.61. R/islem merkez: Sweep NQ "
              "-0.162 (n146, CI [-0.555,+0.270], 2012-21 -0.509); Donchian GC +0.008 (n849, CI [-0.100,+0.112]); "
              "Sweep RTY +0.221 (n81, CI [-0.370,+0.850], 2017-21 -0.145). Ucu de 2x'te <=0 ya da yarida negatif.",
        neden="Brut etki zaten ~0 (Sweep NQ maliyetsiz -0.004R) veya CI cok genis; 2022+ pozitifligi tek basina karar "
              "vermez (post-hoc). Sweep tetigi feed-hassas: CME 15m 146 islem, Dukascopy 237.",
        tarih="2026-11-22",
        kaynak="HANDOFF/scripts_2026-11-21/futures_transfer3.py + HANDOFF/futures_tasima3_onkayit_2026-11-21.md",
        kapsam="Yalniz bu uc kuralin futures tasima testi. Canli SWEEP_CORE_AVOID_MID_VWAP (CFD, LIVE taahhudu ayri "
               "sayilir), NQ Noise Band, BTC 21-23 UTC ve IBS bu maddenin disinda.",
        anahtarlar=("sweep futures", "sweep nq futures", "donchian gc", "donchian futures", "sweep rty", "m2k", "mgc"),
    ),
    Elenen(
        id="futures_volume_rules_carry",
        statu="rejected",
        baslik="Gercek hacim kurallari (B1 yuksek hacim devami, B2 dusuk hacim donusu) ve sinif ici carry (A1)",
        iddia="CME gercek hacmi gun ici yon bilgisi tasir; vade yapisi carry'si 23 vadelide getiri verir.",
        olcum="On-kayitli (4348418, EK 46233b2), Bonferroni 5. bp/islem merkez: B1 NQ -1.50, B1 ES -2.06, B2 NQ "
              "+2.14 CI [-3.1,+7.7] 2012-21 -0.79, B2 ES +2.67 CI [-1.5,+7.3] 2012-21 -0.01. A1 carry aylik "
              "-7.6bp (SR -0.24, maliyet olculmedi: 1 tick alt sinir); 2012-21 -17.0bp.",
        neden="Hicbiri merkezde CI alt siniri >0 degil; B2 pozitifligi yalniz 2022+ dilimde, 2010-11 negatif. Carry "
              "maliyetsiz bile ~0.",
        tarih="2026-11-22",
        kaynak="HANDOFF/scripts_2026-11-21/futures_round4.py + HANDOFF/futures_hacim_carry_onkayit_2026-11-21.md",
        kapsam="Yalniz B1/B2 (NQ/ES, RTH) ve A1 carry (23 kok, v.0/v.1). Order flow (CVD, OFI, footprint) test "
               "edilmedi; canli SWEEP_CORE_AVOID_MID_VWAP, NQ Noise Band, BTC 21-23 UTC bu maddenin disinda.",
        anahtarlar=("rvol", "gercek hacim", "hacim soku", "volume shock", "carry", "vade yapisi", "term structure",
                    "kmpv"),
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
    print(f"    statu  : {x.statu}")
    print(f"    iddia  : {x.iddia}")
    print(f"    olcum  : {x.olcum}")
    print(f"    neden  : {x.neden}")
    if x.kapsam:
        print(f"    KAPSAM : {x.kapsam}")
    print(f"    kaynak : {x.kaynak}  ({x.tarih})")


def _gruplu_yaz(maddeler: list[Elenen]) -> None:
    """Statuye gore ayri baslik.

    Hepsini tek "KULLANMA" basligi altina koymak kategori hatasiydi: olcumu
    negatif cikan fikirle, olculup secilmeyen fikri ayni sey yapiyordu.
    """
    for statu, (baslik, aciklama) in STATULER.items():
        grup = [x for x in maddeler if x.statu == statu]
        if not grup:
            continue
        etiket = "VETO" if veto_mu(statu) else "veto DEGIL"
        print(f"\n{'='*70}\n  {baslik}  ({etiket})\n  {aciklama}\n{'='*70}")
        for x in grup:
            _yaz_elenen(x)


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
    p = argparse.ArgumentParser(description="Olculmus fikirler katalogu (statulu)")
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
            _gruplu_yaz(e)
            print("\n  NOT: statuye BAK -- hepsi veto degil. Veto yalniz "
                  "rejected/retired.")
            print("  NOT: hicbir madde TERSINI AL demez (bkz modul docstring).")
            print("  NOT: KAPSAM satiri varsa oku -- isim benzerligi calisan "
                  "modulu vetolamaz.")
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
    print(f"  OLCULMUS FIKIRLER KATALOGU -- {len(KATALOG)} madde (donmus liste)")
    sayim = {k: sum(1 for x in KATALOG if x.statu == k) for k in STATULER}
    print("  " + "   ".join(f"{k}:{v}" for k, v in sayim.items() if v))
    print(f"{'='*70}")
    _gruplu_yaz(list(KATALOG))
    print(f"\n{'='*70}")
    print("  Yapisal bulgular icin: --yapi   |   Tez kontrolu: --kontrol <kelime>")
    print("  Veto YALNIZ rejected/retired. Digerleri 'secilmedi' der, 'yasak' degil.")
    print("  Hicbir madde TERSINI AL demez (bkz docstring).")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
