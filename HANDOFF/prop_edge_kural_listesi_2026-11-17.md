# Prop'a yarayan edge kural listesi — 2026-11-17

Amaç: challenge'ı geçip funded'da payout alacak edge'i seçmek. Her aday test edilmeden önce
bu listeye göre süzülür, test edildikten sonra `intraday.prop_fit` ile Maven hesabında simüle edilir.

## A. Ön süzgeç (test etmeden önce)
1. Enstrüman Maven MT5'te var ve maliyeti ölçülmüş (`reality_profile.csv`): FX majör/çapraz,
   XAU, XAG, US100/US500/US30/US2000, UK100/FRA40/JAP225, BTCUSD.
2. Kurallar kaynaktan birebir kodlanabilir (giriş, stop, çıkış, saat). Uydurma eşik yok.
3. Sıklık ≥ 8 işlem/ay (tek enstrüman veya küçük sepet).
4. Tutma 15 dk – 5 gün; elle basılabilir (sabit saat veya alarm). Tick scalp, grid, martingale yok.
5. `python -m intraday.elenenler --kontrol <kelime>` veto vermiyor.
6. Mekanizma yazılı (karşı tarafta kim var: hedge akışı, fix, rebalans, likidite).
7. Maliyet/risk oranı ≤ 0.10R: ölçülmüş gidiş-dönüş maliyeti medyan stopun ≤ %10'u
   (EMA12'de 0.09R, Sweep 2022 öncesi bu yüzden negatif).

## B. Backtest kapısı (ön-kayıtlı, tek motor)
8. Veri ≥ 10 yıl (Dukascopy/Binance), dürüst dolum, geleceğe bakış yok.
9. Ölçülmüş merkez maliyette: ortalama > 0 ve blok bootstrap %95 alt sınır > 0 (çoklu testte Bonferroni).
10. 2012–2021 ve 2022+ ayrı ayrı > 0.
11. 2× maliyette ≥ 0.
12. Mevcut edge'lerle (Sweep, Noise Band) günlük korelasyon < 0.5.

## C. Prop kapısı (`intraday.prop_fit`, her tarihsel başlangıç günü, gerçek sıra)
13. Challenge (+%4 / %10 statik): seçilen riskte geçme ≥ %70, medyan süre ≤ 60 işlem günü.
14. Funded (%8 kayan, %4 günlük, %20 tutarlılık, ≥5 işlem günü): ilk payout olasılığı ihlalden
    yüksek olmalı.
15. **Tutarlılık kuralı bağlayıcı:** en iyi gün toplam kârın ≤ %20'si. Seyrek büyük kazançlı edge'ler
    (Sweep: ilk payout %2–6) bu yüzden payout'a ulaşamıyor. Tercih: çok sayıda benzer büyüklükte
    kazançlı gün (yüksek gün-bazlı WR, düşük çarpıklık) veya birbirini seyrelten birden fazla edge.

## Baz ölçüm (prop_fit, 2026-11-17, ölçülmüş merkez maliyet)
| Edge | dönem | boyut | challenge geç / patla / medyan gün | funded payout / ihlal |
|---|---|---|---|---|
| Sweep | 2022+ | %1 risk | 94 / 0 / 62 | 6 / 1 |
| Sweep | 2012+ | %1 risk | 49 / 35 / 64 | 2 / 56 |
| Noise Band | 2022+ | 1× | 68 / 3 / 70 | 28 / 17 |
| Noise Band | 2012+ | 1× | 65 / 1 / 87 | 18 / 9 |
| EMA12 | 2022+ | %0.25 risk | 74 / 0 / 62 | 3 / 40 |
Funded ilk payout varsayımı: ≥14 işlem günü (Maven resmi kuralı doğrulanacak). Kapalı bakiye yaklaşımı.

## D. Kural-eleme raporu: edge mi zayıf, firma kuralı mı eliyor? (2022+, yıllık funded çekim, $5K, %80 pay)
`prop_fit.yearly_ev`: funded hesapta 1 yıl boyunca her uygun döngüde kâr çekilir, ihlalde durur. "Sıfır edge" = aynı
seri, ortalaması çıkarılmış (şans/opsiyon değeri). Edge katkısı = edge − sıfır.

| Edge (boyut) | Maven BNPL funded | Tutarlılık yok | Statik %10, günlük %5, tutarlılık yok | Bağlayıcı kural |
|---|---|---|---|---|
| Sweep (%0.5 risk) | $29/yıl (katkı +29) | $219 (+128) | $219 (+128), ihlal %0 | **%20 tutarlılık** |
| Noise Band (1×) | $126 (+101) | $323 (+150) | $323 (+150), ihlal %8 | **%20 tutarlılık** |
| EMA12 (%0.25 risk) | $14 (+11), ihlal %42 | $238 (+86) | $250 (+82), ihlal %0.4 | **tutarlılık + kayan DD** |
| BTC 21–23 (0.5×) | $100 (+12) | $219 (+35) | $219 (+35), ihlal %11 | tutarlılık; edge katkısı küçük |

Okuma: Maven BNPL funded'daki %20 tutarlılık kuralı yıllık çekimi edge'e göre 2–17 kat düşürüyor. Kayan→statik DD
ihlali azaltıyor, çekimi değiştirmiyor (bu boyutlarda). Tutarlılıksız firmada sıfır edge'in de çekimi var
(opsiyon değeri); edge'in gerçek katkısı "katkı" sütunu.

## E. Tutarlılık kuralı olmayan firma adayları (ajan, yalnız resmi sayfadan doğrulanan, 2026-11-17)
- **E8 Pro:** statik %8 DD, günlük %2.5, tutarlılık yok, günlük kâr sınırı %2, endeks + BTC var. EA politikası bulunamadı.
- **Maven Standard 2-step:** statik %8, günlük %4, tutarlılık yok (5K ~$21 kuponlu). Standard 1-step trailing %5.
- FXIFY Instant Lite: %20 tutarlılık + EA yasak → uygun değil.
- FTMO, The5ers, FundedNext, Funding Pips, Blue Guardian, Alpha Capital, Goat: resmi sayfa okunamadı (403/404) → tarayıcıyla elle doğrulanmalı.

## F. Equity (açık pozisyon dahil) simülasyonu — `intraday.prop_equity` (2026-11-18)
Maven günlük limiti ve kayan DD'yi equity üzerinden ölçüyor. NQ 5m ve BTC 1h barlarıyla her günün en kötü/en iyi
anı (MAE/MFE) eklendi. Funded ihlal %, Maven BNPL kuralları:

| Portföy | dönem | kapanmış bakiye | equity |
|---|---|---|---|
| Noise Band 1× | 2012+ | %8.8 | %13.2 |
| Noise Band 1× | 2022+ | %17.2 | %22.5 |
| BTC 21–23 0.5× | 2012+ | %29.8 | **%53.6** |
| BTC 21–23 0.5× | 2022+ | %19.4 | **%64.6** |
| NB 0.75× + BTC 0.35× | 2012+ | %4.3 | %8.1 |
| NB 0.75× + BTC 0.35× | 2022+ | %0.0 | %0.0 |

Challenge geçme oranları neredeyse değişmiyor (statik %10 geniş). BTC tek başına equity bazında tehlikeli:
en kötü gün içi an 1×'te −%15.4 (NB en kötü −%3.2). Kombine portföyde BTC payı küçük olduğu için sağlam kalıyor.
Tutarlılıksız + statik %10 / günlük %5 kuralında kombine portföy yıllık çekim $347 (2012+), $257 (2022+), ihlal ≤%5.

## G. Firma kuralları — tarayıcıyla resmi sayfadan doğrulama (2026-11-17)

### Maven BNPL (maventrading.com/faqs, BNPL bölümü)
| Kural | Resmi metin | Modelde (`prop_fit.Rules`) | Durum |
|---|---|---|---|
| Faz 1 DD | %10 **statik** (başlangıç bakiyesinden, sabit) | `challenge_trailing=False` | ✅ çelişki çözüldü: statik |
| Faz 1 hedef | %4, günlük limit yok, tutarlılık yok | aynı | ✅ |
| Funded günlük | %4, equity bazlı, 00:00 UTC'de equity/bakiyeden **büyüğüne** göre sıfırlanır | %4 kapalı gün P&L (prop_equity: gün içi) | ✅ |
| Funded maks DD | %8 trailing, **açık pozisyon dahil running equity** zirvesi | `prop_fit` kapalı bakiye zirvesi; `prop_equity` gün içi high | prop_fit iyimser, prop_equity yakın |
| **Çekim sonrası DD** | **İlk çekimden sonra DD tabanı başlangıç bakiyesine kilitlenir** (örnek: $10K→$10,800, $600 çek → tampon $200) | Her çekimde bal=0, peak=0, %8 tampon yeniden | ❌ **model iyimser**: tüm kâr çekilirse tampon 0 |
| Tutarlılık | Funded %20; en iyi gün ≤ döngü toplam kârının %20'si (kayıp günler dahil), her payout'ta sıfırlanır | %20 | ✅ |
| Payout bekleme | **Sabit bekleme yok**; %20 tutarlılık + diğer şartlar sağlanınca | `first_payout_min_days=10` (Standard'ın kuralı) | ❌ model kötümser (BNPL'de 10 gün yok) |
| Min çekim | $20 (pay öncesi kâr) | 0.004 × $5K | ✅ |
| Pay | %80, add-on yok | %80 | ✅ |
| Haber | BNPL funded'da haber işlemi **tamamen serbest** | — | Önceki not "kırmızı haber ±2dk yasak" Standard/OMO içindir |
| Kalan ücret | Kârdan düşülmez, ayrı ödeme; değerlendirme kârı çekilemez | — | — |
| İnaktivite | 30 günde ≥1 işlem | — | — |
| Stil yasakları | İşlemlerin >%50'si <60 sn tutulursa "aşırı scalping"; all-in; gamifying | — | NB/BTC/Sweep etkilenmez |

### Diğer firmalar (resmi sayfa)
| Firma / program | Maks DD | Günlük | Tutarlılık | Not |
|---|---|---|---|---|
| Maven Standard 2-Step | %8 statik | %4 equity | Yok | İlk payout ilk funded işlemden 10 iş günü sonra; kırmızı haber ±2 dk yasak |
| FTMO 2-Step | %10 **statik** (başlangıç sermayesinden) | %5 (başlangıç sermayesinin; 00:00 CE(S)T bakiyesinden) | 2-Step bölümünde yok | Hedef %10 / %5. 1-Step farklı: günlük %3, %10 **gün sonu trailing**, Best Day ≤ %50 |
| The5ers High Stakes | %10 (tipi sayfada yazmıyor) | %5 | Sayfada yok | Min 3 kârlı gün (≥%0.5); haber ±2 dk yasak; kripto + endeks var; MT5 |
| FundedNext Stellar 2-Step | %10 **statik** (taban başlangıç bakiyesi, sabit) | %5 başlangıç bakiyesinin | Şartnamede yalnız "Express + Consistency" seçeneğinde | Sunucu GMT+2/+3 |
| Funding Pips 2-Step | %12 (tipi bulunamadı) | %4 | Bulunamadı | Yardım merkezinde yalnız "Legacy Rules" var → **doğrulanmadı** |

Doğrulanmayan: EA politikası (FTMO, The5ers, FundedNext), The5ers DD tipi, Funding Pips DD tipi/tutarlılık,
her firmada NQ/BTC sembolü ve spread'i (maliyet kuralı gereği ölçülmeden backtest'e girmez).
