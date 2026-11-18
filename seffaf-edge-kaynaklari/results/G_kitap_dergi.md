# G: Kitap / dergi / merkez bankasi / blog / kripto kaynak taramasi (2026-11-18)

Kural: sadece acilan sayfada gorulen olgu, her iddiaya URL. Hafiza-only = "(memory, unverified)". Hicbir aday test EDILMEDI; hepsi aday.

## Erisim durumu (neden eksik)
- Kaufman kitabi/blogu: kural icerigi acik web'de bulunamadi (oreilly 403; sadece icindekiler). Kural YOK.
- Robot Wealth: robotwealth.com/overnight-and-intraday-spx-returns/ ACILDI (tek post, kural/maliyet yok). Strateji listeleri 404.
- Alpha Architect (403), SSRN (403), Springer (login), Reddit/ForexFactory (403): acilamadi.
- Bulkowski thepatternsite: yalniz hisse grafik formasyonu, endeks/FX/futures istatistigi yok (arama sonucu basliklari; sayfa acilmadi).
- Ehlers: sadece forum/indikator scriptleri, kuralli+maliyetli+OOS calisma bulunamadi.
- LUXOR (Tomasini-Jaekle): kural sadece forum ikincil ozeti; birincil kaynak kitap. (memory, unverified) kural: MA cross + onceki bar high/low kirilim filtresi; forum iddiasi GBPUSD 2002-2008 TradeStation $66k (yazarin kendi iddiasi).
- Kaiko/Glassnode/Amberdata/Binance Research: kural iceren zaman-dilimi calismasi bulunamadi.
- BIS/ECB/BoE/Fed: tradable+maliyetli intraday FX kural calismasi bulunamadi (BIS WP366 gunluk momentum, spread ile azaliyor).

## ADAYLAR (kural tam / kismi), cakisma isaretli

### 1. BTC gunluk Donchian ensemble (Zarattini-Pagani-Barbon, SFI 25-80) - YENI, portfoyde yok
- Kural (CXO ozeti, sayfa acildi): her lookback icin gunluk KAPANIS, lookback'teki max kapanisin ustune cikarsa long; lookback = 5,10,20,30,60,90,150,250,360 gun. Cikis: trailing stop = (onceki stop, lookback max/min kapanis ortasi) maksimumu. Boyut: 25% hedef yillik vol (90g getiri std), kaldirac tavani 200%. Esit agirlikli ensemble.
  URL: https://www.cxoadvisory.com/?p=46798
- BTC-only (QuantifiedStrategies ozeti, sayfa acildi, "kendileri dogrulamadi" diyor): Combo CAGR 30%, Sharpe 1.58, Sortino 2.03, MaxDD 19% (BTC al-tut >80%), alfa ~14%. 2015-Oca..2025-Mart. Maliyet 10bp (10/25/50 test; kisa lookback maliyete en hassas; 5-30g en iyi risk-ayarli). Korelasyon SG Trend ~7.4%.
  URL: https://www.quantifiedstrategies.com/?p=1192563
- Makale: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5209907 (403, acilamadi); ozet: https://ideas.repec.org/p/chf/rpseri/rp2580.html
- OOS: ayri OOS split yok (tek 2015-2025 backtest). Replikasyon: bagimsiz yok. Celiski: CXO hem "gunluk" hem "aylik" rebalance diyor. Uyari: Donchian XAU ile ayni aile; BTC al-tut bile 2015-25'te cok yukselen bir varlik.

### 2. NQ/ES "overnight drift" 02:00-03:00 ET (NY Fed Staff Report 917, Boyarchenko-Larsen-Whelan) - YENI; DIKKAT: 2021-25'te kayboldu
- Kural: ES (ayni desen NQ, YM) long 02:00-03:00 ET (Avrupa acilisi). Kosullu varyant: onceki gun kapanis (15:15-16:15 ET) goreli isaretli hacim (RSV) en negatif tercile ise ertesi gece 02-03 getirisi ~7.5% yillik; ust tercile'de yok.
  Orneklem 1998-2019: 02-03 ET ~3.6% yillik; 1998-2020: ~3.7% (kapanis-kapanis 5.9%'un >%60'i). 2021-2025 (1245 gun): ~0.
  URL: https://libertystreeteconomics.newyorkfed.org/2021/05/the-overnight-drift-in-us-equity-returns
  URL: https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/
