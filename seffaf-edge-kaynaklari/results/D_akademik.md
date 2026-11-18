# D: Akademik / pratisyen arastirma kaynaklari (2026-11-18)

Kural: yalniz acilan sayfalarda/PDF'te gorulenler. "(memory, unverified)" = acilmadi. WebSearch ozet metinleri tek basina kanit sayilmadi; sadece sayfa/PDF acilarak dogrulananlar "dogrulandi" ile isaretli.
Kapsam siniri: D4 (Chan/Kaufman/Fitschen) ve D5 (Alpha Architect, Robot Wealth, Quantitativo) icin ucretsiz, kural-seviyesinde acilabilir kaynak bulunamadi; asagida acik yazildi.

---------------------------------------------------------------
## D2. Concretum Group (Zarattini et al.)

Dogrulandi: https://concretumgroup.com/papers/ listesi (15 makale; SSRN id'leri orada). Noise Band ("Beat the Market", SSRN 4824172) = portfoyde, atlandi.

### D2-1. Fast Alphas: 5dk karsi-yon pullback ile "execution overlay" (SPY, ATR/2 breakout tabani)
Kaynak (PDF acildi, pdftotext): https://concretumgroup.com/wp-content/uploads/2026/02/Improving-Performance-with-Fast-Alphas-A-Tactical-Overlay-for-Intraday-Trend-Trading.pdf ; SSRN abstract_id=6391638 (sayfa listesinden). Yazarlar Pagani, Zarattini, Subat 2026.
- Enstruman/donem: SPY ETF, 5dk bar, 2007 - 2026 (RTH, IQFeed).
- Taban kural (Kaufman 2013'ten esinli): her seans acilisinda Ust bant = SessionOpen + 0.5*ATR(14), Alt bant = SessionOpen - 0.5*ATR(14). Fiyat ust bandin USTUNDE KAPANIRSA long, alt bandin ALTINDA kapanirsa short. Stop = seans acilis fiyati (fiyat acilisa donerse cikis). Gun sonu tum pozisyon kapanir. Emirler yalniz HH:00/:15/:30/:45 (15dk kapanislar). Boyut: SPY gunluk getirisinin 14 gunluk realized vol'u ile gunluk portfoy vol hedefi %2; boyut seans acilisinda sabitlenir.
- Overlay: breakout 15dk'da tespit edilince girisi ertele; long icin onceki 5dk getirisi NEGATIF (short icin POZITIF) olana kadar bekle. Cikista da ayni (stop seviyesine gelince karsi yonde 5dk hareket gorulene kadar bekle).
- Sonuc (metinde): taban "CAGR %13'un uzerinde, Sharpe ~0.87" (net); overlay ile net CAGR ~+200 baz puan, Sharpe 0.87 -> 0.99.
- Maliyet: IBKR tiered $0.0035/hisse komisyon, satis tarafi regulatory fee iki katina; SLIPPAGE YOK ("No slippage assumed"). Ham 5dk reversal sinyali (N=1) tek basina brut CAGR ~%31.9 ama komisyonla yok oluyor.
- Saglamlik: tek makale, tek enstruman, parametre taramasi/DSR raporlanmamis (metinde gorulmedi). Bagimsiz replikasyon: bulunamadi.
- Bizim icin: NQ/US100'e uygulanabilir, ama (a) NQ ORB varyantlari reddedildi -> KISMI ORTUSME (ATR-band acilis breakout'u ORB akrabasi; ozgun kisim 5dk pullback execution filtresi ve acilis-seviyesi stop), (b) slippage varsayimi yok, spread ile test edilmeli. Not: Maven CFD'de spread her giriste odenir; "daha iyi giris" etkisi spread'in altinda kalabilir.

