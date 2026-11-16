# NQ EMA12 ilk 5 dk — 14 yıl ön-kaydı — 2026-11-17

Kural: değiştirilmemiş `forward_ea.modules.ema12_first5m_detector` (Maven PAPER `CAND_EMA12_FIRST5M`).
NY 09:30 5m mumunun kapanışı 5m kapanışların EMA12'sinin üstünde → long, altında → short.
Giriş mum kapanışı; stop = mum aralığı (high−low) kadar ters; hedef yok; 72 bar (6 saat) sonra kapanış.
Bar içinde stop dokunursa stop fiyatından çıkış (gap kayması yok sayılır → iyimser yön, raporda yazılır).

Veri: Dukascopy NASDAQ100 5m 2012 → son bar. Bölme: 2012–2021 / 2022+.
Maliyet: Maven `reality_profile.csv` NASDAQ100 `real_cost_per_side_central` (oran), kötümser 2×.
Eski sonuç (Edge Mekanizma notu, maliyet kaynağı belirsiz): n 3560, +0.0636R, CI −0.006..+0.134.

Geçme (ölçülmüş merkez, tek test):
1. Ortalama R > 0 ve 5-günlük blok bootstrap %95 alt sınır > 0
2. 2012–2021 ve 2022+ ayrı ayrı > 0
3. 2× maliyette ortalama R > 0
Rapor: WR, ayda işlem, yıllık R, en kötü ardışık kayıp, max R düşüşü.
Geçen: Maven PAPER devam / LIVE adayı (karar kullanıcıda). Geçmeyen: elenenler.
