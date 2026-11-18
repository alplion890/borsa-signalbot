# B: Acik kod strateji kaynaklari (arastirma 2026-11-18)

Kural: sadece acilan sayfada gorulenler. "not stated" = sayfada yok. Gelismis performans iddialari yazarin kendi beyanidir, dogrulanmadi.
Not: WebFetch bir ozetleyici model uzerinden calisir; kritik kurallari kodu indirip dogrulayin.

## B1 Quantiacs
- https://quantiacs.com/community/user/news-quantiacs : en yeni gorulen duyuru "Q22 Contest started" (S&P 500 hisseleri; teslim Ocak 2025 sonu, canli Mayis 2025 sonu). Q20 = Nasdaq hisseleri. Q15 = Futures + BTC yarismasi (kazanan "Duckling Pentakill", kvanvanvant_test_python, 1M USD). Sayfada tarih yok, ID sirasiyla. Q22 sonrasi vadeli islem yarismasi bulunamadi (not found).
- Hicbir kazanan duyurusunda kod paylasimi yok: sadece isim/sistem/tahsis (ayni sayfa). => Kazanan kod PUBLIC DEGIL.
- https://quantiacs.com/documentation/en/quick_start/quick_start.html : platform futures, BTC future, crypto verisi sunuyor; sablon/ornek stratejiler var (ornegin "Q24 Crypto Guide Strategy"); NQ/GC/FX listesi sayfada yok. Nasdaq-100 icin dual SMA crossover sablonu (https://quantiacs.com/documentation/en/examples/q20_quick_start.html, arama sonucu, acilmadi).
- Sonuc: test edilebilir NQ/GC/FX kural seti cikmadi. DUSUK UYUM.