### D2-2. VWAP Trend Trading (QQQ/TQQQ)
Kaynak (PDF acildi): https://concretumgroup.com/wp-content/uploads/2026/02/Volume-Weighted-Average-Price.pdf ; SSRN 4631351 (liste). Zarattini & Aziz, Kasim 2023.
- Kural (dogrulandi): 09:31 ET'de fiyat VWAP ustundeyse long, altindaysa short (VWAP = yalniz RTH). Stop = 1dk mum VWAP'in karsi tarafinda KAPANIRSA; stop olunca pozisyon ters yone cevrilir (surekli pozisyonda). Gun sonu 16:00 ET'de kapanis, gece yok. Boyut: tum ozkaynak, kaldiracsiz.
- Donem: 2 Ocak 2018 - 28 Eylul 2023.
- Net sonuc (komisyon sonrasi, metinde): QQQ $25k -> $192,656 (%671), MDD %9.4, Sharpe 2.1; B&H QQQ %126, Sharpe 0.7. TQQQ: $2,085,417, MDD %36.1, Sharpe 1.7.
- Maliyet: $0.0005/hisse komisyon; SLIPPAGE YOK varsayildi (yazarlar kendileri "yaklasik 2M'de slippage sorun olabilir" diyor). Islem sayisi: QQQ ~22.000 islem / 5.7 yil (~15/gun, tablo satirlari karisik ama 22,399/21,967 gorunuyor), isabet orani ~%17 (metinde "approximately 17%").
- UYARI (olgu): 15 islem/gun + dusuk isabet = CFD spread'ine ASIRI duyarli. Maven spread'iyle (reality_profiler) test edilmeden anlam yok. Brut nesil iyi, net CFD buyuk olasilikla negatif - bu bir tahmin; olcum yapilmali.
- Bagimsiz replikasyon: bulunamadi. Saglamlik: parametre yok (iyi), ama donem 5.7 yil, sadece ETF.

### D2-3. Catching Crypto Trends (BTC Donchian ensemble, gunluk)
Kaynak (PDF acildi): https://concretumgroup.com/wp-content/uploads/2026/02/Catching-Crypto-Trends.pdf ; SSRN 5209907. Zarattini, Pagani, Barbon (Nisan 2025).
- Kural (dogrulandi): Donchian(n) up/down = n-gun kapanis max/min, Mid = 0.5*(Up+Down). Kapanis = DonchianUp ise long ac; pozisyon trailing stop'a kadar tutulur; TrailingStop(t+1) = max(TrailingStop(t), DonchianMid(t)) (asla asagi cekilmez); yalniz long (Pos in {0,1}). Boyut: w = hedef yillik vol %25 / (3 aylik yillik vol), uzerinde ust sinir var (pdf'te formul bozuk cikti, sinir degeri okunamadi -> "not stated reliably"). Ensemble "Combo": n in {5,10,20,30,60,90,150,250,360} esit agirlikli ortalama.
- Donem: 1 Ocak 2015 - 19 Mart 2025, BTC.
- Tablo 1 (MALIYETSIZ - metinde "Transaction costs are not included"): 5g CAGR %36 Sharpe 1.66 MDD %25; 20g %34 / 1.60 / %26; 60g %28 / 1.30 / %19; Combo %30 / 1.58 / MDD %19 (vol %17).
- Maliyetli (metin): 10 bps + %20 rebalance esigi ile BTC satiri CAGR %30, Sharpe 1.56, MDD %19 (ek tablo; hangi model oldugu net okunmadi, buyuk olasilikla Combo). %50 bps maliyette 5g modeli CAGR %34 -> %18.
- UYARI: yalniz long, spot varsayimi; Maven BTCUSD CFD'de uzun tutma swap'i (sizin olcumunuz: BTC gece -%30/yil) bu sonucu oldurur. Bu yuzden sonuc ancak swap dahil test edilirse anlamli. BTC 21-23 UTC portfoyde; bu multi-day trend, farkli.
- Saglamlik: 9 lookback'in hepsi pozitif (iyi: tek parametre secimi yok). Post-2015 BTC buyume rejimi donem yanlisligi riski: BTC B&H ile alfa/beta tablosu var (alfa %14, beta 0.17 Combo, maliyetsiz). Bagimsiz replikasyon: bulunamadi. Cok varlikli portfoy (top 20 coin): 10bps maliyet, 20% esik; portfoy CAGR ~%18, Sharpe 1.44 (5 varlik) (tablo, dogrulandi) - bu bizim enstruman degil.

### D2-4. Bitcoin Monday Asia-open mevsimselligi (Concretum blog)
https://concretumgroup.com/seasonality-in-bitcoin-intraday-trend-trading/ (sayfa acildi). KURAL YOK: sayfa sinyal tanimi vermiyor. Olgular: yuksek frekansli trend ensemble'in long-short getirisi Pazar ~19:00 New York'tan Pazartesi'ye ~24 saat guclu pozitif; 2018-2025; BRUT Sharpe ~1.6 (long-short) vs vol-hedefli long-only <0.8; maliyet "not stated"; 2020H2 sonrasi daha belirgin. Yazarlar "gelecek calisma" diyor. -> Test edilebilir kural yok; sadece hipotez.

