# Seans brifingi (olgu)

Uretim: **2026-09-03 03:26 TR** / 2026-09-03 00:26 UTC  
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

- Tokyo: ACIK, kapanisa 8.6 saat
- Londra: kapali, acilisa 6.6 saat
- New York: kapali, acilisa 12.6 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29150  (bar 2026-09-03 00:15:00 UTC)
- dun araligi: 29148 → 29213
- bugun araligi: henuz bar yok
- 200EMA (gunluk): 27406  (uzaklik +1743.6 / %+6.36)
- ATR(14) son kapali gun: 457.8  (100 gunun %3. yuzdeligi)
- hacim (son kapali gun): 11,327  (20 gunun %0. yuzdeligi)
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

- son kapanis: 4430.6  (bar 2026-09-03 00:15:00 UTC)
- dun araligi: 4426.7 → 4438.1
- bugun araligi: henuz bar yok
- 200EMA (gunluk): 4312.9  (uzaklik +117.68 / %+2.73)
- ATR(14) son kapali gun: 78.462  (100 gunun %37. yuzdeligi)
- hacim (son kapali gun): 4,592  (20 gunun %95. yuzdeligi)
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

- son kapanis: 1.1592  (bar 2026-09-03 00:25:00 UTC)
- dun araligi: 1.1567 → 1.1605
- bugun araligi: 1.1587 → 1.1593
- 200EMA (gunluk): 1.1568  (uzaklik +0.0023393 / %+0.20)
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

- son kapanis: 1.3485  (bar 2026-09-03 00:25:00 UTC)
- dun araligi: 1.3475 → 1.3515
- bugun araligi: 1.3481 → 1.349
- 200EMA (gunluk): 1.3419  (uzaklik +0.0065413 / %+0.49)
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
| NASDAQ100 | endeks | ustunde | %+6.2 | 15.1 | %-1.6 | %-1.7 |
| SP500 | endeks | ustunde | %+6.5 | 13.2 | %-1.0 | %+3.2 |
| US30 | endeks | ustunde | %+5.9 | 14.8 | %-2.5 | %+2.0 |
| US2000 | endeks | ustunde | %+6.7 | 18.2 | %-2.2 | %-1.3 |
| GER40 | endeks | ustunde | %+4.9 | 25.2 | %-0.9 | %+4.3 |
| UK100 | endeks | ustunde | %+4.8 | 19.5 | %-0.6 | %+3.4 |
| FRA40 | endeks | ustunde | %+0.7 | 25.4 | %-4.2 | %-0.5 |
| JAP225 | endeks | ustunde | %+7.9 | 13.0 | %-2.1 | %-6.7 |
| EURUSD | fx | ustunde | %+0.3 | 31.3 | %+0.5 | %+1.9 |
| GBPUSD | fx | ustunde | %+0.7 | 27.0 | %+0.5 | %+2.4 |
| USDJPY | fx | ustunde | %+1.4 | 38.6 | %+1.6 | %-0.9 |
| AUDUSD | fx | ustunde | %+2.8 | 18.8 | %+1.4 | %+3.3 |
| USDCAD | fx | altinda | %-0.0 | 27.2 | %-1.2 | %-2.2 |
| USDCHF | fx | ustunde | %+1.3 | 17.9 | %+0.3 | %+0.2 |
| NZDUSD | fx | ustunde | %+0.8 | 22.0 | %+0.3 | %+4.1 |
| EURJPY | fx | ustunde | %+1.7 | 18.0 | %+2.1 | %+1.0 |
| GBPJPY | fx | ustunde | %+2.1 | 18.1 | %+2.0 | %+1.5 |
| XAUUSD | emtia | ustunde | %+2.4 | 24.7 | %+4.4 | %+7.3 |
| XAGUSD | emtia | ustunde | %+0.5 | 25.0 | %+6.0 | %+6.1 |
| WTI | emtia | ustunde | %+13.7 | 15.3 | %+20.6 | %+23.9 |
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
