# Satın Alma Öncesi Tam Kör Nokta, Broker Fiziği ve Fırsat Denetimi + 5 Kapılı Doğrulama Protokolü (2026-11-24)

- **Betik:** `HANDOFF/scripts_2026-11-24/tam_kor_nokta_denetimi.py`
- **Ham Çıktı:** `strategy-lab/outputs/intraday/futures_round5/tam_kor_nokta_denetimi_2026-11-24.json`
- **Amaç:** "Kullanıcı sormasa fark edilmeyecek başka hangi handikaplar veya fırsatlar var, bundan nasıl emin olacağız?" sorusunu tek seferlik tahminle değil, **5 otomatik kod kilidi (`assert` invaryantı) + 6 broker fiziği katmanı + çapraz veri kontrolü** ile kalıcı olarak çözmek.

---

## 1. Önceki Hatalar Neden Gözden Kaçtı ve Bu Denetim Neleri Yakaladı?

`strategy-lab/intraday/` altındaki çekirdek modüllerde `715` birim/özellik testi varken, `HANDOFF/scripts_*` altındaki hızlı simülasyon betiklerinde zorunlu mantık kilitleri (`assert`) yoktu. Sistematik denetim betiği (`tam_kor_nokta_denetimi.py`) yazıldığında **3 simülasyon hatası, 4 fiziksel broker handikapı ve 1 sahte fırsat** otomatik yakalandı:

1. **Yakalanan Hata #1 (`sub50_prop_risk_frontier.py` Açık-Risk Çakışma Bugı — `INV-3` yakaladı):**
   - Eski betik gündüz açılıp kapanan `SWEEP + NB` ile gece `21:00–23:00 UTC`'de çalışan `BTC_21_23`'ü aynı saniyede açıkmış gibi topluyor ve FundedNext'in `%3` açık risk kuralını **tüm firmalara** (`The5ers`, `FundingPips`, `FYFX`) uyguluyordu. Bu yüzden Challenge riskini `%1.0`'dan `%2.0`'a çıkarınca `NB`, `B7` ve `BTC` siliniyor, geçiş süresi yapay olarak uzuyordu (`159g → 189g`). Düzeltilince `The5ers` medyan geçiş süresi monoton olarak hızlandı (`%0.8 = 217g → %1.5 = 146g → %2.0 = 118g`).
2. **Yakalanan Hata #2 (`FN Stellar Instant 2K` Çekim Sonrası Kayan DD Kilidi — `INV-5` yakaladı):**
   - Eski betik çekim yapılınca `peak = 0` sıfırlayıp hesaba yeniden `-6%` tampon veriyordu. Oysa resmi FN kuralında `6%` kayan DD başlangıç bakiyesine kadar kilitlenir ve **çekim sonrasında sıfırlanmaz**. Hesabın ilk eksi tikte ölmemesi için içeride `%4` tampon bırakıldığında `FN Instant 2K ($59.99)` yıllık net beklentisi `+$5`'tan **`-$38.4`'e (medyan `-$60`)** düştü → **Kesin elendi.**
3. **Yakalanan Hata #3 (`B7_IBS` Gece MTM Düşüşü ve `-1.18 bp/gece` Swap):**
   - Çok günlük `B7_IBS` işlemlerinin ara gecelerdeki açık (floating) düşüşleri ve gecelik swap maliyeti günlük MTM serisine eklendi.
4. **Yakalanan Sahte "Gizli Fırsat" (`Donchian XAU 1H` Spot-Swap Yanılsaması):**
   - Dukascopy spot `XAUUSD` verisinde `DXAU` eklemek 3 dönemin tamamında (`2013–17`, `2018–21`, `2022+`) yıllık neti `FYFX`'te `+$255`'a, `The5ers`'ta `+$42..+$60`'a fırlattı. Ancak CME altın vadeli (`GC`, faiz/taşıma maliyeti fiyata gömülü) çapraz kontrolüne (`outputs/intraday/futures_transfer3/result.json`) bakıldığında `T2_DONCHIAN_GC` beklentisinin sadece **`+0.008R` (`CI [-0.10, +0.11]`, `PASS=False`)** olduğu görüldü. Spot CFD'deki görünür kâr, spot veride düşülmeyen gecelik altın swap'ından gelmektedir → **Swap-free altın doğrulanmadan portföye eklenmez.**

---

## 2. Dürüst Çekirdek Portföyün (`V3`: `SWEEP=+0.02R`, `NB`, `B7_IBS` MTM+Swap, `BTC_21_23`) Gerçek Gücü

