# Ön-kayıt: derin tarama adayları C1–C8 (2026-11-20)

Test koşulmadan ÖNCE yazıldı. Kaynak: `edge_arama_5k10k/RAPOR.md` + `results/*.json` (18 kalem, Haiku taraması).
Toplam bağımsız test **16** → Bonferroni α = 0.05/16 (iki yönlü, `kaynak_adaylari.judge` ile aynı: alpha = 0.05/16/2).
Parametre taraması YOK. Kaynakta olmayan değer aşağıda sonuca bakmadan sabitlendi. Geçmeyen aday yeniden tanımlanmaz.

## Veto ile alınmayanlar (katalog `rejected`/`retired`, yeniden test edilmez)
ITSM (`gao_itsm_first30_last30`), FX fix dönüşü (`fx_fix_reversal_london_tokyo`), opex haftası long (`opex_week_long`),
son-30-dk momentumu / LETF / GEX mekanizması (`baltussen_last30_momentum`), ay dönümü +1 (`turn_of_month_plus1`),
altın EA'ları (`seffaf_kaynak_b1_b6`), ORB ailesi.

## Veri yüzünden alınmayanlar
GEX (opsiyon zinciri ücretli), TICK/breadth (feed yok), kripto çeyrek-saat dönüşü (1 dk BTC verisi yok; 15 dk ile
test kuralı değiştirir), NQ CISD London 2R (sweep/displacement eşikleri tanımsız; Sweep ile aynı aile),
tug-of-war (hisse kesiti; endeks hali C7 ile aynı).

## Ortak
- Veri: Dukascopy önbellek 5 dk 2012–2026 (`history_fetch.load_history`, UTC). ABD seansı NY saatine çevrilir.
  NYSE takvimi `kaynak_adaylari.NYSECalendar` + `SPECIAL_CLOSED`. Günlük kapanış = 15:55 ET bar kapanışı
  (`kaynak_adaylari.us_closes` ile aynı). Günlük ATR14 = RTH (09:30–16:00 ET) günlük OHLC'den Wilder ATR,
  önceki güne kadar (bilinen).
- VIX/VIX3M/TLT: yfinance günlük (^VIX, ^VIX3M kapanış; TLT Adj Close), 2011-12'den.
- Maliyet: Maven `outputs/intraday/mt5_bridge/reality_profile.csv` (ölçüm 2026-11-12) `real_cost_per_side_central`;
  rapor 3 satır: maliyetsiz / merkez / 2× merkez (`judge`). Gece taşıyan işlemlerde Maven endeks swap'ı
  gece başına 0.000118 (B7 ile aynı, 2026-11-18) ayrı satır; swap 0 satırı da verilir. Geçme kararı swap'lı satırda.
- Geçme (`judge`): merkez ortalama > 0, bootstrap alt sınır > 0, <2022 ve 2022+ ortalamaları > 0, 2× > 0, ve
  adayın `condition` şartı (varsa).
- Bar içi sıra bilinmiyorsa stop önce (dürüst varsayım).

## Adaylar
**C1 — Ay sonu rebalans (Harvey-Mazzoleni-Melone, NBER 33554) — 2 test (SP500, NASDAQ100).**
Giriş: ayın sondan 5. NYSE işlem günü 15:55 ET kapanışı. Çıkış: ayın son NYSE işlem günü 15:55 ET kapanışı.
Sinyal (giriş anında bilinen): endeksin ay-başından-bugüne getirisi (önceki ayın son işlem günü kapanışından giriş
kapanışına) eksi TLT'nin aynı tarihler arası getirisi (TLT için giriş gününden bir önceki gün kapanışı kullanılır,
look-ahead yok). Fark > 0 → short; < 0 → long. Swap: giriş–çıkış arası takvim gecesi sayısı × 0.000118.

**C2 — Tatil öncesi (Ariel; Quantpedia) — 2 test (SP500, NASDAQ100).**
Tatil öncesi gün = tam kapalı NYSE tatilinden hemen önceki işlem günü. Long: bir önceki işlem günü 15:55 ET
kapanışı → tatil öncesi günün son RTH barının kapanışı (erken kapanış varsa 13:00 ET öncesi son bar). Swap 1 gece.

