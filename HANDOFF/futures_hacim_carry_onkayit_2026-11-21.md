# Ön-kayıt: futures'a özgü yeni aileler — gerçek hacim (B1/B2), carry (A1), emir tipi ölçümü (C) (2026-11-21)

Bu dosya `futures_round4.py` gerçek veride çalışmadan ÖNCE commit edilir. Kural, eşik, maliyet yöntemi değişmez.
Tasarım: Gemini 4 Argon istişaresi (scratchpad `istisare_cevap7.json`) + Claude denetimi. Eşikler Argon'un ilk önerisinden
aynen alındı, veriye bakılarak değiştirilmedi.

## Dürüst etiket
- B1/B2 kuralları yayınlanmış **günlük/haftalık hisse** bulgularından (Gervais-Kaniel-Mingelgrin 2001; Campbell-Grossman-Wang
  1993) gün içi futures'a **uyarlamadır**; yayınlanmış gün içi futures testi değildir.
- Carry (KMPV 2018) yayınlanmış ve 2018 sonrası kısmen örneklem dışı; ama bizim 23 kontratlık kümemizde yeni.
- Hepsi CME verisinde ilk kez koşuluyor (bu aileler CFD'de test edilmedi; CFD'de gerçek hacim yok).

## Hipotezler (Bonferroni 5 test: B1 NQ, B1 ES, B2 NQ, B2 ES, A1)

### B1 — yüksek gerçek hacimli 15 dk şokun devamı
- Veri: ohlcv-1m NQ.c.0 / ES.c.0 ayarsız; NY saatiyle 15 dk barlar (label=left). Önceki seansa göre `instrument_id`
  değişen gün (roll günü) işlem yok. Tam 26 adet 15 dk RTH barı olmayan gün yok sayılır.
- Sinyal barları: başlangıcı 09:45 … 14:15 olan barlar (kapanış 10:00 … 14:30).
- RVOL = bar hacmi / önceki 20 işlem gününde **aynı saat barının** hacim medyanı. σ = aynı saat barı getirisinin
  önceki 20 gün standart sapması.
- Giriş (üçü birlikte): RVOL > 2.5; |bar getirisi| > 0.75σ; kapanış barın üst %25'inde → long, alt %25'inde → short
  ((C−L)/(H−L) ≥ 0.75 / ≤ 0.25). Günde ilk sinyal, en fazla 1 işlem.
- Giriş fiyatı sinyal barı kapanışı. Çıkış: 4 bar (60 dk) sonraki barın kapanışı. Felaket stopu giriş ± 2×(H−L) sinyal
  barı; sonraki barların high/low'u stopa değerse stopta (boşlukla açılışta geçerse açılış fiyatında) çıkış.
### B2 — düşük hacimli büyük 30 dk hareketin dönüşü
- 30 dk barlar, sinyal barı başlangıcı 09:30 … 14:00 (kapanış 10:00 … 14:30). RVOL ve σ aynı tanım (30 dk, 20 gün).
- Giriş: |bar getirisi| > 1.5σ **ve** RVOL < 0.85 → hareketin tersine. Günde ilk sinyal. Giriş sinyal barı kapanışı,
  çıkış sonraki 30 dk barın kapanışı. Stop giriş ± 1.5×|C−O| sinyal barı, aynı stop mantığı.
### A1 — varlık sınıfı içinde carry (aylık)
- Veri: ohlcv-1d c.0 ve c.1, 23 kök (ES NQ YM RTY / ZN ZB ZF ZT / 6E 6B 6J 6A 6C 6S / CL BZ GC SI HG NG ZC ZS ZW).
  Vade tarihleri `definition` şemasından `instrument_id` → `expiration`.
- Carry C = (F0 − F1)/F1 × 365/(gün(exp1 − exp0)). S = C / σ60 (σ60: son 60 işlem günü günlük getiri std × √252).
  Sınıf ortalaması çıkarılır: S̃ = S − ort(S, aynı sınıf).
