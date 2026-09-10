# Seans brifingi (olgu)

Uretim: **2026-09-10 19:59 TR** / 2026-09-10 16:59 UTC  
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
- 2026-09-16  FOMC

## Seans

- Tokyo: kapali, acilisa 7.0 saat
- Londra: kapali, acilisa 14.0 saat
- New York: ACIK, kapanisa 4.0 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29213  (bar 2026-09-10 16:45:00 UTC)
- dun araligi: 29333 → 29634
- bugun araligi: 29043 → 29508
- 200EMA (gunluk): 27502  (uzaklik +1711.7 / %+6.22)
- ATR(14) son kapali gun: 438.61  (100 gunun %0. yuzdeligi)
- hacim (son kapali gun): 613,787  (20 gunun %95. yuzdeligi)
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

- son kapanis: 4401.7  (bar 2026-09-10 16:45:00 UTC)
- dun araligi: 4397.4 → 4416
- bugun araligi: 4365.4 → 4479.9
- 200EMA (gunluk): 4318.3  (uzaklik +83.41 / %+1.93)
- ATR(14) son kapali gun: 75.374  (100 gunun %21. yuzdeligi)
- hacim (son kapali gun): 215  (20 gunun %21. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-08-03  4118.5  (direnc)
  - 2026-08-17  4445  (direnc)
  - 2026-08-18  4315  (destek)
  - 2026-08-21  4327.6  (destek)
  - 2026-08-26  4670.9  (direnc)
  - 2026-09-01  4625.5  (direnc)
  - 2026-09-04  4292.2  (destek)
  - 2026-09-08  4510  (direnc)

### EURUSD (5m)

- son kapanis: 1.1623  (bar 2026-09-10 16:55:00 UTC)
- dun araligi: 1.1622 → 1.1654
- bugun araligi: 1.1597 → 1.1644
- 200EMA (gunluk): 1.157  (uzaklik +0.0052717 / %+0.46)
- ATR(14) son kapali gun: 0.0047283  (100 gunun %0. yuzdeligi)
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

- son kapanis: 1.3524  (bar 2026-09-10 16:55:00 UTC)
- dun araligi: 1.3533 → 1.357
- bugun araligi: 1.3493 → 1.356
- 200EMA (gunluk): 1.3424  (uzaklik +0.010049 / %+0.75)
- ATR(14) son kapali gun: 0.0061602  (100 gunun %0. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+7.0 | 12.0 | %-0.6 | %-2.0 |
| SP500 | endeks | ustunde | %+5.8 | 11.8 | %-1.3 | %+1.9 |
| US30 | endeks | ustunde | %+4.2 | 13.8 | %-2.7 | %-0.3 |
| US2000 | endeks | ustunde | %+5.2 | 21.8 | %-3.7 | %-3.6 |
| GER40 | endeks | ustunde | %+2.9 | 18.8 | %-2.9 | %+2.1 |
| UK100 | endeks | ustunde | %+3.3 | 15.4 | %-1.6 | %+1.6 |
| FRA40 | endeks | altinda | %-1.2 | 34.1 | %-6.0 | %-2.2 |
| JAP225 | endeks | ustunde | %+7.3 | 12.3 | %-4.4 | %-9.2 |
| EURUSD | fx | ustunde | %+0.5 | 27.4 | %+0.7 | %+1.9 |
| GBPUSD | fx | ustunde | %+0.9 | 21.0 | %+0.3 | %+2.2 |
| USDJPY | fx | altinda | %-2.8 | 47.0 | %-3.6 | %-5.6 |
| AUDUSD | fx | ustunde | %+3.7 | 20.6 | %+2.2 | %+4.4 |
| USDCAD | fx | altinda | %-0.9 | 24.0 | %-1.0 | %-3.0 |
| USDCHF | fx | ustunde | %+1.0 | 13.2 | %-0.2 | %+0.1 |
| NZDUSD | fx | ustunde | %+0.2 | 23.5 | %-0.4 | %+3.2 |
| EURJPY | fx | altinda | %-2.2 | 31.7 | %-2.9 | %-3.9 |
| GBPJPY | fx | altinda | %-1.9 | 31.5 | %-3.4 | %-3.5 |
| XAUUSD | emtia | ustunde | %+2.0 | 19.9 | %+0.8 | %+9.8 |
| XAGUSD | emtia | ustunde | %+3.7 | 20.6 | %+4.9 | %+16.8 |
| WTI | emtia | ustunde | %+19.7 | 20.7 | %+15.4 | %+35.8 |
| BTCUSDT | kripto | ustunde | %+7.0 | 47.6 | %+7.2 | %+17.7 |

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