- Maliyet: iki sayfada da YOK (tradable degil olculmus). OOS: 2021-25 negatif kanit. Replikasyon: NQ/YM ayni (NY Fed blogu). Sonuc: tarihsel etki var, guncel donemde yok -> yalniz "RSV genislerse geri gelir" tahmini; ON-KAYITLI test icin zayif aday.
  Acilis tersine donusu: 09:30-~12:00 ET negatif, yalniz Persembe/Cuma anlamli (ayni 2021 sayfasi).

### 3. Altin seans-sekli ("hat shape") - COMEX GC, 2001-2018 (CBS yuksek lisans tezi, hakemli DEGIL)
- Kural (acilan PDF): NY saati ile long 11:00->02:00 (ertesi gun), short 02:00->11:00; "Combo" = ikisi. Fixing varyanti: short 05:05-05:35 ve 09:35-10:05 (tum bunlar NY saati; London fix oncesi 30 dk, yazar kayip gosteriyor).
  Gross: ort Sharpe 1.61 (Combo, 18 yil). Net (bid/ask ile): tum yillar ABC ort getiri Short -22.0%, Long -13.5%, Combo -35.5%, Fixing -47.7%; 2001-2006 sermayenin >%90'i yaniyor; 2008 sonrasi 3/4 strateji karli ama al-tutu gecmiyor. Desen yillarin yarisinda kayboluyor; maliyet: ortalama goreli spread %0.144 (temizlik sonrasi), zamanla dusuyor.
  URL: https://research-api.cbs.dk/ws/portalfiles/portal/59803241/651553_Thesis_Contract_13383.pdf
- Yazarlar kendisi in-sample "best case" diyor. Replikasyon yok. XAU 1H Donchian ile iliski: seans filtresi olarak kullanilabilir ama tek basina net negatif. Zayif aday.

### 4. Gold overnight vs gun-ici (Blose-Gondhalekar-Kort 2018, J Econ & Finance 42(3))
- Bulgu: COMEX gold front futures'ta gece getirisi anlamli pozitif, gun getirisi anlamli negatif; yazarlar "maliyetle bile ekonomik onemli" diyor. Orneklem bu sayfada yok. Springer kilitli.
  URL: https://ideas.repec.org/a/spr/jecfin/v42y2018i3d10.1007_s12197-017-9403-0.html
  Onceki makale (Applied Economics Letters 2014, 1985-2012) asimetri "zamanla zayifladi" (arama ozeti, sayfa acilmadi; (memory-level, unverified)).
- Pratisyen kontrol: GLD gece +0.04%/islem, yillik 11.4% vs al-tut 11.8%; GDX gece +0.11%/islem; ham edge kucuk, maliyetle muhtemelen islenemez; filtreli 836 islem ort +0.15% (filtre paywall).
  URL: https://quantifiedstrategies.substack.com/p/a-quantitative-look-at-the-gold-overnight
