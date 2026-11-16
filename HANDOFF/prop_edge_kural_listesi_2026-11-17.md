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
