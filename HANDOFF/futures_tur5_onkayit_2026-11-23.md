# Ön-kayıt: futures 5. tur — order flow (emilim, stacked imbalance, delta sapması, iceberg), opex gün-içi pinning ve CL/ZN/6E çapraz varlık (IBS, Donchian 1h) (2026-11-23)

Bu dosya gerçek veriler indirilmeden ve `HANDOFF/scripts_2026-11-23/` betikleri çalışmadan ÖNCE commit edilir. Kural, eşik, maliyet yöntemi ve karar kriteri sonuç görüldükten sonra değiştirilmez.

---

## 1. Argon (`istisare_2026-11-22_kural_tanimlari.json`) Denetimi

### A. Kaynaksız / keyfi sayılar (sonuç görülmeden sabitlenen varsayılanlar)
1. **OF1 (`FP_ABS_1M`):**
   - `H_t - L_t >= 3.00 puan (12 tick)` minimum bar boyu: kaynaksız filtre.
   - `TopAskVol` / `BotBidVol` için `4 tick (1.00 puan)` uç penceresi ve toplam bar hacmine oranı `>= 0.35`: kaynaksız.
   - Hacim ve `|Delta|` için 20-bar Z-skoru `>= 1.5 sigma`: Trader Dale / ATAS'ta göz kararı "yüksek hacim" vardır, `1.5 sigma` kantitatif uyarlamadır.
   - Stop (`uç +- 1.00 puan`), hedef (`2R`), zaman stopu (`10 dk`) ve `günde en fazla 3 işlem`: kaynaksız.
2. **OF2 (`FP_STACK_1M`):**
   - `300% (3.0x)` diyagonal oran ve `K >= 3` ardışık tick seviyesi ATAS/Sierra Chart standart varsayılanıdır (kaynaklı).
   - `V_min = 30 kontrat/tick`: kaynaksız (boş kademe `0 vs 3` gürültüsünü kesmek için sabitlendi).
   - Bar yönü ve konum filtresi (`C_t > O_t` ve `C_t >= p_stack_top`), stop (`ters uç +- 0.50 puan`, `risk > 15 puan` ise atla), hedef (`1.5R`), zaman stopu (`5 dk`), `günde en fazla 3 işlem`: kaynaksız.
3. **OF3 (`FP_DDIV_5M`):**
   - Yeni fiyat tepesinde `Delta_t < 0` (yeni dipte `Delta_t > 0`) Sierra Chart / ATAS standart tanımıdır (kaynaklı).
   - `5 dk` bar boyu, `N = 20 bar (100 dk)` lookback, kapanış reddi (`bar ortasının altı/üstü`), stop (`ekstremum +- 1.00 puan`), hedef (`2R`), zaman stopu (`3 bar = 15 dk`), `günde en fazla 2 işlem`: kaynaksız.
4. **OF4 (`MBO_ICE_DESC` — yalnız betimleyici):**
   - Native iceberg (`toplam fill > ilk görünür miktar` ve `>= 20 kontrat`) MDP 3.0 mekanizmasına dayalıdır, `20` eşiği keyfidir.
   - Sentetik refill (`<= 50 ms` içinde yeni `order_id`, `5 sn` pencerede `>= 3 refill`, `>= 50 kontrat`, `oran >= 3.0`, `<= 1 tick delinme`): heuristik eşiklerdir.
5. **O1 (`CAL_OPEX`):**
   - Alt Kural 5A (Opex haftası long, Stivers & Sun 2013) ve Alt Kural 5B (3. Cuma காலை hareketi tersi / gün-içi pinning, Ni-Pearson-Poteshman 2005): **Denetim bulgusu:** 5A (`opex_week_long`) ve 3. Cuma sabah SOQ (`edge5k_c1_c8` C3) Dukascopy CFD verisinde zaten test edilip elenmişti. Ancak 5B (**3. Cuma 09:30–11:00 NY hareketi >= 1.0 sigma ise 11:00→15:55 ters yöne gün-içi dönüş**) daha önce hiç test edilmedi. Ön-kayıtta ana hipotezler **O1_ES ve O1_NQ = 5B (gün-içi pinning)** olarak alınır; 5A CME verisinde yalnız referans satırı olarak raporlanır.
