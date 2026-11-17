# FX fix dönüşü + BTC saat mevsimselliği ön-kaydı — 2026-11-17

Kaynak: internet taraması (Haiku ajanları) → `HANDOFF/prop_edge_kural_listesi_2026-11-17.md` ön süzgecinden geçen iki aday.
Kaynak makalelerde tam pencere doğrulanamadığı için pencereler sonuç görülmeden, aşağıda sabitlendi.

## H1–H4: FX fix (Krohn-Mueller-Whelan JF 2024: USD fix öncesi yükselir, sonrası düşer)
Sepet: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF eşit ağırlık; yön "USD" cinsinden.
Veri Dukascopy 5m 2012 → son; hafta içi.
- H1 Londra öncesi: 15:00→16:00 Londra saati USD long
- H2 Londra sonrası: 16:00→17:00 Londra saati USD short
- H3 Tokyo öncesi: 08:55→09:55 Tokyo saati USD long (5m barda 08:55 açılış → 09:55 açılış)
- H4 Tokyo sonrası: 09:55→10:55 Tokyo saati USD short
Giriş pencere başı bar açılışı, çıkış pencere sonu bar açılışı. Stop yok.

## H5–H6: BTC saat (Padyšák & Vojtko / Quantpedia, örneklem 2015–2022-02)
Binance BTCUSDT 1h 2017-08 → son. Yalnız long, her gün.
- H5: 22:00→00:00 UTC
- H6: 21:00→23:00 UTC
2022-03 sonrası makale örnekleminin dışı = gerçek OOS.

## Maliyet
Maven `reality_profile.csv` `real_cost_per_side_central` (her bacak 2 yön), kötümser 2×.
FX sepet maliyeti = çiftlerin ölçülmüş maliyet ortalaması. BTC = BTCUSDT satırı.

## Geçme (her hipotez, ölçülmüş merkez, Bonferroni 6 test)
1. Ortalama işlem/gün getirisi > 0 ve 5-günlük blok bootstrap alt sınır (%99.58 iki yönlü) > 0
2. FX: 2012–2021 ve 2022+ ayrı ayrı > 0 · BTC: 2017-08..2022-02 ve 2022-03+ ayrı ayrı > 0
3. 2× maliyette ortalama > 0
Geçen → `prop_fit` (Maven challenge + funded tutarlılık) ve Maven forward PAPER adayı.

## Sonuç (2026-11-18)
- H1–H4 FX fix: hepsi GEÇMEDİ. Londra brüt ~0; Tokyo brüt +0.64/+0.55 bp/gün (CI>0) ama ölçülmüş −0.10/−0.18.
- H5 BTC 22–24 UTC: GEÇMEDİ (ölçülmüş −0.56 bp).
- **H6 BTC 21–23 UTC: GEÇTİ** — ölçülmüş +5.42 bp/gün, Bonferroni CI [1.29, 9.67], ≤2022-02 +9.00, 2022-03+ +1.97, 2× +2.32.
