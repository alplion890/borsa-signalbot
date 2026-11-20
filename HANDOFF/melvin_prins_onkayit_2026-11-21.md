# Ön-kayıt: Melvin–Prins ay sonu FX hedge akışı (2026-11-21)

Bu dosya `melvin_prins.py` gerçek veride çalışmadan ÖNCE commit edilir. Kural, evren, pencere, eşik değişmez.

## Kaynak (PDF'ten okundu, 2026-11-21)
Melvin & Prins, "Equity hedging and exchange rates at the London 4pm fix", J. Financial Markets 22 (2015) 50–72.
- Mekanizma: fon yöneticileri döviz hedge'ini ayın son iş günü WM/R 16:00 Londra fix'inde ayarlar; tutar, ayın
  sondan bir önceki gününün kapanış hisse fiyatlarından hesaplanır; emir fix'ten ≥1 saat önce bankaya verilir.
- Denk. 3–4: bağımlı = ayın son günü 15:00→16:00 Londra döviz getirisi (pozitif = döviz güçlenir); açıklayıcı =
  ülke hisse endeksinin ayın ilk gününden sondan bir önceki gününe kapanıştan kapanışa getirisi; ikisi de 10 ülke
  kesitinde arındırılmış. Panel katsayı **−0.0142** (p 0.00, R² 0.03): göreli %10 hisse yükselişi → 14 bp döviz düşüşü.
- Ek bulgu (Denk. 5): ay sonu 15–16 hareketinin %72'si ertesi gün 12:00'ye kadar geri dönüyor.
- Örneklem 2004-04-28 – 2012-12-31. **Bizim 2013–2026 verimiz tamamen yayın-sonrası örneklem dışı.**

## Veri
Dukascopy 5m bid (data_quality.clean). Döviz: EURUSD, GBPUSD, USDJPY (yabancı para getirisi USDJPY için ters işaret).
Hisse (Datastream total market yok → CFD ikamesi, sonuca bakılmadan seçildi): ABD SP500; Euro bölgesi GER40 ve FRA40
log getirilerinin ortalaması; İngiltere UK100; Japonya JAP225. Hisse kapanışı = her iş günü 21:00 UTC öncesi son bar
(multi_panel.py ile aynı ortak saat). AUD/CAD/CHF dışarıda: hisse endeksi verisi yok.
Dönem: 2013-01 – 2026-10 ay sonları (veri sonu ne ise; tarih kesimi sonuca bakılmadan).

## Kural (sıfır serbest parametre)
- T = ayın son iş günü (FX verisi olan son hafta içi gün). Hisse getirisi: ayın ilk iş günü kapanışı → T−1 kapanışı.
- s_i = r_eq_i − r_eq_US (i ∈ EUR, GBP, JPY). s_i > 0 → yabancı para **short** vs USD; s_i < 0 → **long**. s_i = 0 → işlem yok.
- Giriş T günü 15:00 Europe/London, çıkış 16:00 Europe/London (DST zoneinfo ile). Fiyat = o saatte başlayan 5m barın açılışı.
- Sepet: 3 döviz eşit nominal, ay başına ortalama (tek gözlem = bir ay sonu).
- Maliyet: Maven `reality_profile.csv` (ölçüm 2026-11-12), `real_cost_per_side_central` EUR 0.233, GBP 0.189, JPY 0.220 bp/taraf;
  her işlem 2 taraf. Kötümser = 2× merkez. Not: ölçüm fix anına özgü değil; fix'te spread açılması ölçülmedi → etiket.

## Birincil test ve karar
- Birincil: 1x maliyette ay başı sepet net getirisi ortalaması > 0, tek yönlü p (ay gözlemleri üzerinde iid bootstrap,
  10.000, seed 20261121; ay sonları arası bağımlılık beklenmiyor). Tek birincil test → düzeltme yok.
- **GEÇER** = p ≤ 0.05 **ve** 4 rejim bloğundan (2013–17, 2018–21, 2022–23, 2024–26) ≥ 3'ünde 1x ortalama > 0 **ve** 2x maliyette ortalama > 0.
- Rapor: maliyetsiz / 1x / 2x, döviz bazında ortalama ve n, blok ortalamaları, isabet oranı, makale yönüyle tutarlılık
  (s_i ile 15–16 getirisi regresyon katsayısı, makale −0.0142 ile yan yana).
- Güç beyanı: makale katsayısıyla tipik |s| %2–4 → beklenen brüt ~3–6 bp/işlem; maliyet ~0.4–0.5 bp gidiş-dönüş.
  ~165 ay, aylık sepet std ~8–10 bp varsayımıyla ~1 bp ortalama tespit edilebilir. "Geçmedi" yine de "etki yok" demek değil.

## Keşif (karar vermez)
- K1: fix sonrası dönüş — T 16:00 → T+1 12:00 Londra, −sign(15–16 getirisi) yönünde (Denk. 5). Yalnız raporlanır.
- K2: |s| ile orantılı ağırlık (makalenin doğrusal formu). Yalnız raporlanır.

## Uygulanabilirlik (geçse bile)
LIVE'a girmez. Sıradaki adım: Maven forward PAPER + prop uygunluğu (yılda 12 işlem/döviz, 1 saat tutuş, haber kuralı:
ay sonu 15:00 Londra = 10:00 ET, bazı aylarda ISM/tüketici güveni açıklamasıyla çakışır → FN haber kısıtı kontrol edilecek).

## SONUÇ (2026-11-21, ön-kayıt 0d6b456 sonrası tek koşu) — GEÇMEDİ
Kod `scripts_2026-11-21/melvin_prins.py`, ham çıktı `strategy-lab/outputs/intraday/melvin_prins/result.json`.
164 ay sonu, 2013-01-31 – 2026-08-28 (önbellek sonu), 492 işlem, eksik fix barı 0.

| bp / ay (3 döviz sepeti) | ortalama | se | isabet | 2013–17 | 2018–21 | 2022–23 | 2024–26 |
|---|---|---|---|---|---|---|---|
| maliyetsiz | +1.22 | 1.26 | %57 | +3.87 | −3.30 | +4.56 | +0.51 |
| ölçülmüş merkez (1x) | +0.79 | 1.26 | %55 | +3.45 | −3.73 | +4.13 | +0.08 |
| kötümser (2x) | +0.36 | 1.26 | %53 | +3.02 | −4.16 | +3.70 | −0.35 |

p(1x) = 0.27 → birincil şart sağlanmadı (blok 3/4 ve 2x > 0 sağlandı). Döviz bazında brüt: EUR +0.78, GBP +2.88, JPY −0.01 bp.
Eğim r_pre ~ s = −0.0049 (makale −0.0142; yön aynı, büyüklük ~1/3). Fix anı spread açılması ölçülmedi.
Keşif (karar vermez): K1 fix sonrası dönüş brüt +5.04 bp/ay se 2.85 n128 (bloklar +4.4/+0.9/+13.1/+5.6);
K2 doğrusal ağırlık brüt +2.26 bp. K1'i bu veride ana teste çevirmek post-hoc olur; yalnız forward ölçümle sınanabilir.
Katalog: `elenenler.py` → melvin_prins_month_end_fx (rejected).
