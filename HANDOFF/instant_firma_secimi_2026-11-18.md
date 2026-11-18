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
