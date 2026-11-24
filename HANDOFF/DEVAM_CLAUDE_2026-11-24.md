# Handoff → Claude (2026-11-24) — 5 İnvaryantlı Broker Fiziği & Kör Nokta Denetimi Özeti

## 1. Bağlam & Neden Bu Denetim Yapıldı?
- `e572935` (`satin_alma_oncesi_denetim.py`) sonrası kullanıcı haklı bir metodolojik soru sordu: *"Ben sormasam bu iyimserlikleri öğrenemeyecektik; başka gizli handikaplar veya kaçırdığımız fırsatlar varsa bundan nasıl emin olacağız?"*
- Geçici simülasyon betiklerinde (`sub50_prop_risk_frontier.py`, `human_delay_and_checklist.py`) zorunlu `assert` kilitleri ve fiziksel broker katmanları (gerçek `0.01` lot basamağı, enstrüman kaldıracı, çok günlük MTM + swap, çekim sonrası kayan DD kilidi, `%75` insan icrası) eksikti.
- Tek bir kendi kendini doğrulayan (`INV-1..INV-5` `assert`) denetim betiği yazıldı ve koşuldu:
  - **Betik:** `HANDOFF/scripts_2026-11-24/tam_kor_nokta_denetimi.py`
  - **Rapor:** `HANDOFF/tam_kor_nokta_ve_protokol_2026-11-24.md`
  - **Ham JSON Çıktı:** `strategy-lab/outputs/intraday/futures_round5/tam_kor_nokta_denetimi_2026-11-24.json`
  - **Commit:** `c26a259`

---

## 2. Yakalanan 3 Simülasyon Hatası + 1 Sahte Fırsat

1. **`sub50_prop_risk_frontier.py` Açık-Risk Çakışma Hatası (`INV-3` yakaladı):**
   - Eski betik (`satır 117–120`) aynı gün içindeki **farklı saat dilimi** modüllerini (`14:30–21:00 UTC` RTH'de kapanan `SWEEP + NB` ile `21:00–23:00 UTC`'de açılan `BTC_21_23`) aynı saniyede açıkmış gibi topluyor ve FundedNext'in `%3` açık-risk kuralını **tüm firmalara** (`The5ers`, `FundingPips`, `FYFX`) uyguluyordu.
   - Bu yüzden Challenge riski `%1.0`'dan `%1.5–%2.0`'a çıkarıldığında döngü `NB`, `B7_IBS` ve `BTC_21_23`'ü sıfırlayıp yalnız `SWEEP`'i bırakıyordu (`%2.0` riskte geçiş süresi `159g → 189g` uzuyordu).
   - **Düzeltme Sonucu:** Açık risk yalnızca aynı saat penceresinde (Window A: RTH, Window B: 21–23 UTC) ve yalnız bu kuralı olan firmada (`FundedNext`) sınırlandı. `The5ers` medyan süresi monoton hızlandı (`%0.8 = 217g → %1.5 = 146g → %2.0 = 118g`).
   - **Ancak:** `V3` (`SWEEP = +0.02R`, `NB = +0.027R`, `B7_IBS` MTM+swap `= +0.009R/gün`, `BTC_21_23 = -0.001R`) altında portföyün `2022+` toplam üretimi yılda **`~+4.6R`** olduğu için, bug düzeltildikten sonra da **Tier-1 Challenge hesapları (`The5ers 5K $39`, `FN Lite 5K $32.99`, `FundingPips Swing 5K $32`)** tek bilette negatif EV'de kalmaktadır (`-$10.8` ile `-$23.6/yıl`, medyan `-$33..-$39`). Riski `%1.8`'e çıkarmak patlamayı `%70–%88`'e fırlatıyor.
2. **`FN Stellar Instant 2K ($59.99)` Çekim Sonrası Kayan DD Kilidi (`INV-5` yakaladı):**
   - Eski betikler (`cheap_sizing.py` satır 158, `sub50_prop_risk_frontier.py` satır 171) her çekimde `peak = 0.0` sıfırlayıp hesaba yeniden `-6%` DD tamponu veriyordu.
   - Resmi FN kuralında (`instant-prop-arastirma/results/FundedNext_Stellar_Instant.json` satır 10) `%6` kayan MLL başlangıç bakiyesine kilitlenir ve **çekim sonrasında sıfırlanmaz (`carries over after withdrawal`)**. Tüm kârı çekersen kalan DD tamponu `$0` olur.
   - İçeride `%4` güvenlik tamponu bırakılarak simüle edildiğinde `FN Instant 2K ($59.99)` yıllık net beklentisi `+$5`'tan **`-$38.4`'e (medyan `-$60`)** düştü → **Kesin elendi.**
