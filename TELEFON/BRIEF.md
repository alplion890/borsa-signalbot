# Seans brifingi (olgu)

Uretim: **2026-09-23 20:52 TR** / 2026-09-23 17:52 UTC  
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

- Tokyo: kapali, acilisa 6.1 saat
- Londra: kapali, acilisa 13.1 saat
- New York: ACIK, kapanisa 3.1 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 30720  (bar 2026-09-23 17:30:00 UTC)
- dun araligi: 30670 → 31066
- bugun araligi: 30643 → 31095
- 200EMA (gunluk): 27679  (uzaklik +3040.4 / %+10.98)
- ATR(14) son kapali gun: 490.23  (100 gunun %27. yuzdeligi)
- hacim (son kapali gun): 546,468  (20 gunun %63. yuzdeligi)
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

- son kapanis: 4319.8  (bar 2026-09-23 17:40:00 UTC)
- dun araligi: 4327.6 → 4414.1
- bugun araligi: 4310.7 → 4407.5
- 200EMA (gunluk): 4348.5  (uzaklik -28.677 / %-0.66)
- ATR(14) son kapali gun: 104.17  (100 gunun %27. yuzdeligi)
- hacim (son kapali gun): 138,203  (20 gunun %0. yuzdeligi)
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

- son kapanis: 1.1393  (bar 2026-09-23 17:50:00 UTC)
- dun araligi: 1.1431 → 1.1481
- bugun araligi: 1.1374 → 1.1455
- 200EMA (gunluk): 1.1566  (uzaklik -0.017218 / %-1.49)
- ATR(14) son kapali gun: 0.0049777  (100 gunun %4. yuzdeligi)
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

- son kapanis: 1.3253  (bar 2026-09-23 17:50:00 UTC)
- dun araligi: 1.3324 → 1.3389
- bugun araligi: 1.3225 → 1.3346
- 200EMA (gunluk): 1.3425  (uzaklik -0.017205 / %-1.28)
- ATR(14) son kapali gun: 0.0063903  (100 gunun %8. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+12.0 | 16.3 | %+6.6 | %+5.3 |
| SP500 | endeks | ustunde | %+7.8 | 16.2 | %+2.1 | %+3.6 |
| US30 | endeks | ustunde | %+3.7 | 23.3 | %-2.3 | %-0.9 |
| US2000 | endeks | ustunde | %+4.5 | 34.1 | %-2.9 | %-1.9 |
| GER40 | endeks | ustunde | %+2.7 | 21.1 | %-2.0 | %+1.8 |
| UK100 | endeks | ustunde | %+3.7 | 15.5 | %-0.7 | %+2.3 |
| FRA40 | endeks | altinda | %-1.3 | 40.8 | %-3.7 | %-2.7 |
| JAP225 | endeks | ustunde | %+9.1 | 10.9 | %+0.6 | %-2.4 |
| EURUSD | fx | altinda | %-0.9 | 27.1 | %-1.7 | %+0.7 |
| GBPUSD | fx | altinda | %-0.4 | 23.2 | %-2.0 | %+0.2 |
| USDJPY | fx | altinda | %-0.2 | 36.5 | %-1.1 | %-3.1 |
| AUDUSD | fx | ustunde | %+2.0 | 19.8 | %-0.5 | %+2.9 |
| USDCAD | fx | ustunde | %+1.0 | 24.1 | %+1.4 | %-0.8 |
| USDCHF | fx | ustunde | %+2.3 | 20.2 | %+2.3 | %+0.7 |
| NZDUSD | fx | altinda | %-2.2 | 38.6 | %-4.3 | %-0.9 |
| EURJPY | fx | altinda | %-1.1 | 33.7 | %-2.8 | %-2.4 |
| GBPJPY | fx | altinda | %-0.6 | 36.0 | %-3.1 | %-3.0 |
| XAUUSD | emtia | ustunde | %+0.3 | 15.0 | %-6.8 | %+9.3 |
| XAGUSD | emtia | ustunde | %+0.7 | 14.1 | %-3.8 | %+14.4 |
| WTI | emtia | ustunde | %+15.4 | 32.0 | %+11.3 | %+21.1 |
| BTCUSDT | kripto | ustunde | %+16.7 | 44.4 | %+11.5 | %+35.7 |

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
