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
