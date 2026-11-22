# Handoff & Denetim: İstatistik Filtrelerini Gevşetme ve Hızlı Payout Simülasyonu (2026-11-22)

> **Dürüst Etiket & Bağlam:**
> Bu çalışma ön-kayıtlı bir "yeni kural testi" **DEĞİLDİR**; kullanıcının *"bizim filtrelerimiz fazla mı sıkı, çıkartabileceğimiz filtreleri çıkartıp hızlı payout için elimizdeki ve o filtrelerden ötürü elenen edge'lerin hepsine baksak ne çıkar?"* sorusu üzerine yapılan **keşifsel (post-hoc) duyarlılık denetimidir**.
> Hiçbir canlı (`LIVE`) yetkiyi, `elenenler.py` veto statüsünü veya risk kuralını kendiliğinden **değiştirmez**. Claude ile yapılacak metodolojik/operasyonel tartışma için tüm olgular aşağıda toplanmıştır.

- **Betik:** `HANDOFF/scripts_2026-11-23/relaxed_fast_payout_audit.py`
- **Ham Çıktılar:** `strategy-lab/outputs/intraday/futures_round5/relaxed_gate_audit.csv` ve `relaxed_fast_payout_audit.json`
- **Önceki 5. Tur Ön-Kaydı & Sonucu:** `HANDOFF/futures_tur5_onkayit_2026-11-23.md` (`1df1cd7` → `21911aa`, 11/11 GEÇMEDİ)
- **Fintek BTC Video Testi:** `HANDOFF/fintek_btc_fvg_st_onkayit_2026-11-22.md` (`20f58b2` → `21911aa`, GEÇMEDİ)

---

## 1. Hangi Filtreler Sabit Tutuldu, Hangileri Kademeli Gevşetildi?

