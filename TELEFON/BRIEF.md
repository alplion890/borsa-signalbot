# Seans brifingi (olgu)

Uretim: **2026-09-08 22:39 TR** / 2026-09-08 19:39 UTC  
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

## Seans

- Tokyo: kapali, acilisa 4.4 saat
- Londra: kapali, acilisa 11.4 saat
- New York: ACIK, kapanisa 1.4 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29566  (bar 2026-09-08 19:15:00 UTC)
- dun araligi: 29468 → 29704
- bugun araligi: 29425 → 29765
- 200EMA (gunluk): 27459  (uzaklik +2106.6 / %+7.67)
- ATR(14) son kapali gun: 457.62  (100 gunun %3. yuzdeligi)
- hacim (son kapali gun): 472,983  (20 gunun %47. yuzdeligi)
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

- son kapanis: 4414.8  (bar 2026-09-08 19:25:00 UTC)
- dun araligi: 4429.8 → 4429.8
- bugun araligi: 4402.4 → 4488.8
- 200EMA (gunluk): 4316.4  (uzaklik +98.438 / %+2.28)
- ATR(14) son kapali gun: 82.093  (100 gunun %47. yuzdeligi)
- hacim (son kapali gun): 145  (20 gunun %11. yuzdeligi)
- donus seviyeleri (son 60 gun):
  - 2026-07-31  4017.9  (destek)
  - 2026-08-03  4118.5  (direnc)
  - 2026-08-17  4445  (direnc)
  - 2026-08-18  4315  (destek)
  - 2026-08-21  4327.6  (destek)
  - 2026-08-26  4670.9  (direnc)
  - 2026-09-01  4625.5  (direnc)
  - 2026-09-04  4292.2  (destek)

### EURUSD (5m)

- son kapanis: 1.1631  (bar 2026-09-08 19:35:00 UTC)
- dun araligi: 1.1608 → 1.1635
- bugun araligi: 1.1612 → 1.1639
- 200EMA (gunluk): 1.1569  (uzaklik +0.0061692 / %+0.53)
- ATR(14) son kapali gun: 0.0050142  (100 gunun %0. yuzdeligi)
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

- son kapanis: 1.3542  (bar 2026-09-08 19:35:00 UTC)
- dun araligi: 1.3506 → 1.355
- bugun araligi: 1.3523 → 1.3562
- 200EMA (gunluk): 1.3422  (uzaklik +0.012066 / %+0.90)
- ATR(14) son kapali gun: 0.0064897  (100 gunun %0. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+7.6 | 13.6 | %-0.9 | %-0.5 |
| SP500 | endeks | ustunde | %+7.0 | 12.5 | %-0.7 | %+4.0 |
| US30 | endeks | ustunde | %+6.3 | 13.1 | %-1.3 | %+2.1 |
| US2000 | endeks | ustunde | %+7.2 | 19.6 | %-2.1 | %-1.8 |
| GER40 | endeks | ustunde | %+4.8 | 19.9 | %-1.2 | %+5.6 |
| UK100 | endeks | ustunde | %+4.9 | 15.9 | %-0.7 | %+3.0 |
| FRA40 | endeks | ustunde | %+0.6 | 31.7 | %-4.8 | %-0.7 |
| JAP225 | endeks | ustunde | %+10.2 | 13.6 | %-0.6 | %-7.5 |
| EURUSD | fx | ustunde | %+0.4 | 28.4 | %+0.5 | %+2.0 |
| GBPUSD | fx | ustunde | %+0.7 | 22.6 | %+0.2 | %+2.4 |
| USDJPY | fx | altinda | %-1.1 | 43.3 | %-1.1 | %-3.5 |
| AUDUSD | fx | ustunde | %+3.5 | 19.4 | %+2.0 | %+4.5 |
| USDCAD | fx | altinda | %-0.5 | 24.5 | %-0.8 | %-2.5 |
| USDCHF | fx | ustunde | %+1.1 | 14.9 | %+0.2 | %-0.0 |
| NZDUSD | fx | ustunde | %+0.6 | 22.3 | %-0.1 | %+4.3 |
| EURJPY | fx | altinda | %-0.7 | 26.0 | %-0.6 | %-1.5 |
| GBPJPY | fx | altinda | %-0.4 | 26.0 | %-0.9 | %-1.1 |
| XAUUSD | emtia | ustunde | %+2.4 | 22.0 | %+2.1 | %+9.9 |
| XAGUSD | emtia | ustunde | %+0.9 | 22.3 | %+4.3 | %+13.2 |
| WTI | emtia | ustunde | %+14.4 | 17.8 | %+17.0 | %+27.2 |
| BTCUSDT | kripto | ustunde | %+8.4 | 48.4 | %+22.2 | %+22.2 |

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