3. **`B7_IBS` Günlük MTM Dip ve `-1.18 bp/gece` Swap Eksikliği:**
   - `human_delay_and_checklist.py` içinde `B7_IBS` yalnız giriş/çıkış gününde tek kalem yazılıyordu ve `B7_SWAP_PER_NIGHT = 0.000118` unutulmuştu. `tam_kor_nokta_denetimi.py` içinde ara gecelerin günlük kapanış MTM'i, gün içi `low` çekilmesi ve gecelik swap tam modellendi.
4. **Sahte "Gizli Fırsat" (`Donchian XAU 1H` Spot-Swap Yanılsaması):**
   - Dukascopy spot `XAUUSD` üzerinde `DXAU` (`N=20, RR=2.0`) eklemek 3 dönemin tamamında (`2013–17: +0.150R`, `2018–21: +0.031R`, `2022+: +0.140R`) `FYFX 5K` netini `+$255/yıl`'a, `The5ers 5K` netini `+$42..+$60/yıl`'a taşıdı.
   - Fakat CME altın vadeli (`GC`, faiz/taşıma maliyeti vade geçişlerinde fiyata gömülü) çapraz kontrolünde (`outputs/intraday/futures_transfer3/result.json` → `T2_DONCHIAN_GC`) aynı kuralın merkezi maliyette **`+0.0079R` (`CI [-0.100, +0.112]`, `2012-21: -0.0067R`, `PASS: false`)** olduğu doğrulandı. Spot CFD'deki görünür edge, spot veride düşülmeyen gecelik long altın swap'ından gelmektedir → **Portföye eklenmedi.**

---

## 3. Tüm Fiziksel Kısıtlar Altında Güncel Hesap Tablosu (`2022+`, `V3`, `0.01` Gerçek Lot `CS=1`)

| Hesap & 2026-11 Doğrulanmış Kurallar | Risk | `p10` / Medyan (`işgünü`) | 12 Ayda `≥1` Payout | İlk Payout Öncesi **Patlama** | Tek Payout Ort. | 12 Ay Net **Ort / Medyan** | Sıfır-Edge EV & `INV-2` Notu |
|---|---|---|---|---|---|---|---|
| **FundYourFX Instant Classic 5K (\$39.60, `%50→%75→%90` split)** | `%1.0` | **9g / 42g** | **%62.7** | **%23.7** | **\$134.8** | **`+$142.4` / `+$55.8`** | `+$75.8` (**UYARI:** Sıfır-edge pozitif → ödeme/gizli kural riski) |
| **FundYourFX 5K — EĞER `%25 (4x Best Day)` Kuralı Varsa** | `%1.0` | 41g / 109g | **%6.7** | %26.7 | \$349.8 | **`-$15.1` / `-$39.6`** | `-$30.0` (**ÖLÜMCÜL:** Bu kural varsa alınmaz) |
| **FN Stellar Instant 2K (\$59.99, Kayan Kilit + `%4` Tampon)** | `%1.0` | 16g / 65g | %36.0 | %12.0 | \$28.3 | **`-$38.4` / `-$60.0`** | `-$46.4` (Elendi) |
| **FN Stellar Lite 5K (\$32.99, `%8+%4`, `%3` Açık Risk, `1:25` Idx / `1:1` BTC)** | `%1.1 / %0.8` | 80g / 163g | %13.0 | %36.3 | \$84.9 | **`-$10.8` / `-$33.0`** | `-$21.3` (Elendi) |
| **The5ers High Stakes 5K (\$39, Classic `%8+%5`, `1:25` Idx / `1:2` BTC)** | `%1.2 / %0.8` | 85g / 164g | %13.3 | %12.0 | \$93.9 | **`-$12.4` / `-$39.0`** | `-$28.6` (Elendi) |
| **The5ers High Stakes 5K (\$39, New `%10+%5`, `1:25` Idx / `1:2` BTC)** | `%1.2 / %0.8` | 92g / 164g | %8.3 | %11.0 | \$93.1 | **`-$22.2` / `-$39.0`** | `-$30.8` (Elendi) |
| **FundingPips 2-Step Swing 5K (\$32, `%8+%5`, `1:5` Idx / `1:1` BTC)** | `%1.2 / %0.8` | 133g / 199g | %6.0 | %3.3 | \$81.6 | **`-$23.6` / `-$32.0`** | `-$30.7` (Elendi) |