- Her ayın son işlem günü kapanışında: S̃ en yüksek 5 (S̃>0 şartıyla) long, en düşük 5 (S̃<0 şartıyla) short.
  Ağırlık ∝ 1/σ60, long ve short bacak ayrı ayrı toplamı 0.5'e normalize. Bir ay tutulur.
- Getiri: c.0 kapanıştan kapanışa, **aynı kontrat**: c.0 `instrument_id` değiştiği gün getiri = F0(t) / F1(t−1) − 1
  (dünkü c.1 aynı kontratsa; değilse o gün getiri 0 ve not edilir). Roll başına 2 yön maliyeti.
- Mevsimsellik düzeltmesi yapılmaz (Argon önerdi; 5 yıllık ısınma örneklemi yarıya indirdiği için alınmadı — bu sapma
  sonuçtan önce yazıldı).

## Maliyet
- B1/B2: MNQ 0.555, MES 0.247 puan/yön (ölçülmüş, bbo-1m + $0.61). Oransal = puan / giriş fiyatı.
- A1: 23 kontratın çoğu için spread **ölçülmedi**. Alt sınır olarak yön başı **1 tam tick** / fiyat (definition
  `min_price_increment`) kullanılır ve sonuç "maliyet ölçülmedi" etiketiyle verilir. 2× satırı da raporlanır.
- Üç satır: maliyetsiz / merkez / 2×.

## Karar kuralı
- B1/B2: işlem başı net (bp) için bootstrap (blok 1, 10.000, seed 20261121) iki yönlü Bonferroni (0.05/5/2) alt sınırı > 0
  **ve** 2012–21 ve 2022+ > 0 **ve** 2× > 0. Değerlendirme 2012-01-01 – 2026-11-19; 2010-06 – 2011 ayrıca raporlanır.
- A1: aylık portföy getirisi için blok bootstrap (blok 3 ay) aynı Bonferroni alt sınırı > 0 **ve** 2012–21 ve 2022+ > 0
  **ve** 2× > 0. Yıllık SR ve t raporlanır.
- Geçen olursa bile LIVE'a girmez. A1 geçse bile prop uygunluğu ayrı (çok kontrat, aylarca taşıma).

## C — emir tipi ölçümü (hipotez değil, betimleyici; karar kuralı yok)
- Veri: Databento `trades` NQ.c.0 2026-09-01 – 2026-11-19 (agresör tarafı). Not: bbo yok; en iyi alış teklifi vekili =
  son satıcı-agresör (side 'A') işlemin fiyatı, en iyi satış = son alıcı-agresör (side 'B') fiyatı.
- Olaylar: RTH içinde her 5 dk barın başı, iki yönde (alış ve satış emri) ayrı; ayrıca aynı dönemdeki NB NQ girişleri.
- Market: anlık karşı taraf vekili fiyatı. Limit: kendi tarafta vekil fiyata 60 sn bekleyen emir. **Dolum** yalnız fiyat
  limitin bir tick ötesine geçerse (alış için limit − 0.25 veya altında işlem) sayılır (kuyruk iyimserliği yok).
- Raporlanan: dolum oranı; dolan/dolmayan için 1, 5, 15 dk sonra orta fiyat değişimi; ters seçim
  AS = E[ΔM] − E[ΔM | dolum]; market'e göre net tasarruf = dolum oranı × yarım spread − AS.

