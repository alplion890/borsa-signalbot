# Seans brifingi (olgu)

Uretim: **2026-09-02 13:09 TR** / 2026-09-02 10:09 UTC  
Kaynak: bulut feed (yfinance/Binance). Otomatik uretilir; yalniz olcum basar.

> **Fiyatlar endeks kotasyonu, broker fiyati DEGIL.** ^NDX ile MavenTrade US100 arasinda olculmus basis ~-170 puan (2026-08-24). Buradaki seviyeleri dogrudan emir fiyati olarak kullanma; terminaldeki fiyatla farki kendin hesapla.

## Sistem durumu

### Mekanik ray (dondurulmus -- yeni modul/parametre yok)

- **NQ_ORB_STRONG_TREND**: n=24, exp_R=-0.171, esige 1 islem
- **SWEEP_CORE_AVOID_MID_VWAP**: n=10, exp_R=+0.613, esige 15 islem

### Diskresyoner ray (birincil)

- acik aday: 0, pas: 0
- Kapanmis islem yok (defter bos).

## Takvim

- Bugun FOMC/CPI/NFP yok.
- 2026-09-04  NFP

## Seans

- Tokyo: kapali, acilisa 13.8 saat
- Londra: ACIK, kapanisa 5.8 saat
- New York: kapali, acilisa 2.8 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 28974  (bar 2026-09-02 09:45:00 UTC)
- dun araligi: 29002 → 29571
- bugun araligi: 28940 → 29170
- 200EMA (gunluk): 27389  (uzaklik +1585.1 / %+5.79)
- ATR(14) son kapali gun: 486.29  (100 gunun %19. yuzdeligi)
- hacim (son kapali gun): 468,460  (20 gunun %37. yuzdeligi)
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

- son kapanis: 4355.7  (bar 2026-09-02 09:55:00 UTC)
- dun araligi: 4329.1 → 4402
- bugun araligi: 4329.2 → 4382
- 200EMA (gunluk): 4311.7  (uzaklik +43.961 / %+1.02)
- ATR(14) son kapali gun: 77.567  (100 gunun %31. yuzdeligi)
- hacim (son kapali gun): 360  (20 gunun %16. yuzdeligi)
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

- son kapanis: 1.1575  (bar 2026-09-02 10:05:00 UTC)
- dun araligi: 1.1589 → 1.1625
- bugun araligi: 1.1571 → 1.16
- 200EMA (gunluk): 1.1568  (uzaklik +0.00074735 / %+0.06)
- ATR(14) son kapali gun: 0.0053006  (100 gunun %8. yuzdeligi)
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

- son kapanis: 1.3485  (bar 2026-09-02 10:05:00 UTC)
- dun araligi: 1.3525 → 1.3561
- bugun araligi: 1.3484 → 1.352
- 200EMA (gunluk): 1.3419  (uzaklik +0.0065942 / %+0.49)
- ATR(14) son kapali gun: 0.0066334  (100 gunun %0. yuzdeligi)
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

200EMA konumu + ADX(14) + 20/50 gunluk degisim, gunluk barlardan. Evrenin TAMAMI listeleniyor; siralama 20 gunluk degisime gore. Eleme yok, esik yok, yorum yok.

**Bu liste islem evreni DEGIL.** Portfoy ve modul kumesi degismedi; burada bir sembolun gorunmesi orada calisan bir modul oldugu anlamina gelmez.

| sembol | grup | 200EMA | uzaklik | ADX | 20g | 50g |
|---|---|---|---|---|---|---|
| BTCUSDT | kripto | ustunde | %+5.4 | 44.1 | %+20.7 | %+17.8 |
| WTI | emtia | ustunde | %+13.4 | 14.4 | %+20.3 | %+23.6 |
| XAGUSD | emtia | altinda | %-1.8 | 26.3 | %+3.5 | %+3.6 |
| XAUUSD | emtia | ustunde | %+0.7 | 25.9 | %+2.6 | %+5.5 |
| EURJPY | fx | ustunde | %+1.3 | 16.9 | %+1.7 | %+0.6 |
| GBPJPY | fx | ustunde | %+1.7 | 16.8 | %+1.6 | %+1.1 |
| USDJPY | fx | ustunde | %+1.2 | 38.6 | %+1.4 | %-1.1 |
| AUDUSD | fx | ustunde | %+2.5 | 19.8 | %+1.1 | %+3.0 |
| USDCHF | fx | ustunde | %+1.8 | 18.1 | %+0.8 | %+0.7 |
| EURUSD | fx | ustunde | %+0.1 | 33.1 | %+0.4 | %+1.7 |
| GBPUSD | fx | ustunde | %+0.5 | 28.8 | %+0.3 | %+2.2 |
| USDCAD | fx | ustunde | %+0.2 | 28.9 | %-0.9 | %-1.9 |
| NZDUSD | fx | altinda | %-0.6 | 21.5 | %-1.2 | %+2.5 |
| UK100 | endeks | ustunde | %+4.3 | 19.5 | %-1.3 | %+3.0 |
| GER40 | endeks | ustunde | %+4.0 | 25.2 | %-1.4 | %+4.2 |
| SP500 | endeks | ustunde | %+5.8 | 13.4 | %-1.6 | %+2.5 |
| NASDAQ100 | endeks | ustunde | %+5.6 | 14.8 | %-2.2 | %-2.3 |
| JAP225 | endeks | ustunde | %+7.2 | 12.6 | %-2.7 | %-7.3 |
| US30 | endeks | ustunde | %+5.2 | 14.6 | %-3.2 | %+1.3 |
| US2000 | endeks | ustunde | %+5.3 | 16.3 | %-3.5 | %-2.6 |
| FRA40 | endeks | ustunde | %+0.0 | 25.4 | %-4.8 | %-1.6 |

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