### `FundYourFX 5K ($39.60)` Fiziksel Handikap Stres Testi (`2022+`)
- **Baz (`US100 CS=1 [$0.01/pt]`, `BTC min 0.001`, `1.0×` maliyet, `%100` icra):** Medyan `42g`, `≥1` payout `%62.7`, patlama `%23.7`, 12ay net **`+$142.4` (medyan `+$55.8`)**. *(2018–21: `+$215.6`, 2013–17: `+$180.3`)*.
- **Kaba Lot (`US100 CS=10 [$0.10/pt]`, `BTC min 0.01`):** `B7_IBS` (`4*ATR ≈ 1600p → 0.01 lot = $160 risk`) yüzünden sinyallerin **`%31.0`'i** min-lot bütçeyi aştığı için atlanır; patlama `%34.0`'a çıkar, 12ay net **`+$111.8` (medyan `+$45.0`)**.
- **`1.5×` Spread/Kayma Maliyeti:** `≥1` payout `%55.3`, patlama `%29.7`, 12ay net **`+$104.4` (medyan `+$40.6`)**.
- **`%75` İnsan Sinyal Yakalama (4 sinyalin 1'i kaçar):** Medyan `50g`, `≥1` payout `%61.3`, 12ay net **`+$119.0` (medyan `+$49.1`)**.
- **Gerçekçi Kombine (`1.5×` maliyet + `%75` icra, `CS=1`):** Medyan `50g`, `≥1` payout **`%55.7`**, patlama **`%21.7`**, 12ay net **`+$89.7` (medyan `+$43.2`)**.

---

## 4. Kalıcı 5 Kapılı Doğrulama Protokolü ve Sıradaki Tek Aksiyon

Yeni simülasyon/satın alma kararlarında zorunlu 5 kapı:
1. **Kapı 1 (`INV-1..INV-5` `assert`):** Sıfır-edge challenge `< $0`, sıfır-edge `> +$10` ise karşı-taraf ödeme/gizli kural uyarısı, monoton hız kontrolü, eşzamanlı pencere açık-risk/marjin sınırı, çekim sonrası kayan DD tabanının gevşememesi.
2. **Kapı 2 (6 Fiziksel Sürtünme + CME Çapraz Kontrol):** `0.01` lot basamağı (`CS=1/10`), kaldıraç, günlük MTM+swap, `1.5×` maliyet, `%75` icra, spot-swap yanılsamasına karşı CME vadeli kontrolü.
3. **Kapı 3 (Çapraz Ajan Kırmızı-Takım Denetimi):** `Claude` ↔ `Antigravity` bağımsız hata arama.
4. **Kapı 4 (Sıfır Paralı Demo & Yazılı Destek Ön-Kontrolü — ŞU ANKİ ADIM):**
   - FundYourFX ücretsiz Match-Trader demoda `US100/BTCUSD` `Contract Size` (`1` mi `10` mu), canlı spread ve swap okuma.
   - Canlı destekten yazılı onay: *(a)* Instant Classic 5K'da `4x best day (%25)` kuralı var mı? *(Varsa EV `-$15` → **ALINMAZ**)*, *(b)* Çekim sonrası `%6` sabit DD tabanı `$4,700`'da kalıyor mu?
5. **Kapı 5 (10 İşlemlik Bedava İcra Kapısı):** `2026-11-09..22` arasındaki 14 günlük denemede **0 emir** girildiği için, para yatırmadan önce demo/kağıt üzerinde gelen **10 gerçek sinyalin en az 8'ine (`%80`)** `H1–H4` yapısal kontrolleriyle zamanında basabildiğini kanıtlama.
