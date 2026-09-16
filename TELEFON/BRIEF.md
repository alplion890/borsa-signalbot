# Seans brifingi (olgu)

Uretim: **2026-09-16 20:38 TR** / 2026-09-16 17:38 UTC  
Kaynak: bulut feed (yfinance/Binance). Otomatik uretilir; yalniz olcum basar.

> **Fiyatlar endeks kotasyonu, broker fiyati DEGIL.** ^NDX ile MavenTrade US100 arasinda olculmus basis ~-170 puan (2026-08-24). Buradaki seviyeleri dogrudan emir fiyati olarak kullanma; terminaldeki fiyatla farki kendin hesapla.

## Sistem durumu

### Mekanik ray (dondurulmus -- yeni modul/parametre yok)

- **SWEEP_CORE_AVOID_MID_VWAP**: n=10, exp_R=+0.613, esige 15 islem

### Diskresyoner ray (birincil)

- acik aday: 0, pas: 0
- Kapanmis islem yok (defter bos).

## Takvim

- BUGUN FOMC duyuru 14:00 ET
- Onumuzdeki 7 gunde FOMC/CPI/NFP yok.

## Seans

- Tokyo: kapali, acilisa 6.4 saat
- Londra: kapali, acilisa 13.4 saat
- New York: ACIK, kapanisa 3.4 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29452  (bar 2026-09-16 17:15:00 UTC)
- dun araligi: 28919 → 29200
- bugun araligi: 29226 → 29550
- 200EMA (gunluk): 27559  (uzaklik +1892.5 / %+6.87)
- ATR(14) son kapali gun: 438.95  (100 gunun %1. yuzdeligi)
- hacim (son kapali gun): 511,803  (20 gunun %37. yuzdeligi)
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

- son kapanis: 4387.7  (bar 2026-09-16 17:25:00 UTC)
- dun araligi: 4301.6 → 4358.2
- bugun araligi: 4315.2 → 4405.2
- 200EMA (gunluk): 4344.1  (uzaklik +43.568 / %+1.00)
- ATR(14) son kapali gun: 108.28  (100 gunun %32. yuzdeligi)
- hacim (son kapali gun): 164,499  (20 gunun %26. yuzdeligi)
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

- son kapanis: 1.1537  (bar 2026-09-16 17:35:00 UTC)
- dun araligi: 1.1528 → 1.1553
- bugun araligi: 1.1534 → 1.1559
- 200EMA (gunluk): 1.157  (uzaklik -0.0033629 / %-0.29)
- ATR(14) son kapali gun: 0.00523  (100 gunun %12. yuzdeligi)
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

- son kapanis: 1.3444  (bar 2026-09-16 17:35:00 UTC)
- dun araligi: 1.3465 → 1.3503
- bugun araligi: 1.344 → 1.3495
- 200EMA (gunluk): 1.3427  (uzaklik +0.0017163 / %+0.13)
- ATR(14) son kapali gun: 0.0062345  (100 gunun %2. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+5.0 | 13.4 | %-3.8 | %-3.3 |
| SP500 | endeks | ustunde | %+4.8 | 13.4 | %-2.3 | %-0.0 |
| US30 | endeks | ustunde | %+3.5 | 18.3 | %-2.7 | %-2.4 |
| US2000 | endeks | ustunde | %+3.2 | 29.7 | %-6.3 | %-5.1 |
| GER40 | endeks | ustunde | %+2.2 | 21.1 | %-2.8 | %-0.2 |
| UK100 | endeks | ustunde | %+3.1 | 17.7 | %-0.6 | %+0.1 |
| FRA40 | endeks | altinda | %-1.9 | 40.2 | %-4.9 | %-4.1 |
| JAP225 | endeks | ustunde | %+5.8 | 13.1 | %-8.1 | %-9.4 |
| EURUSD | fx | altinda | %-0.2 | 23.3 | %-0.3 | %+0.9 |
| GBPUSD | fx | ustunde | %+0.5 | 17.6 | %-0.4 | %+0.8 |
| USDJPY | fx | altinda | %-2.1 | 47.6 | %-3.1 | %-4.8 |
| AUDUSD | fx | ustunde | %+2.4 | 17.8 | %+0.4 | %+2.6 |
| USDCAD | fx | ustunde | %+0.0 | 20.5 | %+0.2 | %-2.2 |
| USDCHF | fx | ustunde | %+1.9 | 14.8 | %+0.8 | %+1.5 |
| NZDUSD | fx | altinda | %-1.2 | 29.3 | %-2.2 | %+1.4 |
| EURJPY | fx | altinda | %-2.3 | 38.0 | %-3.4 | %-3.9 |
| GBPJPY | fx | altinda | %-1.6 | 38.2 | %-3.5 | %-4.0 |
| XAUUSD | emtia | altinda | %-0.6 | 20.1 | %-3.1 | %+4.0 |
| XAGUSD | emtia | altinda | %-3.4 | 16.8 | %-4.4 | %+2.1 |
| WTI | emtia | ustunde | %+30.5 | 30.1 | %+25.2 | %+54.4 |
| BTCUSDT | kripto | ustunde | %+2.9 | 42.4 | %-4.3 | %+18.6 |

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
