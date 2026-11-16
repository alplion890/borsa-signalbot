# Baltussen son-30-dakika momentumu ön-kaydı — 2026-11-17

Kaynak: Baltussen, Da, Lammers, Martens (2021) "Hedging Demand and Market Intraday
Momentum", JFE 142(1). Kural (Tablo 6, rROD): kapanıştan 30 dk önce, önceki seans
kapanışından o ana getiri > 0 → long, < 0 → short; kapanışta çık. Stop yok.

Veri: Dukascopy 5m, 2012 → son bar. Seanslar (America/New_York, DST doğru):
- NQ (NASDAQ100): kapanış 16:00 → giriş 15:30 barının açılışı, çıkış 15:55 barının kapanışı;
  önceki kapanış = önceki seans 15:55 bar kapanışı.
- XAU (XAUUSD): makaledeki COMEX saatleri 08:20–13:30 → giriş 13:00, çıkış 13:25 bar kapanışı;
  önceki kapanış = önceki gün 13:25 bar kapanışı.
Hafta içi, gerekli üç bar mevcut olan günler. Parametre seçimi yok; 2 hipotez.

Maliyet (yön başı oran, Maven `reality_profile.csv`): 0 / `real_cost_per_side_central` / 2×.

Geçme (her enstrüman ayrı, ölçülmüş merkez maliyet):
1. Günlük ortalama net > 0 ve 5-günlük blok bootstrap **%97,5** alt sınırı > 0 (2 test, Bonferroni)
2. 2012–2021 ve 2022+ ayrı ayrı > 0
3. 2× maliyette tüm dönem > 0
Geçen: Maven forward PAPER adayı. Geçmeyen: elenenlere.
Sınır: makale gamma filtresi (opsiyon verisi) uygulanmıyor; CFD kapanış dolumu idealize.