### D2-5. Diger
- "Can Day Trading Really Be Profitable?" (QQQ/TQQQ ORB, 2016-2023, SSRN 4416622) ve "A Profitable Day Trading Strategy ... Stocks in Play" (SSRN 4729284, 5dk ORB, 7000+ hisse 2016-2023): SADECE liste ozeti okundu; PDF acilmadi. NQ ORB reddedildi -> ORTUSME, atlandi. Stocks in Play hisse secimi; bizim enstrumanlara uygulanmaz.
- Diger Concretum: VIX ETN, sektor trendi, GTAA, hisse trend: bizim enstrumanlar disinda.

---------------------------------------------------------------
## D1. SSRN / arXiv

### D1-1. Mesfin, "Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures" (arXiv:2605.04004, q-fin.TR; v1 5 Mayis 2026, v3 15 Eylul 2026)
Sayfa + PDF acildi: https://arxiv.org/abs/2605.04004 , https://arxiv.org/pdf/2605.04004
- Veri: 947 gun, MNQ 5dk, 2021-2025, expanding walk-forward. Surtunme: MNQ 2.0 puan round-trip ($4/mikro sozlesme: spread + NinjaTrader borsa ucreti + "muhafazakar slippage"); MGC 0.50 puan.
- Sonuc: 14 sinyal ailesinden HICBIRI 5 kriteri gecmedi (11'i brut 0.07-1.50 puan < 2.0 surtunme). ORB long (15 bar tutus) net +2.82 puan, T=0.88, yillar arasi tutarsiz. Gap-continuation short: brut +16.53, net +14.52, T=1.46, yil istikrari + fold basi min. islem sayisi basarisiz (yazarin "en yakin aday"i; 2019'a kadar veriyle genisletilmeli diyor). -> NEGATIF DOGRULAMA: bizim ORB reddimizle tutarli.
- "Pozitif kontroller" (yazarin kendi dis programi, GMM rejim siniflandirici): 
  a) RTH Confluence: 3 bilesenli GMM (4 ozellik, 2022 verisine bir kez fit), Rejim 1, rolling-200 bar Markov gecis P(R1->R2)>0.15, 50-bar hacim z>0.5; giris 25*ATR_ratio puan pullback (6 bar icinde), cikis 13. bar, stop 80*ATR_ratio puan; OOS T=3.11, net +11.82 puan, N=196. 
  b) London Session Signal B: 15dk bar, 03:00-08:30 ET, 5 ozellikli GMM, R0 (Bearish Chop)->R2 (Bullish Drift) temiz gecis, long next bar open, cikis 60 dk veya 08:30 ET, stop 20 puan; walk-forward OOS N=247, T=4.30, net +4.09 puan.
  Yazarin kendi sinirlamalari: RTH spesifikasyonu 53+ parametre kombinasyonu uzerinden secilmis (coklu test, duzeltilmemis; yazar Bailey-LdP'yi anip duzeltmenin guveni azaltacagini soyluyor), W1 foldu 2022H2 fit verisiyle ortusuyor (kontamine), London'da 1 bar gecikmede ISARET DEGISIMI (kirilgan), tek yazar, ekstra replikasyon hatalari belirtilmis. Guvenilirlik DUSUK; "aday" degil "dikkat cekici kontrol". Bagimsiz replikasyon yok.
- Bizim icin: gap-continuation short ve London drift fikri test edilebilir ama GMM spesifikasyonu karmasik; yalniz sade bir surumu (Londra seansinda 03:00-08:30 ET icinde long, 60 dk tut) negatif-kontrol amacli denenebilir.

### D1-2. Mesfin, "A Validated Volatility-Volume-Gap Classifier..." (arXiv:2605.11423)
https://arxiv.org/abs/2605.11423 (acildi). 8 yonlu konfigurasyon, hicbiri gecmedi; en iyi: reversal giris + OLS filtresi, 127 OOS islem, T=1.46, net +7.80 puan, 2024'te bozuldu. NEGATIF.

### D1-3. Boyarchenko, Larsen, Whelan, "The Overnight Drift" (NY Fed Staff Report 917, Subat 2020, rev. Agustos 2022)
PDF acildi: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf
- Olgu: S&P 500 e-mini'de en buyuk pozitif getiri 02:00-03:00 ET (Avrupa acilisi), yillik ~%3.7 (gunde 1.48 bps), 1998-2020.
- Stratejiler (Tablo IX, 2004.1-2020.12): OD long 02:00-03:00: maliyetsiz Sharpe 1.1; bid-ask dahil -0.5. OD+ 01:30-03:30: maliyetsiz 1.3, maliyetli 0.3. "Buy-the-dip" (BtD): OD+ penceresinde long, ama yalniz bir onceki gun kapanista negatif relative signed volume (RSV close < 0) varsa; maliyetsiz Sharpe 1.8, maliyetli ~1.1 (metin; tablo cikarimi karisik).
- Maliyet: guzel kisim: gercek bid/ask quote'lari kullanilmis. UYARI: 2020 sonrasi gece spread'i min. tick'e (0.25 puan) indi, bu yuzden orneklem 2020'de bitiyor; yazarlar "ES gunduz oncesi spread" ile OD'nin kar etmedigini kendileri gosteriyor.
- Saglamlik: bootstrap + yillik tutarlilik (23 yildan 20'si pozitif - bu rakam web arama ozetinden, PDF'te dogrulanmadi). Bagimsiz replikasyon: yazarlar Bondarenko-Muravyev (2020)'nin Avrupa acilisi bulgusunu replike ettigini yaziyor (metin satir ~217). 
- Test edilebilirlik: BtD icin kapanis "relative signed volume" gerekli (islem verisi, isaretli hacim). Maven'de CFD tick var ama gercek signed volume yok -> sinyal PROXY ile degisir, ayri hipotez olur. Yalniz OD+ (01:30-03:30 ET long, US100/ES) basit ama maliyet sonrasi Sharpe 0.3 ("OD+ yalniz pozitif"); CFD spread'iyle muhtemelen sifir.

### D1-4. Singha et al., "Forecast-to-Fill: Benchmark-Neutral Alpha ... in Gold Futures (2015-2025)" (arXiv:2511.08571)
Sayfa acildi: https://arxiv.org/html/2511.08571v1
- Kural: EMA log-fiyat egimi z-skoru [-3,3] kirpilmis -> [0,1]; momentum bayragi (fiyat > 50 gun onceki); p_bull = 0.6*trend + 0.4*mom; long-only; giris p_bull >= 0.52 ve egim > 0; cikis: 2xATR(14) hard stop, 1.5xATR(14) trailing, 30 gun zaman, p_bear > 0.5. Vol hedefi %15, kaldirac max 2, Kelly 0.40. GC front-month, gunluk, rolling walk-forward 10y egitim / 6ay test, ilk OOS Ocak 2015, 2793 gun. EMA lambda "not reported".
- Maliyet: 0.7 bps round-trip + karekok etki (gamma 0.02); T+1 kapanis dolumu.
- Sonuc: Sharpe 2.88, ama yillik vol %0.91, CAGR %2.65 (neredeyse yatirimsiz). Maliyet stresi: 1.5x maliyette Sharpe ~ -0.03, 2.0x'te -1.0 (Tablo 3); metin ile tablo celisiyor (metin "2.5 ustu", tablo 1.0x'te 0.937).
- Guvenilirlik DUSUK (kirilgan, ic celiskili, canli yok). Bizim Donchian-20 XAU ile ayni aile; yeni bilgi yok.