## EK (2026-11-22, sonuç görülmeden, kod çalışmadan önce) — carry verisi
c.0 (takvim önayı) GC/SI/HG'de neredeyse işlem görmüyor (günlük medyan hacim 18–65 kontrat) → kapanış fiyatları bayat.
**A1, c.0/c.1 yerine v.0/v.1 (hacim sıralı 1. ve 2. kontrat) ile koşulur**, 23 kökün hepsinde. Getiri yine aynı kontrat
üzerinden: v.0 `instrument_id` değiştiği gün getiri = F_v0(t) / F_v1(t−1) − 1 (dünkü v.1 aynı kontratsa), değilse
o kontratın dünkü fiyatı yoksa 0. Carry tanımı (F0−F1)/F1 × 365/gün(exp1−exp0); exp1 < exp0 olursa (v.1 daha yakın vade)
işaret tanımı aynı formülle korunur (gün farkı negatif → yıllık carry doğru yönde). Diğer her şey aynı.

## EK 2 (2026-11-22, C koşulmadan önce) — C roll haftası
`NQ.c.0` takvim önayı 2026-09-15 … 09-18'de vadesi dolan Eylül kontratı (günlük 2–69 bin işlem; diğer günler ~350 bin).
Hacim Aralık'a geçmiş; bu günlerde vekil kotasyon bayat. **C'de RTH işlem sayısı tüm günlerin medyanının %50'sinden az
olan günler atlanır** ve sayısı raporlanır. Başka değişiklik yok. B1/B2/A1 sonuçları bu EK'ten önce görüldü; EK yalnız C'yi kapsar.

## SONUÇ (2026-11-22, `futures_round4.py` + `limit_vs_market.py`)
### B1/B2 — bp/işlem, 2012-01-01 – 2026-11-19, Bonferroni (5) CI
| Test | n | maliyetsiz | merkez | 2× | merkez CI | 2012–21 / 2022+ | 2010–11 (merkez) |
|---|---|---|---|---|---|---|---|
| B1 NQ | 621 | +0.66 | −1.50 | −3.65 | [−6.1, +3.2] | −2.16 / +2.03 | −10.43 (n85) |
| B1 ES | 685 | −0.13 | −2.06 | −3.99 | [−5.7, +1.7] | −2.69 / +0.01 | −9.62 (n94) |
| B2 NQ | 289 | +3.98 | +2.14 | +0.31 | [−3.1, +7.7] | −0.79 / +8.73 | −11.99 (n40) |
| B2 ES | 295 | +4.62 | +2.67 | +0.71 | [−1.5, +7.3] | −0.01 / +9.75 | −6.29 (n47) |

### A1 carry — aylık portföy bp, 176 ay (maliyet ölçülmedi: 1 tick/yön alt sınır)
| | ortalama | CI | 2012–21 / 2022+ | yıllık SR |
|---|---|---|---|---|
| maliyetsiz | −0.2 | [−21.4, +21.1] | −10.0 / +20.2 | −0.01 |
| merkez | −7.6 | [−28.6, +13.3] | −17.0 / +11.9 | −0.24 |
| 2× | −15.0 | [−36.2, +5.9] | −24.0 / +3.7 | −0.48 |

**B1, B2, A1: beşi de GEÇMEDİ.** Elenenler: `futures_volume_rules_carry`.

### C — limit vs market (betimleyici), NQ.c.0 trades 2026-09-01 – 11-19, 52 gün (EK 2: 5 ince gün atlandı)
Puan/emir, giriş anı vekil orta fiyata göre; limit = kendi tarafta 60 sn, dolum yalnız bir tick geçilirse.
| Olay | n | dolum | market maliyeti | limit (1m / 5m / 15m) | ters seçim 1m |
|---|---|---|---|---|---|
| 5 dk ızgara | 7.800 | %93.9 | −0.38 | −0.50 / −0.53 / −0.57 | 0.91 |
| NB NQ girişleri | 96 | %90.6 | −0.44 | −1.81 / −2.10 / −1.99 | 2.44 |

Bu tanımla limit emir market'ten pahalı: dolan limitlerde fiyat aleyhe yürüyor (ters seçim > yarım spread).
Kuyruk önceliği modellenmedi (tick geçme şartı kötümser tarafta); gerçek kuyrukta dolum oranı ve sonuç değişebilir.