6. **X1 (`DAILY_IBS_CROSS`) ve X2 (`H1_DONCHIAN_20`):**
   - Argon X1'de `IBS < 0.20 long / > 0.80 short, 1 gün tut` ve X2'de `10-bar çıkış + 2 ATR stop` önerdi.
   - **Denetim bulgusu (tutarlılık):** Projede daha önce geçen IBS kuralı (`seffaf_adaylari.simulate_b7`, `futures_transfer_retest.py`) **yalnız long, IBS < 0.20 giriş, IBS > 0.80 ilk kapanışta çıkış** tanımıdır. Daha önce test edilen Donchian 1h kuralı (`donchian_xau_lab.build_signals` + `honest_engine.simulate_trades`, `futures_transfer3.py` T2) **N=20, karşı kanal stop, RR=2.0 hedef, max 200 bar** tanımıdır. Kuralları varlık değiştirirken değiştirmemek (serbestlik derecesi eklememek) için X1 ve X2'de **mevcut commit'li motorlar aynen** kullanılır.

### B. Look-ahead, bar içi sıra ve kuyruk iyimserliği riskleri
1. **Bar içi sıra ve look-ahead (OF1, OF2, OF3):**
   - Bir 1m veya 5m barın `H_t`, `L_t`, `C_t` ve toplam `AskVol`/`BidVol` değerleri yalnızca bar kapandığı an (`t_close`) kesindir. Bar içinde sinyal tetiklemek gelecek bilgisi kullanır.
   - **Çözüm:** Sinyal yalnızca `t_close` anında değerlendirilir; giriş fiyatı `ts_event >= t_close + 150 ms` koşulunu sağlayan **ilk işlemin fiyatıdır** (market emri).
   - Çıkışta (stop vs hedef) bar OHLC özeti kullanılmaz; giriş anından itibaren `trades` akışında **tick-by-tick (`ts_event` sırasıyla)** izlenir. Stop tetiklenirse `ts_stop + 150 ms`'deki ilk işlem fiyatından çıkılır (stop kayması dahil); hedef limit emir olduğundan hedef fiyattan (veya bir tick geçildiğinde) çıkılır.
2. **Kuyruk iyimserliği (OF2, Limit dolumlar):**
   - Stacked imbalance seviyesine geri çekilmede (pullback) limit emir koymak kuyruk önceliği olmadan yalnız kaybeden işlemlerde dolum üretir (C ölçümünde kanıtlandı). Bu yüzden piyasa emriyle devam yönü sabitlendi.
3. **Gece / önceki gün sızıntısı (OF1, OF3):**
   - OF1'deki 20-bar (`1m`) ve OF3'teki 20-bar (`5m`) penceresi önceki günden kalan barları içerirse 09:30 açılış gap'i sahte sinyal üretir.
   - **Çözüm:** Her iki kuralda da 20-bar lookback **yalnızca aynı RTH seansı içindeki tamamlanmış barlardan** hesaplanır (OF1 ilk sinyal değerlendirmesi 09:50 NY, OF3 ilk sinyal değerlendirmesi 11:10 NY — yani RTH içinde 20 adet 5m bar tamamlandıktan sonra).
4. **Günlük `vdaily` Settlement vs Globex High/Low tuzağı (X1):**
   - CME günlük OHLCV (`vdaily`) barlarında `close` 14:30/15:00 NY settlement iken `high`/`low` 17:00 NY'a kadar süren işlemleri kapsayabilir (look-ahead) ve vade geçişlerinde ayarsız fiyat zıplar.
   - **Çözüm:** X1 (CL, ZN, 6E) doğrudan `x1h` (`ohlcv-1h`, `v.0`) barlarından üretilen günlük barlarla (ve `vdaily` ile çapraz kontrol edilerek) koşulur; giriş ile çıkış arasında `instrument_id` değişen (roll) işlemler `futures_transfer_retest.py`'deki gibi atılır.
5. **Birleşik `nqtrades` (`c.0` + `v.0`) ve Thin-Day Kuralı (OF1, OF2, OF3):**
   - `2026-03-01 .. 2026-09-01` dönemi `NQ.v.0`, `2026-09-01 .. 2026-11-19` dönemi `NQ.c.0` şemasındadır.
   - Roll haftalarında (ör. `NQ.c.0` Eylül vade sonu) hacim yeni kontrata geçtiğinde eski kontratta işlem sayısı düşer ve footprint/tick istatistikleri bozulur.
   - **Thin-day kuralı:** RTH (09:30–16:00 NY) toplam işlem (`trades` satır) sayısı, tüm RTH günlerinin medyanının **%50'sinden az** olan günler veri setinden çıkarılır ve atlanan günler rapora yazılır.

