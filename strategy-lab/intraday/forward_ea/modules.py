"""Canli sinyal ureticileri.

Her LiveModule: en son KAPANMIS bar uzerinde sinyal var mi diye bakar; varsa
(dir, entry, sl, tp) doner. Backtest sinyal mantigini birebir kullanir (ayni
fonksiyonlar), sadece "son bar"a uygular.

Ilk somut modul: Gold NY-ORB (temiz + MT5'te mevcut). Digerleri (NQ sweep, EUR
London, ES div) ayni protokolle eklenir — README'ye bak.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from ..config import INSTRUMENTS, ATR_LEN
from ..edge_lab import _adx
from ..indicators import atr
from ..internet_seed_strategies import ORBCase, LondonCase, _build_orb, _build_london


@dataclass(frozen=True)
class Signal:
    direction: int
    entry: float
    sl: float
    tp: float


@dataclass(frozen=True)
class LiveModule:
    name: str
    symbol_key: str          # mt5_io sembol anahtari (XAUUSD, NASDAQ100...)
    tf: str                  # "5m" | "15m"
    weight: float
    max_hold_bars: int
    detect: Callable[[pd.DataFrame], Signal | None]

    @property
    def cost_per_side(self) -> float:
        return INSTRUMENTS[self.symbol_key].cost_per_side


def _dual_thrust_detector(k: float = 0.3, n_days: int = 2, rr: float = 1.5,
                          adx_min: float = 30.0, max_hold: int = 48):
    """Dual Thrust range tanimiyla NQ ORB (ADAY -- kanitlanmadi).

    NQ_ORB ile ayni seans/SL mantigi/RR/hold/ADX filtresi; sadece tetik
    seviyesi farkli: seans acilisi +- k * max(HH-LC, HC-LL) (onceki n_days gun).
    Backtest A/B (intraday/dual_thrust_ab.py, 3 yil): 205 islem, exp_R +0.122,
    4/4 yil pozitif (baseline ORB15: +0.099, 3/4 yil). DSR 0.895 -- 0.95
    esigini GECMEDI, fark bootstrap'ta anlamsiz (%95 GA [-0.132, +0.178]).
    Bu yuzden aday: forward'da bagimsiz veri toplanacak.
    """
    from ..dual_thrust_ab import build_dual_thrust

    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 200:
            return None
        try:
            le, se, lsl, ltp, ssl, stp = build_dual_thrust(df, k, n_days, rr, max_hold)
        except Exception:
            return None
        i = -1
        if adx_min > 0 and not (_adx(df, 14).iloc[i] > adx_min):
            return None
        if bool(le.iloc[i]) and np.isfinite(lsl.iloc[i]) and np.isfinite(ltp.iloc[i]):
            return Signal(1, float(df["close"].iloc[i]), float(lsl.iloc[i]), float(ltp.iloc[i]))
        if bool(se.iloc[i]) and np.isfinite(ssl.iloc[i]) and np.isfinite(stp.iloc[i]):
            return Signal(-1, float(df["close"].iloc[i]), float(ssl.iloc[i]), float(stp.iloc[i]))
        return None

    return detect


def _orb_detector(case: ORBCase, adx_min: float):
    """Genel ORB dedektoru (NQ/Gold). adx_min: rejim filtresi (0=filtre yok)."""
    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 200:
            return None
        le, se, lsl, ltp, ssl, stp = _build_orb(df, case)
        i = -1
        if adx_min > 0 and not (_adx(df, 14).iloc[i] > adx_min):
            return None
        if bool(le.iloc[i]):
            return Signal(1, float(df["close"].iloc[i]), float(lsl.iloc[i]), float(ltp.iloc[i]))
        if bool(se.iloc[i]):
            return Signal(-1, float(df["close"].iloc[i]), float(ssl.iloc[i]), float(stp.iloc[i]))
        return None
    return detect


def _london_detector(case: LondonCase, adx_min: float = 0.0,
                     adx_max: float = 0.0, dow: int | None = None,
                     range_regime: str | None = None):
    """Genel London breakout dedektoru (EUR/GBP).

    Filtreler final ledger'dan birebir geri cikarildi:
      EUR: adx<20 (chop) + Persembe (dow=3)
      GBP: Persembe (dow=3) + ema (case icinde)
    """
    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 200:
            return None
        le, se, lsl, ltp, ssl, stp = _build_london(df, case)
        i = -1
        if dow is not None and df.index[i].dayofweek != dow:
            return None
        if range_regime is not None:
            h = df.index.hour + df.index.minute / 60.0
            in_range = (h >= case.range_start) & (h < case.range_end)
            daily_hi = df["high"].where(in_range).groupby(df.index.date).transform("max")
            daily_lo = df["low"].where(in_range).groupby(df.index.date).transform("min")
            range_pct = (daily_hi - daily_lo) / df["close"]
            daily_range = range_pct.groupby(df.index.date).last()
            rank = daily_range.rolling(20, min_periods=10).rank(pct=True).iloc[-1]
            current_regime = (
                "tight_range" if rank <= 0.33
                else "normal_range" if rank <= 0.67
                else "wide_range"
            )
            if pd.isna(rank) or current_regime != range_regime:
                return None
        adx_val = _adx(df, 14).iloc[i]
        if adx_min > 0 and not (adx_val > adx_min):
            return None
        if adx_max > 0 and not (adx_val < adx_max):
            return None
        if bool(le.iloc[i]):
            return Signal(1, float(df["close"].iloc[i]), float(lsl.iloc[i]), float(ltp.iloc[i]))
        if bool(se.iloc[i]):
            return Signal(-1, float(df["close"].iloc[i]), float(ssl.iloc[i]), float(stp.iloc[i]))
        return None
    return detect


def _sweep_core_detector(adx_thresh: float = 25.0, min_rr: float = 2.0,
                         skip_wednesday: bool = True):
    """NQ sweep core canli dedektoru (geri yuklenen adx_lab ile birebir).

    VWAP trend + ADX>thresh + likidite sweep. TP swing seviyesi; RR ATR rejimine
    gore caplenir (low<0.33:4, mid<0.67:6, high:8). min_rr alti setup atlanir.

    ISIM UYARISI (2026-08-02): Modul adi "SWEEP_CORE_AVOID_MID_VWAP" ama bu
    dedektor mid-VWAP filtresini UYGULAMAZ ve uygulamamalidir. Isim tarihsel;
    veri surekliligi bozulmasin diye degistirilmedi (mevcut forward islemleri
    o ad altinda kayitli).

    Filtre neden UYGULANMIYOR -- taze veriyle test edildi (US100, 6 ay MT5 15m):
        filtresiz (bu dedektor)      n=19  exp_R +1.445
        filtreli (orijinal esikler)  n=13  exp_R +0.948
        filtreli (yeniden terzil)    n=14  exp_R +0.618
    Filtre performansi DUSURUYOR. Sebep: kova bazinda bakildiginda orijinal
    39-islemlik ornekte mid_vwap en kotu kovaydi (+0.332 vs near +1.031); taze
    veride TERSINE dondu (mid +2.013 vs near +0.696). Yani "ortayi at, iki ucu
    tut" deseninin yapisal bir hikayesi yok -- kucuk ornekte olusan gurultuydu
    ve isaret degistirdi. Klasik overfit.

    CARSAMBA FILTRESI (skip_wednesday) -- OLCULDU 2026-08-05, ETKISI IHMAL EDILEBILIR.
    `quality_11` taramasindan gelen "Carsamba kesin kapali" kuralinin bagimsiz
    bir gerekcesi yok (bkz EUR/GBP `dow=3` ile ayni post-hoc kalip), o yuzden
    maliyeti olculdu: US100 15m, 16.1 hafta, filtresiz dedektor, gun dagilimi
        Pzt 5 | Sal 2 | Car 1 | Per 2 | Cum 2 | Paz 1   (toplam 13)
    Yani filtre 13 sinyalin sadece 1'ini kesiyor (%8):
        filtreli 0.74/hafta   vs   filtresiz 0.81/hafta
    Sweep zaten Carsamba gunleri nadiren tetikleniyor -- yasak pratikte bos.

    Karar: varsayilan True BIRAKILDI. Gerekce ilkesel degil pratik --
    SWEEP_CORE'un 9 forward islemi (+10.86R, portfoyun neredeyse tum kari)
    bu filtreyle toplandi; %8'lik bir hacim icin canli modulu degistirip
    defteri karistirmaya degmez.
    A/B adayi (CAND_SWEEP_ALLDAYS) KURULMADI ve kurulmamali: 16 haftada tek
    bir Carsamba sinyali farkiyla test yillarca sonuclanmaz. Olculemeyecek bir
    seyi "olcuyoruz" diye tutmak gold `atr_max_rank` filtresindeki hatanin
    aynisi olur (gold ATR filtresi modulu fiilen kapatti, kimse fark etmedi;
    bkz `intraday.elenenler` id=gold_ny_orb). Soru burada KAPANDI; yeniden acmak icin yeni gerekce gerekir.
    """
    from ..adx_lab import _make_signals  # geri yuklendi

    def detect(df: pd.DataFrame) -> Signal | None:
        if len(df) < 520:
            return None
        if skip_wednesday and df.index[-1].dayofweek == 2:
            return None
        le, se, lsl, ltp, ssl, stp, a = _make_signals(df, adx_thresh)
        i = -1
        atr_pct = (a / df["close"])
        rank = atr_pct.rolling(500, min_periods=100).rank(pct=True).iloc[i]
        if pd.isna(rank):
            return None
        max_rr = 4.0 if rank < 0.33 else (6.0 if rank < 0.67 else 8.0)

        if bool(le.iloc[i]):
            entry = float(df["close"].iloc[i]); sl = float(lsl.iloc[i]); tp = float(ltp.iloc[i])
            risk = entry - sl
            if risk <= 0:
                return None
            rr = (tp - entry) / risk
            if rr < min_rr:
                return None
            tp = entry + min(rr, max_rr) * risk
            return Signal(1, entry, sl, tp)
        if bool(se.iloc[i]):
            entry = float(df["close"].iloc[i]); sl = float(ssl.iloc[i]); tp = float(stp.iloc[i])
            risk = sl - entry
            if risk <= 0:
                return None
            rr = (entry - tp) / risk
            if rr < min_rr:
                return None
            tp = entry - min(rr, max_rr) * risk
            return Signal(-1, entry, sl, tp)
        return None

    return detect


def default_modules() -> list[LiveModule]:
    """Telefona sinyal ureten moduller (mekanik ray).

    Bu liste tier DEGILDIR: LIVE/PAPER ayrimi `signalbot/risk.py`'de tutulur,
    burasi yalnizca "hangi modul taranir ve bildirilir" sorusunu cevaplar.

    GUNCEL (2026-08-28): NQ_ORB, SWEEP_CORE, EUR_LONDON, GBP_LONDON.
    Kume `test_module_parity.test_final_module_count_and_weights` ile kilitli;
    degistiren once gerekce yazar.

    GOLD_NY_ORB_TREND EMEKLI (asagida gerekce). Eski docstring "Gold + NQ ORB"
    diyordu ve EUR/GBP'yi "devre disi" olarak anlatiyordu -- ikisi de artik
    yanlis: EUR/GBP 2026-08-05'te devreye alindi, GOLD 2026-08-28'de cikti.
    """
    nq_orb = ORBCase("NASDAQ100", 14.5, 15, 20.5, "retest", "none", 1.5, "other_side", 1.0, 48)
    return [
        # GOLD_NY_ORB_TREND EMEKLI EDILDI 2026-08-28 (kullanici karari).
        #   forward exp_R -0.411, n=9, t=-2.05 -> defterdeki tek |t|>2 sonuc
        #   ve negatif tarafta; ayrica 2026-07-09'dan beri SIFIR sinyal, cunku
        #   ATR filtresi kurulumlarin ~%88'ini kesiyor. Yani modul 50 gundur ne
        #   dogrulanabilir ne curutulebilir durumdaydi -- PAPER oldugu icin para
        #   riski yoktu ama atesledigi anda telefona sinyal olarak dusuyordu.
        #   Gecmis 9 satir defterde adiyla duruyor. Geri donus: ATR filtresi
        #   yeniden gerekcelendirilir ve CAND_ katmaninda olculur.
        #   Kilit: test_live_whitelist.test_GOLD_artik_default_modules_de_DEGIL
        LiveModule("NQ_ORB_STRONG_TREND", "NASDAQ100", "5m", 1.0, 48,
                   _orb_detector(nq_orb, adx_min=28.0)),
        LiveModule("SWEEP_CORE_AVOID_MID_VWAP", "NASDAQ100", "15m", 1.0, 480,
                   _sweep_core_detector()),
        # PERSEMBE (dow=3) FILTRESI KALDIRILDI 2026-08-05.
        # Gerekce: filtre bu dosyanin kendi yorumunda "final ledger'dan birebir
        # geri cikarildi" diye yaziyordu -- yani sonuca bakilip secilmis, klasik
        # post-hoc cherry-pick. Londra acilisinin Persembe gunu farkli calismasi
        # icin mikroyapisal bir sebep yok.
        # Olculdu (MT5, production penceresi 40g, 2026-08-05):
        #   EUR canli (adx<18 + Persembe)  0 sinyal/hafta
        #   EUR Persembe yok               1.75 sinyal/hafta
        #   GBP canli (Persembe + rejim)   0 sinyal/hafta
        #   GBP Persembe yok (rejim var)   1.75 sinyal/hafta
        # Filtre modulleri fiilen KAPATMISTI: EUR'un 2 forward islemi de ayni
        # gunde, GBP 6 haftadir sessizdi. Silinen veri yok (n=2 ve n=3 zaten
        # hicbir sey kanitlamiyordu), o yuzden aday katmani yerine dogrudan
        # kaldirildi. adx/rejim filtreleri KORUNDU -- onlarin rejim gerekcesi var.
        LiveModule("EUR_LONDON_FADE_EMA", "EURUSD", "5m", 1.0, 48,
                   _london_detector(
                       LondonCase("EURUSD", 2.0, 7.0, 11.0, "none", 1.5, "other_side", 1.0, 48),
                       adx_max=18.0)),
        LiveModule("GBP_LONDON_STRONG_TREND", "GBPUSD", "5m", 0.25, 48,
                   _london_detector(
                       LondonCase("GBPUSD", 0.0, 7.0, 11.0, "ema", 1.5, "other_side", 1.0, 48),
                       range_regime="normal_range")),
        # SWEEP_ES_DIV (w=2.0) KALDIRILDI 2026-07-04: forward test edge'i cürüttü.
        # Backtest avg_loss -0.09R fiziksel olarak sahte (igne-ince stop = sweep dibi
        # -0.25*ATR, ~7-13 puan; temiz dukascopy verisinde hic tetiklenmemis, timeout'ta
        # basabas kapanmis). Canli US100 CFD gürültüsünde ayni stop'lar aninda vuruluyor:
        # forward 10 islem, %20 win, -0.33R (backtest 19 islem, %47, +0.21R iddiasina karsi).
        # 19 islemlik örneklem zaten hic saglam degildi. En yüksek agirlik = en tehlikeli.
    ]


def _btc_absorption_detector():
    """BTCUSDT 1H CVD absorption dedektoru (signalbot ile AYNI kod).

    Ayri bir kopya YAZILMADI bilerek: signalbot Telegram'a bunu gonderiyor,
    forward ayni seyi olcmeli. Kopyalansaydi ikisi zamanla ayrisir ve olcum
    gonderilen sinyali temsil etmezdi.
    """
    from ..signalbot.btc_absorption import detect
    return detect


def candidate_modules() -> list[LiveModule]:
    """ADAYLAR: forward'da olculur, Telegram'a CIKMAZ.

    Neden ayri liste: `default_modules()` hem forward EA hem signalbot tarafindan
    kullaniliyor. Kanitlanmamis bir aday oraya konursa kullanicinin telefonuna
    sinyal duser. Aday once burada bagimsiz veri biriktirir; PSR/DSR yeterli
    olunca ELLE default_modules()'e tasinir.

    Isim onu `CAND_` ile baslar -> defterde bir bakista ayirt edilir.
    Agirlik 0.0: portfoy R'sine katilmaz, sadece kendi kaydini tutar.
    """
    sp500_orb = ORBCase("SP500", 14.5, 15, 20.5, "retest", "none", 1.5, "other_side", 1.0, 48)
    return [
        LiveModule("CAND_NQ_DUAL_THRUST", "NASDAQ100", "5m", 0.0, 48,
                   _dual_thrust_detector(k=0.3, n_days=2, rr=1.5, adx_min=30.0)),
        # NQ_ORB config'inin BIREBIR AYNISI, sadece sembol SP500 (broker: US500).
        # Amac iki katli: (a) forward veri hizini ~2x artirmak, (b) "ORB mantigi
        # endekslerde genellenebilir mi" hipotezini bagimsiz olarak sinamak.
        # Backtest (orb_cross_symbol.py, 3 yil): 270 islem, exp_R +0.031, 2/4 yil
        # pozitif -- NQ'dan (+0.099, 3/4) ZAYIF ama pozitif. Havuzlanmis NQ+SP500:
        # 556 islem, +0.066, PSR 0.925. Endeks disi sembollerde (XAU/XAG/EUR/GBP)
        # ayni config NEGATIF -- likidite profilerinin yapisal tezini dogruluyor.
        # US100 ile korelasyon yuksek: 2 islem != 2 bagimsiz kanit.
        LiveModule("CAND_SP500_ORB", "SP500", "5m", 0.0, 48,
                   _orb_detector(sp500_orb, adx_min=30.0)),
        # SWEEP_CORE'u diger ABD endekslerine yay (multi_index_lab.py, 6 ay MT5 M5).
        # Onceden yazilan karar kurali "HAVUZ exp_R>0 ve PSR>=0.80" idi; sweep
        # havuzu 60 islem, exp_R +0.423, PSR 0.929 ile GECTI -> ekleniyor.
        #
        # DURUST NUANS: havuzu tek basina NASDAQ tasiyor (US100 n=19 exp_R +1.379;
        # US500 +0.036, US30 +0.049, US2000 -0.141). Yani bu ekleme "sweep tum
        # endekslerde calisiyor" demek DEGIL. Amac tam tersini sinamak: sweep
        # NASDAQ'a mi ozgu, yoksa endeks geneli mi? Uc sembol de duz cikarsa
        # sweep'in NASDAQ mikroyapisina bagli oldugu kanitlanir.
        # Olcum icin eklendi, TICARET icin degil. weight=0.0, Telegram'a cikmaz.
        LiveModule("CAND_SWEEP_SP500", "SP500", "15m", 0.0, 480, _sweep_core_detector()),
        LiveModule("CAND_SWEEP_US30", "US30", "15m", 0.0, 480, _sweep_core_detector()),
        LiveModule("CAND_SWEEP_US2000", "US2000", "15m", 0.0, 480, _sweep_core_detector()),
        # 16 endeks taramasi (2026-08-03): ham havuz NEGATIF (-0.101, PSR 0.281),
        # yani "sweep her endekste calisir" YANLIS. Ama guclu bir mekanik oruntu
        # var: korelasyon(spread, exp_R) = -0.731.
        #   spread<2.5 bps (6 sembol): n=108 exp_R +0.345 PSR 0.953
        #   spread>=5.0 bps (6 sembol): n= 56 exp_R -1.024 PF 0.37
        # Bu, AVOID_MID_VWAP gibi uydurma bir filtre DEGIL: spread her islemden
        # dusulen bilinen bir maliyet, yonu sonucu gormeden tahmin edilebilirdi.
        # Esik de kritik degil (2.5/3.5/5.0 hepsi +0.29..+0.35 veriyor).
        #
        # Dusuk-maliyet grubunun TAMAMI ekleniyor -- UK100 tek basina negatif
        # (-0.733) ama onu ayiklamak sonuca bakip secmek olurdu (tam da
        # kacindigimiz sey). Karar kurali GRUP icindi, grup gecti.
        #
        # Amac CHALLENGE degil FUNDED: %20 tutarlilik kurali kari gunlere
        # yaymayi zorunlu kiliyor (NASDAQ tek: ~29 hafta, cok endeks: ~12 hafta).
        LiveModule("CAND_SWEEP_UK100", "UK100", "15m", 0.0, 480, _sweep_core_detector()),
        LiveModule("CAND_SWEEP_FRA40", "FRA40", "15m", 0.0, 480, _sweep_core_detector()),
        LiveModule("CAND_SWEEP_JAP225", "JAP225", "15m", 0.0, 480, _sweep_core_detector()),
        # NOT: CAND_SWEEP_ALLDAYS (Carsamba filtresiz sweep) bilerek EKLENMEDI.
        # Olculdu: filtre 16 haftada 13 sinyalin 1'ini kesiyor (%8), yani A/B
        # yillarca sonuclanmaz. Detay ve karar: _sweep_core_detector docstring.
        #
        # BTC (2026-08-06): signalbot bunu Telegram'a gonderiyordu ama forward
        # defterinde SIFIR kaydi vardi -- olculmeden telefona dusuyordu.
        # Backtest fena degil (138 islem, exp_R +0.073, PF 1.098, PSR 0.694) --
        # NQ_ORB'un forward'iyla (+0.067) ayni seviyede, yani "kotu" degil
        # "dogrulanmamis". Cozum silmek degil OLCMEK: aday olarak forward'a
        # kondu (weight=0.0, Telegram'a cikmaz), veri Binance'ten gelir.
        # NOT: signalbot HALA BTC'yi Telegram'a gonderiyor (ayri kod yolu,
        # _load_modules). Yeterli forward ornegi birikene kadar o sinyallere
        # islem acilmamali.
        # symbol_key "BTCUSDT" (INSTRUMENTS'taki anahtar). "BTC" YAZMA:
        # signalbot kendi sembol tablosunu kullandigi icin orada "BTC" gecerli,
        # ama forward EA maliyeti INSTRUMENTS'tan okur -> "BTC" KeyError verir
        # ve sinyal sessizce dusar (dedektor 4.6 sinyal/hafta uretirken defter
        # bos kalir). Feed yonlendirmesi de bu anahtara bakar.
        LiveModule("CAND_BTC_ABSORPTION", "BTCUSDT", "1H", 0.0, 96,
                   _btc_absorption_detector()),
    ]


def forward_test_modules() -> list[LiveModule]:
    """Forward EA'nin kosturdugu tam liste: canli portfoy + adaylar."""
    return [*default_modules(), *candidate_modules()]


def experimental_modules() -> list[LiveModule]:
    """Henuz dogrulanmamis moduller — forward test esleme sorunu gosterdi.

    Bunlari devreye almak icin backtest modulunun TAM config'i (filtre/rejim)
    pinlenmeli. Su an canli portfoye DAHIL DEGIL.
    """
    eur_london = LondonCase("EURUSD", 2.0, 7.0, 11.0, "none", 1.5, "other_side", 1.0, 48)
    gbp_london = LondonCase("GBPUSD", 0.0, 7.0, 11.0, "ema", 1.5, "other_side", 1.0, 48)
    return [
        LiveModule("EUR_LONDON_FADE_EMA", "EURUSD", "5m", 1.0, 48,
                   _london_detector(eur_london, adx_min=0.0)),
        LiveModule("GBP_LONDON_STRONG_TREND", "GBPUSD", "5m", 0.25, 48,
                   _london_detector(gbp_london, adx_min=30.0)),
    ]
