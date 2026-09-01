# Seans brifingi (olgu)

Uretim: **2026-09-01 23:33 TR** / 2026-09-01 20:33 UTC  
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

- Tokyo: kapali, acilisa 3.4 saat
- Londra: kapali, acilisa 10.4 saat
- New York: ACIK, kapanisa 0.4 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29151  (bar 2026-09-01 20:15:00 UTC)
- dun araligi: 29274 → 29546
- bugun araligi: 29002 → 29571
- 200EMA (gunluk): 27371  (uzaklik +1779.8 / %+6.50)
- ATR(14) son kapali gun: 479.9  (100 gunun %12. yuzdeligi)
- hacim (son kapali gun): 583,609  (20 gunun %89. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-07-14  30078  (direnc)
  - 2026-07-17  30062  (direnc)
  - 2026-07-21  28408  (destek)
  - 2026-07-23  29365  (direnc)
  - 2026-07-31  27202  (destek)
  - 2026-08-07  30074  (direnc)
  - 2026-08-19  30343  (direnc)
  - 2026-08-26  28947  (destek)

### XAUUSD (5m)

- son kapanis: 4374.7  (bar 2026-09-01 20:20:00 UTC)
- dun araligi: 4410.9 → 4466.9
- bugun araligi: 4369.7 → 4510.5
- 200EMA (gunluk): 4311.4  (uzaklik +63.326 / %+1.47)
- ATR(14) son kapali gun: 75.687  (100 gunun %23. yuzdeligi)
- hacim (son kapali gun): 1,758  (20 gunun %84. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-07-21  3964.2  (destek)
  - 2026-07-24  4152.1  (direnc)
  - 2026-07-31  4017.9  (destek)
  - 2026-08-03  4118.5  (direnc)
  - 2026-08-17  4445  (direnc)
  - 2026-08-18  4315  (destek)
  - 2026-08-21  4327.6  (destek)
  - 2026-08-26  4670.9  (direnc)

### EURUSD (5m)

- son kapanis: 1.1593  (bar 2026-09-01 20:30:00 UTC)
- dun araligi: 1.1585 → 1.1623
- bugun araligi: 1.1589 → 1.1628
- 200EMA (gunluk): 1.1568  (uzaklik +0.0025306 / %+0.22)
- ATR(14) son kapali gun: 0.0054286  (100 gunun %13. yuzdeligi)
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

- son kapanis: 1.3513  (bar 2026-09-01 20:30:00 UTC)
- dun araligi: 1.3535 → 1.3565
- bugun araligi: 1.3507 → 1.356
- 200EMA (gunluk): 1.3418  (uzaklik +0.0095081 / %+0.71)
- ATR(14) son kapali gun: 0.0068644  (100 gunun %2. yuzdeligi)
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

200EMA konumu + ADX(14) + 20/50 gunluk degisim, gunluk barlardan. Evrenin TAMAMI listeleniyor; siralama 20 gunluk degisime gore. Eleme yok, esik yok, yorum yok.

**Bu liste islem evreni DEGIL.** Portfoy ve modul kumesi degismedi; burada bir sembolun gorunmesi orada calisan bir modul oldugu anlamina gelmez.

| sembol | grup | 200EMA | uzaklik | ADX | 20g | 50g |
|---|---|---|---|---|---|---|
| BTCUSDT | kripto | ustunde | %+6.5 | 44.0 | %+21.9 | %+24.1 |
| WTI | emtia | ustunde | %+14.0 | 13.4 | %+19.8 | %+21.3 |
| XAGUSD | emtia | altinda | %-1.1 | 27.6 | %+7.7 | %-1.3 |
| XAUUSD | emtia | ustunde | %+1.2 | 26.7 | %+6.8 | %+4.6 |
| EURJPY | fx | ustunde | %+1.6 | 17.5 | %+2.4 | %+0.6 |
| GBPJPY | fx | ustunde | %+2.1 | 17.5 | %+2.3 | %+1.1 |
| AUDUSD | fx | ustunde | %+2.8 | 20.2 | %+2.1 | %+2.2 |
| USDJPY | fx | ustunde | %+1.4 | 39.8 | %+1.7 | %-0.8 |
| EURUSD | fx | ustunde | %+0.3 | 34.4 | %+0.7 | %+1.5 |
| GBPUSD | fx | ustunde | %+0.7 | 30.2 | %+0.6 | %+2.0 |
| NZDUSD | fx | ustunde | %+0.8 | 23.0 | %+0.4 | %+3.1 |
| USDCHF | fx | ustunde | %+1.3 | 19.1 | %+0.2 | %+0.3 |
| UK100 | endeks | ustunde | %+4.8 | 20.0 | %-0.6 | %+3.4 |
| JAP225 | endeks | ustunde | %+8.8 | 12.4 | %-0.8 | %-10.8 |
| GER40 | endeks | ustunde | %+4.9 | 27.1 | %-0.9 | %+4.3 |
| USDCAD | fx | altinda | %-0.0 | 29.8 | %-1.1 | %-1.9 |
| SP500 | endeks | ustunde | %+6.2 | 13.6 | %-1.5 | %+1.4 |
| NASDAQ100 | endeks | ustunde | %+6.4 | 14.5 | %-2.4 | %-4.9 |
| US30 | endeks | ustunde | %+5.4 | 14.4 | %-2.6 | %+1.4 |
| US2000 | endeks | ustunde | %+5.6 | 14.3 | %-3.9 | %-3.3 |
| FRA40 | endeks | ustunde | %+0.6 | 23.5 | %-4.2 | %-0.5 |

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