---

## 2. Hipotezler (Toplam 11 Test → Bonferroni `alpha = 0.05 / 11`, iki yönlü kuantil `0.05 / 11 / 2`)

| Kod | Aile / Kural | Varlık | Veri & Dönem | Birim |
|---|---|---|---|---|
| **OF1** | Footprint Emilim (`FP_ABS_1M`) | NQ | CME `trades` 2026-03-01 – 2026-11-19 (RTH) | R / işlem (ve bp) |
| **OF2** | Stacked Imbalance (`FP_STACK_1M`) | NQ | CME `trades` 2026-03-01 – 2026-11-19 (RTH) | R / işlem (ve bp) |
| **OF3** | Delta Sapması (`FP_DDIV_5M`) | NQ | CME `trades` 2026-03-01 – 2026-11-19 (RTH) | R / işlem (ve bp) |
| **O1_NQ** | Opex 3. Cuma Gün-İçi Pinning (5B) | NQ | CME `ohlcv-1m` (`NQ.c.0`) 2012-01-01 – 2026-11-19 | bp / işlem |
| **O1_ES** | Opex 3. Cuma Gün-İçi Pinning (5B) | ES | CME `ohlcv-1m` (`ES.c.0`) 2012-01-01 – 2026-11-19 | bp / işlem |
| **X1_CL** | Günlük IBS (`simulate_b7`) | CL | CME `CL.v.0` 2012-01-01 – 2026-11-19 | bp / işlem |
| **X1_ZN** | Günlük IBS (`simulate_b7`) | ZN | CME `ZN.v.0` 2012-01-01 – 2026-11-19 | bp / işlem |
| **X1_6E** | Günlük IBS (`simulate_b7`) | 6E | CME `6E.v.0` 2012-01-01 – 2026-11-19 | bp / işlem |
| **X2_CL** | Donchian N=20 1h (`donchian_r`) | CL | CME `CL.v.0` (`x1h`) 2012-01-01 – 2026-11-19 | R / işlem |
| **X2_ZN** | Donchian N=20 1h (`donchian_r`) | ZN | CME `ZN.v.0` (`x1h`) 2012-01-01 – 2026-11-19 | R / işlem |
| **X2_6E** | Donchian N=20 1h (`donchian_r`) | 6E | CME `6E.v.0` (`x1h`) 2012-01-01 – 2026-11-19 | R / işlem |

*(Not: **OF4 Iceberg** 10 günlük `NQ.v.0` MBO verisinde [2026-10-05..16] yalnız **BETİMLEYİCİ** olarak koşulur; karar kuralı yoktur ve Bonferroni paydasına girmez. **O1_5A** [Opex haftası long] CME `ES.c.0`/`NQ.c.0` üzerinde yalnız referans olarak raporlanır.)*

### Kesin Kural Spesifikasyonları