**C3 — Üçüncü Cuma sabah settlement (Terstegge-Whelan AEA 2025) — 4 test (SP500, NASDAQ100 × long, short).**
Kaynakta yön okunamadığı için iki yön de önceden kayıtlı (4 test sayılır). Perşembe 15:55 ET kapanışı → üçüncü
Cuma 09:35 ET bar kapanışı (açılış SOQ penceresi). Cuma tatilse o ay atlanır. Swap 1 gece.

**C4 — VIX contango günü long — 2 test (SP500, NASDAQ100).**
Sinyal: önceki işlem günü ^VIX kapanışı < ^VIX3M kapanışı. İşlem: bugün 09:30 ET bar açılışı → 15:55 ET kapanışı,
long. Gün içi, swap yok. `condition`: sinyalli günlerin ortalaması > sinyalsiz günlerin ortalaması (baz oran kontrolü:
endeks uzun vadede yukarı gittiği için sadece pozitif ortalama yetmez).

**C5 — VIX backwardation filtresi, mevcut NB (NQ) — 1 test.**
NB işlemleri (`stop_testi.base_nb` + `apply_stop`, k=1, mevcut tanım) içinden önceki gün ^VIX kapanışı > ^VIX3M
kapanışı olan günlerdeki işlemler atlanır. Ölçüt: atlanan işlem başına filtre değeri = −(gross − 2·c).
Geçme: bu değer serisine aynı kurallar (ortalama > 0, CI alt > 0, iki dönem > 0, 2× > 0).

**C6 — Küçük boşluk + ilk 15 dk mum doldurma (tradingstats, kural sabitlendi) — 2 test (NASDAQ100, SP500).**
Boşluk = 09:30 ET bar açılışı − önceki gün 15:55 kapanışı. Küçük: |boşluk| < 0.25 × ATR14 (önceki gün).
09:30–09:45 mumunun (3 bar) kapanış−açılış işareti doldurma yönündeyse (boşluk yukarı → negatif mum), 09:45 bar
açılışında doldurma yönüne giriş; hedef = önceki kapanış; stop = ilk 15 dk mumunun karşı ucu (yukarı boşlukta high);
yoksa 15:55 kapanışında çık. Boşluk 0 ise işlem yok. Gün içi.

**C7 — Endeks boşluk tersine işlem, her gün — 2 test (NASDAQ100, SP500).**
Boşluk ≠ 0 her gün: 09:30 açılış → 15:55 kapanış, boşluğun tersi yönde. Stop yok. Gün içi.

**C8 — Altın Asya seansı long (WGC 2024 notu) — 1 test (XAUUSD).**
Her hafta içi gün 00:00 UTC bar açılışı → 08:00 UTC bar açılışı (07:55 bar kapanışı), long. Gün içi.
`condition`: Asya penceresi ortalaması > (8/24) × aynı günlerin 00:00→ertesi 00:00 UTC ortalaması
(baz oran kontrolü: altın yükseliş trendinde her pencere pozitif çıkar).

## Prop aşaması (sonuçtan sonra, hepsi için aynı)
1. Her aday: yıllık işlem sayısı, gece/hafta sonu taşıma, haber çakışması; koruyucu stop 2×ATR14 (günlük) ile en
   küçük lotta risk % (FN endeks kontrat 10 / altın 100, 0.01 lot) 2K/5K/6K/10K için.
2. Firma kuralına takılma listesi: hafta sonu yasağı (IF Evolve, FTM), FN %3 anlık risk, tutarlılık, min lot.
3. YALNIZ geçen adaylar mevcut portföye eklenir; firmalar: FN Stellar Instant 2K ($41.99), FN 1-Step 6K ($44.99),
   FN 2-Step 6K ($34.99), FN Lite 5K ($29.99), IF Evolve 10K ($49). Eklemeli/eklemesiz, sıfır-edge kontrol,
   gün içi 1.5× stres, ilk payout günü + 30 gün tek-hesap olasılığı. Eklenme kararı kullanıcıda.

## Tuzaklar
Post-hoc filtre yasak; C3'te iki yön önceden 4 test olarak sayıldı; C4/C8'de baz oran şartı önceden yazıldı.
16 test birlikte → 1 tanesinin şansla geçme ihtimali Bonferroni ile ~%5'e sınırlı.