- **ASLA gevşetilmeyen (gerçeklik) filtresi:** Ölçülmüş merkez işlem maliyeti (`1×`: Maven `reality_profile.csv` veya CME `bbo-1m` RTH yarım spread + `$0.61/yön` komisyon; order flow'da `+150 ms` gecikme).
- **Kademeli gevşetilen istatistik/dönem kapıları (39 ana aday üzerinde):**
  - **`G0_STRICT` (Mevcut Katı Ön-Kayıt Kuralı):** `1× Merkez > 0` + `Bonferroni CI alt > 0` + `2012–21 > 0` + `2022+ > 0` + `2× Maliyet > 0`. (**6 aday geçiyor**)
  - **`G1_NO_BONF_NO_2X` (Bonferroni ve 2× Kaldırıldı):** Tekil `%95 CI alt > 0` + `2012–21 > 0` + `2022+ > 0` + `1× Merkez > 0`. (**8 aday geçiyor — +2 yeni**)
  - **`G2_2022_CI95` (2012–21 Şartı da Kaldırıldı):** `2022+ > 0` + `1× Merkez > 0` + `%95 CI alt > 0`. (**8 aday geçiyor — +0 yeni**)
  - **`G3_2022_MEAN_POS` (CI Şartı Tamamen Kaldırıldı):** Yalnız `1× Merkez > 0` ve `2022+ > 0` (istatistiksel olarak sıfırdan ayrılmayan gürültülü adaylar dahil). (**22 aday — +14 yeni**)

### Kritik Bulgu A — Negatif Beklentili 17 Aday
39 adayın **17 tanesi** (Order Flow `OF1/OF2/OF3`, `Opex 3. Cuma Pinning NQ/ES`, `X1_ZN`, `X1_6E`, `X2_CL/ZN/6E Donchian 1h`, `Baltussen NQ/ES`, `Williams Oops ES`, `Vol B1 NQ/ES`, `Carry 23 Vadeli`, `Fintek BTC FVG+ST`) **tüm istatistik filtrelerini sıfırlasan bile `1×` gerçek maliyette veya `2022+` döneminde doğrudan negatif**. Yani bunlar filtre sıkı olduğu için değil, para kaybettiği için elendi.

### Kritik Bulgu B — Kapı Seviyesine Göre Pozitif Adaylar Tablosu (22 Aday)

| Aday | Birim | n | 1× Merkez | 2× | 2012–21 | 2022+ | Bonf. CI Alt | %95 CI Alt (Yaklaşık) | G0 (Katı) | G1 (Bonf/2× Yok) | G2 (2022+ & %95 CI) | Not / Zayıf Yanı |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **NB NQ (CME)** | bp/g | 3376 | +2.953 | +1.424 | +1.858 | +5.166 | +1.251 | +1.448 | **EVET** | EVET | EVET | 2010–11 negatif (−4.19) |
| **IBS NQ (CME)** | bp | 382 | +60.853 | +59.187 | +64.518 | +54.149 | +36.201 | +41.307 | **EVET** | EVET | EVET | Gece taşır, stopsuz |
| **IBS ES (CME)** | bp | 362 | +49.857 | +48.060 | +50.655 | +48.326 | +28.914 | +33.607 | **EVET** | EVET | EVET | NQ ile yüksek korelasyon |
| **B7 IBS NQ (CFD)** | bp | 415 | +52.061 | +49.848 | +58.917 | +39.157 | +23.143 | +32.180 | **EVET** | EVET | EVET | Swaplı +46.6 bp ile de geçer |
| **B2 BTC Donchian (CFD)** | bp/g | 3289 | +4.240 | +4.206 | +6.392 | +2.418 | +0.735 | +1.672 | **EVET** | EVET | EVET | **Yalnız swap 0'da** (Maven swapla geçmez) |
| **A4 BTC Gece (CFD)** | bp | 2319 | +15.409 | +12.310 | +23.914 | +7.774 | +0.684 | +0.502 | **EVET*** | EVET | EVET | *İstatistik geçti; Maven −%30 swap ve ikame şartıyla elendi |
| **X1_CL IBS (CME)** | bp | 321 | **+66.279** | +64.472 | +54.601 | +89.312 | −2.467 | **+16.838** | HAYIR | **EVET** | **EVET** | Bonf-11 yüzünden kaldı; **83/354 işlem roll'a takıldı**, petrol kuyruk riski |
| **Turtle Soup NQ (CME)** | bp | 111 | **+18.240** | +16.590 | +1.133 | +42.413 | −2.837 | **+1.392** | HAYIR | **EVET** | **EVET** | CFD'de CI genişti; CME'de %95 CI > 0 ama 2010–11 −12.2 bp |
| **A3 TOM+1 NQ (CFD)** | bp | 178 | +13.995 | +11.782 | +18.862 | +4.177 | −7.090 | −4.655 | HAYIR | HAYIR | HAYIR | Ayda 1 işlem (n=178 → güç düşük), baz orandan +9.3 bp iyi |
| **A3 TOM+1 SP500 (CFD)** | bp | 178 | +7.600 | +4.405 | +9.498 | +3.772 | −9.684 | −7.543 | HAYIR | HAYIR | HAYIR | NQ ile aynı gün |
| **NB ES (CME)** | bp/g | 3501 | +0.882 | −0.805 | +0.373 | +1.911 | −0.485 | −0.321 | HAYIR | HAYIR | HAYIR | NB NQ ile %92 aynı yön |
| **EMA12 5m NQ (CME)** | R | 4162 | +0.032 | −0.052 | −0.006 | +0.109 | −0.044 | −0.033 | HAYIR | HAYIR | HAYIR | 2012–21 sıfır/negatif, 2× negatif |
| **Williams Oops NQ (CME)** | bp | 978 | +2.840 | +1.156 | +2.454 | +3.613 | −4.152 | −2.597 | HAYIR | HAYIR | HAYIR | 2010–11 −14.6 bp |
| **Sweep RTY (CME)** | R | 81 | +0.221 | +0.017 | −0.145 | +0.473 | −0.370 | −0.279 | HAYIR | HAYIR | HAYIR | 2017–21 negatif, n=81 küçük |
| **Vol B2 NQ (CME)** | bp | 289 | +2.143 | +0.308 | −0.788 | +8.731 | −3.107 | −1.950 | HAYIR | HAYIR | HAYIR | 2012–21 ve 2010–11 (−12 bp) negatif |
| **Vol B2 ES (CME)** | bp | 295 | +2.666 | +0.709 | −0.013 | +9.746 | −1.546 | −0.698 | HAYIR | HAYIR | HAYIR | 2012–21 ve 2010–11 negatif |
| **B3 Gold Breakout H1 (CFD)** | bp | 228 | +49.852 | +47.151 | +7.289 | +161.327 | −26.102 | −42.509 | HAYIR | HAYIR | HAYIR | Sağ kuyruk / 2022+ altın trendi |
| **B4 Gold EMA M30 (CFD)** | bp | 1128 | +1.336 | −1.365 | −0.937 | +6.429 | −3.273 | −1.947 | HAYIR | HAYIR | HAYIR | <2022 ve 2× negatif |
| **B5 Turtle Soup NQ (CFD)** | bp | 120 | +4.161 | +1.949 | +2.038 | +8.252 | −16.266 | −10.354 | HAYIR | HAYIR | HAYIR | CI çok geniş |
| **B5 Turtle Soup XAU (CFD)** | bp | 115 | +5.877 | +3.176 | +0.572 | +17.518 | −13.847 | −8.913 | HAYIR | HAYIR | HAYIR | CI çok geniş |
| **B6 Oops NQ (CFD)** | bp | 1028 | +1.564 | −0.648 | +2.027 | +0.616 | −5.945 | −3.786 | HAYIR | HAYIR | HAYIR | 2× negatif |
| **Donchian GC 1h (CME)** | R | 849 | +0.008 | −0.010 | −0.007 | +0.038 | −0.100 | −0.079 | HAYIR | HAYIR | HAYIR | Beklenti ~0 |

---

## 2. Hızlı Payout Prop Simülasyonu: `S0` (Katı) vs `S1` (Makul Gevşek) vs `S2` (Aşırı Gevşek)

Motor: `cheap_sizing.py` (`simulate_multi` uzantısı, 300 yol × 260 işgünü, 20-gün blok bootstrap, `%3` açık risk kapısı, gün içi `1.5×` kötü an stresi, tek hesap / yeniden alım yok).
- **`S0_STRICT_CORE` (5 modül, ~2.5 işlem/işgünü):** `SWEEP + NB + BTC_21_23 + B7_IBS_NQ (k=4) + B2_BTC_DON (swap 0)`
- **`S1_RELAX_CI` (7 modül, ~3.5 işlem/işgünü):** `S0` + `TOM_NQ (k=4)` + `BTC_GECE (k=1.5, swap 0)`
- **`S2_RELAX_2022` (9 modül, ~4.5 işlem/işgünü):** `S1` + `B3_XAU_H1` + `EMA12_NQ`

### A. 2022+ Rejimi (2022-01-01 – 2026-11-17)

| Hesap & Boyutlama | Portföy Seti | İşlem / İşgünü | İlk Payout Medyan (İşgünü) | `p30` (≤21 işgünü) | `p60` (≤42 işgünü) | `p90` (≤64 işgünü) | Payout Öncesi Patlama | 12 Ay Net Ort. ($) | 12 Ay Net Medyan ($) |
|---|---|---|---|---|---|---|---|---|---|
| **FN Instant 2K ($41.99) · `B0.5`** | `S0_STRICT` | 2.51 | **24g** | %43.0 | %60.7 | %72.0 | **%0.0** | +$85.6 | +$77.6 |
| **FN Instant 2K ($41.99) · `B0.5`** | `S1_RELAX_CI` | 3.52 | **16g** | **%53.3** | **%67.3** | **%76.0** | **%0.0** | **+$123.7** | **+$109.2** |
| **FN Instant 2K ($41.99) · `B0.5`** | `S2_RELAX_2022` | 4.55 | **13g** | %53.3 | %67.7 | %72.7 | %0.0 | +$198.1 | +$109.8 |
| **FN Instant 2K ($41.99) · `B1.0`** | `S0_STRICT` | 2.51 | **13g** | %53.0 | %66.0 | %72.3 | %10.3 | +$131.5 | +$102.0 |
| **FN Instant 2K ($41.99) · `B1.0`** | `S1_RELAX_CI` | 3.52 | **12g** | **%56.7** | **%68.0** | **%73.7** | **%9.0** | **+$159.0** | **+$110.4** |
| **FN Instant 2K ($41.99) · `B1.0`** | `S2_RELAX_2022` | 4.55 | **11g** | %57.0 | %66.3 | %68.7 | **%17.3 (2×!)** | **+$89.4 (düştü!)** | **+$27.6** |
| **FN 1-Step 6K ($44.99) · `BT1.0`** | `S0_STRICT` | 2.51 | 59g | %4.0 | %9.0 | %16.3 | %68.0 | +$87.8 | −$45.0 |
| **FN 1-Step 6K ($44.99) · `BT1.0`** | `S1_RELAX_CI` | 3.52 | 54g | %4.3 | %11.0 | %19.3 | %68.3 | +$93.9 | −$45.0 |
| **FN 1-Step 6K ($44.99) · `BT1.0`** | `S2_RELAX_2022` | 4.55 | 44g | %4.3 | %11.3 | %17.7 | **%76.0** | **+$37.5** | −$45.0 |
| **FN 2-Step 6K ($34.99) · `BT1.5`** | `S0_STRICT` | 2.51 | 127g | %0.0 | %0.0 | %1.3 | %50.0 | +$195.8 | −$35.0 |
| **FN 2-Step 6K ($34.99) · `BT1.5`** | `S1_RELAX_CI` | 3.52 | 119g | %0.0 | %0.0 | %1.7 | %51.7 | +$181.3 | −$35.0 |
| **FN 2-Step 6K ($34.99) · `BT1.5`** | `S2_RELAX_2022` | 4.55 | 100g | %0.0 | %0.3 | %4.0 | %52.7 | +$179.4 | −$35.0 |

### B. 2018–2021 Stres Rejimi (Sweep'in Negatif Olduğu Dönem)

| Hesap & Boyutlama | Portföy Seti | İlk Payout Medyan (İşgünü) | `p30` | Payout Öncesi Patlama | 12 Ay Net Ort. ($) | 12 Ay Net Medyan ($) |
|---|---|---|---|---|---|---|
| **FN Instant 2K · `B0.5`** | `S0_STRICT` | 18g | %48.0 | %0.0 | +$65.8 | +$32.8 |
| **FN Instant 2K · `B0.5`** | `S1_RELAX_CI` | 17g | %50.0 | **%0.0** | **+$124.8** | **+$85.0** |
| **FN Instant 2K · `B0.5`** | `S2_RELAX_2022` | 11g | %66.0 | %0.0 | +$126.8 | +$84.0 |
| **FN Instant 2K · `B1.0`** | `S0_STRICT` | 13g | %55.3 | %8.7 | +$112.0 | +$37.9 |
| **FN Instant 2K · `B1.0`** | `S1_RELAX_CI` | 12g | %57.7 | **%4.3** | **+$178.9** | **+$100.8** |
| **FN Instant 2K · `B1.0`** | `S2_RELAX_2022` | 10g | %54.7 | **%21.7** | **+$78.6** | **+$18.7** |

---

## 3. Bilinen Sınırlar & Claude ile Tartışılacak Sorular

1. **Lot İnceliği (Granülerlik) ve Çok Günlük Taşıma Sınırı:**
   - Bu karşılaştırma motorunda yalnız `NB`'ye `0.01` lot basamaklaması uygulandı; `B7`, `TOM`, `B2`, `BTC_GECE` kesirli/ideal risk boyutuyla (`want`) modellendi.
   - Gerçek `FN 2K` hesabında endeks sözleşme çarpanı `10` ise `0.01` lot US100'de `B7 (k=4 ATR)` ve `TOM (k=4 ATR)` tek başına `%3` açık riski aşar (`fn2k.py` notu: 2K'ya sığmıyor, **6K veya 5K hesapta sığıyor**).
   - Ayrıca `B7` ve `BTC_GECE` gibi çok günlük işlemlerin PnL'i giriş gününe toplandı; gün içi/gece MTM düşüşü (`stop_sim.py` / `prop_equity.py`) ayrı kontrol edilmelidir.
