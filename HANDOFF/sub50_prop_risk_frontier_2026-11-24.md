# ≤$50 Prop Firmaları (Instant / 1-Step / 2-Step, 5K–6K) ve Hız–Patlama Risk Eğrisi (2026-11-24)

- **Betik:** `HANDOFF/scripts_2026-11-23/sub50_prop_risk_frontier.py`
- **Ham Çıktı:** `strategy-lab/outputs/intraday/futures_round5/sub50_prop_risk_frontier.json`
- **Veri Güncelliği:** 2026-11 itibarıyla resmi kural sayfaları + web doğrulaması (`search_web` + `instant-prop-arastirma/results/*.json`).

---

## 1. 2026-11 İtibarıyla ≤$50 (ve $59.99 Referans), Türkiye'ye Açık, Bizim Sisteme Uyan Hesaplar

> **10K Boyut Hakkında Dürüst Bulgu:** 2026-11 itibarıyla **$50 altında 10K** boyutta tutarlılık kuralı (`%15–20 Best Day`) olmayan **hiçbir firma yoktur** (10K hesaplar `$59.99–$97` bandında başlar: FN Lite 10K `$59.99`, FundingPips 2-Step 10K `$50–70`, FundYourFX Instant 10K `$71.60`).
> **$50 altında 5K ve 6K** boyutta ise Türkiye'ye açık ve kurallarımıza uyan **6 seçenek** vardır:

| # | Firma & Program | Boyut & Fiyat (2026-11) | Türü & Temel Kurallar | Kural Kitabına Göre **Teorik En Erken** İlk Payout | Simülasyonda **Şanslı Seri (`p10`)** İlk Payout | Simülasyonda **Ortanca (`Medyan`)** İlk Payout |
|---|---|---|---|---|---|---|
| **1** | **FundYourFX — Instant Classic** | **5K · \$39.60** | **INSTANT** · `%6` Sabit (Static) DD, `%4` günlük, min 6 işlem günü, `%3` (\$150) hedef, haftalık döngü | **6. İşgünü** *(6 işlem günü + %3 kâr tamamlandığında)* | **7. İşgünü (~1.5 Hafta!)** | **28 – 30 İşgünü** |
| **2** | **FundedNext — Stellar Instant** *(Ref)* | **2K · \$59.99** *(EA'sız elle)* | **INSTANT** · `%6` Kayan DD (başlangıçta kilit), **günlük limit YOK**, **min gün YOK**, `%5` (\$100) **On-Demand** veya 14 günde `%1` (\$20) | **1. İŞGÜNÜ!** *(`%5` kârda aynı gün On-Demand; yoksa 10. işgününde [14 takvim günü] `%1`)* | **10. İşgünü (2 Hafta)** | **13 – 15 İşgünü** |
| **3** | **Alpha Capital / E8 — 1-Step** | **5K · \$40–\$48** | **1-STEP** · Tek faz `%10` hedef (min 2 gün), `%6` kayan/statik DD, `%4` günlük, Funded'da `%40` Best-Day, 14g çekim | **12. İşgünü** *(2 gün challenge + 10 işgünü [14 takvim günü] funded bekleme)* | **70 – 74 İşgünü (~3.5 Ay)** | **153 – 160 İşgünü** |
| **4** | **FundingPips — 2-Step Standard** | **5K · \$29–\$36** | **2-STEP** · `%8 + %5` hedef, `%10` Sabit DD, `%5` günlük, min 3 gün/faz, 14 günde çekim *(Funded'da hafta sonu için Swing gerekli)* | **16. İşgünü** *(3g Faz 1 + 3g Faz 2 + 10 işgünü funded)* | **86 – 90 İşgünü (~4 Ay)** | **159 – 161 İşgünü** |
| **5** | **The5ers — High Stakes** | **5K · \$39.00** | **2-STEP** · `%8 + %5` hedef, `%10` Sabit DD, `%5` günlük, min 3 kârlı gün (`≥%0.5`)/faz, **hafta sonu serbest**, 14g çekim + ilk çekimde \$39 iade | **16. İşgünü** *(3g + 3g + 10 işgünü funded)* | **87 – 91 İşgünü (~4 Ay)** | **159 – 161 İşgünü** |
| **6** | **FundedNext — Stellar Lite** | **5K · \$32.99** | **2-STEP** · `%8 + %4` hedef, `%8` Sabit DD, `%4` günlük, min 2 gün/faz, **hafta sonu serbest**, ilk çekim 21 takvim günü | **19. İşgünü** *(2g + 2g + 15 işgünü [21 takvim günü] funded)* | **79 – 88 İşgünü (~4 Ay)** | **152 – 154 İşgünü** |
| **7** | **FundedNext — Stellar 2-Step** | **6K · \$34.99** *(Kasım kodu `NOVSTR`, liste \$59.99)* | **2-STEP (6K)** · `%8 + %5` hedef, `%10` Sabit DD, `%5` günlük, min 5 gün/faz, **hafta sonu serbest** | **25. İşgünü** *(5g + 5g + 15 işgünü funded)* | **90 – 93 İşgünü (~4.5 Ay)** | **159 – 162 İşgünü** |

### Neden Diğer ≤$50 Instant Hesaplar Elendi?
- **Maven Instant 5K (\$18.05):** `%20` tutarlılık + `%1` anlık açık zarar (floating loss) + `%3` sıkı kayan DD → simülasyonda `%95+` patlama / 146 gün kilit.
- **Blue Guardian Instant Starter 5K (\$11–\$50):** `%15` tutarlılık + `%1` Guardian Shield açık zarar kesici + Starter yalnız tek çekim (`$225` tavan) sonra hesap kapanıyor.
- **FundingPips Zero Instant 5K (\$48):** Hafta sonu pozisyon tutmak **kesin ihlal (hard breach)** + her çekimde kalıcı `%15` tutarlılık kuralı.
- **FXIFY Instant Lite 5K (\$39):** Cuma gecesi tüm pozisyonlar zorunlu kapatılıyor + `%20` tutarlılık + min 10 işlem günü.
- **AquaFunded Instant Standard 5K (\$23–\$60):** `%15` tutarlılık kuralı.

---

## 2. Riskimizi Nasıl Ayarlarsak "En Az Patlama İhtimaliyle En Hızlı" Alırız? (Tek Bilet Simülasyonu, 2022+)

Hilesiz, post-hoc filtresiz (`EXACT_T0` — 2 dk ön-uyarılı zamanında giriş, `%3` açık risk kapılı) 6 farklı risk ayarının sonuçları:

### A. `FundYourFX Instant Classic 5K ($39.60)` — Risk Eğrisi
| Risk Ayarı | Açıklama | En Erken (`p10`) | Ortanca (`Medyan`) | 1 Ayda Çekim (`p30`) | 2 Ayda Çekim (`p60`) | 12 Ayda Çekim Alan (%) | İlk Çekim Öncesi **Patlama (%)** | 12 Ay Net Kâr (Ort / Medyan) |
|---|---|---|---|---|---|---|---|---|
| **`A_SAFE_BUFFER_0.5%`** | Tampon orantılı `%0.5` risk | 15 işgünü | 56 işgünü | %15.0 | %36.0 | **%94.0** | **%0.0!** | `+$307.4` / `+$305.4` |
| **`D_CHAL_1.5_FUND_0.8%`** | Tampon orantılı `%0.8` risk | **9 işgünü** | 44 işgünü | %23.3 | %42.3 | **%86.3** | **%8.0** | `+$320.8` / **`+$301.5`** |
| **`B_SWEET_BUFFER_1.0%` (ÖNERİLEN)** | **Tampon orantılı `%1.0` risk** | **7 işgünü (~1.5 hf!)** | **30 işgünü (~1.5 ay)** | **%30.7** | **%50.0** | **%83.3** | **%10.0** | **`+$341.8`** / `+$278.9` |
| **`C_FAST_TAPER_1.2%`** | `%2` kâra kadar `%1.2`, sonra `%0.66` | **7 işgünü** | 31 işgünü | **%31.7** | %48.7 | %82.3 | %16.7 | `+$338.2` / `+$287.8` |
| **`E_AGGR_FIXED_1.2%`** | Sabit `%1.2` risk (tamponsuz) | **7 işgünü** | **28 işgünü** | %30.7 | %49.3 | %75.0 | **%25.0** | `+$313.0` / `+$211.1` |

### B. `FundedNext Stellar Instant 2K ($59.99, EA'sız Elle)` — Risk Eğrisi
| Risk Ayarı | Açıklama | En Erken (`p10`) | Ortanca (`Medyan`) | 1 Ayda Çekim (`p30`) | 2 Ayda Çekim (`p60`) | 12 Ayda Çekim Alan (%) | İlk Çekim Öncesi **Patlama (%)** | 12 Ay Net Kâr (Ort / Medyan) |
|---|---|---|---|---|---|---|---|---|
| **`A_SAFE_BUFFER_0.5%`** | Tampon orantılı `%0.5` risk | 10 işgünü | 22 işgünü | %46.7 | %67.7 | **%96.0** | **%0.0!** | `+$80.1` / `+$75.2` |
| **`B_SWEET_BUFFER_1.0%` (ÖNERİLEN 1)** | **Tampon orantılı `%1.0` risk** | **10 işgünü (2 hf)** | **15 işgünü (3 hf)** | **%57.7** | **%72.0** | **%94.0** | **%0.0!** | **`+$126.0` / `+$98.6`** |
| **`C_FAST_TAPER_1.2%` (ÖNERİLEN 2)** | **`%3.2` kâra kadar `%1.2`, sonra `%0.66`** | **10 işgünü (2 hf)** | **14 işgünü (<3 hf)** | **%62.0** | **%76.3** | **%94.0** | **Sadece %4.3!** | **`+$132.2` / `+$111.7`** |
| **`E_AGGR_FIXED_1.2%`** | Sabit `%1.2` risk | 10 işgünü | 13 işgünü | %57.7 | %72.7 | %83.3 | %16.7 | `+$105.0` / `+$68.4` |

### C. Challenge Hesapları (`The5ers 5K $39`, `FundingPips 5K $32`, `FN Lite 5K $32.99`, `Alpha/E8 1-Step 5K $45`) Neden Çok Yavaş?
- Tek hesapla (ve `%3` toplam açık risk sınırı içinde) `%10–%13` challenge hedefini geçip üstüne 14–21 gün funded beklemek, en iyi ayarda (`CHAL %1.5 → FUND %0.8`) bile **şanslı seride (`p10`) 74–90 işgünü (~3.5–4 ay), ortanca 152–161 işgünü (~7 ay)** sürüyor ve tek hesapların sadece `%34–%51.7`'si ilk payout'a ulaşabiliyor.
- **Matematiksel Sebep:** Bizim portföy yılda `~%20–30` (`%1` riskte) yüksek Sharpe'lı (`~1.5`) istikrarlı getiri üretiyor; `%1–%3` isteyen **Instant** hesapları 7–30 işgününde rahatça çözerken, `%12–%13` isteyen **Challenge** hesaplarını tek bilette hızlı geçmek için gereken aşırı kaldıraç `%4–%5` günlük DD sınırına çarpıyor.

---

## 3. Nihai Karar ve Tüm Bilgilerin Son Kontrolü

1. **En Hızlı + En Az Patlama Risk Ayarı:**
   - **`B_SWEET_BUFFER_1.0%` (Tampon Orantılı `%1.0` Baz Risk)** veya **`C_FAST_TAPER_1.2%` (Hedefin ilk `%65`'inde `%1.2` risk, son `%35`'inde `%0.66` risk + tampon koruması)**.
2. **Seçilecek 2 Hesap (`≤$50–$60` Bandı):**
   - **Seçenek 1 (`$39.60` — FundYourFX Instant Classic 5K, Match-Trader, Elle):**
     - **Kural en erken:** **6. işgünü** · **Simülasyon en erken (`p10`):** **7. işgünü (~1.5 hafta)** · **Ortanca:** **30 işgünü**.
     - `BUFFER %1.0` ile patlama `%10` (`%0.5` riskte `%0` patlama), 12 ay net ortalama **`+$342` (`$39.60`'ın `8.6 katı`)**.
     - *Satın almadan önce tek doğrulama:* Canlı desteğe *"Instant Classic 5K'da 'profit balance 4x best day' (%25 tutarlılık) kuralı var mı ve US100 + BTCUSD işlem görüyor mu?"* diye sor.
   - **Seçenek 2 (`$59.99` — FundedNext Stellar Instant 2K, MT5, EA Paketsiz Elle):**
     - **Kural en erken:** **1. işgünü (`%5` = $100 kârda anında On-Demand)** veya **10. işgünü (14. takvim gününde `%1` = $20)**.
     - **Simülasyon en erken (`p10`):** **10. işgünü (2 hafta)** · **Ortanca:** **14–15 işgünü (3 hafta)**.
     - `BUFFER %1.0` ile **%0.0 patlama**, `FAST_TAPER %1.2` ile **%4.3 patlama** ve 1 ayda çekim alma ihtimali **`%62.0`**.
     - *Satın almadan önce tek doğrulama:* Checkout ekranında (`app.fundednext.com/plans`) Türkiye kabulü ve Swap-Free paketinin BTC'yi kapsayıp kapsamadığını kontrol et.