### A. Modül Bazlı 3 Dönem Drift Kontrolü (`1.0x` Ölçülmüş Maven Maliyeti)
| Modül | `2022+` (`n` / Ort `R` / Top `R`) | `2018–21` (`n` / Ort `R` / Top `R`) | `2013–17` (`n` / Ort `R` / Top `R`) | Not |
|---|---|---|---|---|
| `SWEEP` *(örneklem içi)* | `79` / `+0.728R` / `+57.5R` | `87` / `-0.540R` / `-47.0R` | `51` / `+0.041R` / `+2.1R` | `V3`'te canlı forward **`+0.020R`** kullanılır |
| `NB` *(Noise Band NQ, k=1)* | `653` / `+0.027R` / `+17.5R` | `552` / `+0.025R` / `+13.6R` | `681` / `+0.002R` / `+1.5R` | 3 dönemde de pozitif |
| `B7_IBS` *(MTM + swap, k=4)* | `472g` / `+0.009R` / `+4.1R` | `337g` / `+0.026R` / `+8.7R` | `436g` / `+0.027R` / `+11.8R` | 3 dönemde de pozitif |
| `BTC_21_23` *(k=1.5, 0 gece)* | `1271` / `-0.001R` / `-0.7R` | `1044` / `+0.008R` / `+8.2R` | `95` / `+0.054R` / `+5.1R` | `2022+`'ta başabaş |

> **Matematiksel Gerçek:** `SWEEP = +0.02R` alındığında portföyün `2022+` gerçek üretimi yılda **`~+4.6R`**'dir (`%1` riskte yılda `~+%4.6` net büyüme).

### B. Tüm ≤$50 (ve $59.99 Ref) Hesapların Tam Broker Fiziği Altında Karşılaştırması (`2022+`, Gerçek `0.01` Lot `CS=1`)
| Hesap & Güncel Kurallar (2026-11) | Risk (Chal/Fund) | En Erken / Medyan (`gün`) | 12 Ayda `≥1` Payout | İlk Payout Öncesi **Patlama** | Tek Payout Ort. | 12 Ay Net **Ort / Medyan** | Sıfır-Edge Kontrolü & Karşı Taraf Notu |
|---|---|---|---|---|---|---|---|
| **1. FundYourFX Instant Classic 5K (\$39.60, `%50→%90` split)** | `%1.0` | **9g / 42g** | **%62.7** | **%23.7** | **\$134.8** | **`+$142.4` / `+$55.8`** | `+$75.8` (**UYARI:** Sıfır-edge pozitif → firma ödeme/gizli kural riski!) |
| **2. FundYourFX 5K + EĞER `%25 (4x Best Day)` Kuralı Varsa** | `%1.0` | 41g / 109g | **%6.7** | %26.7 | \$349.8 | **`-$15.1` / `-$39.6`** | `-$30.0` (**ÖLÜMCÜL HANDİKAP:** Bu kural varsa hesap alınmaz!) |
| **3. FN Stellar Instant 2K (\$59.99, Kayan Kilit + `%4` Tampon)** | `%1.0` | 16g / 65g | %36.0 | %12.0 | \$28.3 | **`-$38.4` / `-$60.0`** | `-$46.4` (Çekim sonrası kayan kilit yüzünden elendi) |
| **4. The5ers High Stakes 5K (\$39, Classic `%8+%5`)** | `%1.2 / %0.8` | 85g / 164g | %13.3 | %12.0 | \$93.9 | **`-$12.4` / `-$39.0`** | `-$28.6` (`+4.6R/yıl` drift tek bilette `%13` hedefe yavaş kalıyor) |
| **5. The5ers High Stakes 5K (\$39, New `%10+%5`)** | `%1.2 / %0.8` | 92g / 164g | %8.3 | %11.0 | \$93.1 | **`-$22.2` / `-$39.0`** | `-$30.8` (2026-11 yeni `%10+%5` hedefi daha da zor) |
| **6. FN Stellar Lite 5K (\$32.99, `%8+%4`, `%3` Açık Risk)** | `%1.1 / %0.8` | 80g / 163g | %13.0 | %36.3 | \$84.9 | **`-$10.8` / `-$33.0`** | `-$21.3` (`%4` günlük DD sınırı yüksek riskte patlatıyor) |
| **7. FundingPips 2-Step Swing 5K (\$32, `1:5` Endeks Kaldıraç)** | `%1.2 / %0.8` | 133g / 199g | %6.0 | %3.3 | \$81.6 | **`-$23.6` / `-$32.0`** | `-$30.7` (Swing paketinde `1:5` endeks kaldıracı lotları boğuyor) |

