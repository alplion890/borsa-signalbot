# Noise Band 14 yıl ön-kaydı — 2026-11-17

Kaynak: Zarattini et al., "Beat the Market" (SSRN 4824172). 2026-10-27'de yalnız
6 ay Maven verisinde koşuldu (`noise_band_research.py`, sonuç: 1× +%3,1, CI sıfırı içeriyor).

Bu koşu: **aynı kurallar, değiştirilmemiş `simulate()`**, veri Dukascopy NASDAQ100 5m
2012 → son bar (UTC, America/New_York seans 09:30–16:00, yalnız tam 78 barlı günler).
Parametre seçimi yok → tek hipotez.

Maliyet (yön başı, nominal oran), Maven `reality_profile.csv`:
- maliyetsiz 0
- ölçülmüş merkez `real_cost_per_side_central` (NASDAQ100)
- kötümser = 2 × merkez

Geçme kriteri (hepsi, ölçülmüş merkez maliyet):
1. Tüm dönem ortalama günlük net getiri > 0 ve 5-günlük dairesel blok bootstrap %95 alt sınırı > 0
2. 2012–2021 ve 2022+ ayrı ayrı > 0
3. Kötümser maliyette tüm dönem > 0

Geçerse: Maven forward PAPER adayı (LIVE değişmez, karar kullanıcıda). Geçmezse elenenlere.

Sınırlar: Dukascopy hacmi tick hacmi (VWAP yaklaşık); tatil listesi yalnız 2026
(eksik barlı günler zaten dışlanıyor); seans kapanış dolumu idealize; gün içi DD ölçülmez.
