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
