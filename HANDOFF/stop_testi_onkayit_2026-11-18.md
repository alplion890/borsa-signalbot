# Ön-kayıt: stop'suz modüllere sabit stop (2026-11-18)

Test koşulmadan ÖNCE yazıldı. Amaç: stop zorunlu / açık-risk kurallı firmalara (FYFX, FN %3, Blueberry %1.5)
uyum. Soru: stop eklenince edge yaşıyor mu, hangi stop mesafesi en az zarar veriyor.

## Literatür (yöntem seçimi için, sonuç beklentisi)
- Kaminski & Lo 2014 (J. Financial Markets 18:234–254): rastgele yürüyüşte stop beklenen getiriyi HER ZAMAN düşürür;
  yalnız momentum/rejim değişiminde değer katar. Ortalamaya dönüşte (B7, Ay dönümü) zarar beklenir.
- Lo & Remorov 2017: stop etkisi getiri sürecine bağlı; sık stop + maliyet kötüleştirir.
- MAE (Sweeney): kazanan işlemlerin en kötü ters gidişi (MAE) dağılımının ötesine stop → kazananları az kesen
  "felaket stop'u". Burada yalnız TANIMLAYICI raporlanır, seçimde kullanılmaz.
- Seçim tek parametreli, küçük ızgara, örneklem-dışı (walk-forward) — stop optimizasyonu klasik overfit kaynağı.

## Modüller (5, önceden sabit)
B7_IBS_NQ, BTC_GECE, BTC_21_23, AY_DONUMU_NQ, NOISE_BAND. Giriş/çıkış kuralları değişmez; yalnız stop eklenir.
(Sweep ve Donchian XAU zaten stop'lu — kapsam dışı.)

## Stop kuralı
- Sabit, girişten mesafe = k × ATR14 (Wilder, günlük bar; girişten ÖNCEKİ tamamlanmış güne kadar).
  NQ günlük bar = NY 09:30–16:00; BTC günlük = UTC takvim günü (1h'den).
- k ∈ {0.5, 1, 1.5, 2, 3, 4} + "stop yok". Trailing yok, kırılımda taşıma yok.
- Yol: NQ 5 dk (Dukascopy, gece seansı dahil — CFD stop'u gece de tetiklenir), BTC 1 saat (Binance).
  Girişten çıkışa kadar her bar: açılış stop'un ötesindeyse açılıştan (gap), değilse low/high stop'a değerse stop
  fiyatından çık. Stop olmazsa orijinal çıkış.
- B7 stop olunca düz kalır, bir sonraki IBS<0.2 sinyalinde yeniden girer (orijinal "flat iken gir" kuralı).
- Maliyet: Maven `real_cost_per_side_central` (2026-11-12 ölçümü), 3 satır: 0 / merkez / 2×.
  Swap 0 (FN swap-free eklentisi varsayımı); B7 için −1.18 bp/gece swap satırı ayrıca.

## Ölçüt ve seçim
- Birim: R = net getiri / (ATR/giriş) → k'dan bağımsız oynaklık-normalize getiri ("stop yok" dahil karşılaştırılabilir).
  Prop boyutlamasında işlem başına risk = k·ATR; bilgi için R_k = net / (k·ATR/giriş) ve en büyük kayıp (gap) R_k raporlanır.
- Seçim: k* = 2012–2021 (BTC: 2017-08–2021) dönemde işlem başına Sharpe'ı (ortalama R / std R) en yüksek olan seçenek;
  "stop yok" da aday. 2022+ verisine seçimde BAKILMAZ.
- Geçme (k* ile, her modül ayrı): merkez maliyetle ortalama R > 0; bootstrap (seed 20261118, 10.000, işlem bazlı)
  alt sınır > 0, Bonferroni α = 0.05/5; <2022 ve 2022+ ikisi > 0; 2× maliyet > 0.
- Tüm k değerleri 2022+ dahil raporlanır (gizleme yok), ama karar yalnız k* üzerinden.
- k* = "stop yok" çıkarsa: modül stop'suz kalır; en iyi stop'lu seçeneğin bedeli (Sharpe farkı) raporlanır.

## Sonra (yalnız geçen stop'lu modüller)
Stop belli olunca işlem başına risk tanımlı → FN %3 açık risk ve firma simülasyonu (FN Instant, FXIFY, FYFX) yeniden.
Eklenme/firma kararı kullanıcıda.

## Tuzaklar
Sonuca bakıp k ızgarası genişletilmez, trailing/zaman stop'u eklenmez; geçmeyen modül yeniden tanımlanmaz.
6 k × 5 modül = 30 kombinasyon; yalnız 5 seçilmiş test sayılır, diğerleri bilgi.

## SONUÇ (2026-11-18, ön-kayıt 440d204 sonrası tek koşu)
Kod `strategy-lab/intraday/stop_testi.py`. Kontrol: "stop yok" satırı mevcut sonuçları üretti
(B7 n=415 +52.1bp, BTC gece n=2318 +15.4bp).
R = net / (ATR/giriş), merkez maliyet. Biçim: ortalama R · CI (Bonferroni 0.05/5) · <2022/2022+ · stop vurma % · en kötü işlem (R_k, gap dahil).
- **B7 IBS NQ — k* = stop yok → GEÇTİ** (+0.344 · [0.178, 0.509] · +0.42/+0.20). Stop her mesafede zarar verdi,
  dar olan daha çok (literatür: ortalamaya dönüşte stop zarar). k=0.5 +0.039 (2022+ −0.011, n 594), k=1 +0.120,
  k=1.5 +0.167, k=2 +0.216, k=3 +0.263 · [0.077, 0.440] · stop %10 · en kötü −1.53R, k=4 +0.283 · [0.086, 0.471] ·
  +0.36/+0.14 · stop %5 · en kötü −1.52R. Kazananların MAE p90/p95 = 1.46/1.83 ATR.
- **AY_DONUMU NQ — k* = 0.5 → GEÇMEDİ** (+0.105 · [−0.041, 0.263] · 2022+ −0.039). Stop'suz hali de bu kuralla
  geçmiyor: +0.123 · [−0.059, 0.308] · 2022+ +0.003. k=4 stop'suzla aynı (stop %0, en kötü −0.74R).
- **NOISE_BAND — k* = 0.5 → GEÇMEDİ** (+0.014 · [−0.002, 0.031]). Tüm k ≈ aynı (stop'suz +0.014 · [−0.003, 0.031]);
  k ≥ 1 stop hiç vurulmuyor (gün içi işlem, günlük ATR geniş). İşlem bazlı bu test NB'nin önceki günlük kabul
  testinden farklı; burada CI 0'ı içeriyor.
- **BTC 21–23 — k* = stop yok → GEÇTİ** (+0.009 · [+0.000, 0.017] · +0.016/+0.002; sınırda). k ≥ 1.5 stop ≈ %0,
  ortalama +0.008, CI alt −0.001..−0.003.
- **BTC gece — k* = 1.0 → GEÇMEDİ** (+0.035 · [−0.000, 0.072]). Stop'suz +0.040 · [+0.001, 0.078] (sınırda);
  k=1.5 +0.039 · [+0.003, 0.076] · stop %4 · en kötü −1.01R (bilgi, karar değil).
Seçim notu: NB (0.034 vs 0.032) ve AY_DONUMU'nda k* farkı gürültü düzeyinde — "optimum stop" tek nokta değil, düz bölge.
