# İnsan Gecikmesi (5 Dk), Ön-İşlem Görsel Kontrol Listesi ve Ucuz Manuel Prop Hesapları (2026-11-24)

- **Betik:** `HANDOFF/scripts_2026-11-23/human_delay_and_checklist.py`
- **Ham Çıktı:** `strategy-lab/outputs/intraday/futures_round5/human_delay_and_checklist.json`
- **Metodoloji (Hilesiz / Örneklem Dışı Doğrulamalı):**
  - Görsel kontrollerin işe yarayıp yaramadığı **2012–2021 (IS)** döneminde seçildi ve **2022–2026 (OOS)** döneminde aynı yönde kalıp kalmadığı sınandı. İki dönemde yön değiştiren (flip eden) tüm filtreler (`NO`) elendi; yalnızca her iki dönemde de tutarlı olan **5 görsel kontrol (`OK`)** lot büyütme (`1.25×`) veya işlem atlama (`Veto = 0×`) kuralı olarak uygulandı.

---

## 1. İnsan Gecikmesi (`T+0` Bot Anlık vs `T+5 dk` Elle Giriş)

| Edge | İşlem Sayısı | Tüm Dönem `T+0` → `T+5m` (Net R) | 2022+ `T+0` → `T+5m` (Net R) | İnsan Gecikmesi Etkisi |
|---|---|---|---|---|
| **`NB` (Noise Band NQ)** | 3.087 | `+0.014R` → `+0.008R` | `+0.018R` → `+0.010R` | 5 dk gecikme kârın ~%40'ını törpülüyor ama **pozitif kalıyor** (2 dk ön-uyarıyla sıfırlanabilir). |
| **`B7_IBS` (Günlük IBS NQ)** | 425 | `+0.071R` → `+0.060R` | `+0.035R` → `+0.027R` | 22:55 vs 23:00 TR farkı çok küçük; **güçlü pozitif kalıyor**. |
| **`BTC_GECE`** | 2.318 | `+0.026R` → `+0.023R` | `+0.018R` → `+0.015R` | 18 saatlik işlemde 1–5 dk gecikme **neredeyse etkisiz**. |
| **`SWEEP` (NQ 15m)** | 230 | `+0.057R` → `+0.027R` | `+0.689R` → `+0.659R` | 2022+ hedef geniş (`4R–8R`) olduğu için 1–2 dk gecikmede bile **`+0.659R` çok güçlü**. |
| **`TOM_NQ` (Ay Dönümü)** | 178 | `+0.031R` → `+0.028R` | `+0.003R` → `−0.001R` | Tek başına 2022+'da zayıf, **ancak aşağıdaki görsel filtreyle (`C1+C2`) çok güçlü pozitife dönüyor**. |
| **`BTC_21_23`** | 3.376 | `+0.005R` → `+0.002R` | `+0.001R` → `−0.003R` | 2 saatlik dar pencerede 2 bp ekstra kayma 2022+ ince kârını siliyor → **tam saat 00:00 TR'de (gecikmesiz) veya bekleyen emirle açılmalı**. |

---

## 2. Doğrulanan 5 Görsel Kontrol ("Açmadan Önce Şuna Bak: Veto Et veya Lot Büyüt")