- Kural: kapanista al, ertesi acilista sat (COMEX ile CFD "seans" tanimi Maven'de ayri olculmeli). BTC overnight reddi ile iliskili degil (farkli varlik) ama ayni aile.

### 5. SPY/ES overnight vs intraday (Robot Wealth, tanimlayici)
- SPY 2000-04-10 sonrasi: getirinin cogu gece; "SPY gun-ici toplam getiri 2000'den beri negatif". Kural: gece = kapanista al sabah ac; gun-ici = aciista al kapanista sat. Maliyet modeli YOK, backtest istatistigi yok.
  URL: https://robotwealth.com/overnight-and-intraday-spx-returns/
- Ters yon: CXO/Della Corte et al. CO-OC (onceki gece getirisi dusuk -> sonraki gun-ici long) hisse icin gross Sharpe 24 ama gunluk ~%100 devir, maliyetle yok olur; vadeli kontratlarda "cok daha zayif". URL: https://www.cxoadvisory.com/technical-trading/overnightintraday-return-reversal-trading/

### 6. BTC MAX10/MIN10 (Padysak-Vojtko, SSRN 4081000; Quantpedia)
- Kural (metinden): BTC onceki x gun (10..50) maksimumunda ise ertesi gun long (trend, MAX); minimumunda ise long (mean reversion, MIN); birlesik: MAX veya MIN ise long, degilse flat. Gemini gunluk acilis 00:00. Bilinmeyen: tutma suresi/agirliklar (formul gorsel).
  Orneklem 26 Kas 2015-3 Sub 2022: birlesik %98.43 yillik, vol %47.75, MaxDD -%37.67. Genisletme (in-sample 9 Eki 2015-20 Agu 2024); OOS 4 Sub 2022-20 Agu 2024: MAX etkili (20g > 10g), MIN zayif/negatif. Maliyet HIC anilmiyor (gross).
  URL: https://quantpedia.com/trend-following-and-mean-reversion-in-bitcoin/
  URL: https://quantpedia.com/?p=35597
- Bu, Aday 1 ile ayni aile (gun-bazli yeni yuksek long); MAX 20g OOS'ta calisti ama gross.

### 7. BTC 21-23 UTC (PORTFOYDE) - ek filtre bulgusu
- Quantpedia 9.10.2015-30.6.2023: 21:00->23:00 UTC long, yillik %40.64, Calmar 1.79, MaxDD -%22.7; yalniz yuksek-vol gunler (30g saatlik vol > 365g medyan, 00:00 UTC'de olculur): %37.26, MaxDD -%18.87, Calmar 1.97. Maliyet belirtilmemis. Trend filtresi (10/20/50/200g MA) sonuc gorselde.
  URL: https://quantpedia.com/the-seasonality-of-bitcoin/
- Baur vd. (7 borsa, 15M gozlem): zamana bagli, kalici desen yok -> verimli. URL: https://quantpedia.com/are-there-any-simple-calendar-effects-in-bitcoin-market/
- Quantpedia sayfasi (intraday-seasonality) 22:00 UTC giris diyor, arastirma 21-23 diyor: tutarsiz. URL: https://quantpedia.com/strategies/intraday-seasonality-in-bitcoin
- Concretum: BTC trend-ensemble getirileri Pazar ~19:00 NY'den ~24 saat pozitif ("Monday Asia Open"), 2018-2025, brut; kural/maliyet/OOS YOK. URL: https://concretumgroup.com/seasonality-in-bitcoin-intraday-trend-trading/

## ELENEN / ZAYIF (is-zamani tasarrufu icin)
- Altin 5dk SMA/EMA/WMA (Urquhart-Batten-Lucey-McGroarty-Peat, SSRN 2652637): spot altin 2008-01-01..2014-09-10; standart parametreler karsiz; parametre taramasi (66,297 kural) uzun pencerelerde anlamli; en iyi SMA 41-356 in-sample buy-sell 0.001040 (z 2.23), OOS 0.000581 (z 2.27); kirilim 31 Agu 2010. Maliyet analizi YOK (PDF'te sadece literatur). URL (indirilen PDF): https://c.mql5.com/forextsd/forum/174/does_technical_analysis_beat_the_market__evidence_from_high_frequency_trading_in_gold_and_silver.pdf . Sonuc: maliyetsiz, spot, 2014 bitisli -> aday degil.
- BTC EMA crossover dakikalik walk-forward (arXiv 2602.10785): fast/slow {5..200}, WF 7/28 ve 14/10 gun; unseen 7 Kas 2019-22 Agu 2021; maliyet %0.1/islem, basabas ~%0.4; OOS Sharpe al-tutu gecmiyor (BTC WF14/10 1.1064 vs 1.1281). Kod: https://github.com/tmr-crypto/wf_optim_crypto_analysis . ELENDI. URL: https://arxiv.org/html/2602.10785v1
- MNQ VVG sinifi (arXiv 2605.11423): 8 yonlu konfigurasyon gecmedi (en iyi T=1.46, 127 OOS islem, 2024 bozuyor); 40 gun; net maliyet tanimi yok. Tek bulgu: siniflandirici gunlerin %77.6'si zirveden kapanisa dusuyor (olgu, kural degil). URL: https://arxiv.org/abs/2605.11423 . ELENDI.
- Altin gunluk "Forecast-to-Fill" (arXiv 2511.08571): GC surekli ay on, 2015-2025 OOS, walk-forward 10y egitim/6ay test, Sharpe 2.88, MaxDD 0.52%, maliyet 0.7 bp round-trip + sqrt etki (gama 0.02). Kural: EMA log-fiyat egimi z-skoru, pbull=0.6*ptrend+0.4*(P_t/P_{t-50}>1), long pbull>=0.52 ve egim>0; cikis 2xATR14 stop, 1.5xATR14 trailing, 30g timeout, pbear>0.5'te yari/kapat; vol hedef %15, kaldirac<=2, Kelly 0.40. lambda belirtilmemis; T+0 / T+1 dolum ve LBMA/COMEX veri tutarsizligi var; 0.7bp maliyet gercekci degil (GC icin). "Tam kural" DEGIL -> kullanma. URL: https://arxiv.org/html/2511.08571v1
- Noise Band / SPY intraday (Zarattini-Aziz-Barbon): zaten PORTFOYDE (Noise Band NQ). Quantified Strategies sayfasi: SPY, 14g, hisse basi $0.0035, slipaj yok, yillik %19.6, Sharpe 1.33; kendileri backtest etmedi. URL: https://quantifiedstrategies.substack.com/p/systematic-intraday-trend-following
- Algomatic "3-Down Daily Pullback": NQ/ES/DJ, 2000-2026 backtest, 2 puan spread; KURAL PAYWALL; "iki parametre"; 2 yillik OOS grafigi MAR al-tuttan biraz dusuk. URL: https://algomatictrading.substack.com/p/strategy-14-the-3-down-daily-pullback . Kural yok -> test edilemez.
- Rogue Quant Turtle (20g high giris, 10g cikis, ATR boyut, 43 piyasa, 2007-2025): maliyet yok, kurallar paywall'da celiskili. URL: https://roguequant.substack.com/p/i-backtested-the-legendary-turtle
- FX fix reversal (BoC SWP 2021-48; Krohn-Mueller-Whelan): ZATEN REDDEDILDI (cakisma); kaynak notu: maliyetten sonra zor, sadece dar spread'li oyunculara. URL: https://www.bankofcanada.ca/2021/10/staff-working-paper-2021-48/
- Bitcoin intraday TS momentum (Shen-Urquhart-Wang, Financial Review 2022): ilk yarim saat -> son yarim saat = REDDEDILEN "first30->last30" ile CAKISIR. URL: https://centaur.reading.ac.uk/100181
- Hata ayiklama: Deprez-Frommel 2024 (IREF 93:858): 75,360 kural BTC gunluk+gun-ici, maliyet sonrasi coklu-hipotez secimi, portfoyler OOS al-tutu geciyor; sayfada rakam/kural yok. URL: https://econpapers.repec.org/RePEc:eee:reveco:v:93:y:2024:i:pb:p:858-874 . Tam metin acilmadi.
- CXO (Schulmeister tipi): S&P futures 30dk veriyle 2580 kural, 1983-2000 brut %8.8 yillik, 2001-2006 brut %0.9 / net -%3.8 (ikincil ozet, sayfa acilmadi, yalniz arama ozeti). Intraday teknik kural etkisi zamanla yok oluyor.
- BTC gunluk/saatlik ML (dev.to/arXiv 2026): sadece arama ozeti, dogrulanmadi.
