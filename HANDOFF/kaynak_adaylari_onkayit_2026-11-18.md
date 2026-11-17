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

---
## SONUÇLAR (ön-kayıt fe57dc4 sonrası, 2026-11-18)
Kod: `strategy-lab/intraday/kaynak_adaylari.py`; çıktı `outputs/intraday/kaynak_adaylari/A1..A4.json`.
Maliyet: Maven merkez (reality_profile.csv). Swap hariç.

| Aday | Maliyetsiz | Ölçülmüş merkez | 2× | Alt dönemler (merkez) | Sonuç |
|---|---|---|---|---|---|
| A1 UK100 | +0.03 bp | −1.45 bp | −2.93 | −1.23 / −1.86 | GEÇMEDİ |
| A1 FRA40 | −0.26 | −2.31 | −4.36 | −2.30 / −2.34 | GEÇMEDİ |
| A1 JAP225 | +0.10 | −3.05 | −6.19 | −2.60 / −3.62 | GEÇMEDİ |
| A1 GER40 | +0.70 (CI [−0.22, 1.57]) | ölçülmedi | — | maliyetsiz 2022+ +0.10 | maliyet ölçülmedi; 2022+ her pozitif maliyette < 0 → şart (2) sağlanamaz |
| A2 SP500 OE haftası | +8.9 bp/hafta | +5.7 | +2.5 | +15.8 / −14.6 | GEÇMEDİ (OE − diğer = −20.5 bp) |
| A2 NQ | +16.0 | +13.8 | +11.6 | +31.8 / −22.4 | GEÇMEDİ (OE − diğer = −24.1 bp) |
| A3 SP500 TOM+1 | +10.8 | +7.6, CI [−9.7, 24.9] | +4.4 | +9.5 / +3.8 | GEÇMEDİ (CI) — TOM − diğer = +5.8 bp |
| A3 NQ | +16.2 | +14.0, CI [−7.1, 35.5] | +11.8 | +18.9 / +4.2 | GEÇMEDİ (CI) — TOM − diğer = +9.3 bp |
| A4 BTC gece | +18.5 | +15.4, CI [0.7, 30.5] | +12.3 | +23.9 / +7.8 | İSTATİSTİK GEÇTİ, İKAME ŞARTI GEÇMEDİ |

A4 ikame şartı (NB 0.75× + BTC, Maven BNPL, 2022+, equity):
- H6 21–23 UTC 0.35×: çekim $99/yıl, funded ihlal %33, challenge %65 geç.
- A4 0.101× (eşit std): çekim $154/yıl, funded ihlal **%67**, challenge %72 geç / %1.6 patla.
- Sharpe 2022+ (işlem başı) A4 0.030 > H6 0.016; korelasyon 0.25; A4 gün içi en kötü −%37 (1×).
- Karar (ön-kayıt kuralı): ihlal H6'dan yüksek → H6 kalır. A4 `not_adopted` (veto değil).
- Bilgi (ön-kayıtta şart değildi): tutarlılıksız statik %10 kural setinde A4 $362/yıl ihlal %5.4; H6 $265 ihlal %0.
- Gündüz 10–16 ET aynı BTC saatleri: 2022+ −0.81 bp/saat log → etki gece/gündüz ayrımı, salt BTC yükselişi değil.

Ek: Gao ilk30→son30 kuralı NQ/XAU/EUR/GBP'de 2026-09-21'de de negatifti; ikisi `elenenler` `gao_itsm_first30_last30` maddesinde birleştirildi.

## Ek: Maven swap ölçümü ve A4 kuyruk dağılımı (2026-11-18, MT5 MavenTrade-Server)
Kaynak: `MetaTrader5.symbol_info` (salt okuma). Sunucu saati = UTC (tick zamanı UTC ile aynı) → rollover 00:00 UTC.

| Sembol | swap_mode | Long | Short | Üçlü gün | Gece başı (oran, bugünkü fiyat) |
|---|---|---|---|---|---|
| BTCUSD | 6 (açılış fiyatına yıllık faiz) | −%30/yıl | −%30/yıl | 7 (her gün) | −8.33 bp |
| US100 | 1 (puan) | −319.5 puan | +80.7 | Cuma | long −1.18 bp, short +0.30 bp |
| XAUUSD | 1 | −45.3 | +25.2 | 7 | long −1.18 bp, short +0.66 bp |
| US500 | 1 | −9.36 | +2.37 | Cuma | küçük |
| GER30 | 1 | −26.5 | −1.27 | Cuma | — |

- A4 BTC gece: ortalama 1.45 rollover/işlem (1: 1812, 3: 419 hafta sonu, 4: 63, 2: 25). Swaplı merkez net
  **+3.3 bp, CI [−11.4, 18.4], 2017–21 +11.8 / 2022+ −4.4 → GEÇMEZ.** `elenenler` statüsü rejected.
- H6 BTC 21–23 UTC 00:00 UTC'den önce kapanıyor → swap yok. **Risk:** sunucu yaz saatinde UTC+1'e geçerse
  rollover 23:00 UTC = H6 çıkış anı; yazın kontrol edilmeli.
- Noise Band gün içi kapanır → swap yok. Sweep/Donchian gece taşırsa long ~−1.2 bp/gece.

A4 gün içi en kötü an dağılımı (1×, n=2319): medyan −%1.5; %10'luk −%5.4; %5'lik −%7.9; %1'lik −%15.8; %0.1'lik −%28.1.
−%10 veya kötüsü 70 işlem (%3.0), −%20 veya kötüsü 11 (%0.5). En kötü: 2020-03-12 −%37.3 (Covid çöküşü), 2021-05-18 −%30.7,
2020-03-11 −%29.1. Yıllık en kötü 2023–2026: −9.8, −21.8, −12.6, −11.1.

## Ek: başka firma araştırması (2026-11-18)
BTC gece elendiği için hafta sonu BTC tutma şartı düştü. H6 21–23 UTC hafta sonu payı küçük:
tüm günler 2022+ +1.21 bp (%4.4/yıl), yalnız hafta içi +1.12 bp (%2.9/yıl), hafta sonu +1.42 bp (%1.5/yıl).
Gerekenler: NAS100 + XAU + hafta içi BTC CFD, tutarlılık kuralı yok, statik DD, gece tutma serbest.

- FTMO 2-Step: statik %10, günlük %5, tutarlılık kuralı yok — resmi sayfa (73e5e4f'de doğrulandı). Kripto
  enstrüman listesi ve funded hesapta hafta sonu/haber kuralı resmi sayfadan DOĞRULANMADI.
- FTMO 1-Step: EOD trailing %10, günlük %3, Best Day %50 (resmi, 73e5e4f).
- FundedNext Stellar 2-Step: statik %10, günlük %5; tutarlılık yalnız Express'te (73e5e4f). Resmi yardım
  merkezi kripto makalesi İngilizce/Fransızca sürümde çelişkili (biri hafta sonu tutma var, biri yalnız hafta içi).
- Ajan raporu eksik: 11 firmadan yalnız FTMO ve FundedNext'e baktı; The5ers, E8, FundingPips, Alpha Capital,
  Blue Guardian vb. açılmadı. Ajanın "FTMO haberden 2 saat önce gap yasağı" ifadesi doğrulanmadı, kullanılmadı.
- Başka firmada maliyet (spread/swap) ölçülmedi: maliyet kuralı gereği hesap açılmadan sonuç verilemez.