1. **OF1 — Footprint Emilim (`FP_ABS_1M`):**
   - RTH (09:30–16:00 NY) içinde 1 dakikalık barlar (`t_close` 09:31 .. 16:00). Fiyat kademesi `p` (0.25 tick): `AskVol(p)` (`side == 'B'`), `BidVol(p)` (`side == 'A'`), `Vol = sum(AskVol + BidVol)`, `Delta = sum(AskVol - BidVol)`.
   - `TopAskVol = sum_{p in [H - 0.75, H]} AskVol(p)`, `BotBidVol = sum_{p in [L, L + 0.75]} BidVol(p)`.
   - Aynı seans içi önceki 20 tamamlanmış 1m barın ortalaması ve std'si ile (ilk sinyal kontrolü 09:50 kapanışı, son sinyal kontrolü 15:45 kapanışı):
     - `H - L >= 3.00` puan,
     - `Vol >= mean(Vol_prev20) + 1.5 * std(Vol_prev20)`,
     - `|Delta| >= mean(|Delta|_prev20) + 1.5 * std(|Delta|_prev20)`.
   - **Short:** `Delta > 0` ve `TopAskVol / Vol >= 0.35` ve `C <= H - 0.50 * (H - L)`. Stop = `H + 1.00`.
   - **Long:** `Delta < 0` ve `BotBidVol / Vol >= 0.35` ve `C >= L + 0.50 * (H - L)`. Stop = `L - 1.00`.
   - **Giriş:** `t_close + 150 ms` sonrası ilk `trades` fiyatı (`entry`). Risk `R_pts = |entry - stop|` (`entry` stop'un yanlış tarafındaysa işlem iptal).
   - **Çıkış:** Tick-by-tick `trades` üzerinde: hedef `entry +- 2 * R_pts`, stop `stop` (tetiklenirse `+150 ms` ilk işlem fiyatı), veya `t_close + 10 dk` (veya `15:55:00 NY`) sonrası ilk işlem. Aynı anda tek açık pozisyon, günde en fazla 3 işlem.

2. **OF2 — Stacked Imbalance (`FP_STACK_1M`):**
   - 1 dakikalık RTH footprint barında (kontrol penceresi `t_close` 09:35 .. 15:45 NY) her tick `p` için:
     - Buy imbalance: `AskVol(p) >= 3.0 * max(BidVol(p - 0.25), 1)` ve `AskVol(p) >= 30`.
     - Sell imbalance: `BidVol(p) >= 3.0 * max(AskVol(p + 0.25), 1)` ve `BidVol(p) >= 30`.
   - **Buy Stack (Long):** Aynı barda en az 3 ardışık tick seviyesinde (`p, p+0.25, p+0.50`) Buy imbalance var, `C > O` ve `C >= p_stack_top` (en yüksek stack kademesi). Stop = `L - 0.50`.
   - **Sell Stack (Short):** Aynı barda en az 3 ardışık tick seviyesinde Sell imbalance var, `C < O` ve `C <= p_stack_bot` (en düşük stack kademesi). Stop = `H + 0.50`.
   - Aynı barda hem Buy hem Sell stack varsa işlem yok.
   - **Giriş:** `t_close + 150 ms` sonrası ilk işlem fiyatı (`entry`). `R_pts = |entry - stop|`; `R_pts <= 0` veya `R_pts > 15.0` puan ise işlem açılmaz.
   - **Çıkış:** Tick-by-tick: hedef `1.5 * R_pts`, stop (`+150 ms` ilk işlem), veya `t_close + 5 dk` (veya `15:55:00 NY`). Aynı anda tek açık pozisyon, günde en fazla 3 işlem.

3. **OF3 — Delta Sapması (`FP_DDIV_5M`):**
   - RTH içinde 5 dakikalık barlar (09:30..16:00 NY, 78 bar/gün). Aynı seans içinde en az 20 bar tamamlandıktan sonra (`t_close` 11:15 .. 15:30 NY):
     - `H_prev20 = max(H_{t-20..t-1})`, `L_prev20 = min(L_{t-20..t-1})`.
     - **Short:** `H_t > H_prev20` ve `Delta_t < 0` ve `C_t < H_t - 0.50 * (H_t - L_t)`. Stop = `H_t + 1.00`.
     - **Long:** `L_t < L_prev20` ve `Delta_t > 0` ve `C_t > L_t + 0.50 * (H_t - L_t)`. Stop = `L_t - 1.00`.
   - **Giriş:** `t_close + 150 ms` sonrası ilk işlem fiyatı.
   - **Çıkış:** Tick-by-tick: hedef `2.0 * R_pts`, stop (`+150 ms` ilk işlem), veya `t_close + 15 dk` (veya `15:55:00 NY`). Aynı anda tek açık pozisyon, günde en fazla 2 işlem.

4. **OF4 — MBO Iceberg Betimlemesi (`MBO_ICE_DESC`, yalnız betimleyici):**
   - `NQ.v.0` MBO verisi, 2026-10-05 – 2026-10-16 (10 işlem günü, RTH 09:30–16:00 NY).
   - **Native Iceberg:** Aynı `order_id` için toplam dolum (`action == 'F'` veya `'T'` size toplamı) > ilk `add` (`action == 'A'`) görünür miktarı ve toplam dolum `>= 20` kontrat.
   - **Sentetik Refill:** Aynı fiyat `p` ve aynı pasif tarafta bir dolumdan sonraki `<= 50 ms` içinde yeni `order_id` ile `add` gelmesi; `5 sn` pencerede `>= 3 refill` ve toplam dolum `>= 50` kontrat.
   - **Raporlanan:** Günlük/saatlik olay sayısı, ortanca kontrat büyüklüğü, tespit anı (`t_detect`) ile `t_detect + 150 ms` arasındaki fiyat kayması (toksisite), `t_detect + 1 dk / 5 dk` sonrası yönlü fiyat hareketi, ve OF1 emilim barlarıyla örtüşme oranı.

5. **O1 — Opex 3. Cuma Gün-İçi Pinning (`O1_NQ`, `O1_ES`):**
   - Veri: `NQ.c.0` ve `ES.c.0` `ohlcv-1m` (2010-06-06 – 2026-11-19). Roll günü (`instrument_id` değişen gün) ve tam RTH seansı olmayan günler atlanır.
   - Her gün sabah hareketi `r_morn = P_{11:00} / P_{09:30} - 1` (`09:30` barı `open`, `10:59` barı `close`). `sigma_20` = önceki 20 işlem gününün `r_morn` standart sapması.
   - Her ayın **3. Cuma** günü (NYSE tatiliyse bir önceki işlem günü olan Perşembe): eğer `|r_morn| >= 1.0 * sigma_20` ise saat `11:00` barı açılışında **sabah hareketinin tersi yönde (`-sign(r_morn)`)** gir, `15:55` barı kapanışında çık. Stop: sabah ekstremumu (`09:30..10:59` `high` veya `low`) `+- 0.5 * sigma_20 * P_{09:30}` (1m barlarda stop değerse stop fiyatından/açılıştan çık).
   - Ayrıca referans olarak Stivers & Sun Opex Haftası Long (2. Cuma 15:55 kapanış → 3. Cuma 15:55 kapanış, aynı kontratta) vs diğer haftalar farkı raporlanır.

6. **X1 — Günlük IBS (`X1_CL`, `X1_ZN`, `X1_6E`):**
   - Veri: `x1h` (`CL.v.0`, `ZN.v.0`, `6E.v.0` `ohlcv-1h`, 2010-06-06 – 2026-11-19) → NY seansı (09:30–16:00 NY) günlük OHLC barlarına toplanır (`seffaf_adaylari.resample_nq_daily` ile birebir aynı; ayrıca `vdaily` tam gün barlarıyla duyarlılık satırı bilgi olarak yazılır).
   - Motor: `seffaf_adaylari.simulate_b7` (değiştirilmeden: `IBS < 0.20` kapanışta long, `IBS > 0.80` ilk kapanışta çık). Giriş ile çıkış arasında `instrument_id` değişen (roll) işlemler atılır (`futures_transfer_retest.py` `daily_rule` ile aynı).

7. **X2 — Donchian N=20 1h (`X2_CL`, `X2_ZN`, `X2_6E`):**
   - Veri: `x1h` (`CL.v.0`, `ZN.v.0`, `6E.v.0` `ohlcv-1h`, 2010-06-06 – 2026-11-19), `futures_transfer3.back_adjust` ile ardışık saat barlarında `instrument_id` değişimlerinde oranla geriye ayarlanır (`raw_close` maliyet dönüşümü için saklanır).
   - Motor: `futures_transfer3.donchian_r` (`donchian_xau_lab.build_signals` N=20, karşı kanal stop, RR=2.0, max 200 bar, `honest_engine.simulate_trades`).

---

## 3. Maliyet (Ölçülmüş, 3 Satır Rapor: Maliyetsiz / Merkez / 2×)

- **MNQ:** `0.555` puan/yön (bbo-1m NY RTH yarım spread `0.25` + `$0.61 / $2`).
- **MES:** `0.247` puan/yön (bbo-1m NY RTH yarım spread `0.125` + `$0.61 / $5`).
- **CL, ZN, 6E:** `bbox` (`bbo-1m` 2025-01-01 – 2026-11-20, NY 09:30–16:00) paketinden `(ask_px_00 - bid_px_00) / 2` medyanı ölçülür:
  - Öncelikle mikro kontrat varsa (`MCL.c.0` çarpan 100, `M6E.c.0` çarpan 12.500) ve ana kontrat (`CL.c.0` çarpan 1.000, `6E.c.0` çarpan 125.000, `ZN.c.0` çarpan 1.000) yarım spread medyanları ayrı ayrı raporlanır.
  - Karar satırında (perakende prop hesabında işlem gören en ucuz/standart birim olarak) ana kontrat (`CL.c.0`, `ZN.c.0`, `6E.c.0`) bbo-1m RTH yarım spread medyanı + `$0.61 / ana_çarpan` (ve kıyas için mikro kontrat `MCL`, `M6E` maliyeti ayrı bilgi satırı) kullanılır. Eğer bir sembolün `bbo-1m` verisi boş/eksik çıkarsa `definition` `min_price_increment / 2` alt sınır alınıp `"maliyet ölçülmedi"` etiketi vurulur.
- Tüm testlerde **maliyetsiz (0)**, **ölçülmüş merkez (1×)** ve **kötümser (2×)** olmak üzere 3 satır raporlanır.

---

## 4. Karar Kuralı (Değişmez)

- **Uzun tarihli testler (`O1_NQ`, `O1_ES`, `X1_CL`, `X1_ZN`, `X1_6E`, `X2_CL`, `X2_ZN`, `X2_6E`):**
  - Değerlendirme dönemi: `2012-01-01 – 2026-11-19` (`2010-06-06 – 2011-12-31` görülmemiş holdout ayrıca raporlanır).
  - **GEÇER =** Merkez maliyette işlem başı net getiri (bp veya R) için bootstrap (`10.000` tekrar, `seed = 20261123`, blok = 1 işlem) iki yönlü Bonferroni (`alpha = 0.05 / 11`, alt kuantil `0.05 / 22 = 0.002273`) **CI alt sınırı > 0** **VE** `2012–2021` ortalaması > 0 **VE** `2022+` ortalaması > 0 **VE** `2× (kötümser)` maliyet ortalaması > 0.
- **Kısa tarihli order flow testleri (`OF1`, `OF2`, `OF3` — `2026-03-01 – 2026-11-19`):**
  - Dönem tek yıl içinde (~8.5 ay) olduğundan iki yarı ayrımı kronolojik ortanca tarihten (`2026-07-10` öncesi = İlk Yarı, `2026-07-10` ve sonrası = İkinci Yarı) yapılır.
  - **GEÇER =** Merkez maliyette işlem başı net R için bootstrap (`10.000` tekrar, `seed = 20261123`, blok = 1) iki yönlü Bonferroni (`0.05 / 22` kuantil) **CI alt sınırı > 0** **VE** İlk Yarı (`< 2026-07-10`) > 0 **VE** İkinci Yarı (`>= 2026-07-10`) > 0 **VE** `2×` maliyet ortalaması > 0.
- Geçen çıkarsa bile LIVE'a girmez; sonraki adım forward PAPER ölçümüdür. Geçmeyenler `strategy-lab/intraday/elenenler.py` kataloğuna eklenir.

---

## SONUÇ (2026-11-22, ön-kayıt `1df1cd7` sonrası tek koşu)

Kodlar: `HANDOFF/scripts_2026-11-23/{run_opex_cross.py, run_orderflow.py, run_mbo_iceberg.py}`.
Çıktılar: `strategy-lab/outputs/intraday/futures_round5/{opex_cross_result.json, orderflow_result.json, mbo_iceberg_desc.json}`.

### Ölçülmüş maliyetler (`bbox` bbo-1m, 2025-01-01 – 2026-11-19, NY RTH, + $0.61/yön komisyon)
- **MNQ:** `0.555` puan/yön · **MES:** `0.247` puan/yön (önceki ölçüm).
- **CL.c.0:** yarım spread `0.005`, komisyon `0.00061` → **`0.00561` puan/yön** (`MCL.c.0` bilgi: yarım spread `0.010`, toplam `0.01610`).
- **ZN.c.0:** yarım spread `0.0078125`, komisyon `0.00061` → **`0.00842` puan/yön**.
- **6E.c.0:** yarım spread `0.00005`, komisyon `0.00000488` → **`0.0000549` puan/yön** (`M6E.c.0` bilgi: toplam `0.0000988`).

### 11 Ön-Kayıtlı Hipotez — **11/11 GEÇMEDİ** (Bonferroni `alpha = 0.05 / 11`)

| Kod | Aile / Varlık | Birim | n | Maliyetsiz | Merkez | 2× | Bonf. CI (Merkez) | 1. Yarı / 2. Yarı | 2010–11 Holdout | Sonuç |
|---|---|---|---|---|---|---|---|---|---|---|
| **OF1** | Footprint Emilim NQ | R | 0 | — | — | — | — | — | — | **GEÇMEDİ** (0 sinyal) |
| **OF2** | Stacked Imbalance NQ | R | 16 | −0.345 | −0.459 | −0.574 | [−1.015, +0.263] | −0.353 / −0.779 | — | **GEÇMEDİ** |
| **OF3** | Delta Sapması 5m NQ | R | 259 | −0.057 | −0.104 | −0.150 | [−0.283, +0.087] | −0.063 / −0.136 | — | **GEÇMEDİ** |
| **O1_NQ** | Opex 3. Cuma Pinning | bp | 37 | −19.42 | −20.82 | −22.21 | [−41.98, +0.65] | −17.14 / −24.70 | +44.56 (n3) | **GEÇMEDİ** |
| **O1_ES** | Opex 3. Cuma Pinning | bp | 29 | −13.11 | −14.62 | −16.13 | [−30.91, +2.29] | −10.35 / −19.19 | +35.86 (n5) | **GEÇMEDİ** |
| **X1_CL** | Günlük IBS CL | bp | 321 | +68.09 | +66.28 | +64.47 | [−2.47, +140.81] | +54.60 / +89.31 | +41.54 (n33) | **GEÇMEDİ** (CI alt −2.47; 83 roll atıldı) |
| **X1_ZN** | Günlük IBS ZN | bp | 382 | +0.33 | −1.05 | −2.42 | [−10.33, +8.16] | +1.46 / −5.84 | +5.02 (n43) | **GEÇMEDİ** |
| **X1_6E** | Günlük IBS 6E | bp | 367 | −4.35 | −5.30 | −6.24 | [−19.98, +9.21] | −9.42 / +2.14 | +31.24 (n45) | **GEÇMEDİ** |
| **X2_CL** | Donchian 1h CL | R | 848 | +0.013 | +0.006 | −0.001 | [−0.122, +0.130] | +0.052 / −0.089 | +0.043 (n96) | **GEÇMEDİ** |
| **X2_ZN** | Donchian 1h ZN | R | 839 | +0.016 | −0.021 | −0.057 | [−0.145, +0.109] | −0.072 / +0.082 | +0.145 (n87) | **GEÇMEDİ** |
| **X2_6E** | Donchian 1h 6E | R | 805 | −0.000 | −0.017 | −0.034 | [−0.145, +0.112] | −0.045 / +0.038 | +0.118 (n82) | **GEÇMEDİ** |

- Order flow verisi: 187 RTH günü, medyan 279.927 işlem/gün; 11 ince gün (`< %50 medyan`) atlandı → 176 geçerli gün.
- Opex 5A Referans (CME, brüt haftalık): NQ Opex haftası `+26.8 bp` vs diğer haftalar `+40.7 bp` (fark `−13.8 bp`, 2022+ `−24.9 bp`); ES Opex `+22.0 bp` vs diğer `+30.5 bp` (fark `−8.5 bp`, 2022+ `−8.6 bp`).

### OF4 — MBO Iceberg Betimleyici Ölçüm (10 Gün, 2026-10-05..16, ~147M RTH satırı, karar kuralı yok)
- **Native Iceberg (borsa yönetimli):** `n = 1.067` (~107/gün). `t_detect → +150ms` kayma: ort. `+0.184` puan (medyan `0.25` = 1 tick). `+150ms → +1 dk` pasif yöne sürüklenme: **`+0.437` puan** (WR `%53.6`), `+5 dk`: `+0.058` puan (WR `%52.6`). **Kritik:** `+0.437` puanlık brüt 1 dk hareket, MNQ gidiş-dönüş maliyetinin (`1.11` puan) yarısından bile küçüktür.
- **Sentetik Refill (algoritmik yenileme):** `n = 4.370` (~437/gün). `+150ms` kayma: ort. `+0.463` puan (medyan `0.50` = 2 tick). `+150ms → +1 dk`: **`−0.076` puan** (WR `%49.2`), `+5 dk`: **`−0.574` puan** (WR `%49.0`) — pasif tarafın tersine (kırılım/toksik akış).
- **OF1 örtüşmesi:** OF1 `n = 0` olduğu için örtüşme yok.
