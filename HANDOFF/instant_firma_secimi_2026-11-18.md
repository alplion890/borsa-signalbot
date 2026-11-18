# Instant firma taraması: bot + VPS + US100/XAU/BTC + swap + Türkiye (2026-11-18)

Kriter: instant (değerlendirme yok), bot/EA serbest, MT5 (Python MetaTrader5 köprüsü), VPS, hafta sonu taşıma
(B7, BTC gece), US100+XAU+BTC, swap-free veya düşük swap, tutarlılık yok/zayıf, Türkiye yasaklı değil, güvenilir.
Portföy artık stop'lu ve risk boyutlu (işlem başı %0.5; bkz stop_portfoy_firma_sim_2026-11-18.md).
Kaynak: 4 paralel resmi sayfa taraması (+3. taraf yalnız güvenilirlik için, etiketli).

## Tüm kriterlerden en çok geçen: FundedNext Stellar Instant
- Fiyat: $5K $104.99 (liste $149.99, sayfada NOVINS %30), $10K $209.99. Toplam instant tavanı $20K.
- EA: 3. taraf dahil serbest, ücretli EA eklentisi (fiyat checkout'ta). Her EA farklı strateji; FN hesapları arası
  aynı kurulum kopyası yasak. VPS: $50K altı serbest, ücretli. MT5 var.
- Swap-free eklentisi var. Hafta sonu/gece serbest. Günlük limit yok, tutarlılık yok, min gün yok.
- Limit %6 kayan (başlangıç bakiyesini geçmez). Açık risk her an ≤ %3 (stop'a göre + gerçekleşmemiş zarar).
- Payout: %5 büyümede talep üzerine, ya da 14 günde %1–5; split %70 (Tier 3+ %80). Haber ±5 dk kârın %40'ı sayılır.
- Türkiye yasaklı listede yok. Ödeme USDT/USDC/Rise/banka. Trustpilot 4.5 (84.213 yorum).
- Doğrulanmayan: MT5 sembol adları (US100/XAU/BTC), swap-free eklentisi endeks+kripto kapsıyor mu, eklenti fiyatları.
- Simülasyon (risk boyutlu 6'lı+B7, liste fiyatı): ilk payout medyan 21 gün, 12 ay net $188, zarar %21.

## İkinci: Blueberry Funded Instant Elite
- $5K $200, $10K $400 (BERRY15 kodu instant'a geçer mi belirsiz). MT5.
- EA yalnız kendi yazdığın + destek onayı (kod sende → uyar). VPS yazmıyor.
- %10 kayan-kilit, günlük yok, tutarlılık yok, işlem fikri başına %1.5 (bizim %0.5 sığar). Min 5 gün (%0.5), 14 gün, %80.
- Swap-free YOK. Haber kuralı instant için belirsiz. Türkiye yasaklı değil. Trustpilot puanı gizli (sahte yorum).

## Elenenler (neden)
- FTMO Instant: 2 saatten uzun piyasa arasında taşıma yasak (hafta sonu), %30 tutarlılık.
- FXIFY Instant: EA "strictly prohibited". FundingPips Zero: hafta sonu taşıma yok, açık risk %1.
- Goat Funded Trader: 2026-10-06'dan beri VPS/hosting yasak, swap-free yok.
- FT+ (Mayıs 2026'da el değiştirdi): hafta sonu taşıma yasak (3. taraf). CTI: %20 tutarlılık, swap.
- Blue Guardian, AquaFunded, Finotive, Audacity: Trustpilot puanı gizli/zayıf + payout şikayetleri.
- iFunds: MT5 doğrulanamadı. Instant Funding (IF Pro): hafta sonu ek ürün, Türkiye belirsiz, puan gizli.
- FYFX: stop 3 dk zorunlu (artık karşılanır) ama MT5 yok. Maven Instant: %3 kayan limit dar.

## Satın almadan önce firmadan yazılı teyit
1. MT5'te US100 (NDX100?), XAUUSD, BTCUSD sembol adları. 2. Swap-free eklentisi endeks + kriptoyu kapsıyor mu.
3. Python MetaTrader5 köprüsüyle bot = EA sayılır mı, eklenti fiyatı. 4. %3 açık risk stop'lu pozisyonda nasıl hesaplanır.
5. Türkiye'den ödeme (kart engeli → kripto).
## Botta eksik
"Açık risk + yeni işlem > %3 ise işlemi atla" kuralı yok; risk boyutlu portföy günlerin %1.5–4'ünde %3'ü aşıyor.
B7 forward ölçülmedi.

## Ek (2026-11-19): en ucuz uygun seçenek, bütçe ~$30
- FN Stellar Instant 2K: $41.99 (NOVINS, liste $59.99), resmi sayfa 2026-11-19. Kurallar 5K ile aynı (%6 kayan, açık risk %3,
  günlük yok, tutarlılık yok, hafta sonu serbest). Kaldıraç: endeks/emtia 1:10, kripto 1:1. EA/VPS "add-on" — fiyat yazmıyor.
- Ücret/hesap oranı 5K ile aynı (%2.1 indirimli, %3 liste) → simülasyon ölçekle aynı: liste fiyatında 12 ay net medyan ≈ $75
  (5K'nın 0.4'ü), zarar olasılığı ≈ %21, 12 ayda ortalama 2.4 hesap alımı. Min lot inceliği 2K'da modellenmedi.
- Maven Instant 2K $14.25: %3 kayan + %2 günlük + %1 açık zarar + %20 tutarlılık → elendi. Blue Guardian resmi sayfası 404.

## Ek (2026-11-19): FN challenge'ları, stop'lu portföy (6'lı+B7), 500 yol × 365 gün, seed 20261118
Fiyat/kurallar 2026-11-18 resmi okuma. Biçim: ilk payout medyan gün · 12 ay net medyan · zarar olasılığı. Funded'da risk 1×.
- Lite 5K $32.99: risk boyutlu x1 235g/$2/%50, x2 152g/$297/%14, x3 117g/$374/%8; mevcut lot x2 98g/$635/%4, x3 69g/$717/%2.
- 2-Step 6K $59.99: risk boyutlu x3 127g/$429/%6; mevcut lot x2 117g/$742/%4, x3 84g/$845/%3.
- 1-Step 6K $65.99: risk boyutlu x3 77g/$479/%8; mevcut lot x3 43g/$730/%9 (yılda 7.5 hesap).
- Sıfır edge (x3, risk boyutlu): üçü de negatif (−$29..−$76, zarar %53–57) → model değeri edge'den alıyor.
- Doğrulanmadı: challenge'da EA/hafta sonu kuralı, funded'da açık risk kuralı var mı. Script scripts_2026-11-18/step_sim.py.

## Ek (2026-11-19): ucuz instant'ı ne engelliyor? (keşif, ön-kayıtsız; karar için değil teşhis için)
Risk boyutlu 7 modül (6'lı + B7), 500 yol × 365 gün. Açık zarar %1 kuralı gün içi en kötü (stres 1.5×) ile YAKLAŞIK modellendi
(kötümser: gerçekleşmiş zararı da sayıyor). FN %3 açık risk kuralı modellenmedi.
- Maven Instant 5K $18.05, x0.5: 200g · $109 · zarar %40. x1: zarar %94 (yılda 21 hesap). Tek modül çıkarmak hiçbirinde düzeltmiyor;
  tek modül tek başına daha kötü. Patlamaların çoğu "%1 açık zarar" (x0.5: 580/747), kalanı %3 kayan.
- Kural kapatma (x0.5): tutarlılık %20 yok → 117g · $214 · %7; açık %1 yok → 202g · $173 · %34; kayan %6 → değişmez.
  x1 ikisi yok → 51g · $665 · %0 (üst sınır, gerçek değil). Bağlayan kurallar: %20 tutarlılık (süre) + %1 açık zarar (patlama).
  En iyi gün dağılımı p50 %0.13, p90 %0.87, max %3.15 → %3 kârla payout için en iyi gün ≤ %0.6 olmalı.
- FN Instant 2K $41.99, 7 modül x1: 21g · $109 · %9 (sıfır edge −$22 · %59); x0.5: 38g · $46 · %16. Modül çıkarmak hep kötüleştiriyor.
- Uyarlama seçenekleri: bot "açık risk ≤ %1" kapısı (Maven) uygulanabilir; tutarlılık için temiz çözüm yok (hedef küçültme = strateji
  değişikliği → ön-kayıt + test gerekir).

## Ek (2026-11-19): FN Stellar Instant 2K detay — resmi kurallar + en küçük lot
Resmi (help.fundednext.com 17253243, 11641338, 8020350, 11641300, 8019806, 8020080; fundednext.com/general-rules/cfds/symbols-and-conditions):
- $2K $59.99 → $41.99 (NOVINS), iadesiz; reset %10 indirimli, promosyon reset'te geçmez. Swap-free +%10 fiyat (kapsam yazmıyor).
- %6 kayan (başlangıçta kilitlenir, payout sonrası inmez), günlük yok, **%3 max risk: stop mesafesi + açık zarar, ihlal = hesap biter**.
- Haber ±5 dk: kârın %40'ı. Min tutma yok; 30 sn altı "quick strike" yasak. Hafta sonu serbest. Hareketsizlik 30 veya 60 gün (çelişkili).
- EA MT4/MT5'te ücretli (fiyat yok); VPS ücretli; **Telegram/WhatsApp entegrasyonlu EA yasak**; Python köprüsü EA mı belirsiz.
- Semboller NDX100, XAUUSD, BTC/USD. **Kontrat: endeks 10, altın 100, kripto 1/100/1000 (BTC belirtilmemiş). Min lot yayınlanmamış.**
- Kaldıraç: endeks 1:5, emtia 1:7.5, kripto 1:1. Komisyon: endeks 0, metal %0.0016/lot, **kripto %0.04/lot** (açılışta). Spread yayınlanmamış.
- Payout %5'te anında veya 14 günde ≥%1; %70 → Tier 3 %80. Türkiye yasaklı değil. Instant toplam tavan $20K.
En küçük lot (0.01 VARSAYIMI) ile 2K'da işlem başı risk (hedef %0.5): Sweep medyan %0.14 (uyar), NB %1.49 (p90 %2.15, max %3.86),
B7 ≈ %6, Ay dönümü ≈ %6 (→ %3 kuralını tek işlemde aşar, imkânsız), Donchian XAU %1.59 (p90 %4.78, max %21), BTC 0.01 lotta %1.62 / 0.001 lotta %0.16.
Simülasyon FN 2K x1 (fn2k.py, fn2k_c10.py): yalnız Sweep 54g · $28 · %29; Sweep+BTC(0.001) 33g · $67 · %17;
Sweep+NB(min lot)+BTC 21g · $102 · %9 (sıfır edge −$32 · %63); Sweep+NB 24g · $79 · %14. Altını/BTC'yi büyük lotla zorlamak sıfır edge'de
de pozitif çıkıyor → kumar geometrisi, güvenilmez. FN maliyeti ölçülmedi (kripto komisyonu BTC 21–23'ün küçük edge'ini yiyebilir).

## Ek (2026-11-19): ≤ $50 Kasım taraması
Kaynak: propfirmdeals.org (16 Kas), quantvps BF listesi (14–17 Kas), propfirmmap/deals (18 Kas) + resmi sayfalar.
- **FN Stellar 2-Step 6K $34.99 (NOVSTR, liste $59.99)**: %8+%5, günlük %5, max %10 statik, min 5 gün; funded'da %3 max risk (stop+açık),
  tutarlılık yok, haber ±5 dk %40; ilk ödeme 21 gün sonra, sonra 14 gün; %80; ücret 1. ödemede iade; hafta sonu serbest; EA "add-on" (ücret belirsiz);
  kaldıraç endeks 1:25. MT5 bu sayfalarda yazmıyor (Instant'ta var).
- 6K gerçek lot (endeks kontrat 10, min 0.01 varsayım): NB %0.50, Donchian medyan %0.53 (max %7), B7/Ay dönümü ~%2 → "%1'i aşan işlemi atla"
  kapısıyla Sweep+NB+Donchian+BTC: yıl %12.8, Sharpe 1.53. Challenge x3: 132g · $414 · zarar %8; x2: 175g · $311 · %18; x1: zarar %55.
  Sıfır edge x2: −$70 · %68. BTC'siz x3: 166g · $264 · %18. Challenge'da %3 kuralı geçerliyse x3 sınıra dayanır (doğrulanmadı).
- Elenen: Maven 2-Step/Omo ($15–21 5K) — "EAs and automated trading are prohibited". NLF Instant Flex 10K $9.90 — %4 DD, %1 max risk,
  %15 tutarlılık, tek payout. Blue Guardian 1-Step 5K $28 — güvenilirlik. FXIFY BLACK35 — instant'ta EA yasak. Top One Trader %80 — fiyat/güven doğrulanmadı.
- Black Friday 27 Kasım; çoğu firma BF kodunu henüz yayınlamadı (14 Kas itibarıyla).
