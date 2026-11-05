# SWEEP_CORE prop uyumu ve tetik dayanıklılığı — ön-kayıt (2026-11-05)

Bu belge koşumdan ÖNCE commit edilir. Dayanak: [[Borsa - Edge Mekanizma ve Zayiflik Analizi 2026-11-05]].
Taban: arşiv SWEEP_CORE tanımı (`long_history_ab._sweep_build` + ATR rejim tavanı 4/6/8R, min 2R, max 480 bar),
NASDAQ100 15m Dukascopy 2012–2026, `honest_engine` bar/SL-önce dolum, `INSTRUMENTS` maliyeti.
Deney kopyası, maskeler boşken motorla birebir aynı R serisini üretmek ZORUNDA (koşumda assert).

## H1 — prop uyumu (dış kurallardan türetildi, sonuçtan değil)
Kaynak: prop firma kuralları (hafta sonu gap riski; yüksek etkili haberde ±5 dk işlem yok).
- **Hafta sonu kapanışı:** Cuma 20:00 UTC ve sonrasındaki ilk bar kapanışında açık pozisyon kapatılır; Cuma 20:00 UTC sonrası yeni giriş yok.
- **Haber penceresi:** giriş anı (sinyal barının kapanışı = index + 15 dk) FOMC/CPI/NFP olay saatine ±5 dk içindeyse giriş yok (`event_calendar.all_events()`, ET saatleri). Açık pozisyon tutulur.
- **Karar:** H1 benimsenir eğer (a) ort. R düşüşü ≤ 0.02R/işlem **ve** (b) en kötü tek işlem R'si VEYA kapanmış işlemlerle maksimum düşüş (R) tabandan kötü değil. Aksi halde "uyum maliyeti" olarak raporlanır; LIVE kural yine kullanıcı kararıyla değişir.

## H2 — asgari süpürme derinliği (kaynak dayanıklılığı)
- Tetik ek şartı: long için `rolling_low_20 − low ≥ 0.10·ATR(14)`, short için `high − rolling_high_20 ≥ 0.10·ATR(14)`. **k=0.10 sabit, tarama yok.**
- **Birincil ölçüt:** Maven US100 15m ile NQ=F 15m ortak barlarında ham sinyal örtüşmesi (Jaccard = ortak / birleşim) tabandan yüksek.
- **İkincil:** uzun geçmiş ort. R tabandan 0.02R'den fazla düşük değil ve işlem sayısı tabanın ≥ %60'ı.
- **Karar:** birincil ve ikincil birlikte sağlanırsa "kaynak-dayanıklı aday"; değilse reddedilir. Sonuç LIVE kuralını kendiliğinden değiştirmez.

## Raporlanacak (karar ölçütü değil)
2012–2021 ve 2022–2026 alt dönem ortalamaları; kesilen işlem sayıları; en kötü 5 işlem.

## Yasak
Ara sonuca göre k, saat veya pencere değiştirmek; ek filtre eklemek.

## Sonuç (koşum 2026-11-05, ön-kayıt eb30887 sonrası)
Kod: `strategy-lab/intraday/sweep_prop_lab.py`; çıktı `outputs/intraday/sweep_prop_lab/result_2026-11-05.json`.
Motorla parite: birebir (assert geçti). Veri: Dukascopy NASDAQ100 15m 2012-01-19 → 2026-08-28.

| | n | ort R | toplam R | en kötü | max DD (R) | <2022 | ≥2022 |
|---|---|---|---|---|---|---|---|
| Taban | 235 | +0.0485 | +11.40 | −22.46 | 58.64 | −0.357 | +0.752 |
| H1 prop uyumu | 231 | +0.0559 | +12.92 | −22.46 | 60.71 | −0.376 | +0.813 |
| H2 derinlik ≥0.10·ATR | 142 | +0.0123 | +1.75 | −2.10 | 22.36 | +0.020 | −0.004 |

Feed örtüşmesi (Maven US100 vs NQ=F, 4366 ortak bar): taban Jaccard 0.391 (16/16, ortak 9); H2 0.333 (12/12, ortak 6).

- **H1: kural gereği BENİMSENDİ** (ort. R +0.007, en kötü işlem eşit). Etki marjinal; 4 işlem kesildi. En kötü işlem hafta sonu gap'i değildi (aşağıda).
- **H2: REDDEDİLDİ** (birincil: örtüşme düştü; ikincil: ort. R −0.036, n %60). H2'nin en kötü işlemi/DD'yi düzeltmesi ölçüt değildi; sonradan ölçüt yapılmaz.

## Yan bulgu: veri kalitesi
−22.46R işlemi (2013-02-25 16:00) bozuk veride: barlar saatlerce ~2 puanlık sabit aralıkta tekrarlıyor. Önbellekte 205 "donuk" gün var (çoğu hafta sonu/tatil sabit dolgusu); Sweep'te yalnız bu işlemi etkiliyor. Çıkarılınca uzun geçmiş: n234, **ort +0.145R**, <2022 −0.208, ≥2022 +0.752. 10-29'daki "+0.132 yeniden üretilemedi" farkının büyük kısmı bu tek işlem. Temizlik ayrı iş (veri temizliği rayı); bu koşumda sonuçlar ham veriyle raporlandı.
