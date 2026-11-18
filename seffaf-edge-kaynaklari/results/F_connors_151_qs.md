# F: Connors / 151 Strategies / QuantifiedStrategies / Alvarez (2026-11-18)

Kural: yalniz acilan sayfalarda gorulen olgular; her iddianin yaninda URL. "(search-snippet)" = arama ozetinde goruldu, sayfa acilamadi/paywall. "(memory)" = dogrulanmadi.

## OZET (en onemli bulgu)
- **Bagimsiz, 2010 sonrasi, maliyet dahil, endeks/SPY/QQQ/NQ icin Connors replikasyonu BULUNAMADI.** Bulunanlar: (a) saticinin kendi backtesti (QS, StrategyQuant), maliyetsiz; (b) tek-hisse/ETF sepeti (Quantitativo, Concretum); (c) tek bagimsiz NAS100 CFD testi (backtrex) = zayif.
- Connors'in kendi orijinal testleri 1995-2007, maliyetsiz, OOS yok, data-mining duzeltmesi yok: https://cxoadvisory.com/technical-trading/a-few-notes-on-short-term-trading-strategies-that-work
- 151 Trading Strategies: **formul kitabi, hicbir stratejide backtest/performans YOK** (PDF'ten okundu). Kripto bolumu sadece ANN + Twitter-sentiment (ML), kural yok.
- QuantifiedStrategies kalite notu: bircok sayfa paywall'lu (kurallar gizli), sayfada "slippage/komisyon dahil degil" diyor, sayfa icinde tutarsiz buy&hold rakamlari (QQQ B&H %6.39 vs %9), uretilmis/genel izlenimli "OOS 2015-2025 hafif bozulma" iddiasi veri vermiyor. Guven: dusuk-orta.

## ADAYLAR

### 1. IBS (Internal Bar Strength) mean reversion — SPY/QQQ/NQ (YENI, kirpilmis listemizde yok)
- Kural: IBS=(C-L)/(H-L) onceki gun; IBS<0.2 kapanista al; IBS>0.8 kapanista sat (herhangi sonraki gun). Long-only. https://www.quantifiedstrategies.com/ibs-internal-bar-strength-indicator-strategies/
- SPY 1993-bugun: 919 islem, ort %0.41, win %68, CAGR %12.5 (B&H %9.9), PF 1.9, maxDD -%26. QQQ: 742 islem, %0.56/islem, CAGR %16.6 (B&H %9). **Slippage+komisyon dahil degil** (ayni sayfa).
- Bozulma kanitlari: QS "2017 ve 2018'de kotu, 2018 yy ilk negatif" ve 2019-2020 toparlandi (ayni sayfa). Kinlay: SPY'de etki ~2013'ten beri zayifladi (%99 guvende dogrulanmadi), 2015-2016 YTD negatif; QQQ rendition'da komisyon $0.005+slippage $0.02/hisse ile IBS-tek getirileri "cok dusuruyor", "verimlilik ~%55" https://jonathankinlay.com/?p=2199
- Orijinal: Pagonidis 2013: IBS<0.20 sonrasi ort %0.35, IBS>0.80 sonrasi -%0.13, 1990'lardan beri, yuksek hacim gunlerinde (ikincil kaynak Kinlay, ayni URL). Bagimsiz yeni replikasyon: arXiv 2306.12434 ulke-ETF sepeti (sadece search-snippet): https://arxiv.org/pdf/2306.12434
- NQ vadeli: IBS ES/NQ/YM testi, ES 765 islem PF 1.72 yillik getiri %4.91 (tek kontrat, birlesmeyen); NQ "ham dolarda en guclu" ama rakam metinde yok; kurallar/tarih paywall. https://algotr.substack.com/p/the-mean-reversion-portfolio-that
- Cakisma: reddettigimiz listede yok. Ancak "inside-day break" / "first30-last30" ile farkli. Yorum yok.
- Gold icin: QS "IBS altin ve metallerde zayif" https://www.quantifiedstrategies.com/ibs-internal-bar-strength-indicator-strategies/

### 2. Connors RSI(2) klasik (trend filtresi + RSI(2) < 5 veya 10, SMA5 cikis)
- Kural (kitap, QS ozeti): close>SMA200; RSI(2)<5 (veya <10) kapanista al; close>SMA5 (veya RSI(2)>65-75) cikis. Short ayna: close<SMA200, RSI(2)>95. https://www.quantifiedstrategies.com/rsi-2-strategy/
- QS SPY 1993-: RSI(2)<10 al/ >80 sat: ort %0.9, CAGR %9, maxDD %34, %28 piyasada; 200MA filtresi ile CAGR %6.8, DD %31, %18 piyasada (ayni sayfa; maliyet belirtilmemis).
- **En guclu bagimsiz NQ kanit (olumsuz):** NAS100 CFD gunluk 2016-10..2026-10, RSI(2)<5 + close>SMA200, cikis close>SMA5 veya <SMA200, long+short, %0.02/taraf komisyon: toplam +%26.9 vs B&H +%528.3, CAGR %2.4 vs %20.2, 65 islem, win %75.38, PF 1.55, ort kazanc %1.58 / kayip %3.11; yillar: 2020 -%12.2, 2018 -%1.4, 2019 -%1.7. https://backtrex.com/en/backtests/connors-rsi-2-nasdaq-100
- NDX hisseleri 2006-2025 (4 slot, RSI(2)<10, close<SMA5 ve >SMA200): yillik %17.84, win %64.33, PF 1.45, maxDD %29.15, Sharpe 1.10; maliyet yok, OOS yok, survivorship belirsiz. https://backtest.substack.com/p/the-2-period-rsi-a-simple-system
- S&P 500 tum tarihsel bilesenler 1996-Kas 2025 (RSI(2)<5 + close<SMA5, cikis close>SMA5 veya 5 gun): 114,189 islem, ort 45 bps, hit %64; net/brut belirsiz; kapasite/"opportunity-set bias": gunde 5 islem sinirinda tam-ornek ortalama hicbir bootstrap'te yakalanamadi. https://concretumgroup.com/opportunity-set-bias-in-mean-reversion-trading-systems/
- Kripto (13 strateji, taker+slippage, OOS): Connors RSI-2 1/5 gate, -3.7 bp/islem net, 12,141 OOS islem (brut pozitif, net negatif). Kurallar/varlik listesi yok. https://dev.to/tessen/we-graded-13-famous-trading-strategies-on-6-years-of-data-all-13-failed-26o4
- EURUSD saatlik 2011-: RSI(2)<5 + >SMA200, cikis SMA5, hit %78, risk/odul 0.47, maliyet YOK. https://abouttrading.substack.com/p/back-testing-a-famous-profitable
- Alvarez: S&P 500 1957-2023, RSI2<20 sonrasi 1 gun getiri: 1957-82 ters (momentum), 1983-94 duzensiz, 1995+ mean-reversion; "2000 ortasindan beri az degisti"; 2020: %0.65 vs %0.07 (tum gunler). Komisyonsuz; 2010+ rakami grafiklerde. https://alvarezquanttrading.com/blog/mean-reversion-vs-trend-following-through-the-years/
- Degerlendirme: endekste net kazanc kanitsiz; hisse sepetinde guclu ama kapasite sorunu. NQ CFD icin tek bagimsiz test zayif.

### 3. Connors Double 7s (SPY): close>SMA200 ve close <= 7 gunluk en dusuk kapanis -> al; close >= 7 gunluk en yuksek kapanis -> sat
- SPY 1993-Eyl 2026: 333 islem, ~$143k net ($10k, %100), PF 2.35, Sharpe 0.85, maxDD ~%12.5, ~%28 piyasada; **sifir komisyon/spread/slippage; train/test yok**; vendor (StrategyQuant). https://strategyquant.com/blog/larry-connors-double-7-strategy-tested-on-spy-and-8-other-markets/
- Diger 8 piyasa rakami sayfada yok; uzun vadeli tahvilde "kotu".
- Bagimsiz 2010+ replikasyon yok.

### 4. TPS (Time-Price-Scale in), ETF sepeti
- Kural: close>SMA200, RSI(2)<25 iki gun ust uste -> pozisyonun %10; sonraki gunler close<onceki giris -> +%20, +%30, +%40; cikis RSI(2)>70; short ayna (RSI(2)>75 x2, SMA200 alti, cikis <30); sonraki acilis. https://hn.jakechampion.name/reader/https://www.quantitativo.com/p/trading-etfs-while-fear-and-greed
- Norgate ETF'ler, ort. >$100M hacim, 1998/99+; **2 bp slippage+maliyet**; nihai (3-6 pozisyon, long+short): yillik %21.0, Sharpe 0.91, maxDD %35, yillik ~81 islem, win %77. Tek pozisyon 1/10: %4.7, Sharpe 0.74, DD %14.5. OOS/2010 ayrimi YOK; yazar DD'yi yuksek buluyor.
- Tek endekse (NQ) uygulama: sepet olmadan getiri dusuk (yukaridaki tek pozisyon satirlari).

### 5. Connors %b: close>SMA200; Bollinger %b < 0.2 ust uste 3 gun -> kapanista al; %b>0.8 kapanista cikis
- Kural: (search-snippet, QS sayfasi paywall) https://quantifiedstrategies.substack.com/p/larry-connors-b-strategy-bollinger-ab6 ve web ozeti. SPY 1993-2024: 63 islem, ort ~%1.3, ~%4 piyasada (snippet; dogrulanmadi).
- ES+TY vadeli (1997/2001-), sinyal "temel mean reversion", ES win %74.41 PF 2.48; ES sonuclarinin yarisindan fazlasi yayin (2009) sonrasi (resmi OOS degil); maliyet belirtilmemis; kurallar gizli. https://algotr.substack.com/p/this-simple-2009-strategy-still-wins
- Cok seyrek -> NQ icin istatistiksel guc dusuk.

### 6. Cumulative RSI (Connors-Alvarez) — SPY
- Kural: close>SMA200, 2 gunluk RSI(2) toplami < Y; cikis RSI(2)>65. (search-snippet: autochartist/ThinkOrSwim ozetleri; kitap SPY 1993-2007, %88 dogruluk) -> in-sample; sayfa acilmadi. Alvarez sitesinde OOS testi bulunamadi.

### 7. VIX stretch (Connors)
- Search-snippet: VIX 10-gun MA'nin >=%X ustunde ... kural ve rakam sayfada dogrulanamadi; %5 ve 3+ gun, RSI(2)>65 cikis varyanti forumda (NexusFi, anekdot). Kullanilmamali (kural tutarsiz). CXO: VIX tabanli sonuclar 1995-2007 maliyetsiz.

### 8. Donchian 15g + ADX(14)<25 — BTC long-only (QS) [Donchian XAU ile ayni ailede]
- Kural: BTC close > 15 gun yuksek ve ADX(14)<25 -> kapanis/ertesi acilis al; close < 15 gun dusuk -> cik; short yok. CAGR %90 vs B&H %66, 35 islem, win %63, ~%50 piyasada; veri "201x"den (basi kesik); **maliyet belirtilmemis**, ChatGPT ile uretilmis, OOS yok. https://www.quantifiedstrategies.com/how-we-built-bitcoin-trend-following-strategy-using-chatgpt/
- Not: BTC fiyat hareketinin ~yari pozisyonda; 35 islem = dusuk n.

### 9. 151 Strategies — endeks/FX/emtia/kripto uygulanabilir formuller (backtest YOK)
Kaynak: https://www.smallake.kr/wp-content/uploads/2019/12/SSRN-id3247865.pdf (SSRN 3247865 tam metin, yerelde pdftotext ile okundu).
- 3.15 Channel/Donchian: Bup=max(P(1..T)), Bdown=min; floor'da al, ceiling'de sat (mean-reversion yorumu) ya da kirilimi takip (trend). (Donchian XAU ile ortusen.)
- 3.11 Tek MA: P>MA(T) long, P<MA(T) short; 3.12 iki MA.
- 4.4 Mean-reversion (ETF): IBS=(PC-PL)/(PH-PL); IBS yuksek "pahali", dusuk "ucuz"; ETF'leri IBS'e gore sirala, ust desil short alt desil long (dolar-notr) (kitapta tek paragraf).
- 4.6 Multi-asset trend: kumulatif getiri Rcum (6-12 ay) >0 ve P>MA(100-200), agirlik w ~ Rcum/sigma^2.
- 6.5 Endeks vol-targeting: w = sigma_hedef/sigma, haftalik/aylik rebalans, esik ile.
- 8.1 FX: HP filtreli iki MA; 8.2 carry (forward premium'daki para birimini sat, iskontoyu al); 8.4 momentum+carry kombinasyonu (min-varyans agirliklari).
- 10.3 Vadeli contrarian: haftalik getiri Ri, w_i = -gamma(Ri - Rm), dolar-notr, hacim/OI filtreli varyant (10.3.1); 10.4 vadeli trend: w ~ sign(Ri)/sigma_i. Evren genis vadeli sepeti ister (NQ/Gold/FX tek basina degil).
- 9.1 emtia roll-yield, 9.4 value: carry/curve verisi gerekir.
- 18 Kripto: sadece ANN (BTC kisa vade) ve Twitter naive-Bayes; kural yok.
- Hicbirinde performans/maliyet/OOS yok; "aday" degil, test edilmemis formul listesi.

## KISA YARGI (olgu)
- Test edilebilir ve ONEMLI: IBS (1), Connors RSI(2) (2, NQ'da olumsuz bagimsiz kanit), Double 7 (3). 4-7 ya seyrek ya kural eksik.
- Hicbiri icin bagimsiz + 2010 sonrasi + maliyetli NQ/SPX replikasyonu yok; IBS icin 2013 sonrasi zayiflama yazili (Kinlay, QS).
- Altin: QS "altin mean reversion daha az" ve IBS altinda zayif (yukaridaki URL'ler); FX: Connors EURUSD testi maliyetsiz, ters bir beklenti raporu yok.

## Kaynak listesi
1. https://www.quantifiedstrategies.com/rsi-2-strategy/
2. https://www.quantifiedstrategies.com/connors-rsi/
3. https://www.quantifiedstrategies.com/ibs-internal-bar-strength-indicator-strategies/
4. https://www.quantifiedstrategies.com/rsi-mean-reversion-trading-strategy/ (kurallar paywall)
5. https://www.quantifiedstrategies.com/how-we-built-bitcoin-trend-following-strategy-using-chatgpt/
6. https://www.quantifiedstrategies.com/bitcoin-intraday-seasonality-trading-strategy-backtest-results/ (BTC 21-23 UTC; portfoyde, ortusuyor)
7. https://www.quantifiedstrategies.com/gold-trading-strategies/ (kurallar gizli)
8. https://alvarezquanttrading.com/blog/mean-reversion-vs-trend-following-through-the-years/
9. https://alvarezquanttrading.com/blog/spy-sso-and-tlt-strategy/ (aylik SPY/TLT SMA200 rotasyonu 2007-2024; sayisal CAR/MDD metinde yok, maliyet yok, OOS yok)
10. https://strategyquant.com/blog/larry-connors-double-7-strategy-tested-on-spy-and-8-other-markets/
11. https://backtrex.com/en/backtests/connors-rsi-2-nasdaq-100
12. https://backtest.substack.com/p/the-2-period-rsi-a-simple-system
13. https://concretumgroup.com/opportunity-set-bias-in-mean-reversion-trading-systems/
14. https://hn.jakechampion.name/reader/https://www.quantitativo.com/p/trading-etfs-while-fear-and-greed
15. https://jonathankinlay.com/?p=2199
16. https://algotr.substack.com/p/the-mean-reversion-portfolio-that , https://algotr.substack.com/p/this-simple-2009-strategy-still-wins
17. https://cxoadvisory.com/technical-trading/a-few-notes-on-short-term-trading-strategies-that-work
18. https://dev.to/tessen/we-graded-13-famous-trading-strategies-on-6-years-of-data-all-13-failed-26o4
19. https://articles.stockcharts.com/article/articles-arthurhill-2016-12-systemtrader---testing-and-tweaking-an-rsi-mean-reversion-system-for-spy-qqq-and-ijr/ (RSI(5) <30/>70, SMA50>SMA200 filtresi, SPY/QQQ/IJR 2000-2016, $10 komisyon; tablolar gorsel, sayisal sonuc yok)
20. https://articles.stockcharts.com/article/articles-arthurhill-2018-03-systemtrader---would-you-have-the-nerve---revisiting-mean-reversion-and-adding-leverage/
21. https://www.smallake.kr/wp-content/uploads/2019/12/SSRN-id3247865.pdf

## Erisilemeyen
- QS RSI-2/Connors sayfalari WebFetch'te bot dogrulamasina takildi; tarayici panesinde sayfa kendiliginden gecti (CAPTCHA cozulmedi). QS %b, R3, 3-day high/low, multiple-days-up, "Gold weekly mean reversion" kurallari paywall; kitap (Connors) sayfalari acilmadi.
- Reddit r/Trading RSI2 thread (mirror ECONNREFUSED); pulse.bot 404.