### D1-5. Notlar (acildi ama kullanilamaz)
- Yu, Rentzler, Wolf, "Nasdaq-100 Index Futures: Intraday Momentum or Reversal?" (JOIM): sayfa 404 verdi; icerik yalniz arama ozeti ("onceki gecenin getirisi agirlikla reversal ile iliskili") -> (memory/search snippet, unverified). Cok eski (2005).
- Kuzey Zhou ve digerleri: first-30min -> last-30min = REDDEDILDI listesinde.

---------------------------------------------------------------
## D3. Carver (Systematic Trading / Advanced Futures Trading Strategies)

Kitaplara erisim yok; yalniz blog sayfalari acildi.
### D3-1. Breakout kurali (dogrulandi): https://qoppac.blogspot.com/2016/05/a-simple-breakout-trading-rule.html
- Formul: forecast = 40*(price - roll_mean)/(roll_max - roll_min), roll_mean=(roll_min+roll_max)/2, rolling pencere = lookback is gunu; sonra EWMA smooth, span = max(int(lookback/4),1). Lookback'ler 10,20,40,80,160,320 (yorumda 2021: breakout10 pahali oldugu icin 20-320 kullaniliyor). Pooled forecast scalar: 0.714 / 0.791 / 0.817 / 0.837 / 0.841 / 0.834 (10..320). Forecast +-20 kirpilir (kitap/yorumdan; post govdesinde yok).
- Ortalama devir (37 vadeli, yilda): breakout10 88.9; 20: 41.3; 40: 20.1; 80: 9.75; 160: 4.59; 320: 2.13. Maliyetler SR birimi yilda (ornek: ham petrol 250g lookback ~0.06 SR/yil; 4g lookback ~0.40 SR/yil).
- Performans: yazar kasitli olarak getiri istatistigi VERMIYOR. => "net sonuc: not stated".
- Bizim icin: Carver'in tasarimi maliyeti SR/yil cinsinden olcup devire gore filtreliyor (hizli lookback pahali). Bu, Maven maliyet kuraliyla ayni mantik; kural olarak US100, XAU, BTC icin 40-320 breakout ensemble ve cost-per-turnover olcumu test edilebilir ama pozitif getiri iddiasi YOK (kanit degil).

