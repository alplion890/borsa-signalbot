# Seans brifingi (olgu)

Uretim: **2026-09-09 20:37 TR** / 2026-09-09 17:37 UTC  
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

- Tokyo: kapali, acilisa 6.4 saat
- Londra: kapali, acilisa 13.4 saat
- New York: ACIK, kapanisa 3.4 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29465  (bar 2026-09-09 17:15:00 UTC)
- dun araligi: 29425 → 29765
- bugun araligi: 29333 → 29634
- 200EMA (gunluk): 27482  (uzaklik +1982.8 / %+7.21)
- ATR(14) son kapali gun: 449.21  (100 gunun %1. yuzdeligi)
- hacim: BU FEED HACIM VERMIYOR (spot FX) -- hacim katmani brifingten doldurulamaz
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

- son kapanis: 4465.3  (bar 2026-09-09 17:25:00 UTC)
- dun araligi: 4384.4 → 4406.1
- bugun araligi: 4384.1 → 4479
- 200EMA (gunluk): 4317.3  (uzaklik +147.99 / %+3.43)
- ATR(14) son kapali gun: 79.472  (100 gunun %41. yuzdeligi)
- hacim: BU FEED HACIM VERMIYOR (spot FX) -- hacim katmani brifingten doldurulamaz
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

- son kapanis: 1.1641  (bar 2026-09-09 17:35:00 UTC)
- dun araligi: 1.1609 → 1.1636
- bugun araligi: 1.1624 → 1.1656
- 200EMA (gunluk): 1.1569  (uzaklik +0.007217 / %+0.62)
- ATR(14) son kapali gun: 0.0048462  (100 gunun %0. yuzdeligi)
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

- son kapanis: 1.3559  (bar 2026-09-09 17:35:00 UTC)
- dun araligi: 1.3523 → 1.3562
- bugun araligi: 1.3531 → 1.3568
- 200EMA (gunluk): 1.3423  (uzaklik +0.013613 / %+1.01)
- ATR(14) son kapali gun: 0.006343  (100 gunun %0. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+7.4 | 12.7 | %-0.7 | %+0.6 |
| SP500 | endeks | ustunde | %+6.3 | 11.8 | %-1.2 | %+3.8 |
| US30 | endeks | ustunde | %+5.1 | 13.1 | %-2.3 | %+1.2 |
| US2000 | endeks | ustunde | %+6.7 | 20.3 | %-2.0 | %-2.0 |
| GER40 | endeks | ustunde | %+4.7 | 18.8 | %-1.5 | %+4.0 |
| UK100 | endeks | ustunde | %+4.7 | 15.0 | %-0.5 | %+3.1 |
| FRA40 | endeks | ustunde | %+0.8 | 32.5 | %-4.6 | %-1.0 |
| JAP225 | endeks | ustunde | %+9.0 | 12.7 | %-2.2 | %-6.4 |
| EURUSD | fx | ustunde | %+0.5 | 27.6 | %+0.7 | %+1.8 |
| GBPUSD | fx | ustunde | %+0.9 | 21.7 | %+0.3 | %+2.2 |
| USDJPY | fx | altinda | %-2.6 | 45.2 | %-3.3 | %-5.0 |
| AUDUSD | fx | ustunde | %+3.7 | 19.9 | %+2.3 | %+4.9 |
| USDCAD | fx | altinda | %-0.7 | 24.3 | %-0.9 | %-2.8 |
| USDCHF | fx | ustunde | %+1.0 | 13.9 | %-0.1 | %+0.2 |
| NZDUSD | fx | ustunde | %+0.6 | 22.9 | %-0.1 | %+4.1 |
| EURJPY | fx | altinda | %-2.0 | 29.0 | %-2.6 | %-3.2 |
| GBPJPY | fx | altinda | %-1.6 | 28.8 | %-3.1 | %-2.9 |
| XAUUSD | emtia | ustunde | %+1.5 | 21.0 | %+0.7 | %+7.7 |
| XAGUSD | emtia | ustunde | %+1.3 | 20.9 | %+1.8 | %+12.0 |
| WTI | emtia | ustunde | %+16.1 | 19.1 | %+13.3 | %+34.4 |
| BTCUSDT | kripto | ustunde | %+7.4 | 47.9 | %+13.2 | %+20.2 |

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
