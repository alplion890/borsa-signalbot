# Seans brifingi (olgu)

Uretim: **2026-09-07 14:00 TR** / 2026-09-07 11:00 UTC  
Kaynak: bulut feed (yfinance/Binance). Otomatik uretilir; yalniz olcum basar.

> **Fiyatlar endeks kotasyonu, broker fiyati DEGIL.** ^NDX ile MavenTrade US100 arasinda olculmus basis ~-170 puan (2026-08-24). Buradaki seviyeleri dogrudan emir fiyati olarak kullanma; terminaldeki fiyatla farki kendin hesapla.

## Sistem durumu

### Mekanik ray (dondurulmus -- yeni modul/parametre yok)

- **SWEEP_CORE_AVOID_MID_VWAP**: n=10, exp_R=+0.613, esige 15 islem

### Diskresyoner ray (birincil)

- acik aday: 0, pas: 0
- Kapanmis islem yok (defter bos).

## Takvim

- Bugun FOMC/CPI/NFP yok.
- 2026-09-11  CPI

## Seans

- Tokyo: kapali, acilisa 13.0 saat
- Londra: ACIK, kapanisa 5.0 saat
- New York: kapali, acilisa 2.0 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29565  (bar 2026-09-04 20:45:00 UTC)
- dun araligi: 29468 → 29704
- bugun araligi: 29530 → 29684
- 200EMA (gunluk): 27454  (uzaklik +2111.5 / %+7.69)
- ATR(14) son kapali gun: 457.62  (100 gunun %3. yuzdeligi)
- hacim (son kapali gun): 539,285  (20 gunun %63. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-07-21  28408  (destek)
  - 2026-07-23  29365  (direnc)
  - 2026-07-31  27202  (destek)
  - 2026-08-07  30074  (direnc)
  - 2026-08-19  30343  (direnc)
  - 2026-08-26  28947  (destek)
  - 2026-09-01  29812  (direnc)
  - 2026-09-04  28927  (destek)

### XAUUSD (5m)

- son kapanis: 4476.6  (bar 2026-09-04 20:55:00 UTC)
- dun araligi: 4429.8 → 4429.8
- bugun araligi: 4430.4 → 4481.3
- 200EMA (gunluk): 4316.4  (uzaklik +160.2 / %+3.71)
- ATR(14) son kapali gun: 82.093  (100 gunun %47. yuzdeligi)
- hacim (son kapali gun): 16  (20 gunun %0. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-07-31  4017.9  (destek)
  - 2026-08-03  4118.5  (direnc)
  - 2026-08-17  4445  (direnc)
  - 2026-08-18  4315  (destek)
  - 2026-08-21  4327.6  (destek)
  - 2026-08-26  4670.9  (direnc)
  - 2026-09-01  4625.5  (direnc)
  - 2026-09-04  4292.2  (destek)

### EURUSD (5m)

- son kapanis: 1.1628  (bar 2026-09-07 10:55:00 UTC)
- dun araligi: 1.1587 → 1.1633
- bugun araligi: 1.1609 → 1.1639
- 200EMA (gunluk): 1.1568  (uzaklik +0.0059439 / %+0.51)
- ATR(14) son kapali gun: 0.005188  (100 gunun %4. yuzdeligi)
- hacim: BU FEED HACIM VERMIYOR (spot FX) -- hacim katmani brifingten doldurulamaz
- donus seviyeleri (son 60 gun):
  - 2026-07-27  1.1365  (destek)
  - 2026-07-27  1.1438  (direnc)
  - 2026-07-30  1.1354  (destek)
  - 2026-08-11  1.1518  (destek)
  - 2026-08-11  1.1579  (direnc)
  - 2026-08-17  1.1513  (destek)
  - 2026-08-25  1.1712  (direnc)
  - 2026-09-04  1.1567  (destek)

### GBPUSD (5m)

- son kapanis: 1.3539  (bar 2026-09-07 10:55:00 UTC)
- dun araligi: 1.349 → 1.3549
- bugun araligi: 1.3507 → 1.3545
- 200EMA (gunluk): 1.3421  (uzaklik +0.011858 / %+0.88)
- ATR(14) son kapali gun: 0.006651  (100 gunun %1. yuzdeligi)
- hacim: BU FEED HACIM VERMIYOR (spot FX) -- hacim katmani brifingten doldurulamaz
- donus seviyeleri (son 60 gun):
  - 2026-07-16  1.3343  (destek)
  - 2026-07-20  1.3545  (direnc)
  - 2026-07-30  1.3273  (destek)
  - 2026-08-05  1.3501  (direnc)
  - 2026-08-11  1.3435  (destek)
  - 2026-08-17  1.3476  (destek)
  - 2026-08-25  1.3675  (direnc)
  - 2026-09-04  1.3475  (destek)

## Trend katmani (sabit tanim, 21 sembol)

200EMA konumu + ADX(14) + 20/50 gunluk degisim, gunluk barlardan. Evrenin TAMAMI on-kayitli sabit sirada listeleniyor. Eleme yok, esik yok, yorum yok.

**Bu liste islem evreni DEGIL.** Portfoy ve modul kumesi degismedi; burada bir sembolun gorunmesi orada calisan bir modul oldugu anlamina gelmez.

| sembol | grup | 200EMA | uzaklik | ADX | 20g | 50g |
|---|---|---|---|---|---|---|
| NASDAQ100 | endeks | ustunde | %+7.6 | 13.6 | %-0.9 | %-0.5 |
| SP500 | endeks | ustunde | %+7.0 | 12.5 | %-0.7 | %+4.0 |
| US30 | endeks | ustunde | %+6.4 | 13.1 | %-1.3 | %+2.1 |
| US2000 | endeks | ustunde | %+7.2 | 19.6 | %-2.1 | %-1.8 |
| GER40 | endeks | ustunde | %+5.0 | 21.3 | %-1.0 | %+5.6 |
| UK100 | endeks | ustunde | %+5.0 | 16.6 | %-0.3 | %+2.9 |
| FRA40 | endeks | ustunde | %+0.3 | 30.7 | %-5.0 | %-1.3 |
| JAP225 | endeks | ustunde | %+10.2 | 13.6 | %-0.6 | %-7.5 |
| EURUSD | fx | ustunde | %+0.6 | 29.2 | %+0.9 | %+2.3 |
| GBPUSD | fx | ustunde | %+0.9 | 23.9 | %+0.6 | %+2.6 |
| USDJPY | fx | altinda | %-1.5 | 41.6 | %-1.7 | %-3.8 |
| AUDUSD | fx | ustunde | %+3.5 | 19.0 | %+2.4 | %+4.4 |
| USDCAD | fx | altinda | %-0.8 | 25.5 | %-1.6 | %-2.9 |
| USDCHF | fx | ustunde | %+0.8 | 15.8 | %-0.6 | %-0.4 |
| NZDUSD | fx | ustunde | %+0.7 | 22.3 | %+0.3 | %+4.3 |
| EURJPY | fx | altinda | %-0.9 | 23.3 | %-0.8 | %-1.5 |
| GBPJPY | fx | altinda | %-0.6 | 23.3 | %-1.2 | %-1.3 |
| XAUUSD | emtia | ustunde | %+2.4 | 22.0 | %+2.1 | %+9.9 |
| XAGUSD | emtia | ustunde | %+0.9 | 22.3 | %+4.3 | %+13.2 |
| WTI | emtia | ustunde | %+14.4 | 17.8 | %+17.0 | %+27.2 |
| BTCUSDT | kripto | ustunde | %+10.1 | 48.0 | %+24.5 | %+23.9 |

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
