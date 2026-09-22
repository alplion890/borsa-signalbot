# Seans brifingi (olgu)

Uretim: **2026-09-22 21:57 TR** / 2026-09-22 18:57 UTC  
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

- Tokyo: kapali, acilisa 5.1 saat
- Londra: kapali, acilisa 12.1 saat
- New York: ACIK, kapanisa 2.1 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 30984  (bar 2026-09-22 18:45:00 UTC)
- dun araligi: 29904 → 30863
- bugun araligi: 30670 → 31010
- 200EMA (gunluk): 27645  (uzaklik +3339 / %+12.08)
- ATR(14) son kapali gun: 497.51  (100 gunun %36. yuzdeligi)
- hacim (son kapali gun): 512,823  (20 gunun %53. yuzdeligi)
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

- son kapanis: 4390.8  (bar 2026-09-22 18:45:00 UTC)
- dun araligi: 4360.3 → 4422.1
- bugun araligi: 4327.6 → 4414.1
- 200EMA (gunluk): 4348.2  (uzaklik +42.603 / %+0.98)
- ATR(14) son kapali gun: 105.53  (100 gunun %29. yuzdeligi)
- hacim (son kapali gun): 142,919  (20 gunun %5. yuzdeligi)
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

- son kapanis: 1.1444  (bar 2026-09-22 18:55:00 UTC)
- dun araligi: 1.1467 → 1.1495
- bugun araligi: 1.1432 → 1.1481
- 200EMA (gunluk): 1.1567  (uzaklik -0.012246 / %-1.06)
- ATR(14) son kapali gun: 0.004979  (100 gunun %4. yuzdeligi)
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

- son kapanis: 1.3333  (bar 2026-09-22 18:55:00 UTC)
- dun araligi: 1.3369 → 1.3399
- bugun araligi: 1.3322 → 1.3388
- 200EMA (gunluk): 1.3426  (uzaklik -0.0093222 / %-0.69)
- ATR(14) son kapali gun: 0.0063879  (100 gunun %7. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+11.2 | 14.9 | %+4.8 | %+2.5 |
| SP500 | endeks | ustunde | %+7.9 | 16.0 | %+1.8 | %+2.8 |
| US30 | endeks | ustunde | %+4.1 | 24.1 | %-1.6 | %-0.8 |
| US2000 | endeks | ustunde | %+4.0 | 35.2 | %-4.1 | %-3.2 |
| GER40 | endeks | ustunde | %+2.7 | 21.1 | %-2.0 | %+1.8 |
| UK100 | endeks | ustunde | %+3.7 | 15.5 | %-0.7 | %+2.3 |
| FRA40 | endeks | altinda | %-1.3 | 40.8 | %-3.7 | %-2.7 |
| JAP225 | endeks | ustunde | %+9.8 | 11.2 | %+0.3 | %-4.2 |
| EURUSD | fx | altinda | %-0.8 | 25.6 | %-1.7 | %+0.7 |
| GBPUSD | fx | altinda | %-0.3 | 21.8 | %-1.9 | %+0.0 |
| USDJPY | fx | altinda | %-0.4 | 39.1 | %-1.2 | %-3.0 |
| AUDUSD | fx | ustunde | %+2.1 | 19.0 | %-0.7 | %+2.6 |
| USDCAD | fx | ustunde | %+0.7 | 22.6 | %+1.5 | %-1.2 |
| USDCHF | fx | ustunde | %+2.5 | 20.1 | %+2.8 | %+1.6 |
| NZDUSD | fx | altinda | %-2.0 | 36.7 | %-4.3 | %-0.6 |
| EURJPY | fx | altinda | %-1.2 | 35.4 | %-2.9 | %-2.3 |
| GBPJPY | fx | altinda | %-0.7 | 37.1 | %-3.1 | %-3.0 |
| XAUUSD | emtia | ustunde | %+0.5 | 15.5 | %-6.3 | %+6.6 |
| XAGUSD | emtia | ustunde | %+0.5 | 14.7 | %-5.2 | %+10.1 |
| WTI | emtia | ustunde | %+17.0 | 33.4 | %+10.0 | %+34.1 |
| BTCUSDT | kripto | ustunde | %+17.5 | 43.2 | %+11.9 | %+36.3 |

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