### D3-2. Diger kurallar (dogrulandi): https://qoppac.blogspot.com/2017/06/some-more-trading-rules.html
Relative carry, normalised momentum (R=ΔP/σ, +-6 kirpma, EWMAC uzerinde), aggregate momentum, cross-sectional mean reversion; sonuc: "EWMAC+carry'e eklemek hafifce kotu, istatistiksel anlamsiz". Maliyet/scalar bu sayfada yok. Bizim enstrumanlara ozel pozitif kanit YOK.

### D3-3. EWMAC scalar'lari
Dogrulanmadi: arama ozetlerinde 16/64 icin 5.3 (EliteTrader, kitap s.285'e atif) ve 4.1 (QuantConnect) celisiyor -> (memory/search snippet, unverified). pysystemtrade defaults.yaml: https://raw.githubusercontent.com/robcarver17/pysystemtrade/master/sysdata/config/defaults.yaml (acildi): forecast_cap 20, average_absolute_forecast 10, percentage_vol_target 16, buffer_size 0.10, buffer_method forecast; EWMAC scalar'i orada YOK.
"Maliyet <= 1/3 ham SR" ve "hiz siniri" kurali: yalniz CXO Advisory arama ozeti (https://www.cxoadvisory.com/?p=27652), sayfa acilmadi -> unverified.

---------------------------------------------------------------
## D4. Chan / Kaufman / Fitschen

- Chan leveraged-ETF intraday momentum (kitap Algorithmic Trading 2013) - QuantRocket tekrar testi acildi: https://www.quantrocket.com/blog/leveraged-etf-intraday-momentum/ . Kural: onceki kapanistan 14:00'e getiri >+%2 ise long, <-%2 ise short (3x ETF => altta ~%0.67), kapanista cik; tarama 2/4/6/8%, en iyi 6%. DRN: 2011-12 ornek ici iyi, sonrasi maliyet sonrasi KARSIZ; 14 ETF seti, +-%6 esikle 2008-2016 net CAGR %31 Sharpe 1.95, 2017'den sonra DUZ (decay). Maliyet modeli: "not stated". Enstrumanimiz (US100 CFD) kaldiracli ETF degil; mekanizma (gunluk rebalance akisi) CFD'de yok. -> Uygulanamaz; ancak "yayin sonrasi decay" ornegi.
- Kaufman: yalniz Concretum PDF'i Kaufman 2013 (Trading Systems and Methods) ATR-band breakout'una atif yapiyor (D2-1). Kitap acilmadi.
- Fitschen "Building Reliable Trading Systems": yalniz yayinci/katalog ozeti goruldu (sistemler hisse scalping + emtia orta vade trend); kural/sonuc ucretsiz acilmadi. 

## D5. Alpha Architect / Quantocracy / Robot Wealth / Quantitativo / Quantpedia

- Quant Returns (Substack) "Overnight Mean-Reversion": https://quantreturns.substack.com/p/overnight-mean-reversion (acildi). Kural: gunluk, enstrumanlar arasi (ES, YM, NQ, EMD, NKD, RTY vadeli + ETF'ler) overnight (kapanis->acilis) getirisini cross-sectional demean et; dusuk overnight alan al, yuksek alani sat, esit agirlikli long/short (%100 long/-%100 short), acilista gir kapanista cik; iki yanli winsorize. Donem 2007-2025. Metinde sayisal vadeli sonucu YOK (grafik resim); biotech ETF CO-OC ort. gunluk %0.29, Sharpe 4.44 (brut mu net mi belirtilmemis). Maliyet rakami: not stated. Yazar: sinyal ve icra acilis fiyatina bagimli, perakende icin zor. Okuyucu yorumlari look-ahead soruyor, yanit gorulmedi. -> Dogrulanamaz; tek-enstrumanli (yalniz NQ) surum farkli hipotez olur.
- Quantpedia BTC intraday seasonality (21:00-23:00 UTC): bizde portfoyde (BTC 21-23 UTC); QuantConnect replikasyonlari Sharpe 0.77-0.85 (arama ozeti; sayfalar acilmadi) -> ek bilgi yok.
- Robot Wealth, Alpha Architect, Quantitativo: bu turda hicbir sayfa acilmadi / kural cikmadi -> kapsama DISI birakildi, uydurma yok.

---------------------------------------------------------------
## D7. Metodoloji (dogrulandi PDF'ten)

### Bailey & Lopez de Prado, "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality", Journal of Portfolio Management (forthcoming 2014; surum Temmuz 2014); SSRN 2460551 (https://papers.ssrn.com/abstract=2460551; PDF https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf acildi). JPM cilt/sayfa (40(5), 94-107) arama ozetinden, PDF'te dogrulanmadi.
Gerekli girdiler (PDF metnine gore): secilen stratejinin tahmini SR'si (periyodik, yillandirilmamis), orneklem uzunlugu T, getirilerin carpikligi ve basikligi (kurtosis), denenen tum denemelerin SR tahminlerinin varyansi V[{SR_n}], bagimsiz deneme sayisi N (bagimsiz degilse Appendix 3 ile efektif N). Beklenen maksimum SR (Eq. 1) Euler-Mascheroni sabiti (~0.5772) ve normal CDF'in tersini kullanir. DSR = PSR'nin esigi SR0 = E[max SR_n] ile degistirilmis hali. Sembolik formul PDF'ten metin olarak cikmadi (Yunan harfler kayip); standart yazim (memory, unverified):
  PSR(SR*) = Z[ (SR_hat - SR*) * sqrt(T-1) / sqrt(1 - g3*SR_hat + ((g4-1)/4)*SR_hat^2) ]
  SR0 = sqrt(V[SR_n]) * ( (1-gamma)*Zinv(1-1/N) + gamma*Zinv(1-1/(N*e)) )
  DSR = PSR(SR0).
Bizim projede N = denenen hipotez/parametre kombinasyonu sayisi (bagimsiz sayilan); ortusen bacaklar N'i degistirir.

### McLean & Pontiff (2016), "Does Academic Research Destroy Stock Return Predictability?", Journal of Finance
PDF (taslak) acildi: https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf . Dogrulandi: 97 degisken; getiriler orneklem disinda %26, yayin sonrasi %58 dusuk; fark %32 = yayin kaynakli islem tahmini; yayin sonrasi dusus, orneklem ici getirisi yuksek olan tahmincilerde daha buyuk; yayin sonrasi diger yayinlanmis portfoylerle korelasyon artiyor. (Cross-section hisse; vadeli/FX/kripto icin dogrudan sayi YOK.) "JF 2016" atfi: metinde "Forthcoming"; yil/cilt arama ozetinden.

### PBO (Bailey, Borwein, Lopez de Prado, Zhu 2017)
Yalniz Mesfin PDF'inde "Bailey et al. (2017)" olarak atif goruldu; tam kunye acilmadi -> unverified.

---------------------------------------------------------------
## Sonuc: Ilk 10 test adayi (guven sirali, hepsi acilmis kaynaktan)
1. Fast-alpha execution overlay (D2-1) - SPY->US100; ortusme: NQ ORB (kismi). Net slippage'siz.
2. VWAP trend (D2-2) - US100/CFD; spread'e cok duyarli, 15 islem/gun.
3. BTC Donchian ensemble 5-360 gun (D2-3) - swap dahil olculmeli.
4. Overnight Drift OD+ / BtD (D1-3) - ES/US100; maliyet sonrasi OD+ Sharpe 0.3, BtD sinyali signed volume ister.
5. MNQ gap-continuation short (D1-1) - yazarin "en yakin aday"i, T=1.46, yetersiz N.
6. London session drift long (D1-1) - dusuk guvenilirlik, GMM'siz basit surum.
7. Carver breakout 20-320 ensemble + SR-maliyet filtresi (D3-1) - getiri iddiasi yok, yontem.
8. Gold "Forecast-to-Fill" (D1-4) - kirilgan, Donchian ile ayni aile.
9. Overnight mean reversion tek enstruman (D5) - dogrulanamadi.
10. Chan 2PM-dev-hareket momentum (D4) - decay, uygulanamaz (ETF mekanizmasi).