*Not — Challenge Risk Eğrisi (`A2`):* `The5ers Classic 8%+5%` hesabında Challenge riskini `%1.8`'e çıkarmak beklenen değeri `+$4.1`'e taşısa da ilk payout öncesi patlama oranını **`%70.3`**'e fırlatmaktadır (medyan getiri `-$39`). Dolayısıyla `+4.6R/yıl` drift ile Challenge hesaplarında gizli bir mucize yoktur.

---

## 3. `FundYourFX 5K ($39.60)` Üzerinde Gizli Handikap Stres Testleri

| Senaryo | Medyan İlk Payout | 12 Ayda `≥1` Payout | Patlama | Lot Yüzünden Atlanan İşlem | 12 Ay Net **Ort / Medyan** |
|---|---|---|---|---|---|
| **1. Baz (`US100 CS=1 [$0.01/pt]`, `1.0×` maliyet, `%100` icra)** | 42 işgünü | %62.7 | %23.7 | %0.0 | **`+$142.4` / `+$55.8`** |
| **2. Kaba Lot (`US100 CS=10 [$0.10/pt]`, `BTC min 0.01`)** | 44 işgünü | %57.7 | **%34.0** | **%31.0** | **`+$111.8` / `+$45.0`** |
| **3. Kötü Broker Maliyeti (`1.5×` Spread + Kayma)** | 36 işgünü | %55.3 | %29.7 | %0.0 | **`+$104.4` / `+$40.6`** |
| **4. İnsan İcra Kaybı (`%75` yakalama — 4 sinyalin 1'i kaçar)** | 50 işgünü | %61.3 | %13.7 | %0.0 | **`+$119.0` / `+$49.1`** |
| **5. Gerçekçi Kombine (`1.5×` maliyet + `%75` icra, `CS=1`)** | 50 işgünü | **%55.7** | **%21.7** | %0.0 | **`+$89.7` / `+$43.2`** |

- **3 Tarihsel Dönem Kontrolü (`FYFX 5K`, `CS=1`):** `2022+` **`+$142.4`** · `2018–21` **`+$215.6`** · `2013–17` **`+$180.3`**.

---

## 4. Bundan Sonra Gözden Bir Şey Kaçmaması İçin Kalıcı 5 Kapılı Protokol

1. **Kapı 1 — Kod İçi 5 Otomatik `assert` İnvaryantı:** Sıfır-edge challenge kontrolü (`INV-1`), sıfır-edge pozitifse karşı-taraf ödeme/gizli kural uyarısı (`INV-2`), risk arttıkça hedefin hızlanması (`INV-3`), eşzamanlı pencere açık-risk ve kaldıraç sınırı (`INV-4`), çekim sonrası kayan DD tabanının asla gevşememesi (`INV-5`).
2. **Kapı 2 — 6 Fiziksel Broker Sürtünmesi + CME Çapraz Kontrol:** Kesirli R-çarpanı yerine `0.01` lot adımı (`CS=1` ve `CS=10`), varlık kaldıracı, çok günlük MTM + swap, `1.5×` maliyet, `%75` insan icrası ve spot-CFD yanılsamalarına karşı CME vadeli kontrolü (`DXAU` örneği).
3. **Kapı 3 — Çapraz Ajan "Şeytanın Avukatı" Denetimi:** Satın alma veya canlı kural değişikliği öncesi karşı ajana (`Claude` ↔ `Antigravity`) kodu ve çıktıyı verip yalnızca "buradaki hatayı/iyimserliği bul" denetimi yaptırmak.
4. **Kapı 4 — Sıfır Paralı Demo & Yazılı Destek Kapısı (Kart Girmeden Önce):**
   - Ücretsiz Match-Trader demo açıp `US100` / `BTCUSD` `Contract Size` (`1` mi `10` mu), `Min Lot`, canlı spread ve swap değerlerini ekrandan okumak.
   - Canlı desteğe yazılı sorup ekran görüntüsü almak: *(a)* Instant Classic 5K'da `4x best day (%25)` kuralı var mı? *(Varsa beklenen değer `-$15` → **ALINMAZ**)*, *(b)* Çekim sonrası `%6` sabit DD tabanı `$4,700`'da kalıyor mu? *(Kalmayıp `$5,000`'a kilitleniyorsa `FN Instant` gibi ölür → **ALINMAZ**)*, *(c)* İlk çekimde kârı çekince kalan işlem marjini sıfırlanıyor mu yoksa kârın bir kısmını içeride bırakmak serbest mi?
5. **Kapı 5 — 10 İşlemlik Bedava İcra Kapısı:** `2026-11-09..22` arasındaki 14 günlük denemede **0 emir** girildiği için, para yatırmadan önce mevcut demo/kağıt üzerinde arka arkaya **10 sinyalin en az 8'ine (`%80`)** kurallara uygun basabildiğini kanıtlamak.
