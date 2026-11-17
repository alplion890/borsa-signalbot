# Kaynak taraması adayları ön-kaydı (A1–A4) — 2026-11-18

Kaynak: `HANDOFF/kaynak_taramasi_concretum_quantpedia_kripto_2026-11-17.md`.
Bu dosya sonuçlara bakılmadan commit edilir. Parametre seçimi yok; her aday tek kural.

Ortak:
- Maliyet (yön başı oran): Maven `outputs/intraday/mt5_bridge/reality_profile.csv`
  `real_cost_per_side_central` (ölçüm tarihi dosyada). Satırlar: 0 / merkez / 2×.
- **Swap ölçülmedi** (gece taşıyan A2, A3, A4). Sonuçlar swap hariçtir; geçen aday için
  swap MT5 sembol özelliklerinden ölçülmeden forward'a girmez.
- Ayrım: 2012–2021 vs 2022+ (A4: 2017-08..2021 vs 2022+).
- Bootstrap: 10.000 tekrar, seed 20261118. Günlük/işlem serileri ardışık değilse iid,
  günlük seri ise 5-gün blok.
- Geçme (her test ayrı, merkez maliyet): (1) ortalama net > 0 ve Bonferroni alt sınırı > 0,
  (2) iki alt dönem ayrı ayrı > 0, (3) 2× maliyette tüm dönem > 0, (4) adaya özel ek şart.
- Geçen → `prop_fit`/`prop_equity` ile Maven BNPL simülasyonu (+ tutarlılıksız statik %10
  kural seti karşılaştırma) → Maven forward PAPER adayı. Geçmeyen → `elenenler`.
- Not: Gao-Han-Li-Zhou kuralı NQ/XAU/EUR/GBP'de 2026-09-21'de test edilmiş, hepsi negatif
  (`outputs/intraday/intraday_momentum_research_lab/REPORT.md`); bu sonuç `elenenler`
  kataloğuna da işlenecek. A1 yalnız test edilmemiş ABD dışı endeksleri kapsar.

## A1 — Gün içi zaman serisi momentumu, ABD dışı endeksler
Kaynak: Gao-Han-Li-Zhou JFE 2018; Li-Sakkas-Urquhart JFM 2022 (16 gelişmiş piyasa).
Veri: Dukascopy 5m bid, 2012 → son bar. Seans saatleri yerel saatle (DST zoneinfo ile):
- UK100: Europe/London 08:00–16:30
- GER40: Europe/Berlin 09:00–17:30
- FRA40: Europe/Paris 09:00–17:30
- JAP225: Asia/Tokyo 09:00–15:00 (2024-11-05 ve sonrası 15:30; TSE kapanış uzatması)
Kural: r1 = önceki seans kapanışından (son 5m bar kapanışı) ilk 30 dk sonuna (açılış+25 dk
barının kapanışı) getiri. Son 30 dk'nın ilk barının açılışında sign(r1) yönünde gir, son
barın kapanışında çık. r1 = 0 → işlem yok. Gerekli barlar yoksa gün atlanır. Stop yok.
Test sayısı 4 → Bonferroni alt sınır = 0,05/4/2 kantili (5-gün blok bootstrap, günlük seri).
Maliyet: UK100, FRA40, JAP225 ölçülü. **GER40 ölçülmedi**: yalnız maliyetsiz sonuç ve
"maliyet ölçülmedi" etiketi; geçme kararı MT5 ölçümüne kadar verilmez.

## A2 — Opsiyon vadesi haftası long (Stivers-Sun JBF 2013)
Veri: SP500, NASDAQ100 Dukascopy 5m; günlük kapanış = America/New_York 15:55 barının kapanışı.
OE haftası: ayın 3. Cuması'nı içeren hafta. Giriş: o haftadan önceki son işlem gününün
kapanışı; çıkış: 3. Cuma kapanışı (3. Cuma işlem günü değilse önceki son işlem günü).
Kontrol grubu: diğer tüm haftalar aynı tanımla (önceki hafta son kapanış → hafta son kapanış).
Test sayısı 2 → Bonferroni 0,05/2/2 (iid bootstrap, ~170 hafta/enstrüman).
Ek şart (4): OE haftası ortalaması − diğer haftalar ortalaması > 0 (aksi halde yalnız endeksin
genel yükselişi = baz oran). Not: yılda 12 işlem; tutarlılık kuralı simülasyonda bakılacak.

## A3 — Ay dönümü "+1" günü (Carchano-Pardo 2011)
Veri: SP500, NASDAQ100; günlük kapanış A2 ile aynı.
Kural: ayın son işlem günü kapanışında long, ertesi işlem günü kapanışında çık.
Test sayısı 2 → Bonferroni 0,05/2/2 (iid bootstrap, ~175 işlem/enstrüman).
Ek şart (4): TOM günü ortalaması − diğer tüm günlerin ortalaması > 0 (baz oran kontrolü).

## A4 — BTC NYSE kapalıyken long (Quantpedia/Dujava 2024)
Veri: Binance BTCUSDT 1h (`outputs/intraday/cache/binance/BTCUSDT_1h.csv`), 2017-08 → son bar.
Gündüz seansı Quantpedia tanımıyla 10:00–16:00 America/New_York (NYSE işlem günleri =
NASDAQ100 5m verisinde 15:55 barı olan günler). Kural: her NYSE günü 16:00 ET saat barının
açılışında long, bir sonraki NYSE günü 10:00 ET saat barının açılışında çık (hafta sonu ve
tatiller pozisyonda geçer). Tek test: Bonferroni yok, alt sınır %2,5 kantil (5-gün blok).
Ek şart (4) — ikame kuralı: mevcut BTC 21–23 UTC (H6) ile karşılaştırma. A4 ancak
(1)–(3)'ü geçer VE 2022+ alt döneminde günlük ortalama/std (Sharpe) H6'dan yüksek VE
equity bazlı `prop_equity` simülasyonunda (NB 0.75× ile portföy; A4 ölçeği = 2022+ günlük
std'si H6 0.35× ile eşit olacak kaldıraç; kural seti `maven_bnpl`, 2022+) funded ihlal oranı
H6'dan yüksek değilse H6'nın yerine aday olur. Aksi halde H6 kalır. İkisi birlikte
portföye eklenmez (aynı etki, örtüşen bacak).
