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
