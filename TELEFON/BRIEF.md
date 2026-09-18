# Seans brifingi (olgu)

Uretim: **2026-09-18 20:06 TR** / 2026-09-18 17:06 UTC  
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

- Tokyo: kapali, acilisa 6.9 saat
- Londra: kapali, acilisa 13.9 saat
- New York: ACIK, kapanisa 3.9 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29728  (bar 2026-09-18 16:45:00 UTC)
- dun araligi: 28958 → 29498
- bugun araligi: 29648 → 29967
- 200EMA (gunluk): 27596  (uzaklik +2131.7 / %+7.72)
- ATR(14) son kapali gun: 449.49  (100 gunun %7. yuzdeligi)
- hacim (son kapali gun): 167,542  (20 gunun %0. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-07-23  29365  (direnc)
  - 2026-07-31  27202  (destek)
  - 2026-08-07  30074  (direnc)
  - 2026-08-19  30343  (direnc)
  - 2026-08-26  28947  (destek)
  - 2026-09-01  29812  (direnc)
  - 2026-09-04  28927  (destek)
  - 2026-09-10  29765  (direnc)

### XAUUSD (5m)

- son kapanis: 4420.6  (bar 2026-09-18 16:55:00 UTC)
- dun araligi: 4294.5 → 4423.3
- bugun araligi: 4372.2 → 4439.8
- 200EMA (gunluk): 4345.6  (uzaklik +74.982 / %+1.73)
- ATR(14) son kapali gun: 111.84  (100 gunun %45. yuzdeligi)
- hacim (son kapali gun): 249,081  (20 gunun %89. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-07-31  3993.8  (destek)
  - 2026-08-04  4170.7  (direnc)
  - 2026-08-17  4509.1  (direnc)
  - 2026-08-18  4365.5  (destek)
  - 2026-08-21  4378  (destek)
  - 2026-08-27  4755  (direnc)
  - 2026-09-04  4329.2  (destek)
  - 2026-09-08  4558.5  (direnc)

### EURUSD (5m)

- son kapanis: 1.1481  (bar 2026-09-18 17:05:00 UTC)
- dun araligi: 1.1457 → 1.1498
- bugun araligi: 1.1459 → 1.1496
- 200EMA (gunluk): 1.1569  (uzaklik -0.0087984 / %-0.76)
- ATR(14) son kapali gun: 0.0052517  (100 gunun %16. yuzdeligi)
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

- son kapanis: 1.3385  (bar 2026-09-18 17:05:00 UTC)
- dun araligi: 1.3338 → 1.3407
- bugun araligi: 1.3337 → 1.3386
- 200EMA (gunluk): 1.3428  (uzaklik -0.0042501 / %-0.32)
- ATR(14) son kapali gun: 0.0067095  (100 gunun %12. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+6.6 | 14.2 | %-0.2 | %-0.1 |
| SP500 | endeks | ustunde | %+5.4 | 15.5 | %-1.2 | %+1.5 |
| US30 | endeks | ustunde | %+2.8 | 22.4 | %-3.2 | %-1.6 |
| US2000 | endeks | ustunde | %+3.3 | 33.7 | %-5.4 | %-3.2 |
| GER40 | endeks | ustunde | %+3.4 | 20.6 | %-1.0 | %+2.4 |
| UK100 | endeks | ustunde | %+4.5 | 16.7 | %+0.7 | %+3.1 |
| FRA40 | endeks | altinda | %-0.7 | 40.3 | %-3.1 | %-1.7 |
| JAP225 | endeks | ustunde | %+8.0 | 12.0 | %-1.6 | %-3.8 |
| EURUSD | fx | altinda | %-0.9 | 23.8 | %-1.7 | %+0.4 |
| GBPUSD | fx | altinda | %-0.4 | 19.3 | %-1.6 | %-0.1 |
| USDJPY | fx | altinda | %-1.0 | 45.2 | %-1.4 | %-4.0 |
| AUDUSD | fx | ustunde | %+1.6 | 18.6 | %-0.5 | %+2.2 |
| USDCAD | fx | ustunde | %+0.7 | 20.9 | %+1.3 | %-1.3 |
| USDCHF | fx | ustunde | %+2.9 | 17.4 | %+3.5 | %+2.1 |
| NZDUSD | fx | altinda | %-2.1 | 33.1 | %-3.6 | %+0.1 |
| EURJPY | fx | altinda | %-1.9 | 39.3 | %-3.1 | %-3.6 |
| GBPJPY | fx | altinda | %-1.4 | 39.9 | %-3.0 | %-4.1 |
| XAUUSD | emtia | ustunde | %+1.0 | 17.8 | %-3.2 | %+7.8 |
| XAGUSD | emtia | ustunde | %+0.1 | 14.9 | %-0.4 | %+12.6 |
| WTI | emtia | ustunde | %+25.0 | 33.2 | %+18.7 | %+38.6 |
| BTCUSDT | kripto | ustunde | %+4.1 | 40.6 | %-1.8 | %+19.4 |

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
