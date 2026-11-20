# Ön-kayıt: ucuz hesapta edge'i bozmadan boyutlama/kapı yöntemleri (2026-11-20)

Bu dosya test kodu çalışmadan ÖNCE commit edilir. Sonuca bakıp eşik/yöntem/firma değiştirmek yasak.

## Soru
≤ $60 bütçe + bot + tek hesap (FN aynı EA'yı birden fazla hesapta yasaklıyor) koşulunda, mevcut edge'lerin
SİNYAL kuralına dokunmadan yalnız **boyutlama, kapı ve hesap yönetimi** değiştirilerek hangi yöntem
piyasa rejimine en az bağlı sonuç verir?

## Sabit girdiler (değişmez)
- Modüller: SWEEP (trades_SWEEP_CORE r0, Maven ölçülmüş maliyet), NB (stop_testi base_nb + k=1 ATR stop),
  BTC 21–23 (stop_testi base_btc_21_23 + k=1.5 ATR stop). Her işlem R cinsinden (1R = stop mesafesi).
  Gece/hafta sonu modülleri (Donchian, B7, Ay dönümü, BTC gece) DAHİL DEĞİL (min lot / %3 kuralı / basitlik).
- Maliyet: Maven reality_profile `real_cost_per_side_central` (1x) ve 2x. FN maliyeti ÖLÇÜLMEDİ — etiket.
- Gün içi dip: kapanış zararı × 1.5 (önceki işlerle aynı kötümser yaklaşım).
- Lot inceliği: NB ve SWEEP'te endeks kontrat 10, min 0.01 lot, adım 0.01 (FN sembol sayfası; min lot yayınlanmamış → VARSAYIM).
  BTC 0.001 adım (VARSAYIM, sürekli sayılır). İstenen riskin altına yuvarlanır; 0'a düşen işlem atlanır.
- Açık risk kapısı (bot): aynı gün planlanan stop riskleri toplamı > %3 ise önce NB, sonra BTC atlanır.

## Firmalar (resmi okuma 2026-11-18..20, tek hesap, x1 = işlem başı %0.5)
- I2K: FN Stellar Instant 2K $41.99 — %6 kayan (başlangıçta kilit), günlük yok, payout ≥%5 anında ya da 14 günde ≥%1, %70.
- L5K: FN Stellar Lite 5K $29.99 — %8 + %4, günlük %4, statik %8, min 2 gün/faz; funded aynı limitler, ilk payout 14 gün, %80.
- S2: FN Stellar 2-Step 6K $34.99 — %8 + %5, günlük %5, statik %10, min 5 gün/faz; funded ilk payout 21 gün, %80.
- S1: FN Stellar 1-Step 6K $44.99 — %10, günlük %3, statik %6, min 2 gün; funded ilk payout 5 iş günü (7 takvim), %80.
  Funded'da kâr ≥ %1 ise payout alınır; payout sonrası bakiye başlangıca döner.

## Yöntemler (hepsi botla uygulanabilir: gün başında yalnız hesap bakiyesini bilir)
- F(b): sabit işlem riski b ∈ {%0.5, %1.0, %1.5}.
- B(b): tampon orantılı — risk = b × (mevcut tampon / başlangıç tamponu); tampon = bakiye − ihlal tabanı
  (günlük limit varsa min(statik/kayan tampon, günlük limit)). Kayıp serisinde otomatik küçülür.
- BT(b): B(b) + hedefe kalan mesafe kapısı: risk ≤ (hedefe kalan) / 2 (challenge'da hedefi "aşırı" riskle kovalamaz).

## Ölçüm
- Rejim blokları (yıl içi 20 günlük blok bootstrap, 300 yol, seed 20261120): 2013–2017, 2018–2021, 2022–2023, 2024–2026.
  (SWEEP 2022 öncesi negatif → ilk iki blok gerçek stres testi.) BTC verisi yoksa o blokta BTC = 0.
- Metrikler (tek hesap, yeniden alım yok, 365 gün): P(payout ≤ 30 gün), P(payout ≤ 90 gün), P(payout'tan önce patlama),
  12 ay net $ (ücret düşülmüş, yeniden alım YOK) medyan ve ortalama.
- Sıfır-edge kontrolü: her modülün R serisi kendi ortalamasından arındırılır (aynı oynaklık, sıfır beklenti).

## Karar kuralı (sabit)
1. Bir yöntem/firma çifti "piyango" sayılır: sıfır-edge 12 ay net ORTALAMASI > 0 ise → elenir.
2. Kalanlar arasında "en dayanıklı" = 4 rejim bloğunun **en kötüsündeki** 12 ay net ortalaması en yüksek olan (maximin), 1x maliyetle;
   2x maliyette de en kötü blok ortalaması ≥ −ücret olmalı (yani beklenen kayıp ücreti aşmamalı).
3. Rapor: her firma × yöntem için en kötü blok, en iyi blok, tüm 2022+ ve sıfır-edge. Sonuç LIVE kuralını veya riski kendiliğinden değiştirmez.

## Ek ön-kayıt (Argon fikri #4, sonuçlar görülmeden önce; ilk koşu yalnız F/B/BT içeriyordu)
- R(b) "kâr merdiveni": bakiye ≤ +%1.5 → risk b; +%1.5..+%3.5 → 1.7b; > +%3.5 → 2.2b (challenge'da faz bakiyesi, funded/instant'ta payout sonrası sıfırlanan bakiye).
  b ∈ {%0.5, %1.0}. Aynı karar kuralı, aynı veri, aynı seed. Gün içi devre kesici modellenmez (yalnız %3 açık risk kapısı).
