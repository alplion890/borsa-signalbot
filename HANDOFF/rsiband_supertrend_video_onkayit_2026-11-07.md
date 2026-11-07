# "Ücretsiz al-sat sistemi" (RSI Bands + Supertrend + TDI + RSI, Heikin Ashi) — ön-kayıt (2026-11-07)

Bu belge koşumdan ÖNCE commit edilir. Kaynak: YouTube `02i_B842SRk`, "Kripton Gezegeni",
"Bu ÜCRETSİZ AL-SAT SİSTEMİNİ Öğrenmeden İşlem Açma! (TradingView)". Video bir broker (XM ortaklık kodu)
ve ücretli sinyal grubu reklamı içerir. İddia: "tüm zaman dilimlerinde, kripto ve forexte çalışır";
hiçbir sayı (WR, R, örneklem) verilmedi — yalnız seçilmiş grafik örnekleri. `elenenler --kontrol`:
supertrend / rsi / heikin katalogda YOK (ölçülmemiş).

## Göstergeler (videodaki ayar ekranlarından okundu, 01:11–03:21)
Tümü **Heikin Ashi** mumları üzerinde hesaplanır (video grafiği HA'ya çeviriyor, TradingView göstergeleri grafik mumundan hesaplar).
- **RSIBANDS_LB** (LazyBear): RSI length 12, OB 70, OS 30. Üst/alt bant = RSI'ın 70/30 olacağı fiyat.
- **Supertrend**: ATR period 10, kaynak hl2, çarpan 0.8, ATR yöntemi RMA ("Change ATR Calculation Method" açık).
- **TDIGM**: RSI period 11, band 31, fast MA 1, slow MA 9.
- **RSI**: uzunluk 10, kaynak kapanış, RSI-MA = SMA 14.

## Kurallar (transkript 03:26–06:50'den)
LONG (short ayna):
1. **Silahlanma:** HA mumu RSI alt bandının altına sarkar (`HA_low < lb`). (Short: `HA_high > ub`.)
2. **RSI kesişimi:** silahlanmadan sonra RSI(10) kendi SMA(14)'ünü aşağıdan yukarı keser. Video "30 altında olmalı,
   ama üstünde de kabul" diyor → seviye şartı yok.
3. **Tetik:** kesişimden sonraki **ilk Supertrend buy** (trend aşağı→yukarı dönüşü). Giriş tetik barının kapanışı.
4. **Hedef:** RSI üst bandı (tetik barındaki değer, sabit — motor dinamik hedef desteklemiyor).
5. **Stop:** RSI alt bandı (tetik barındaki değer) eksi tampon. Video "belli bir yüzde altı" diyor, sayı yok →
   **birincil tampon 0.5·ATR(14)** (gerçek mumlardan). Duyarlılık: 0 ve 1.0·ATR, hepsi raporlanır, seçilmez.
6. Silahlanma 30 bar içinde tetiklenmezse düşer; her Supertrend dönüşünden sonra durum sıfırlanır.
- **Varyant B (TDI):** ek şart — silahlanma ile tetik arasında TDI fast (RSI11) slow MA9'u aynı yönde kesmiş olmalı.
  ("İki indikatörün benzer hareketi" ölçülemez; en yakın ölçülebilir karşılığı bu.)

## Motor ve maliyet (tek motor, tek maliyet modeli)
`honest_engine.simulate_trades` (bar/SL-önce), dolumlar **gerçek** OHLC'den (HA fiyatından değil).
`INSTRUMENTS` maliyeti (BTC 0.0006/yön, FX/XAU/NQ config). Video RR filtresi koymuyor → `min_rr=0.01`, `max_rr=20`, `max_hold=480` bar.
Ayrıca 2x maliyet koşusu.

## Veri ve evren
- **Birincil (videonun enstrümanı):** BTCUSDT 15m, 1h, 4h (Binance; 15m/1h önbellek 2023-06→2026-06; 4h 1h'den yeniden örneklenir).
- **İkincil ("forexte de çalışır" iddiası):** EURUSD, GBPUSD, XAUUSD, NASDAQ100 — 15m ve 1h (15m'den yeniden örnek), Dukascopy önbellek.

## Karar kuralı (sonuca bakmadan sabit)
Sistem bir zaman diliminde **"aday"** sayılır ancak ve ancak birincil tamponla (0.5 ATR), varyant A'da:
(a) n ≥ 30, (b) 1x maliyetle exp_R > 0, (c) 2x maliyetle exp_R > 0, (d) verinin iki yarısında da exp_R > 0.
Birincil 3 BTC zaman diliminden hiçbiri geçmezse sistem **ELENİR** ve `elenenler` kataloğuna girer.
Çoklu test uyarısı: 3 TF × 2 varyant × 3 tampon + 8 ikincil seri koşuluyor; tek bir hücrenin pozitif olması tek başına kanıt değildir.
Sonuç LIVE kuralını, riski veya portföyü kendiliğinden değiştirmez.

## Yasak
Ara sonuca göre parametre, tampon, pencere, enstrüman veya filtre değiştirmek.
