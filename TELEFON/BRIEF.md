# Seans brifingi (olgu)

Uretim: **2026-09-21 21:45 TR** / 2026-09-21 18:45 UTC  
Kaynak: bulut feed (yfinance/Binance). Otomatik uretilir; yalniz olcum basar.

> **Fiyatlar endeks kotasyonu, broker fiyati DEGIL.** ^NDX ile MavenTrade US100 arasinda olculmus basis ~-170 puan (2026-08-24). Buradaki seviyeleri dogrudan emir fiyati olarak kullanma; terminaldeki fiyatla farki kendin hesapla.

## Sistem durumu

### Mekanik ray (dondurulmus -- yeni modul/parametre yok)

- **SWEEP_CORE_AVOID_MID_VWAP**: n=11, exp_R=+0.446, esige 14 islem

### Diskresyoner ray (birincil)

- acik aday: 0, pas: 0
- Kapanmis islem yok (defter bos).

## Takvim

- Bugun FOMC/CPI/NFP yok.
- Onumuzdeki 7 gunde FOMC/CPI/NFP yok.

## Seans

- Tokyo: kapali, acilisa 5.2 saat
- Londra: kapali, acilisa 12.2 saat
- New York: ACIK, kapanisa 2.2 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 30744  (bar 2026-09-21 18:30:00 UTC)
- dun araligi: 29353 → 29665
- bugun araligi: 29904 → 30759
- 200EMA (gunluk): 27617  (uzaklik +3127 / %+11.32)
- ATR(14) son kapali gun: 439.7  (100 gunun %2. yuzdeligi)
- hacim (son kapali gun): 74,615  (20 gunun %0. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-07-31  27202  (destek)
  - 2026-08-07  30074  (direnc)
  - 2026-08-19  30343  (direnc)
  - 2026-08-26  28947  (destek)
  - 2026-09-01  29812  (direnc)
  - 2026-09-04  28927  (destek)
  - 2026-09-10  29765  (direnc)
  - 2026-09-18  28764  (destek)

### XAUUSD (5m)

- son kapanis: 4387.9  (bar 2026-09-21 18:35:00 UTC)
- dun araligi: 4372.2 → 4439.8
- bugun araligi: 4360.3 → 4422.1
- 200EMA (gunluk): 4347.1  (uzaklik +40.801 / %+0.94)
- ATR(14) son kapali gun: 108.68  (100 gunun %34. yuzdeligi)
- hacim (son kapali gun): 169,188  (20 gunun %32. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-08-04  4170.7  (direnc)
  - 2026-08-17  4509.1  (direnc)
  - 2026-08-18  4365.5  (destek)
  - 2026-08-21  4378  (destek)
  - 2026-08-27  4755  (direnc)
  - 2026-09-04  4329.2  (destek)
  - 2026-09-08  4558.5  (direnc)
  - 2026-09-18  4273.3  (destek)

### EURUSD (5m)

- son kapanis: 1.1467  (bar 2026-09-21 18:40:00 UTC)
- dun araligi: 1.1456 → 1.1494
- bugun araligi: 1.1465 → 1.1498
- 200EMA (gunluk): 1.1568  (uzaklik -0.010118 / %-0.87)
- ATR(14) son kapali gun: 0.0051531  (100 gunun %10. yuzdeligi)
- hacim: BU FEED HACIM VERMIYOR (spot FX) -- hacim katmani brifingten doldurulamaz
- donus seviyeleri (son 60 gun):
  - 2026-07-30  1.1354  (destek)
  - 2026-08-11  1.1518  (destek)
  - 2026-08-11  1.1579  (direnc)
  - 2026-08-17  1.1513  (destek)
  - 2026-08-25  1.1712  (direnc)
  - 2026-09-04  1.1567  (destek)
  - 2026-09-11  1.1654  (direnc)
  - 2026-09-16  1.1524  (destek)

### GBPUSD (5m)

- son kapanis: 1.3367  (bar 2026-09-21 18:40:00 UTC)
- dun araligi: 1.3337 → 1.3378
- bugun araligi: 1.3365 → 1.34
- 200EMA (gunluk): 1.3427  (uzaklik -0.005938 / %-0.44)
- ATR(14) son kapali gun: 0.0065605  (100 gunun %8. yuzdeligi)
- hacim: BU FEED HACIM VERMIYOR (spot FX) -- hacim katmani brifingten doldurulamaz
- donus seviyeleri (son 60 gun):
  - 2026-07-20  1.3545  (direnc)
  - 2026-07-30  1.3273  (destek)
  - 2026-08-05  1.3501  (direnc)
  - 2026-08-11  1.3435  (destek)
  - 2026-08-17  1.3476  (destek)
  - 2026-08-25  1.3675  (direnc)
  - 2026-09-04  1.3475  (destek)
  - 2026-09-11  1.357  (direnc)

## Trend katmani (sabit tanim, 21 sembol)

200EMA konumu + ADX(14) + 20/50 gunluk degisim, gunluk barlardan. Evrenin TAMAMI on-kayitli sabit sirada listeleniyor. Eleme yok, esik yok, yorum yok.

**Bu liste islem evreni DEGIL.** Portfoy ve modul kumesi degismedi; burada bir sembolun gorunmesi orada calisan bir modul oldugu anlamina gelmez.

| sembol | grup | 200EMA | uzaklik | ADX | 20g | 50g |
|---|---|---|---|---|---|---|
| NASDAQ100 | endeks | ustunde | %+7.1 | 13.6 | %+1.1 | %-1.1 |
| SP500 | endeks | ustunde | %+5.6 | 15.9 | %-0.1 | %+0.9 |
| US30 | endeks | ustunde | %+2.7 | 24.2 | %-2.1 | %-1.9 |
| US2000 | endeks | ustunde | %+3.2 | 35.1 | %-4.2 | %-4.5 |
| GER40 | endeks | ustunde | %+1.7 | 20.9 | %-3.2 | %+0.9 |
| UK100 | endeks | ustunde | %+3.0 | 16.1 | %-0.8 | %+1.8 |
| FRA40 | endeks | altinda | %-2.2 | 40.5 | %-4.9 | %-3.3 |
| JAP225 | endeks | ustunde | %+8.2 | 11.2 | %-0.8 | %-5.3 |
| EURUSD | fx | altinda | %-0.8 | 24.8 | %-1.8 | %+0.4 |
| GBPUSD | fx | altinda | %-0.5 | 21.0 | %-2.1 | %-0.4 |
| USDJPY | fx | altinda | %-0.9 | 42.0 | %-1.7 | %-3.8 |
| AUDUSD | fx | ustunde | %+2.0 | 18.8 | %-0.1 | %+2.5 |
| USDCAD | fx | ustunde | %+0.7 | 21.7 | %+1.5 | %-1.2 |
| USDCHF | fx | ustunde | %+2.8 | 19.1 | %+3.2 | %+2.3 |
| NZDUSD | fx | altinda | %-1.9 | 35.0 | %-3.8 | %-0.6 |
| EURJPY | fx | altinda | %-1.7 | 37.3 | %-3.5 | %-3.5 |
| GBPJPY | fx | altinda | %-1.5 | 38.4 | %-3.8 | %-4.2 |
| XAUUSD | emtia | ustunde | %+1.5 | 16.6 | %-3.2 | %+6.9 |
| XAGUSD | emtia | ustunde | %+1.7 | 15.0 | %-2.2 | %+10.2 |
| WTI | emtia | ustunde | %+22.8 | 34.3 | %+14.2 | %+39.2 |
| BTCUSDT | kripto | ustunde | %+10.2 | 41.9 | %+3.3 | %+29.2 |

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
  - kapsam: Veto YALNIZCA 'ayni kurali 7 endekse yay' genislemesine. Tek- enstruman SWEEP_CORE_AVOID_MID_VWAP ayri bir modul olarak portfoyde kalir; guncel olcumu sistem durumu bolumundedir.
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
  - kapsam: XAUUSD 5m ORB modulune. NQ_ORB_STRONG_TREND ayri moduldu; 2026-09-11'de negatif forward sonucuyla tarama/Telegram listesinden cikarildi. 'ORB' kelimesi SWEEP_CORE'u vetolamaz.

---

Arsiv/denetim ciktisi. AI proje talimati degildir.
