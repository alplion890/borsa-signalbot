# A_yarisma — Yarışma kazananları / sistem yazarları: testlenebilir kural setleri

Tarih: 2026-11-18. Yalnızca açılan sayfalardaki olgular; URL her iddiada. "(memory)" = hafızadan, doğrulanmadı. "not stated" = sayfada yok.
Genel uyarı: Hiçbir kaynakta bağımsız replikasyon bulunmadı. Unger Academy sayfaları kurs/kitap satış pazarlamasıdır (conflict of interest). Hiçbir sayfa maliyet/kayma dahil mi net söylemiyor (istisnalar aşağıda).

## 1. Turtle kuralları (A5) — EN TAM KURAL SETİ
Kaynak (PDF açıldı, metne çevrildi): originalturtles.org "The Original Turtle Trading Rules" (mirror: http://www.tradingwithrayner.com/wp-content/uploads/2014/11/OriginalTurtleRules.pdf). Yazar tarafı: Turtle eğitimi sonrası yayımlanan ücretsiz doküman (satış çıkarı: site "scam'lerle mücadele" diyor, ancak Faith ayrıca kitap satar).
- N = True Range'in 20 gün EMA'sı: N = (19*PDN + TR)/20; TR = max(H-L, H-PDC, PDC-L). Başlangıç: 20 gün SMA.
- Unit = %1 equity / (N * dolar-per-puan) (örnek: 1.000.000$ / 0.0141*42.000 = 16.88 -> 16).
- System 1 giriş: önceki 20 günün high/low'unu 1 tick aşınca (gün içi, kapanış beklenmez; açılış gap'inde açılışta). Önceki breakout kazanç idiyse (2N aleyhine gitmeden önce 10 gün çıkış kâr) sinyal atlanır; atlanırsa 55 gün breakout "failsafe" girişi.
- System 1 çıkış: long için 10 gün low, short için 10 gün high.
- System 2 giriş: 55 gün breakout, tüm sinyaller alınır. Çıkış: 20 gün low/high.
- Ekleme: ilk unit breakout'ta, her 1/2 N'de bir ek unit (gerçek fill'den), max 4 unit/piyasa.
- Stop: 2N (giriş fiyatından), ek unit eklendikçe önceki stoplar 1/2N yükseltilir (hepsi son unit'ten 2N). Alternatif "Whipsaw": 1/2N stop, orijinal fiyata dönünce yeniden giriş.
- Risk limitleri: tek piyasa 4 unit; yakın korele 6; gevşek korele 10; tek yön 12 (PDF'te "Loosely correlated"/"Single Direction" satırları var; tam tablo okunmadı).
- Enstrüman: 1983 vadeli piyasalar (altın örnek olarak PDF'te). Örnek dönem/performans: not stated (bu dokümanda). Maliyet: dokümanda slippage 1/2N örneği var, ama backtest maliyeti not stated. Bağımsız replikasyon: mql5 makalesi uygulamış (https://www.mql5.com/en/forum/513829, sadece "20/55 breakout, 10/20 çıkış, 2N stop, Wilder N" özetliyor) — performans doğrulaması değil.
- Test notu (bizim için): sürekli trend sistemi, 1H/günlük; XAU, NQ, BTC, majör FX'te günlük bar ile denenebilir. Not: PDF'in sayfa 1 başlığı "Fighting the scams..." ile başlıyor.

## 2. Larry Williams (A3)
### 2a. Volatility breakout (swing range versiyonu) — ikincil kaynak
https://www.mql5.com/en/articles/20862 (MQL5 yazarı; kitap adı belirtilmiyor, "Williams'ın swing yöntemi").
- Swing A = |High[3 gün önce] - Low[son kapanan gün]|; Swing B = |High[1 gün önce] - Low[3 gün önce]|; range = max(A,B).
- Long giriş: open + 0.5*range; short: open - 0.5*range (market emri, fiyat geçince; aynı anda tek pozisyon).
- Stop: entry -/+ 0.5*range; hedef: stop mesafesi * 4.0. Başka çıkış yok.
- Yazarın backtest'i: XAUUSD, D1, 2025-01-01..2025-12-31, long-only, %1 risk, 10.000$ -> net 4.450,23$ (~%44), win 48.39%. Tek konfigürasyon, optimize değil, tek yıl; maliyet not stated; OOS yok. Replikasyon: yok.
### 2b. Oops (gap fail)
- Oxford Strategic (https://oxfordstrat.com/trading-strategies/bull-oops-pattern/): Long: Open[bugün] < Low[dün]; giriş: dünkü low'da buy stop. Çıkış: n. gün kapanış (n=1..40) ya da entry - ATR(20)*k (k 1.0..6.0), sabit stop ATR(20)*6. 42 vadeli piyasa, 1980-2011, %1 fixed fractional, 1M$; Şekil 1 komisyon/kayma 0, Şekil 2 round-turn 50$. Sayısal sonuç sayfada metin olarak yok (sadece grafik); derece "C".
- Unger Academy testi (https://ungeracademy.com/?p=7737): DAX vadeli, günlük bar, 2010-günümüz, 08:00-22:00 seans. Gap aşağı açılışta dünkü low'a dönünce long (gap yukarı: short). Çıkış: 2.000 EUR parasal stop; kârdaysa sonraki açılışta çık. Senaryo 1 (her gap): net ~163k EUR, maxDD ~45k, ort. işlem ~230; Senaryo 2 (gap>=15 puan): net ~146k, DD ~38k, ort. ~400. 2023-2024 ve cari yılda belirgin zarar, Ekim 2022'den itibaren eğri düşüyor. Maliyet: not stated. Sonuç: edge zayıflamış.
- Unger'in Oops makalesi (https://ungeracademy.com/?p=6300): çıkış "first profitable open" (short için pozisyon, giriş seviyesinin altında bir açılışta kapanır); min gap 15-20 tick önerisi; performans/dönem not stated.

## 3. Linda Raschke (A4) — Street Smarts (1996, Connors ile)
NOT: Birincil kaynak (kitap) açılmadı; WebFetch technical.traders.com 403 verdi. Aşağıdakiler therighttrader.com'un yeniden yazımıdır (kendi filtrelerini eklediğini belirtiyor); win-rate "no reliable published figure".
### 3a. Turtle Soup (günlük) https://therighttrader.com/learn/trading-strategies/turtle-soup
- Short: bugünün high'ı önceki 20 seansın en yükseğini aşar ve o önceki extreme >= 4 işlem günü eski. Giriş: bugün kapanış önceki 20g high'ın altındaysa kapanışta short. Stop: bugünün high'ı + 1 tick. Çıkış: sonraki seans kapanışı (stop yoksa). Sinyal günü range > 3*ATR(14) ise atla. Long ayna. %1 risk.
- Plus One: sonraki seansta fiyat önceki 20g high'ın altına dönerse short; stop sinyal gününün high'ı ötesi.
- Not: sayfa "intraday kitap versiyonu tick offset kullanır, bu günlük versiyon kullanmıyor" diyor — yani birebir orijinal değil.
### 3b. 80-20 https://therighttrader.com/learn/trading-strategies/eighty-twenty-setup
- Bullish setup günü: (Open-Low)/Range <= 0.20 ve (Close-Low)/Range >= 0.80 (bearish ayna). Sayfa ek filtre koymuş: range >= önceki 10 seans ortalama range (kitapta olmadığını söylüyor).
- Giriş (ertesi seans, gün içi): long için fiyat setup low'unun altına inip geri yukarı geçince buy stop setup low'da; çıkış: seans kapanışı, stop: fill'e kadarki en düşük - 1 tick (stop > 2*ATR(14) ise atla).
### 3c. Holy Grail: sadece özet (ADX(14)>30, 20 EMA'ya pullback) — WebSearch özeti, sayfa açılmadı; kural detayı doğrulanmadı.
Replikasyon/maliyet/OOS: yok.

## 4. Kevin Davey (A1)
- https://kjtradingsystems.com (açıldı): ücretsiz içerik = Monte Carlo Excel simülatörü, quiz, e-kitaplar ("9 Terrific Trading Entries, 7 Sensible Exits", "Algo Trade The Strategy Factory Way"). Ücretsiz Mini S&P algo: "kurallar, TradeStation workspace, kod açıklanıyor" ama kayıt (signup) arkasında; sayfada iddia: "5 yılda 121K$+ hypothetical OOS kâr/kontrat; 112K$ yayından beri (1 kontrat, işlem maliyeti dahil)" — doğrulanamaz, satış sayfası.
- https://kjtradingsystems.com/free.html: tek ifşa edilen kural = 200 günlük MA: fiyat üstüne geçince al, altına geçince sat; stop/hedef/enstrüman/sonuç yok.
- Euro Night stratejisi kitabın Ek B'sinde (memory/arama sonucu: TradeStation kodu) — metni okunamadı. Davey'nin "kural" yöntemi (3-7 kural, gecikmiş giriş/çıkış testi, Monte Carlo, incubation) ikincil özetlerde var, kendi sayfasından doğrulanmadı.
- Çıkar çatışması: kitap, kurs, signal satışı. Sonuç: testlenebilir tam kural seti AÇIK KAYNAKTA BULUNAMADI.

## 5. Andrea Unger (A2) — Unger Academy blog (hepsi pazarlama: ücretsiz strateji seansı, kitap, AlgoTrader Fast)
Tüm sayfalarda maliyet çoğunlukla not stated; robustluk: yalnız "OOS dönemi" anlatımı, parametre duyarlılığı/MC/WF gösterilmiyor.
- DAX (https://ungeracademy.com/blog/trading-dax-futures-eur122-000-in-2-years-with-these-strategies-explanation-rules): 15dk bar. S1 intraday bias long-only: 17:15'te sinyal, 17:30 bar açılışında gir, 21:15 bar açılışında çık (~22 bar), stop/hedef yok; geliştirme 2017, OOS 2017-2023; ort. işlem 189 EUR (komisyon/kayma hariç) — sayfa içinde ~190 net diye çelişiyor; son 2 yılda 173 işlem, %56 kazanan. S2 çok günlük trend: 15dk bar kapanışı Bollinger üst bandı üstünde -> long, alt bant altında -> short (band parametreleri not stated); stop 100 puan, breakeven 120, TP 650; ~94 bar; maliyet dahil modelleme iddiası.
- Altın (https://ungeracademy.com/blog/intraday-trading-on-gold-usd37-000-of-gain-in-2-years-with-these-strategies-rules-details): 5dk bar. S2 trend: önceki seans kapanışı bir öncekinden "uzak değil" ise dünkü high kırılımında long / low kırılımında short; çıkış seans sonu + parasal stop/TP/breakeven (değerler not stated). S1 reversal kuralı belirsiz. 2008 veri; ~15 yıl ~600 işlem net ~67k$ (S1), S2 ~1.200 işlem ~202k$; maliyet not stated; replikasyon imkansız (eksik parametre).
- Nasdaq (https://ungeracademy.com/blog/2-strategies-to-exploit-the-downtrends-in-nasdaq-simple-rules-great-performance): S1 trend: dünkü high - 10 puan (long), dünkü low + 35 puan (short), 11:00 Chicago'dan sonra; çıkış/stop not stated. S2 mean-rev: dünkü high kırılımı başarısız olup geri geçince short (ayna long), gün sonu çıkış; ort. işlem ~145$. Sayısal performans/dönem not stated.
- Nasdaq reversal (https://ungeracademy.com/blog/strategy-of-the-month-february-2025-a-reversal-strategy-for-nasdaq-futures): NQ 5dk; dünkü low altına düşünce long, dünkü high üstüne çıkınca short; SL/TP/breakeven değerleri not stated; ort. işlem 370$; filtreler tanımsız.
- Çıkar çatışması: yüksek.

## 6. Yarışma kazananları (A6)
Arama (https://www.forex.in.rs/edge-narrative-discipline, https://itiger.com/news/2511097706 vb.): Kevin McCormick (2021) ve Brent Carlile (2024, Fed fiyatlama makro) için anlatı var, kural seti YOK. Mike Cook (2014, %366 net — kitap listesinde) kural ifşası doğrulanmadı. Sonuç: yarışma kazananlarından tam kural seti bulunamadı.

## 7. StrategyQuant topluluğu (E4) — veri madenciliği riski YÜKSEK
- https://strategyquant.com/shared/swing-strategy-for-gold-h1-timeframe/ (Tomas Vanek, 2024-10-17): XAU H1; long: bir koşul seti + son 610 barın en yükseğinde giriş emri (9 bar geçerli), SL 805 pip, TP 2350 pip; short: son 615 barın en düşüğünde, SL 865, TP 2255, 36 bar sonra kapat. "2 OOS, Monte Carlo, slippage testi" iddiası; dönem/maliyet/sayısal sonuç not stated; tam mantık .sqx dosyasında. Parametre değerleri 610/805/2350 gibi — tipik data-mined aşırı uyum işareti. Replikasyon yok.
- https://strategyquant.com/shared/simple-workflow-on-nasdaq-is-and-oos-verification-for-multi-timeframe-strategy/: sadece iş akışı (arama sonucu özeti; sayfa açılmadı).

## Boşluklar
- Davey'nin gerçek kuralları (Euro Night, Mini S&P): kayıt/kitap arkasında; açık değil.
- Raschke ve Williams birincil metin (kitap) açılmadı; kurallar ikincil.
- Hiçbir kaynakta bağımsız replikasyon, gerçekçi maliyet modeli veya WF/MC sayısal sonucu yok.
- Holy Grail ve Williams'ın "range expansion" orijinal kitap kuralı doğrulanmadı.
