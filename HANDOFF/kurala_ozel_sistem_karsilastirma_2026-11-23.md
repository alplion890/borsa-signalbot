# Karşılaştırmalı Sonuç: Prop Kuralına Özel Sistem — "Consistency Grinder" vs "Uncapped Sprinter" (2026-11-23)

- **Spec:** `docs/superpowers/specs/2026-11-23-rule-shaped-prop-system-design.md`
- **Betik:** `HANDOFF/scripts_2026-11-23/rule_shaped_showdown.py`
- **Ham Çıktılar:** `strategy-lab/outputs/intraday/futures_round5/rule_shaped_showdown.csv` ve `rule_shaped_showdown.json`
- **Dürüst Etiket:** Keşifsel kural-geometrisi ve bilet-ekonomisi (`ticket + rebuy`) karşılaştırması. Gerçek bar yolları (`Path5`, 5m/1h) ve Maven ölçülmüş merkez maliyeti (`reality_profile.csv`) kullanıldı.

---

## 1. Motor 1 (`Consistency Grinder` — Erken TP `0.35R..1.0R` + Günlük Tavan) Neden Çöktü?

Mevcut sinyallerin (`Sweep`, `NB`, `BTC 21–23`, `B7 IBS`, `BTC Gece`, `TOM`, `B2`) gerçek 5m/1h bar yollarında erken kâr al (`TP = tp_r * Stop`) uygulandığında oluşan işlem dağılımı (`2022+`):

| Varyant | İşlem Sayısı (2022+) | Kazanma Oranı (WR %) | Ortalama Net R (`mean_R`) | 95. Yüzdelik Kazanç (`p95_R`) |
|---|---|---|---|---|
| **`UNCAPPED_FULL`** (Orijinal Sağ-Kuyruk) | 3.748 | **%48.1** | **`+0.026R`** | `+0.70R` (Sweep `+4R..+8R`) |
| **`CLIP_1.0R`** | 3.748 | %48.1 | `+0.001R` | `+0.74R` |
| **`CLIP_0.75R`** | 3.748 | %48.2 | **`−0.005R`** | `+0.74R` |
| **`CLIP_0.50R`** | 3.748 | %48.6 | **`−0.017R`** | `+0.49R` |
| **`CLIP_0.35R`** | 3.748 | **%49.7** | **`−0.026R`** | `+0.35R` |
| **`CLIP_0.50R_PLUS_EMA12`** | 5.211 | %45.0 | **`−0.128R`** | `+0.49R` |

### Teşhis
1. **Kazanma Oranı (`WR`) Yükselmiyor:** Zaman bazlı/kapanış bazlı çıkan işlemlerde (`NB`, `BTC 21–23`, `B7`) kaybeden işlemler zaten `0.35R` veya `0.50R` kâra hiç geçmeden eksi kapanıyor (`WR` sadece `%48.1 → %49.7` oluyor).
2. **Beklenti (`mean_R`) Negatife Dönüyor:** Sağ kuyruğu (`+1.5R..+8R`) kestiğin anda, sabit spread/komisyon ve tam boy stop zararları ağır basıyor ve sistemin matematiksel beklentisi negatife (`−0.017R / −0.026R`) düşüyor.
3. **Tutarlılık Firmalarında (`Maven %20`, `FTUK %20`, `FTM %15+5g`) Sonuç:**
   - `Maven 5K ($18, %3 DD, %1 günlük)`: İlk bilet patlama `%95.7–100`, 12 ay net `−$160 .. −$714`.
   - `FTUK 5K ($40, %20 Cons, %6 DD)`: `CLIP_0.75R` ilk payout medyanını `153 → 90` işgününe çekiyor ama ilk bilet patlama `%74.7` ve 12 ay net `−$21.3` (negatif).
   - `FTM 5K ($45, %15 Cons+5g, %6 DD)`: `CLIP_0.75R` medyan `111` işgünü, patlama `%87.3`, 12 ay net `−$82.5`.

> **Sonuç 1:** `%15–%20` Tutarlılık (Best Day) kuralı olan ucuz firmalar, mevcut sinyalleri kırparak (`TP clip` + `daily cap`) **çözülemiyor**. Tutarlılık kuralı olan firmalardan tamamen uzak durmak matematiksel zorunluluk.

---

## 2. Motor 2 (`Uncapped Sprinter` — FN Stellar Instant'ta Sıfır Patlama Kısıtını Kaldırmak)

Tutarlılık kuralı olmayan **FundedNext Stellar Instant (`5K = $149.99`, `2K = $59.99`, `%6` trailing DD, `%70` split, 14 günde `%1+` veya on-demand `%5+`)** üzerinde orijinal sağ-kuyruk (`UNCAPPED_FULL`) portföyünün boyutlama eğrisi:

### A. `2022+` Dönemi (Son 4.8 Yıl — `FN Stellar 5K`, `$149.99` Ücret Düşülmüş)

