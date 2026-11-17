# Prop firma × hesap × risk simülasyonu: ilk payout ne zaman? (2026-11-18)

Soru (kullanıcı): FundedNext 2-Step 1x'te funded olma ~6.5 ay — çok uzun, düzelt.

## Girdi
- Portföy: 6 strateji (Sweep, NB, Donchian XAU, BTC 21–23, BTC gece, ay dönümü NQ), 2022+ günlük
  sonuç, Maven ölçülmüş maliyet (FundedNext maliyeti ÖLÇÜLMEDİ), BTC gece swap 0 (swap-free varsayımı).
  1x = Sweep/Donchian %0.5 risk, NB 0.75×, H6 0.35×, A4 0.101×, TOM 0.5×. Yılda ~%18, Sharpe 1.48.
- Firma kuralları resmi sayfalardan 2026-11-18 (FundedNext help center, FTMO, The5ers, FundYourFX, Maven).
- Motor: scratchpad `firms.py` (`journey`): challenge fazları → funded → payout döngüsü; challenge/funded
  patlarsa aynı gün yeni hesap alınır (ücret eklenir). Boyutlama başlangıç bakiyesine sabit. 365 gün,
  20 günlük blok bootstrap 800–1000 yol, seed 20261118. Sabit girdi testleri geçti (faz/payout/iade/ihlal).
- Kontroller: (a) **sıfır edge** (getiri ortalamadan arındırılmış), (b) **gün içi stres**: limit kontrolünde
  kaybeden gün 1.5× derin (kapanış P&L değişmez).
- `mc` = challenge risk çarpanı, `mf` = funded risk çarpanı (aşağıda mf=1).

## Sonuç (medyan ilk payout günü · 12 ay medyan net $ · 12 ayda zarar olasılığı)
FundedNext Stellar 2-Step (10% statik, %5 günlük, 21 gün sonra ilk ödeme, %80):
- 6K mc=1: 214g · $262 · %31 — mc=2: 127g · $599 · %7 — mc=3: 99g · $700 · %4 (stres %9)
- 25K ($199.99) mc=3: 99g · $2,968 · %3 (stres $2,675 · %7); sıfır edge −$91 · %52
FundedNext Stellar 1-Step (10% hedef, %6 max, %3 günlük, 5 iş günü döngü, iade 3. ödemede):
- 6K mc=3: 52g · $710 · %8 (stres $491 · %24, ~9 hesap/yıl)
- 25K ($219.99) mc=3: 52g · $3,166 · %5 (stres $2,386 · %19); sıfır edge −$1,617
FundedNext Lite (8%+4%, %8 max, %4 günlük, 10 iş günü):
- 5K ($32.99) mc=3: 82g · $614 · %4 — 25K ($139.99) mc=3: 82g · $3,113 · %4 (stres %9)
FundYourFX Instant Classic 5K ($39.60 promo, 22 Kas'a kadar): 38g · $520 · %1 — AMA sıfır edge de
  +$202 çıkıyor → model firmanın gerçek kısıtlarını (işlem başı risk, SL, ret pratiği) yakalamıyor; güvenilmez.
FundedNext Instant 5K ($149.99, %6 kayan, %70): 18g · $251 · %22 zarar; sıfır edge −$246.
Maven Instant 5K ($18.05, %3 kayan equity, %2 günlük, %20 tutarlılık): 153g · ~$525 · %20 zarar.

## Bulgular
1. Süreyi **challenge risk çarpanı** belirliyor: FN 2-Step mc 1→3 ile 214→99 gün; FN 1-Step 153→52 gün.
   Challenge patlaması yalnız ücrete mal oluyor; funded'da 1x'e dönülüyor.
2. Parayı **hesap büyüklüğü** belirliyor: süre aynı, net $ ~4.2× (6K→25K), ücret ~3.3×.
3. Değer edge'den geliyor: FundedNext yapılarında sıfır edge negatif (FYFX hariç).
4. 1-Step hızlı ama kırılgan (%3 günlük): gün içi streste zarar olasılığı %5→%19, yılda ~9 hesap alımı.
   2-Step yavaş ama strese dayanıklı (%3→%7).
5. Strateji çıkarmak: Sharpe 1.48→1.55 (BTC 21–23 hariç) — gürültü sınırında, post-hoc riski.

## Ölçülmeyen / doğrulanmayan
- FundedNext maliyeti (spread/komisyon), endeks/kripto kaldıraç sınırları (resim içinde), mc=3'te
  NB 2.25× notional ve Sweep %1.5 risk bu kaldıraca sığar mı.
- Funded "aynı anda en fazla %3 risk" kuralı: stopsuz pozisyon (NB, BTC) nasıl sayılıyor.
- Haber ±5 dk kuralı (kârın %40'ı sayılır) etkisi; NDX100 = US100 mü.
- Gün içi dip gerçek veriyle değil 1.5× varsayımıyla; ~4.8 yıllık tek geçmiş (bağımsız örnek az).
- `mc` seçimi aynı veride yapıldı (risk parametresi, monoton etki; yine de iyimser).
- FTMO fiyatı alınamadı (sayfa render etmedi) → kıyasa girmedi.
