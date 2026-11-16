# Noise Band çapraz endeks ön-kaydı — 2026-11-17

Önceki: NQ 14 yıl GEÇTİ (`noise_band_14y_onkayit_2026-11-17.md`, 7122592).
Bu koşu iki amaçlı: (1) NQ sonucunun bağımsız tekrarı (makalenin asıl enstrümanı SPY →
SP500 en yakın), (2) aynı kuralın daha fazla işlem verip vermediği.

Kurallar: **değiştirilmemiş** `noise_band_research.simulate`, ABD nakit seansı 09:30–16:00 NY.
Veri: Dukascopy 5m 2012 → son bar: SP500, US30, US2000. Parametre seçimi yok; 3 hipotez.
Maliyet: Maven `reality_profile.csv` `real_cost_per_side_central`, kötümser 2×.

Geçme (her enstrüman ayrı, ölçülmüş merkez):
1. Ortalama günlük net > 0 ve 5-günlük blok bootstrap alt sınır > 0 — Bonferroni (3 test):
   %98,33 iki yönlü aralığın alt ucu (0,83. yüzdelik)
2. 2012–2021 ve 2022+ ayrı ayrı > 0
3. 2× maliyette tüm dönem > 0

Ek rapor (kriter değil): NQ Noise Band günlük getirisiyle korelasyon ve aynı gün aynı yön
oranı — yüksekse yeni enstrüman bağımsız edge değil, aynı bahsin kopyasıdır (slot kısıtı,
[[Borsa - Portfoy Kompozisyonu ve Slot Kisiti]]).
Geçen: Maven forward PAPER adayı. LIVE/risk kendiliğinden değişmez.
