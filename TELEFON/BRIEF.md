# Seans brifingi (olgu)

Uretim: **2026-09-25 22:17 TR** / 2026-09-25 19:17 UTC  
Kaynak: bulut feed (yfinance/Binance). Otomatik uretilir; yalniz olcum basar.

> **Fiyatlar endeks kotasyonu, broker fiyati DEGIL.** ^NDX ile MavenTrade US100 arasinda olculmus basis ~-170 puan (2026-08-24). Buradaki seviyeleri dogrudan emir fiyati olarak kullanma; terminaldeki fiyatla farki kendin hesapla.

## Sistem durumu

### Mekanik ray (dondurulmus -- yeni modul/parametre yok)

- **SWEEP_CORE_AVOID_MID_VWAP**: n=12, exp_R=+0.302, esige 13 islem

### Diskresyoner ray (birincil)

- acik aday: 0, pas: 0
- Kapanmis islem yok (defter bos).

## Takvim

- Bugun FOMC/CPI/NFP yok.
- 2026-10-02  NFP

## Seans

- Tokyo: kapali, acilisa 4.7 saat
- Londra: kapali, acilisa 11.7 saat
- New York: ACIK, kapanisa 1.7 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 30881  (bar 2026-09-25 19:00:00 UTC)
- dun araligi: 30370 → 30828
- bugun araligi: 30679 → 31000
- 200EMA (gunluk): 27746  (uzaklik +3135 / %+11.30)
- ATR(14) son kapali gun: 485.35  (100 gunun %23. yuzdeligi)
- hacim (son kapali gun): 543,487  (20 gunun %58. yuzdeligi)
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

- son kapanis: 4327.3  (bar 2026-09-25 19:05:00 UTC)
- dun araligi: 4278.3 → 4338
- bugun araligi: 4289.2 → 4351.6
- 200EMA (gunluk): 4348.3  (uzaklik -20.959 / %-0.48)
- ATR(14) son kapali gun: 100.51  (100 gunun %15. yuzdeligi)
- hacim (son kapali gun): 143,873  (20 gunun %16. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-08-17  4509.1  (direnc)
  - 2026-08-18  4365.5  (destek)
  - 2026-08-21  4378  (destek)
  - 2026-08-27  4755  (direnc)
  - 2026-09-04  4329.2  (destek)
  - 2026-09-08  4558.5  (direnc)
  - 2026-09-18  4273.3  (destek)
  - 2026-09-22  4439.8  (direnc)

### EURUSD (5m)

- son kapanis: 1.1404  (bar 2026-09-25 19:15:00 UTC)
- dun araligi: 1.136 → 1.14
- bugun araligi: 1.1371 → 1.1413
- 200EMA (gunluk): 1.1563  (uzaklik -0.015891 / %-1.37)
- ATR(14) son kapali gun: 0.005447  (100 gunun %31. yuzdeligi)
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

- son kapanis: 1.3254  (bar 2026-09-25 19:15:00 UTC)
- dun araligi: 1.3211 → 1.3256
- bugun araligi: 1.321 → 1.3263
- 200EMA (gunluk): 1.3423  (uzaklik -0.016902 / %-1.26)
- ATR(14) son kapali gun: 0.0072622  (100 gunun %28. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+10.8 | 18.2 | %+5.0 | %+3.6 |
| SP500 | endeks | ustunde | %+6.8 | 14.7 | %+1.0 | %+2.0 |
| US30 | endeks | ustunde | %+2.5 | 23.4 | %-3.4 | %-2.2 |
| US2000 | endeks | ustunde | %+2.4 | 34.1 | %-5.1 | %-4.5 |
| GER40 | endeks | ustunde | %+1.4 | 20.7 | %-4.2 | %+1.4 |
| UK100 | endeks | ustunde | %+3.0 | 14.9 | %-1.8 | %+1.6 |
| FRA40 | endeks | altinda | %-1.9 | 39.9 | %-2.9 | %-3.5 |
| JAP225 | endeks | ustunde | %+8.9 | 10.2 | %-0.4 | %-3.0 |
| EURUSD | fx | altinda | %-1.6 | 31.0 | %-2.3 | %-0.8 |
| GBPUSD | fx | altinda | %-1.4 | 27.6 | %-2.6 | %-2.2 |
| USDJPY | fx | ustunde | %+0.4 | 33.5 | %-0.6 | %-2.3 |
| AUDUSD | fx | ustunde | %+0.7 | 23.7 | %-2.1 | %+0.4 |
| USDCAD | fx | ustunde | %+1.4 | 27.8 | %+1.7 | %+0.5 |
| USDCHF | fx | ustunde | %+2.7 | 22.1 | %+2.5 | %+2.5 |
| NZDUSD | fx | altinda | %-2.8 | 42.7 | %-4.6 | %-3.0 |
| EURJPY | fx | altinda | %-1.2 | 31.1 | %-2.9 | %-3.1 |
| GBPJPY | fx | altinda | %-1.0 | 34.4 | %-3.2 | %-4.5 |
| XAUUSD | emtia | altinda | %-1.5 | 15.0 | %-7.6 | %+6.1 |
| XAGUSD | emtia | altinda | %-3.1 | 13.1 | %-6.7 | %+11.1 |
| WTI | emtia | ustunde | %+15.0 | 28.5 | %+15.1 | %+18.9 |
| BTCUSDT | kripto | ustunde | %+13.9 | 44.3 | %+6.0 | %+30.5 |

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