15 aday filtreden **10 tanesi** iki dönem arasında yön değiştirdiği için **elendi** (`SMA20` NB/B7/BTC'de gürültü çıktı). Hem **2012–2021** hem **2022–2026** döneminde hiç şaşmadan aynı yönde çalışan **5 altın kural**:

| Edge | Elle Açmadan Önce Ekranda Bakacağın Şey | 2012–21 (IS) Net R | 2022–26 (OOS) Net R | Ne Yapacaksın? (Karar Kuralı) |
|---|---|---|---|---|
| **1. `SWEEP NQ`** | **`ADX < 38` mi?** (15m grafikte ADX aşırı şişmemiş, 25–38 arasında mı?) | `ADX<38`: `−0.177R`<br>`ADX≥38`: **`−0.673R`** | `ADX<38`: **`+1.066R` (n=61)**<br>`ADX≥38`: **`−0.295R` (n=26)** | **`ADX ≥ 38` ise HİÇ AÇMA (VETO)!** (Aşırı uzamış trendde ters/devam sweep'i patlıyor). `ADX < 38` ise **Lotu `1.25×` büyüt!** |
| **2. `NB` (Noise Band NQ)** | **Kırılım mumu güçlü mü?** (Bant kırılırken son 5 dk mumu kırılım yönünde en az `%0.05` [`~10–14 puan`] dolu gövdeli mi?) | Güçlü: **`+0.020R`**<br>Zayıf: `−0.001R` | Güçlü: **`+0.016R` (n=495)**<br>Zayıf: `+0.004R` (n=503) | Kırılım mumu cılız/fitilli ise (`<10 puan`) **HİÇ AÇMA (veya yarı lot)**; dolu gövdeliyse **Lotu `1.25×` büyüt!** |
| **3. `B7_IBS` (NQ Günlük Dip)** | **Bugünkü kırmızı mum geniş mi?** (`Günlük Boy > 1.2 × ATR14` — yani sert satış günü mü, yoksa dar yatay gün mü?) | Geniş gün: **`+0.093R`**<br>Dar gün: `+0.069R` | Geniş gün: **`+0.051R` (n=40)**<br>Dar gün: `+0.017R` (n=106) | Sert satış gününün dibiyse (`Range > 1.2 ATR`) **Lotu `1.25×` büyüt**; dar günse **`0.70×` küçült**. |
| **4. `TOM_NQ` (Ay Sonu Long)** | **Ayın son günü yeşil/ortada mı (`IBS ≥ 0.50`)?** (Ayın son günü sert satışla en dipte [`IBS < 0.50`] mi kapanıyor?) | `IBS≥0.50`: **`+0.162R`**<br>`IBS<0.50`: **`−0.160R`** | `IBS≥0.50`: **`+0.106R` (n=33)**<br>`IBS<0.50`: **`−0.136R` (n=26)** | Ayın son günü dip kapanışlı kırmızı mumsa (`IBS < 0.50`) **HİÇ AÇMA (VETO)!** Güçlü kapanışsa **Lotu `1.25×` büyüt!** |
| **5. `TOM_NQ` (Ay Sonu Long)** | **Fiyat 20 günlük ortalamanın (`SMA20`) üstünde mi?** | Üstünde: **`+0.111R`**<br>Altında: **`−0.093R`** | Üstünde: **`+0.048R` (n=35)**<br>Altında: **`−0.071R` (n=24)** | Fiyat `SMA20` altındaysa ay sonu long işlemini **HİÇ AÇMA (VETO)!** |

---

## 3. Ucuz Manuel Prop Hesaplarında Simülasyon (`$39.60 FundYourFX 5K` vs `$59.99 FN 2K EA'sız`)

Üç durumu yan yana simüle ettik:
1. `EXACT_T0` (Bot milisaniyesinde açıyor, kontrol listesi yok)
2. `HUMAN_5M` (Sen 5 dakika geç açıyorsun, kontrol listesi yok)
3. **`HUMAN_5M_CHECKLIST` (Sen 5 dakika geç açıyorsun AMA yukarıdaki 5 görsel kontrolle veto/lot büyütme yapıyorsun)**

| Firma & Fiyat | Risk Ayarı | İcra Modu | İlk Payout Medyan (2022+) | `p15` (≤3 hafta) | `p30` (≤1 ay) | 1. Bilet Patlama | Yıllık Payout Sayısı | 12 Ay Net Kâr (2022+) | Yatırılan Bilet Başına ROI | 2018–21 Stres 12 Ay Net |
|---|---|---|---|---|---|---|---|---|---|---|
| **FundYourFX 5K (\$39.60)** | `B0.8%` | `EXACT_T0` (Bot) | 46 işgünü | %18.3 | %25.3 | %0.0 | 3.1 | `+$389.1` | `9.83×` | `+$222.8` |
| **FundYourFX 5K (\$39.60)** | `B0.8%` | `HUMAN_5M` (Geç) | 45 işgünü | %16.7 | %23.0 | %0.0 | 2.5 | `+$292.8` | `7.39×` | `+$162.4` |
| **FundYourFX 5K (\$39.60)** | **`B0.8%`** | **`HUMAN_5M_CHECKLIST`** | **36 işgünü** | **%20.0** | **%28.7** | **%3.3** | **3.3** | **`+$447.1`** | **`11.29×`** | **`+$207.6`** |
| **FundYourFX 5K (\$39.60)** | `B1.0%` | `EXACT_T0` (Bot) | 32 işgünü | %19.0 | %31.0 | %2.7 | 3.3 | `+$451.0` | `11.39×` | `+$302.3` |
| **FundYourFX 5K (\$39.60)** | `B1.0%` | `HUMAN_5M` (Geç) | 33 işgünü | %19.0 | %28.0 | %3.0 | 2.6 | `+$334.8` | `8.46×` | `+$223.3` |
| **FundYourFX 5K (\$39.60)** | **`B1.0%`** | **`HUMAN_5M_CHECKLIST`** | **31 işgünü** | **%25.0** | **%34.0** | **%5.0** | **3.5** | **`+$514.3`** | **`12.99×`** | **`+$275.6`** |
| **FN Stellar 2K (\$59.99)** | `B1.0%` | `EXACT_T0` (Bot) | 15 işgünü | %47.3 | %57.7 | %0.0 | 5.9 | `+$130.8` | `2.18×` | `+$57.4` |
| **FN Stellar 2K (\$59.99)** | `B1.0%` | `HUMAN_5M` (Geç) | 17 işgünü | %43.3 | %52.0 | %0.0 | 4.7 | `+$91.1` | `1.52×` | `+$31.4` |
| **FN Stellar 2K (\$59.99)** | **`B1.0%`** | **`HUMAN_5M_CHECKLIST`** | **15 işgünü** | **%47.7** | **%53.7** | **%0.0** | **5.8** | **`+$144.1`** | **`2.40×`** | **`+$52.5`** |

---

## 4. Çıkarım: Neden Senin Elle Kontrol Ederek Açman Bottan Bile İyi Çıktı?

1. **5 dakikalık insan gecikmesi (`HUMAN_5M`)** tek başına yıllık kazancı `~%25` azaltıyor (`$451 → $335`).
2. **AMA senin açmadan önce ekranda 5 saniye bakıp yukarıdaki 5 kontrolü uygulaman (`HUMAN_5M_CHECKLIST`):**
   - `Sweep`'teki aşırı şişmiş `ADX ≥ 38` tuzaklarını (`26` zararlı işlemi) ve `TOM`'daki düşüş trendi aylarını eliyor,
   - Güçlü kırılım mumlarında ve sert satış diplerinde lotu `1.25×` büyütüyor,
   - **Sonuçta 5 dakika geç girilmesine rağmen yıllık net kazancı `+$335`'dan `+$514`'a çıkarıp milisaniyelik botu (`+$451`) bile geçiyor!**
3. **`$39.60`'lık FundYourFX 5K vs `$59.99`'lık FN Stellar 2K Farkı:**
   - **FundYourFX 5K (`$39.60`):** `%3` (`$150`) minimum çekim eşiği olduğu için ilk çekim biraz daha uzun sürüyor (medyan **31 işgünü = ~1.5 ay**), ama hesap **5K** olduğu ve `%6 sabit (static) DD` verdiği için patlama sadece `%5` ve yıllık net kazanç **`+$514` (`$39.60` bilet parasının `13 katı`!)**. *(Not: FundYourFX'te `"profit balance rule 4x best day"` [%25 tutarlılık] olup olmadığı canlı destekte tek cümleyle sorulmalı.)*
   - **FN Stellar 2K (`$59.99`, EA paketsiz elle):** `%1` (`$20`) çekim eşiği olduğu için ilk çekim çok daha hızlı (**15 işgünü = 3 hafta**), patlama **`%0`**, yıllık net **`+$144`**.

---

## 5. DÜZELTME & ÖZELEŞTİRİ (Kullanıcı İtirazı Sonrası Permütasyon Denetimi)

Kullanıcı haklı olarak sordu: *"Madem bu filtrelerle daha iyiydi, neden en başta öyle çıkmadı? Şu an şansa bağlı seçicilik (post-hoc) mi yapıyoruz?"*

10.000 tekrarlı permütasyon testi ve 14-test Bonferroni düzeltmesi (`p_bonf = min(1, p_raw * 14)`) koşulduğunda yukarıdaki 5 görsel kontrolün gerçek istatistiksel gücü:

| Kontrol | IS (2012–21) `raw_p` | OOS (2022+) `raw_p` (`Bonf_14`) | 14Y Tamamı `raw_p` (`Bonf_14`) | Gerçek Teşhis |
|---|---|---|---|---|
| **1. `SWEEP ADX < 38`** | `p = 0.1320` | `p = 0.0215` (`0.3010`) | `p = 0.0049` (`0.0686`) | **POST-HOC / KANIT DEĞİL:** IS'te zaten anlamlı değilmiş (`p=0.13`); 16 Kasım `meta_label` testinde de (`Holm p=0.55`) elenmişti. Simülasyondaki `+$335 → +$514` sıçramasının büyük kısmı Sweep'in 26 kaybeden işlemini sonuca bakıp silmekten ve kalan 61 işlemi `1.25×` ile çarpmaktan geliyor! |
| **2. `NB Güçlü 5m Mum`** | `p = 0.1926` | `p = 0.5093` (`1.0000`) | `p = 0.1413` (`1.0000`) | **%100 GÜRÜLTÜ (ŞANS):** İki yarıda da işaretin `+` çıkması tamamen yazı-tura (`p=0.51`). |
| **3. `B7 Geniş Gün > 1.2 ATR`** | `p = 0.6234` | `p = 0.6000` (`1.0000`) | `p = 0.3965` (`1.0000`) | **%100 GÜRÜLTÜ (ŞANS):** Sıfırdan hiçbir farkı yok (`p=0.60`). |
| **4. `TOM IBS ≥ 0.50`** | `p < 0.0001` | `p < 0.0001` (`< 0.0001`) | `p < 0.0001` (`< 0.0001`) | **İSTATİSTİKSEL OLARAK GEÇEN TEK KURAL** — ancak `TOM` zaten elenmiş/yardımcı bir takvim kuralı (ayda 1 işlem) ve bu da ön-kayıtsız keşif. |
| **5. `TOM > SMA20`** | `p < 0.0001` | `p = 0.0121` (`0.1694`) | `p < 0.0001` (`< 0.0001`) | `TOM IBS ≥ 0.50` ile örtüşüyor (ön-kayıtsız keşif). |

### Bağlayıcı Sonuç
- **`HUMAN_5M_CHECKLIST` (`+$514` / `+$144`) satırı post-hoc seçim yanlılığı içerdiği için GEÇERSİZDİR ve KULLANILAMAZ.**
- Manuel icrada geçerli ve dürüst olan rakamlar yalnızca **filtresiz `EXACT_T0` (2 dk ön-uyarıyla zamanında giriş: FundYourFX 5K `+$451/yıl`, FN 2K `+$131/yıl`)** ve **filtresiz `HUMAN_5M` (5 dk gecikmeli giriş: FundYourFX 5K `+$335/yıl`, FN 2K `+$91/yıl`)** aralığıdır.

---

## 6. Post-Hoc Olmayan 4 Yapısal İcra Kontrolü (`structural_human_checks.py`) ve Toplu Karar Denetimi

Grafik üzerinden yön tahmini yapmayan (post-hoc olmayan) 4 mekanik/icra kontrolünün ölçümü:

1. **`H1 — Canlı Spread Kapısı` (`bbo-1m` 2025–2026 gerçek ölçüm):**
   - `NB` karar dakikalarında (`:00` ve `:30`) işlemlerin **`%3.66`'sında spread normalin (`0.50p`) 2 katından fazla açılıyor** ve o anlarda ortalama **`+3.54 puan`** ekstra spread ödeniyor.
   - Kapanışta `15:55–15:59 NY` (`22:55–22:59 TR`) p95 spread `0.75p` iken, `16:15–18:15 NY` (`23:15–01:15 TR` rollover) p95 spread **`1.75p`**'ye fırlıyor.
   - **Hilesiz Kural 1:** Ekranda canlı spread normalin `>2×` katıysa o saniye basma (1–2 dk bekle); kapanış işlemlerini (`B7`, `BTC Gece`) `23:00 TR` sonrasına bırakma, `22:55–22:59 TR`'de aç.
2. **`H2 — 5 Dk Gecikmede Fiyatın Bant İçine Geri Düşmesi (Fakeout İptali)`:**
   - `NB` kırılım sinyalinden 5 dk sonra ekranı açtığında fiyat sinyal fiyatının gerisine (bandın içine) düşmüşse: **IS `−0.0096R`, OOS `−0.0120R`**; kırılım yönünde devam ediyorsa: **IS `+0.0235R`, OOS `+0.0286R`** (`IS p = 0.0382`, `OOS p = 0.0323`, `14Y p = 0.0053`). (`B7_IBS`'te ise `p = 0.73` → anlamsız).
   - **Hilesiz Kural 2:** `NB` sinyaline 1–2 dk içinde zamanında gir; eğer 5 dk geç kaldıysan ve fiyat kırılım seviyesinin gerisine düştüyse (kırılım bozulduysa) işlemi açma.
3. **`H3 — Kırmızı Klasör Haber Saniyesi (±5 Dk)`:**
   - Yön tahmini için değil, prop firma sözleşmesi (`FundedNext` / `FundYourFX` ±5 dk haber kuralı ve spread patlaması) gereği `CPI / NFP / FOMC` açıklamalarından `±5 dk` içinde emir basma.
4. **`H4 — Aynı Gün Çoklu-Sinyal / `%3` Açık Risk Kapısı:**
   - 2022+ günlerinin `%60.1`'inde aynı gün 3+ sinyal geliyor. Açık pozisyonların toplam stop riski `%2.5–%3.0`'e ulaştıysa yeni sinyali pas geç.