| Boyutlama Modu | Baz Risk | İlk Payout Medyan | `p15` (≤15 işgünü) | `p30` (≤21 işgünü) | 1. Bilet Patlama | Tek Bilet 12 Ay Net ($) | Rebuy (Yeni Bilet) 12 Ay Net ($) | Yıllık Ort. Bilet / Payout Sayısı | Sıfır-Edge Rebuy 12 Ay ($) |
|---|---|---|---|---|---|---|---|---|---|
| **`BUFFER` (Eski Güvenli)** | `%0.5` | 16 işgünü | %43.3 | %53.3 | **%0.0** | `+$262.4` | `+$262.4` | `1.00 bilet / 5.3 pay` | `+$29.3` |
| **`BUFFER` (Tatlı Nokta 1)** | **`%0.8`** | 16 işgünü | %44.0 | %54.0 | **%0.0** | **`+$288.2`** | **`+$288.2`** | `1.00 bilet / 4.9 pay` | `+$25.2` |
| **`BUFFER` (Tatlı Nokta 2)** | **`%1.0`** | **12 işgünü** | **%51.7** | **%62.0** | **%7.0** | **`+$318.7`** | **`+$400.2`** | `1.40 bilet / 6.1 pay` | `+$63.2` |
| **`FIXED` (Bilet Modeli 1)** | **`%0.8`** | 15 işgünü | %52.3 | %63.3 | %13.0 | `+$326.0` | **`+$639.2`** | `2.57 bilet / 11.3 pay` | `+$101.0` |
| **`FIXED` (Tam Bilet Modeli)** | **`%1.0`** | **13 işgünü** | **%56.0** | **%72.3** | **%17.0** | **`+$326.8`** | **`+$847.3`** | `3.49 bilet / 13.0 pay` | `+$174.4` |
| **`SPRINT_LOCK` (Hızlı+Kilit)** | **`%1.0`** | **12 işgünü** | **%57.3** | **%70.0** | **%14.3** | **`+$375.6`** | **`+$839.1`** | `2.87 bilet / 12.4 pay` | `+$205.9` |

*(Not: `FN Stellar 2K [$59.99]` için tüm dolar rakamları tam `2/5 = 0.40` katıdır: ör. `FIXED %1.0` veya `SPRINT_LOCK %1.0`'da ilk payout medyan **12–13 işgünü**, `p30 = %70–72.3`, 12 ay Rebuy net **`+$335..+$339`**, yani `$60` bilet parasına karşı **5.65× net ROI**.)*

### B. `2018–2021` Stres Dönemi (Sweep'in Negatif Olduğu Rejim — `FN Stellar 5K`)

| Boyutlama Modu | Baz Risk | İlk Payout Medyan | `p15` (≤15 işgünü) | `p30` (≤21 işgünü) | 1. Bilet Patlama | Tek Bilet 12 Ay Net ($) | Rebuy 12 Ay Net ($) | Yıllık Ort. Bilet / Payout | Sıfır-Edge Rebuy 12 Ay ($) |
|---|---|---|---|---|---|---|---|---|---|
| **`BUFFER`** | `%0.5` | 17 işgünü | %41.3 | %49.3 | **%0.0** | `+$264.3` | `+$264.3` | `1.00 bilet / 4.7 pay` | `+$95.8` |
| **`BUFFER`** | **`%0.8`** | **12 işgünü** | %48.3 | %56.7 | **%0.0** | **`+$321.7`** | **`+$321.7`** | `1.00 bilet / 4.5 pay` | `+$144.9` |
| **`BUFFER` (En Sağlam Hızlı)** | **`%1.0`** | **11 işgünü** | **%50.3** | **%59.0** | **%3.3** | **`+$370.3`** | **`+$384.5`** | `1.10 bilet / 4.5 pay` | `+$208.5` |
| **`FIXED`** | **`%0.8`** | 15 işgünü | %50.3 | %60.7 | %19.3 | `+$253.5` | **`+$554.0`** | `3.32 bilet / 10.2 pay` | `+$359.5` |
| **`FIXED`** | **`%1.0`** | **13 işgünü** | **%55.0** | **%65.7** | **%22.3** | `+$227.6` | **`+$759.5`** | `4.78 bilet / 12.4 pay` | `+$484.2` |
| **`SPRINT_LOCK`** | `%1.0` | **12 işgünü** | **%56.3** | **%64.3** | %25.7 | `+$80.0` | `+$194.6` | `4.59 bilet / 9.7 pay` | `+$181.5` |

---

## 3. Kazanan Kurgu ve Operasyonel Karar Özeti

1. **En Tutarlı + Hızlı ("Tek Bilet, Neredeyse Sıfır Patlama") Kazananı → `FN Stellar Instant + BUFFER %1.0 (B1.0)`:**
   - `%0 patlama` (`B0.5`) yerine sadece **`%3.3 – %7.0` ilk bilet patlama riskini** kabul ederek:
   - İlk payout medyanını **16–17 işgününden → 11–12 işgününe (~2.5 takvim haftasına)** indiriyor.
   - 1 ayda (`p30`) payout alma olasılığını **`%59–%62`'ye** çıkarıyor.
   - 12 aylık net kazancı her iki rejimde de (`2022+` ve `2018–21`) **`+$262 → +$385..+$400`** seviyesine taşıyor ve yılda ortalama sadece `1.1–1.4` bilet harcıyor.
2. **En Yüksek Nakit Akışı ("Agresif Bilet + Rebuy") Kazananı → `FN Stellar Instant + FIXED %0.8 – %1.0`:**
   - İlk bilette `%13–%22` patlama riskini kabul edip (patladığında yeni bilet açacak yedek sermaye bulundurmak şartıyla):
   - İlk payout medyanı **13–15 işgünü**, 1 ayda payout alma ihtimali **`%63–%72.3`**.
   - Yılda ortalama **10–13 kez payout** alarak 5K hesapta **`+$554..+$847`**, 2K hesapta **`+$220..+$339`** net nakit üretiyor.
   - **Kritik Uyarı:** Bu agresif modda yılda `2.6–4.8` bilet satın alınıyor; yani kasada en az **3 biletlik sermaye** olmadan `FIXED %1.0` oynanırsa ilk `%17–22`'lik patlama dilimine denk gelindiğinde oyun biter. Tek bilet parası varsa **`BUFFER %1.0` (`B1.0`)** kesinlikle üstündür.