## B2 QuantConnect
- https://www.quantconnect.com/learning ve /strategies sayfalari "Loading strategies..." (icerik yuklenmedi); futures/altin/BTC/FX stratejisi listelenemedi.
- Forum (arama sonucu, tam acilmadi): NQ ORB yok; Boot Camp ORB 30 dk (https://www.quantconnect.com/forum/discussion/10724/boot-camp-5-opening-range-breakout-all-text-and-code/p1), FX ORB cikarmasi (https://www.quantconnect.com/forum/discussion/8661/replicating-the-opening-range-breakout-bootcamp-exercise-for-forex-market/). Intraday ETF Momentum (SPY) Sharpe -0.628 (https://www.quantconnect.com/learning/articles/investment-strategy-library/intraday-etf-momentum). Stocks-in-Play ORB hisse evreni, bizim enstruman degil.
- Canli iz kaydi olan acik NQ/XAU/BTC strateji bulunamadi. DUSUK UYUM.

## B3 MQL5 CodeBase (listeden https://www.mql5.com/en/code/mt5/experts ; hepsi Kasim 2026, cok yeni, canli iz yok)
1. Gold Trend Breakout Lite https://www.mql5.com/en/code/79733 (SGupta30, 2026-11-18)
   - XAUUSD. H1 kapanis > onceki 120 bar en yuksek VE D1 EMA(100) son 3 tam gunde yukseliyor => long; tersi short. Bar kapanisinda, pozisyon yokken.
   - Stop 3xATR(14,H1). TP yok. H1 kapanis +1R olunca stop entry+0.1R. Lot 0.01 sabit.
   - Sonuc/maliyet: not stated. Test notu: real ticks, 2012 veya oncesi baslat; beklenen win %30-40.
   - Parametre sayisi az (120, 100, 3 gun, ATR14, 3x, 1R/0.1R), grid/martingale yok. En temiz aday.
2. Giano Session Range Breakout https://www.mql5.com/en/code/79679 (Alessandro Lupi, 2026-11-16)
   - XAUUSD, M1'den aralik. Aralik = 01:00-06:00 sunucu saati (GMT+2/+3) high-low (60 5dk dilimden >=30 quote gerek). Giris: 06:15-21:30 arasi acilan ilk M15 bar aralik disinda kapanirsa, kapanis sonrasi ilk quote. Gunde tek karar.
   - SL aralik karsi ucu; TP aralik boyu kadar kirilan yonun otesinde; 22:00 kapat. Lot 0.01.
   - Sonuc: not stated. Yazar: "out-of-sample results do not show a proven edge" (sayfada). Zayif kanit.
3. NY Open Candle: The Basics https://www.mql5.com/en/code/78392 (Aleksei Labuzin, 2026-11-13)
   - US100/USTEC M5. 09:30 NY ilk M5 mum; govde > fitiller toplami ve tick hacmi > 1.5x onceki 20 bar ortalamasi ise mum yonunde gunde 1 islem. SL 30 puan, TP 120 puan (varsayilan), gun sonu kapanis saati.
   - Tester (USTEC M5, every tick, 2025, deposit 10000, risk 100/islem): 91 islem, +2559, PF 1.41, win %29.7, max DD %7.3, en uzun kayip serisi 10. Yazar kendi M1 2023-2026 testi PF~1.4, 2023 ~0.
   - Komisyon/swap: not stated. Giris emri tipi/saatleri: not stated. n=91 kucuk. SL/TP birimi puan, fiyat olcegine gore olceklendiriliyor.
4. EMA Trend Cross XAUUSD M30 https://www.mql5.com/en/code/78968 (Christophe Trouillas, 2026-11-02)
   - EMA20 EMA50'yi yukari keser ve kapanis > EMA20 ve EMA200 => long; ters short. 07:00-19:00 sunucu saati giris. SL fiyatin %1'i, TP yok, 20:00 hepsini kapat. Risk %1.
   - Tester XAUUSD M30 2020.01.01-2026.10.01, IC Markets EU, 1000 USD, every tick %99 kalite: +1107 (+%110.7), PF 1.46, 500 islem, win %52.8, DD %8.07 bakiye. Komisyon, spread, slipaj, swap: not stated. OOS: not stated.
5. Supertrend EA Gold Breakeven https://www.mql5.com/en/code/79531 (09151993a, 2026-11-14): Supertrend(ATR10, x3.0) donusunde giris, SL cizgi+50 puan, TP 2x stop, BE 1x stopta, ters donuste kapat, risk %1. Sonuc/maliyet: not stated.
6. Atlanan: Xander Grid RSI Gold (grid), G7 FVG OB (SMC, belirsiz), Moving Average Crossover EA Gold (https://www.mql5.com/en/code/79234, ozeti listeden, ayrinti acilmadi).
- BTCUSD ve EURUSD icin listede ozel EA yok. BTC icin sadece gosterge: Gold Donchian Breakout Channel https://www.mql5.com/en/code/79728 (default Donchian 120 bar, D1 EMA100 egim filtresi; BTC H1/H4 icin kanal 60-160, D1 EMA 50-100 onerisi; sonuc not stated) ve Trend Filtered Donchian https://www.mql5.com/en/code/79607 (BTCUSD H1, islem acmaz).

## B4 MQL5 Articles / blog (tam kural + sonuc olanlar)
- Tokyo range breakout, GBPUSD M15 https://www.mql5.com/en/articles/24936 : Tokyo 02:00-10:00 sunucu aralik; M15 kapanis aralik kenari + 0.05 ATR disinda; body orani >= 0.80; mesafe filtreleri; zaman bazli boyut carpani; SL/TP R katlari (UP: SL 0.60R TP 0.85R; DOWN: SL 1.50R TP 0.30R); dead-man 0.25R; trail 1.5 ATR; 32 bar/21:45 cikis. Test: JustMarkets demo, spread tick gecmisinden, komisyon yok, slipaj not stated. GBPUSD IS 2025.01-2026.08: 65 islem PF 1.06, expectancy CI -2.46..+3.23 USD; GBPUSD "OOS" 2022-2024: 107 islem PF 1.99 ama tick kalitesi %0 (M1'den uretilmis); EURUSD 2019-2026: 261 islem PF 0.82. SONUC: EURUSD'de basarisiz, GBPUSD'de kanitsiz. Cok sayida elle ayarli filtre (curve-fit riski yuksek). Elenmeli.
- Shifted-bar stress test, XAUUSD M15 SMA10/30 cross https://www.mql5.com/en/articles/24077 : SL/TP yok, close-and-reverse, 2025-06..2026-01, 519-547 islem, PF 1.05-1.21, max DD %18-32. Edge degil, sadece test metodolojisi (bar siniri duyarliligi) icin yararli. Real ticks'e gecis: 14 offset ~%0.04-2.5 fark.
- MQL5 article "Where your backtest stops being real" https://www.mql5.com/en/articles/24562 (arama ozeti; acilmadi): real tick gecmis derinligi kontrolu, XAUUSD bir testte Agu 2025 %0 real tick.
- ORB Indices (ARGUS) blog https://www.mql5.com/en/blogs/post/771405 : US100+US500 ORB, 09:30 NY, MA trend filtresi, kapanisla giris, TP aralik kati, SL karsi uc, gunde 1. 2020-2026: PF 1.32, 8310 islem, win %52.92, DD %5.51. Kod yok (Market urunu), aralik suresi/MA/TP carpani not stated, maliyet not stated, OOS not stated. Test edilemez (kapali).
- 09:30 Liquidity Expansion blog https://www.mql5.com/en/blogs/post/779066 : 09:30-10:00 NY aralik; tick duzeyinde Ask >= high+offset giris; SL aralik karsi ucu; TP1 2R (%50), TP2 3R, kalan icin BE; gunde 1. NAS100/US30/XAUUSD onerilir. Sonuc not stated, kod yayinlanmamis. Kurallar acik, backtest edilebilir (sonuc yok).

## B5 TradingView (acik kaynak)
- Acik kaynak NQ/XAU stratejisi bulunmasi zor: Winning-Day ORB (maliyet: 2.50$/sozlesme/taraf + 1 tick slipaj) ve FXC NQ ORB V2.4 (0.35$ komisyon) closed-source (arama sonucu). 
- MNQ 5M https://www.tradingview.com/script/uO0KLOxH-MNQ-5M : OPEN-SOURCE ama gosterge (strategy degil), SL/TP/sonuc not stated.
- NY Session Trend Retest https://www.tradingview.com/script/zV6RrYm5-NY-Session-Trend-Retest-Strategy/ : acik kaynak; NQ/ES/GC icin VWAP/premarket/EMA retest; SL, saatler, parametreler, sonuc, komisyon not stated (Pine kodu sayfa metninde gorulmedi, yeniden dogrulanmali).
- MuLegend Break-Retest URL 404. IU ORB strategy (2:1 R:R, gunluk limit, EOD kapanis, NQ'ye ozgu degil) ve Opening Candle Breakout (MPL-2.0) arama ozetinden; acilmadi.
- Sonuc: dogrudan portlanabilir, maliyetli, dogrulanmis TV adayi cikmadi.

## B6 WorldQuant 101 Alphas
- https://arxiv.org/abs/1601.00991 : ortalama tutma suresi 0.6-6.4 gun (abstract). Hisse capraz kesit (ADV, VWAP, sektor notralizasyonu kullaniyor, memory unverified; PDF binary okunamadi). Vadeli/FX intraday icin DUSUK UYUM.

## B7 GitHub
- pysystemtrade https://github.com/robcarver17/pysystemtrade (GPL-3.0). Kurallar (raw dosyalar acildi):
  - EWMAC: forecast = (EWMA_fast(price) - EWMA_slow(price)) / gunluk fiyat-birimi vol; https://raw.githubusercontent.com/robcarver17/pysystemtrade/master/systems/provided/rules/ewmac.py
  - Chapter15 config (https://raw.githubusercontent.com/robcarver17/pysystemtrade/master/systems/provided/futures_chapter15/futuresconfig.yaml): ewmac2_8..64_256 scalar 10.6/7.5/5.3/3.75/2.65/1.87, carry scalar 30, forecast cap 20, vol hedefi %20, agirlik ewmac16_64 0.21, 32_128 0.08, 64_256 0.21, carry 0.50, FDM 1.31; ornek enstrumanlar SOFR, US10, EUROSTX, V2X, MXP, CORN (NQ/GC/FX yok).
  - Breakout: 40*(price - (rollmax+rollmin)/2)/(rollmax-rollmin), varsayilan lookback 10, EWM smooth=max(lookback/4,1); https://raw.githubusercontent.com/robcarver17/pysystemtrade/master/systems/provided/rules/breakout.py
  - Gunluk bar, portfoy-seviyesi trend takibi; gun ici degil. Python yoluyla Dukascopy gunluk barlarinda yeniden uretilebilir (NQ, XAU, BTC icin tek enstruman EWMAC denemesi). Maliyet modeli sayfada acilmadi.
- awesome-systematic-trading https://github.com/wangzhe3224/awesome-systematic-trading : cerceve/kutuphane listesi (pysystemtrade, vnpy, QUANTAXIS); strateji kodu yok. Tam liste okunmadi (ilk 100k karakter).
- maker-tung/xauusd-trend-follow https://github.com/maker-tung/xauusd-trend-follow (CC BY-NC 4.0, ticari degil): XAUUSD H1 long-only: Close>EMA200; opsiyonel ADX14>=20; giris (VEYA) MACD yukari kesisim / Stoch %K>%D (<60) / EMA9>EMA21; SL Ask-1.25 ATR14; TP Ask+6 ATR14; 60 bar zaman cikisi; risk %0.25. 2022.01-2026.05, %100 real tick FTMO feed, spread modeli sabit 0.30, komisyon/swap not stated: +%54.8, max DD %6.22, win %25.8, PF ~1.17, ~1354 islem, Sharpe ~2.42. OOS: WFO yapilmadi; parametreler 2022-2023'te kesfedilmis (README kendi icinde tutarsiz). Uc tetikleyici + ADX + 21 girdi => curve-fit isareti, ama kurallar acik.
- Nyao Scalper/Straddle https://github.com/elrizwiraswara/nyao_scalper_mt5 (BSD-3): XAUUSD M5 skorlu trend; 2022-2024 uretilmis tick ile -13.4% toplam, 2026 real tick +%93.8 (OOS temiz degil, yazar kabul ediyor); Straddle karin %82'si Ocak 2026 cokusunden. Opsiyonel hedge zinciri martingale, kapali. Cok parametre, rejim bagimli. Onerilmez.
- wholeticket/mt5bot https://github.com/wholeticket/mt5bot : Nasdaq SMC/FVG EA; sonuc ve lisans not stated (rapor dosyasi icerigi gorulmedi); cok parametreli. Dusuk oncelik.
- Arama sonucunda gorulup acilmamislar: yanstd888/institutional-smc-scalper-mt5 (iddia Sharpe 8.5, scalper, supheli), leadfyy/xauusd-ai-scalper (M5 scalper), yulz008/GOLD_ORB.
- yulz008/GOLD_ORB https://github.com/yulz008/GOLD_ORB : XAUUSD H1 ORB: ilk H1 mum (01:02 sunucu), aralik >=3 mum aralik icinde kapanana dek guncellenir; kirilimda giris; TP 1200 SL 400 (birim not stated, muhtemelen puan); opsiyonel trailing 700 tetik 100; gunde en fazla 2; lisans not stated; sonuc metin olarak yok.

## Genel degerlendirme
- Gercek, dogrulanmis canli iz kaydi olan acik kod strateji: HICBIRI bulunmadi.
- Cogu kaynak Kasim 2026 yeni, tester sonuclari yazar beyani. Tek bagimsiz test yolu: kendi MT5 real tick + Maven maliyeti.
