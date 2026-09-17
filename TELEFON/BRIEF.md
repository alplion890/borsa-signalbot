# Seans brifingi (olgu)

Uretim: **2026-09-17 22:05 TR** / 2026-09-17 19:05 UTC  
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
- Onumuzdeki 7 gunde FOMC/CPI/NFP yok.

## Seans

- Tokyo: kapali, acilisa 4.9 saat
- Londra: kapali, acilisa 11.9 saat
- New York: ACIK, kapanisa 1.9 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29724  (bar 2026-09-17 18:45:00 UTC)
- dun araligi: 28764 → 29252
- bugun araligi: 29248 → 29762
- 200EMA (gunluk): 27578  (uzaklik +2146.3 / %+7.78)
- ATR(14) son kapali gun: 442.49  (100 gunun %4. yuzdeligi)
- hacim (son kapali gun): 197,428  (20 gunun %0. yuzdeligi)
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

- son kapanis: 4390.5  (bar 2026-09-17 18:55:00 UTC)
- dun araligi: 4273.3 → 4413.1
- bugun araligi: 4294.5 → 4423.3
- 200EMA (gunluk): 4345  (uzaklik +45.464 / %+1.05)
- ATR(14) son kapali gun: 110.54  (100 gunun %38. yuzdeligi)
- hacim (son kapali gun): 146,019  (20 gunun %5. yuzdeligi)
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

- son kapanis: 1.148  (bar 2026-09-17 19:00:00 UTC)
- dun araligi: 1.1531 → 1.1556
- bugun araligi: 1.146 → 1.1501
- 200EMA (gunluk): 1.157  (uzaklik -0.0090017 / %-0.78)
- ATR(14) son kapali gun: 0.0050334  (100 gunun %5. yuzdeligi)
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

- son kapanis: 1.3355  (bar 2026-09-17 19:00:00 UTC)
- dun araligi: 1.3446 → 1.3495
- bugun araligi: 1.3338 → 1.3406
- 200EMA (gunluk): 1.3428  (uzaklik -0.0073076 / %-0.54)
- ATR(14) son kapali gun: 0.0061834  (100 gunun %1. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+4.9 | 14.3 | %-2.1 | %-1.5 |
| SP500 | endeks | ustunde | %+4.3 | 14.8 | %-2.0 | %+0.1 |
| US30 | endeks | ustunde | %+2.3 | 20.4 | %-3.6 | %-3.2 |
| US2000 | endeks | ustunde | %+2.8 | 32.1 | %-5.4 | %-4.6 |
| GER40 | endeks | ustunde | %+2.7 | 21.3 | %-2.1 | %+2.6 |
| UK100 | endeks | ustunde | %+3.3 | 17.8 | %-0.4 | %+0.2 |
| FRA40 | endeks | altinda | %-1.3 | 40.8 | %-4.2 | %-1.4 |
| JAP225 | endeks | ustunde | %+7.0 | 12.8 | %-3.1 | %-4.9 |
| EURUSD | fx | altinda | %-0.3 | 22.8 | %-0.4 | %+1.2 |
| GBPUSD | fx | ustunde | %+0.3 | 17.6 | %-0.5 | %+0.9 |
| USDJPY | fx | altinda | %-1.5 | 46.9 | %-2.7 | %-4.4 |
| AUDUSD | fx | ustunde | %+2.2 | 17.8 | %+0.6 | %+2.9 |
| USDCAD | fx | ustunde | %+0.2 | 20.2 | %+0.2 | %-2.0 |
| USDCHF | fx | ustunde | %+2.2 | 15.6 | %+0.8 | %+1.3 |
| NZDUSD | fx | altinda | %-1.6 | 31.1 | %-2.1 | %+1.3 |
| EURJPY | fx | altinda | %-1.8 | 38.6 | %-3.0 | %-3.2 |
| GBPJPY | fx | altinda | %-1.2 | 38.9 | %-3.1 | %-3.5 |
| XAUUSD | emtia | ustunde | %+0.7 | 19.0 | %-0.7 | %+5.5 |
| XAGUSD | emtia | altinda | %-1.7 | 15.6 | %+0.5 | %+5.5 |
| WTI | emtia | ustunde | %+26.0 | 32.2 | %+20.6 | %+45.4 |
| BTCUSDT | kripto | ustunde | %+3.8 | 41.3 | %-5.0 | %+19.2 |

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
