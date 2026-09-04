# Seans brifingi (olgu)

Uretim: **2026-09-04 13:08 TR** / 2026-09-04 10:08 UTC  
Kaynak: bulut feed (yfinance/Binance). Otomatik uretilir; yalniz olcum basar.

> **Fiyatlar endeks kotasyonu, broker fiyati DEGIL.** ^NDX ile MavenTrade US100 arasinda olculmus basis ~-170 puan (2026-08-24). Buradaki seviyeleri dogrudan emir fiyati olarak kullanma; terminaldeki fiyatla farki kendin hesapla.

## Sistem durumu

### Mekanik ray (dondurulmus -- yeni modul/parametre yok)

- **NQ_ORB_STRONG_TREND**: n=25, exp_R=-0.106, esikte
- **SWEEP_CORE_AVOID_MID_VWAP**: n=10, exp_R=+0.613, esige 15 islem

### Diskresyoner ray (birincil)

- acik aday: 0, pas: 0
- Kapanmis islem yok (defter bos).

## Takvim

- BUGUN NFP duyuru 08:30 ET
- 2026-09-11  CPI

## Seans

- Tokyo: kapali, acilisa 13.9 saat
- Londra: ACIK, kapanisa 5.9 saat
- New York: kapali, acilisa 2.9 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29658  (bar 2026-09-04 09:45:00 UTC)
- dun araligi: 29075 → 29584
- bugun araligi: 29482 → 29673
- 200EMA (gunluk): 27435  (uzaklik +2222.8 / %+8.10)
- ATR(14) son kapali gun: 474.62  (100 gunun %13. yuzdeligi)
- hacim (son kapali gun): 442,250  (20 gunun %21. yuzdeligi)
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

- son kapanis: 4513.4  (bar 2026-09-04 09:55:00 UTC)
- dun araligi: 4426 → 4510
- bugun araligi: 4506.6 → 4537.8
- 200EMA (gunluk): 4314.7  (uzaklik +198.7 / %+4.61)
- ATR(14) son kapali gun: 83.646  (100 gunun %52. yuzdeligi)
- hacim (son kapali gun): 72  (20 gunun %0. yuzdeligi)
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

- son kapanis: 1.1623  (bar 2026-09-04 10:05:00 UTC)
- dun araligi: 1.1585 → 1.1629
- bugun araligi: 1.162 → 1.1636
- 200EMA (gunluk): 1.1568  (uzaklik +0.0054643 / %+0.47)
- ATR(14) son kapali gun: 0.0052211  (100 gunun %4. yuzdeligi)
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

- son kapanis: 1.3525  (bar 2026-09-04 10:05:00 UTC)
- dun araligi: 1.3481 → 1.3543
- bugun araligi: 1.3523 → 1.3548
- 200EMA (gunluk): 1.342  (uzaklik +0.010512 / %+0.78)
- ATR(14) son kapali gun: 0.0066596  (100 gunun %1. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+7.5 | 14.6 | %+0.1 | %+0.0 |
| SP500 | endeks | ustunde | %+7.5 | 12.9 | %+0.3 | %+4.4 |
| US30 | endeks | ustunde | %+7.1 | 13.9 | %-0.5 | %+2.8 |
| US2000 | endeks | ustunde | %+7.1 | 19.0 | %-1.3 | %-1.5 |
| GER40 | endeks | ustunde | %+4.9 | 22.6 | %-0.5 | %+4.0 |
| UK100 | endeks | ustunde | %+5.1 | 17.8 | %-0.5 | %+3.5 |
| FRA40 | endeks | ustunde | %+0.4 | 29.2 | %-4.8 | %-1.7 |
| JAP225 | endeks | ustunde | %+8.2 | 14.0 | %-1.5 | %-6.9 |
| EURUSD | fx | ustunde | %+0.2 | 30.1 | %+0.2 | %+2.0 |
| GBPUSD | fx | ustunde | %+0.5 | 25.4 | %+0.1 | %+2.4 |
| USDJPY | fx | ustunde | %+0.6 | 40.2 | %+0.8 | %-1.8 |
| AUDUSD | fx | ustunde | %+3.0 | 18.8 | %+1.5 | %+3.8 |
| USDCAD | fx | altinda | %-0.4 | 26.7 | %-1.2 | %-2.7 |
| USDCHF | fx | ustunde | %+1.5 | 16.8 | %+0.8 | %+0.0 |
| NZDUSD | fx | ustunde | %+0.1 | 22.4 | %-0.6 | %+3.7 |
| EURJPY | fx | ustunde | %+0.8 | 20.7 | %+1.1 | %+0.2 |
| GBPJPY | fx | ustunde | %+1.1 | 20.8 | %+0.9 | %+0.6 |
| XAUUSD | emtia | ustunde | %+3.8 | 23.7 | %+5.9 | %+12.6 |
| XAGUSD | emtia | ustunde | %+2.4 | 23.7 | %+9.0 | %+15.4 |
| WTI | emtia | ustunde | %+14.4 | 16.9 | %+18.1 | %+29.8 |
| BTCUSDT | kripto | ustunde | %+11.8 | 45.2 | %+28.9 | %+25.5 |

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
