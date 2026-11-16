# Meta-label ön-kaydı — 2026-11-16

Soru (kullanıcı): mekanik edge'ler geçmişte **hangi koşullarda** kaybetti?
O koşullar bilinirse, genel olarak negatif/zayıf bir edge'in sinyali o
koşullarda geçilip (skip) kalan işlemler pozitif olur mu?
Yöntem adı: meta-labeling (López de Prado 2018, böl. 3; Joubert 2022 JFDS).

Bu dosya koşudan ÖNCE commit edilir. Sonuca bakıp özellik, eşik, modül,
dönem veya geçme kriteri değiştirmek yasak.

## Kapsam
Modüller (14 yıllık altyapısı olan, değiştirilmemiş girişler,
`long_history_ab.SPECS`): SWEEP_CORE (NQ 15m, adaptif RR — canlı ATR tavanı
ile), NQ_ORB (NQ 5m), GOLD_ORB (XAU 5m), EUR_LONDON, GBP_LONDON (5m).

Veri: Dukascopy, 2012 → son bar. Keşif (IS): 2012-01-01..2021-12-31.
Doğrulama (OOS): 2022-01-01 → son. OOS tek atış.

## Özellikler (hepsi sinyal mumu KAPANDIĞINDA bilinir)
1. `atr_rank` — günlük ATR14'ün son 100 gündeki yüzdeliği (önceki gün) — oynaklık
2. `adx` — modül zaman diliminde ADX14 — trend gücü
3. `eff20` — 20 mumluk verim oranı |Δ| / Σ|Δ| — trend vs testere
4. `rel_vol` — sinyal mumu hacmi / son 20 mum medyanı — hacimli mum
5. `bar_atr` — sinyal mumu aralığı / ATR14 (modül TF) — büyük mum
6. `event_day` — aynı gün FOMC/CPI/NFP (resmi takvim, `event_calendar`) — haber
7. `hour` — sinyal saati (UTC)
8. `gap` — günün ilk mumu açılışı − önceki gün kapanışı, / günlük ATR (mutlak)
9. `with_trend` — işlem yönü kapanmış 1s EMA20/EMA50 yönüyle aynı mı (1/0)

Plansız haber (savaş vb.) için geçmiş takvim yok → ölçülemez; dolaylı vekil
olarak 1, 4, 5, 8 var. Bu sınır raporda yazılır.

## Test A — tek özellik (kullanıcının gözle uygulayabileceği kural)
Her modül × her özellik: IS'te özelliği tercile böl (event_day, with_trend
ikili), IS'te exp_R'si en kötü dilimi seç. Kural = "o dilimde sinyali geç".
OOS'ta değerlendir. Hipotez sayısı 5 × 9 = 45.

## Test B — çok özellikli model
Her modül: lojistik regresyon (standartlaştırılmış 9 özellik, L2, C=1.0),
etiket = R>0, yalnız IS'te eğitim. Eşik = IS olasılık medyanı (işlemlerin
~yarısı alınır). OOS'ta değerlendir. Hipotez sayısı 5.

## Maliyet
Ölçülmüş Maven: `reality_profile.csv` (spread_one_side_now + slippage_p90
+ FX komisyonu 1e-5), bugünkü fiyatta puan olarak sabit, işlem başına kendi
stopuna oranlanır (`live_cost_check` ile aynı). Üç satır: maliyetsiz /
ölçülmüş merkez / kötümser (2× ölçülmüş).

## Geçme kriteri (hepsi OOS, ölçülmüş merkez maliyetle)
1. Alınan işlemler exp_R > 0
2. Alınan exp_R > tüm işlemler exp_R
3. Permütasyon testi (OOS'ta alınan/geçilen etiketi 10.000 kez karıştır,
   tek yönlü): p, Holm düzeltmesiyle (A: 45, B: 5 hipotez) < 0.05
4. OOS'ta alınan işlem n ≥ 30
5. Kötümser maliyette de alınan exp_R > 0

Geçen kural yalnız **aday** olur: Maven forward'da PAPER ölçülür, LIVE kuralı
ve risk kendiliğinden değişmez (karar kullanıcıda). Hiçbiri geçmezse sonuç
"geçmişte bu özelliklerle kayıplar ayrılamıyor" olarak yazılır ve elenenler
kataloğuna girer.

## Bilinen sınırlar
- Aynı gün birden fazla işlem permütasyonda bağımsız sayılır (n şişebilir);
  gün sayısı ayrıca raporlanır.
- SWEEP'in 2022 rejim kırılması: IS negatif, OOS pozitif. Bir filtre IS'te
  "kötü dilimi" bulsa bile OOS genel pozitifliği filtreye mal edilmez —
  kriter 2 (tümüne göre fark) bunun için var.
