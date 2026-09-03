# Seans brifingi (olgu)

Uretim: **2026-09-03 13:21 TR** / 2026-09-03 10:21 UTC  
Kaynak: bulut feed (yfinance/Binance). Otomatik uretilir; yalniz olcum basar.

> **Fiyatlar endeks kotasyonu, broker fiyati DEGIL.** ^NDX ile MavenTrade US100 arasinda olculmus basis ~-170 puan (2026-08-24). Buradaki seviyeleri dogrudan emir fiyati olarak kullanma; terminaldeki fiyatla farki kendin hesapla.

## Sistem durumu

### Mekanik ray (dondurulmus -- yeni modul/parametre yok)

- **NQ_ORB_STRONG_TREND**: n=24, exp_R=-0.171, esige 1 islem
- **SWEEP_CORE_AVOID_MID_VWAP**: n=10, exp_R=+0.613, esige 15 islem

### Diskresyoner ray (birincil)

- acik aday: 0, pas: 0
- Kapanmis islem yok (defter bos).

## Takvim

- Bugun FOMC/CPI/NFP yok.
- 2026-09-04  NFP

## Seans

- Tokyo: kapali, acilisa 13.7 saat
- Londra: ACIK, kapanisa 5.7 saat
- New York: kapali, acilisa 2.7 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29141  (bar 2026-09-03 10:00:00 UTC)
- dun araligi: 28927 → 29213
- bugun araligi: 29075 → 29293
- 200EMA (gunluk): 27406  (uzaklik +1735.2 / %+6.33)
- ATR(14) son kapali gun: 471.96  (100 gunun %10. yuzdeligi)
- hacim (son kapali gun): 556,412  (20 gunun %68. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-07-17  30062  (direnc)
  - 2026-07-21  28408  (destek)
  - 2026-07-23  29365  (direnc)
  - 2026-07-31  27202  (destek)
  - 2026-08-07  30074  (direnc)
  - 2026-08-19  30343  (direnc)
  - 2026-08-26  28947  (destek)
  - 2026-09-01  29812  (direnc)

### XAUUSD (5m)

- son kapanis: 4470.6  (bar 2026-09-03 10:10:00 UTC)
- dun araligi: 4292.2 → 4390.2
- bugun araligi: 4426.7 → 4490
- 200EMA (gunluk): 4312.3  (uzaklik +158.25 / %+3.67)
- ATR(14) son kapali gun: 79.026  (100 gunun %39. yuzdeligi)
- hacim (son kapali gun): 191  (20 gunun %0. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-07-24  4152.1  (direnc)
  - 2026-07-31  4017.9  (destek)
  - 2026-08-03  4118.5  (direnc)
  - 2026-08-17  4445  (direnc)
  - 2026-08-18  4315  (destek)
  - 2026-08-21  4327.6  (destek)
  - 2026-08-26  4670.9  (direnc)
  - 2026-09-01  4625.5  (direnc)

### EURUSD (5m)

- son kapanis: 1.1604  (bar 2026-09-03 10:20:00 UTC)
- dun araligi: 1.1567 → 1.1605
- bugun araligi: 1.1587 → 1.1617
- 200EMA (gunluk): 1.1568  (uzaklik +0.0035497 / %+0.31)
- ATR(14) son kapali gun: 0.0052839  (100 gunun %6. yuzdeligi)
- hacim: BU FEED HACIM VERMIYOR (spot FX) -- hacim katmani brifingten doldurulamaz
- donus seviyeleri (son 60 gun):
  - 2026-07-20  1.1478  (direnc)
  - 2026-07-27  1.1365  (destek)
  - 2026-07-27  1.1438  (direnc)
  - 2026-07-30  1.1354  (destek)
  - 2026-08-11  1.1518  (destek)
  - 2026-08-11  1.1579  (direnc)
  - 2026-08-17  1.1513  (destek)
  - 2026-08-25  1.1712  (direnc)

### GBPUSD (5m)

- son kapanis: 1.349  (bar 2026-09-03 10:20:00 UTC)
- dun araligi: 1.3475 → 1.3515
- bugun araligi: 1.3481 → 1.3507
- 200EMA (gunluk): 1.3419  (uzaklik +0.007087 / %+0.53)
- ATR(14) son kapali gun: 0.0066944  (100 gunun %1. yuzdeligi)
- hacim: BU FEED HACIM VERMIYOR (spot FX) -- hacim katmani brifingten doldurulamaz
- donus seviyeleri (son 60 gun):
  - 2026-07-14  1.3452  (direnc)
  - 2026-07-16  1.3343  (destek)
  - 2026-07-20  1.3545  (direnc)
  - 2026-07-30  1.3273  (destek)
  - 2026-08-05  1.3501  (direnc)
  - 2026-08-11  1.3435  (destek)
  - 2026-08-17  1.3476  (destek)
  - 2026-08-25  1.3675  (direnc)

## Trend katmani (sabit tanim, 21 sembol)

200EMA konumu + ADX(14) + 20/50 gunluk degisim, gunluk barlardan. Evrenin TAMAMI on-kayitli sabit sirada listeleniyor. Eleme yok, esik yok, yorum yok.

**Bu liste islem evreni DEGIL.** Portfoy ve modul kumesi degismedi; burada bir sembolun gorunmesi orada calisan bir modul oldugu anlamina gelmez.

| sembol | grup | 200EMA | uzaklik | ADX | 20g | 50g |
|---|---|---|---|---|---|---|
| NASDAQ100 | endeks | ustunde | %+6.4 | 15.3 | %-1.4 | %-1.6 |
| SP500 | endeks | ustunde | %+6.5 | 13.2 | %-0.9 | %+3.2 |
| US30 | endeks | ustunde | %+5.9 | 14.9 | %-2.5 | %+2.0 |
| US2000 | endeks | ustunde | %+6.8 | 18.3 | %-2.2 | %-1.3 |
| GER40 | endeks | ustunde | %+4.3 | 24.0 | %-1.1 | %+4.4 |
| UK100 | endeks | ustunde | %+4.4 | 19.1 | %-1.1 | %+3.1 |
| FRA40 | endeks | ustunde | %+0.4 | 27.4 | %-4.5 | %-1.3 |
| JAP225 | endeks | ustunde | %+8.6 | 13.3 | %-1.5 | %-6.1 |
| EURUSD | fx | ustunde | %+0.3 | 31.3 | %+0.5 | %+1.9 |
| GBPUSD | fx | ustunde | %+0.7 | 27.0 | %+0.5 | %+2.4 |
| USDJPY | fx | ustunde | %+1.4 | 38.6 | %+1.6 | %-0.9 |
| AUDUSD | fx | ustunde | %+2.8 | 18.8 | %+1.4 | %+3.3 |
| USDCAD | fx | altinda | %-0.0 | 27.2 | %-1.2 | %-2.2 |
| USDCHF | fx | ustunde | %+1.3 | 17.9 | %+0.3 | %+0.2 |
| NZDUSD | fx | ustunde | %+0.8 | 22.0 | %+0.3 | %+4.1 |
| EURJPY | fx | ustunde | %+1.7 | 18.0 | %+2.1 | %+1.0 |
| GBPJPY | fx | ustunde | %+2.1 | 18.1 | %+2.0 | %+1.5 |
| XAUUSD | emtia | ustunde | %+1.0 | 25.5 | %+2.8 | %+5.7 |
| XAGUSD | emtia | altinda | %-1.0 | 25.2 | %+4.2 | %+4.4 |
| WTI | emtia | ustunde | %+14.1 | 15.6 | %+21.0 | %+24.3 |
| BTCUSDT | kripto | ustunde | %+6.4 | 44.2 | %+21.8 | %+18.9 |

## Olculmus fikirler katalogu

Tez kontrolu icin. Statuye bak: veto YALNIZ rejected/retired.

**ELENMIS -- BU TEZI KULLANMA** (VETO)

- `equal_high_low_raid` — Equal high/low avlandiktan sonra donus
  - kapsam: 'raid/sweep DONUSU' tezine dair. Calisan SWEEP_CORE ayri bir sey olcuyor (NASDAQ 15m, ADX rejimi + VWAP konumu) ve forward defterinde duruyor -- bu madde onu veto ETMEZ.
- `ny_londra_surdurme` — NY seansi Londra yonunu surdurur
- `prevday_continuation` — Dun yukari kapadiysa once PDH vurulur
- `inside_day_kirilim` — Inside day sonrasi kirilim (Kathy Lien)
- `btc_absorption` — BTC absorption modulu
- `fomc_oncesi_drift` — FOMC duyurusu oncesi long (15-30 dk pencere)
  - kapsam: 15-30 dakikalik pencere. Lucca-Moench 24 SAATLIK pencereyi olcer; o soru burada CURUTULMEDI, sorulmadi bile.
- `sweep_cok_endeks` — SWEEP'i 7 endekse yayarak kari katlamak
  - kapsam: Veto YALNIZCA 'ayni kurali 7 endekse yay' genislemesine. Tek- enstruman SWEEP_CORE_AVOID_MID_VWAP calisiyor (n=9, +0.804) ve portfoyde kaldi.
- `ic_bar_bazli` — Bar-bazli IC (Information Coefficient) ile bekleme suresini kisaltmak
- `sunucu_kiralama` — Sunucu kiralayip daha cok strateji taramak

**TEK BASINA EDGE DEGIL -- giris kurali yapma** (veto DEGIL)

- `fvg_doldurma` — FVG (fair value gap) doldurulur
  - kapsam: Giris kurali olarak. Diskresyoner seansta baska bir gerekcenin yaninda baglam diye bakmak yasak degil; tek basina tez olamaz.
- `ema_vwap_sicrama` — EMA20 / EMA50 / VWAP'tan sicrama
  - kapsam: Giris kurali olarak. Confluence/baglam kullanimi ayri soru -- olculen sey 'tek basina sicrama al' idi.

**ADOPTE EDILMEDI -- veto DEGIL** (veto DEGIL)

- `donchian_xau` — Donchian kanal kirilimi, XAUUSD 1H (turtle)
  - kapsam: XAUUSD 1H turtle kanali. Yasak degil: olculdu, pozitif cikti, mevcut kitabin altinda kaldigi icin secilmedi.

**EMEKLI EDILDI -- yeniden acmak icin yeni gerekce gerekir** (VETO)

- `gold_ny_orb` — GOLD NY ORB modulu
  - kapsam: XAUUSD 5m ORB modulune. NQ_ORB_STRONG_TREND AYRI modul, canli ve olculmeye devam ediyor -- 'ORB' kelimesi ikisini birden vetolamaz.

---

Bu dosyayi okuyan asistan icin kural seti: `TELEFON/SISTEM.md`.
