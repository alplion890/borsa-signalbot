# Seans brifingi (olgu)

Uretim: **2026-09-12 16:51 TR** / 2026-09-12 13:51 UTC  
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
- 2026-09-16  FOMC

## Seans

- Tokyo: kapali, acilisa 10.2 saat
- Londra: ACIK, kapanisa 2.2 saat
- New York: ACIK, kapanisa 7.2 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29387  (bar 2026-09-11 20:45:00 UTC)
- dun araligi: 29040 → 29500
- bugun araligi: henuz bar yok
- 200EMA (gunluk): 27541  (uzaklik +1845.9 / %+6.70)
- ATR(14) son kapali gun: 441.87  (100 gunun %2. yuzdeligi)
- hacim (son kapali gun): 568,263  (20 gunun %68. yuzdeligi)
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

- son kapanis: 4408.9  (bar 2026-09-11 20:55:00 UTC)
- dun araligi: 4365.8 → 4389.5
- bugun araligi: henuz bar yok
- 200EMA (gunluk): 4319.4  (uzaklik +89.475 / %+2.07)
- ATR(14) son kapali gun: 72.699  (100 gunun %10. yuzdeligi)
- hacim (son kapali gun): 73  (20 gunun %11. yuzdeligi)
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

- son kapanis: 1.1602  (bar 2026-09-11 21:25:00 UTC)
- dun araligi: 1.1574 → 1.1621
- bugun araligi: henuz bar yok
- 200EMA (gunluk): 1.1571  (uzaklik +0.003161 / %+0.27)
- ATR(14) son kapali gun: 0.0048352  (100 gunun %2. yuzdeligi)
- hacim: BU FEED HACIM VERMIYOR (spot FX) -- hacim katmani brifingten doldurulamaz
- donus seviyeleri (son 60 gun):
  - 2026-07-27  1.1438  (direnc)
  - 2026-07-30  1.1354  (destek)
  - 2026-08-11  1.1518  (destek)
  - 2026-08-11  1.1579  (direnc)
  - 2026-08-17  1.1513  (destek)
  - 2026-08-25  1.1712  (direnc)
  - 2026-09-04  1.1567  (destek)
  - 2026-09-11  1.1654  (direnc)

### GBPUSD (5m)

- son kapanis: 1.3529  (bar 2026-09-11 21:25:00 UTC)
- dun araligi: 1.3484 → 1.3534
- bugun araligi: henuz bar yok
- 200EMA (gunluk): 1.3426  (uzaklik +0.010265 / %+0.76)
- ATR(14) son kapali gun: 0.0062511  (100 gunun %2. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+6.7 | 12.2 | %-2.7 | %-2.4 |
| SP500 | endeks | ustunde | %+5.9 | 12.7 | %-2.1 | %+1.5 |
| US30 | endeks | ustunde | %+4.5 | 16.0 | %-2.5 | %-0.2 |
| US2000 | endeks | ustunde | %+4.5 | 25.8 | %-5.1 | %-4.3 |
| GER40 | endeks | ustunde | %+2.9 | 19.6 | %-3.3 | %-0.8 |
| UK100 | endeks | ustunde | %+3.1 | 16.9 | %-1.1 | %-0.0 |
| FRA40 | endeks | altinda | %-0.9 | 37.1 | %-5.3 | %-3.9 |
| JAP225 | endeks | ustunde | %+8.0 | 11.8 | %-6.3 | %-7.1 |
| EURUSD | fx | ustunde | %+0.3 | 24.3 | %+0.6 | %+1.6 |
| GBPUSD | fx | ustunde | %+0.8 | 18.6 | %+0.3 | %+1.4 |
| USDJPY | fx | altinda | %-2.7 | 48.1 | %-3.7 | %-4.9 |
| AUDUSD | fx | ustunde | %+2.7 | 17.9 | %+1.3 | %+3.5 |
| USDCAD | fx | altinda | %-0.5 | 21.7 | %-0.7 | %-2.5 |
| USDCHF | fx | ustunde | %+1.4 | 13.3 | %-0.1 | %+1.1 |
| NZDUSD | fx | altinda | %-0.7 | 25.8 | %-0.8 | %+2.0 |
| EURJPY | fx | altinda | %-1.7 | 35.3 | %-2.5 | %-2.7 |
| GBPJPY | fx | altinda | %-1.9 | 35.3 | %-3.4 | %-3.5 |
| XAUUSD | emtia | ustunde | %+0.8 | 19.2 | %+0.1 | %+7.3 |
| XAGUSD | emtia | altinda | %-1.4 | 18.2 | %-0.5 | %+7.4 |
| WTI | emtia | ustunde | %+24.1 | 25.6 | %+23.1 | %+45.9 |
| BTCUSDT | kripto | ustunde | %+5.5 | 45.6 | %+0.2 | %+18.6 |

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
  - kapsam: XAUUSD 5m ORB modulune. NQ_ORB_STRONG_TREND ayri moduldu; 2026-09-11'de negatif forward sonucuyla tarama/Telegram listesinden cikarildi. 'ORB' kelimesi SWEEP_CORE'u vetolamaz.

---

Bu dosyayi okuyan asistan icin kural seti: `TELEFON/SISTEM.md`.