2. **Swap-Free ve Madde 8.15 Şartı (`BTC_GECE` & `B2`):**
   - `A4 BTC Gece` ve `B2 BTC Donchian` yalnızca **swap-free** (veya swap ≤%1/yıl) hesapta geçerlidir. FundedNext'te funded aşamada swap-free durumu ve Madde 8.15 ("excessive one-sided exposure") yazılı teyit gerektirir.
3. **Claude'a Sorulacak Somut Karar Soruları:**
   - **Soru 1 (Metodoloji vs Hız):** `G3` (`S2`: `EMA12` + `B3 Gold` gibi CI'si sıfırı geniş kapsayan gürültülü kuralları eklemek) `B1.0` ve `1-Step` ayarlarında patlamayı 2 katına çıkarıp net kazancı düşürüyor. Buna karşılık `G1` (`S1`: istatistiksel olarak iki dönemde de pozitif olan `A4 BTC Gece [swap-free]` + `TOM+1 NQ` veya CME'de `X1_CL` + `Turtle Soup NQ`) eklemek kabul edilebilir bir ödünleşim mi, yoksa post-hoc seçim tuzağı mı?
   - **Soru 2 (Hesap Seçimi):** Kullanıcı "uzun vadeli değil, hızlı ilk payout" istiyor. Simülasyonda ≤30 günde (`p30 > %50`) düşük patlamayla payout veren tek yapı **Instant (`B0.5` / `B1.0`)**; ancak 2K'da lot inceliği `B7`/`TOM`'u kısıtlıyor. İlk adım olarak FN ücretsiz demo hesabında `reality_profiler` + min lot/çarpan kontrolü mü yapılmalı, yoksa 5K/6K hesap mı hedeflenmeli?
