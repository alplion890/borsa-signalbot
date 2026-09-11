# Seans brifingi (olgu)

Uretim: **2026-09-11 20:01 TR** / 2026-09-11 17:01 UTC  
Kaynak: bulut feed (yfinance/Binance). Otomatik uretilir; yalniz olcum basar.

> **Fiyatlar endeks kotasyonu, broker fiyati DEGIL.** ^NDX ile MavenTrade US100 arasinda olculmus basis ~-170 puan (2026-08-24). Buradaki seviyeleri dogrudan emir fiyati olarak kullanma; terminaldeki fiyatla farki kendin hesapla.

## Sistem durumu

### Mekanik ray (dondurulmus -- yeni modul/parametre yok)

- **SWEEP_CORE_AVOID_MID_VWAP**: n=10, exp_R=+0.613, esige 15 islem

### Diskresyoner ray (birincil)

- acik aday: 0, pas: 0
- Kapanmis islem yok (defter bos).

## Takvim

- BUGUN CPI duyuru 08:30 ET
- 2026-09-16  FOMC

## Seans

- Tokyo: kapali, acilisa 7.0 saat
- Londra: kapali, acilisa 14.0 saat
- New York: ACIK, kapanisa 4.0 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29420  (bar 2026-09-11 16:45:00 UTC)
- dun araligi: 29043 → 29508
- bugun araligi: 29040 → 29500
- 200EMA (gunluk): 27523  (uzaklik +1897.7 / %+6.90)
- ATR(14) son kapali gun: 440.5  (100 gunun %1. yuzdeligi)
- hacim (son kapali gun): 497,007  (20 gunun %47. yuzdeligi)
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

- son kapanis: 4403.3  (bar 2026-09-11 16:50:00 UTC)
- dun araligi: 4330.7 → 4420
- bugun araligi: 4333 → 4444.9
- 200EMA (gunluk): 4319  (uzaklik +84.345 / %+1.95)
- ATR(14) son kapali gun: 76.368  (100 gunun %27. yuzdeligi)
- hacim (son kapali gun): 86  (20 gunun %11. yuzdeligi)
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

- son kapanis: 1.1601  (bar 2026-09-11 17:00:00 UTC)
- dun araligi: 1.1593 → 1.1643
- bugun araligi: 1.1574 → 1.1621
- 200EMA (gunluk): 1.157  (uzaklik +0.0030568 / %+0.26)
- ATR(14) son kapali gun: 0.0047473  (100 gunun %1. yuzdeligi)
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

- son kapanis: 1.3522  (bar 2026-09-11 17:00:00 UTC)
- dun araligi: 1.3493 → 1.3561
- bugun araligi: 1.3484 → 1.3534
- 200EMA (gunluk): 1.3425  (uzaklik +0.0097298 / %+0.72)
- ATR(14) son kapali gun: 0.0062077  (100 gunun %1. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+5.8 | 12.1 | %-2.4 | %-4.5 |
| SP500 | endeks | ustunde | %+5.1 | 12.5 | %-2.2 | %+0.7 |
| US30 | endeks | ustunde | %+3.6 | 15.1 | %-3.3 | %-1.1 |
| US2000 | endeks | ustunde | %+4.1 | 23.8 | %-5.2 | %-5.0 |
| GER40 | endeks | ustunde | %+2.1 | 19.2 | %-3.6 | %-0.9 |
| UK100 | endeks | ustunde | %+2.7 | 16.4 | %-2.1 | %+1.2 |
| FRA40 | endeks | altinda | %-1.6 | 35.9 | %-6.2 | %-4.2 |
| JAP225 | endeks | ustunde | %+7.0 | 12.0 | %-6.3 | %-9.8 |
| EURUSD | fx | ustunde | %+0.6 | 26.1 | %+0.9 | %+2.2 |
| GBPUSD | fx | ustunde | %+1.0 | 19.6 | %+0.4 | %+2.1 |
| USDJPY | fx | altinda | %-2.7 | 47.6 | %-3.6 | %-5.5 |
| AUDUSD | fx | ustunde | %+3.7 | 19.2 | %+2.2 | %+4.8 |
| USDCAD | fx | altinda | %-0.7 | 23.3 | %-1.0 | %-2.9 |
| USDCHF | fx | ustunde | %+1.1 | 13.0 | %-0.4 | %+0.1 |
| NZDUSD | fx | altinda | %-0.0 | 24.7 | %-0.3 | %+3.0 |
| EURJPY | fx | altinda | %-2.1 | 33.5 | %-2.7 | %-3.4 |
| GBPJPY | fx | altinda | %-1.8 | 33.4 | %-3.2 | %-3.6 |
| XAUUSD | emtia | ustunde | %+0.7 | 19.5 | %-1.0 | %+8.5 |
| XAGUSD | emtia | altinda | %-1.9 | 19.1 | %-1.9 | %+8.1 |
| WTI | emtia | ustunde | %+27.4 | 23.2 | %+23.1 | %+47.5 |
| BTCUSDT | kripto | ustunde | %+4.6 | 46.3 | %-2.3 | %+15.8 |

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
