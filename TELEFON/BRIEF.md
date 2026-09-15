# Seans brifingi (olgu)

Uretim: **2026-09-15 22:02 TR** / 2026-09-15 19:02 UTC  
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

- Tokyo: kapali, acilisa 5.0 saat
- Londra: kapali, acilisa 12.0 saat
- New York: ACIK, kapanisa 2.0 saat

## Semboller


### NASDAQ100 (15m)

- son kapanis: 29237  (bar 2026-09-15 18:45:00 UTC)
- dun araligi: 28816 → 29303
- bugun araligi: 29216 → 29495
- 200EMA (gunluk): 27545  (uzaklik +1691.8 / %+6.14)
- ATR(14) son kapali gun: 451.08  (100 gunun %5. yuzdeligi)
- hacim (son kapali gun): 563,849  (20 gunun %63. yuzdeligi)
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

- son kapanis: 4349.5  (bar 2026-09-15 18:50:00 UTC)
- dun araligi: 4293 → 4396.8
- bugun araligi: 4301.6 → 4358.2
- 200EMA (gunluk): 4344.2  (uzaklik +5.2539 / %+0.12)
- ATR(14) son kapali gun: 112.26  (100 gunun %47. yuzdeligi)
- hacim (son kapali gun): 187,975  (20 gunun %47. yuzdeligi)
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

- son kapanis: 1.1546  (bar 2026-09-15 19:00:00 UTC)
- dun araligi: 1.1524 → 1.1596
- bugun araligi: 1.153 → 1.1555
- 200EMA (gunluk): 1.1571  (uzaklik -0.002468 / %-0.21)
- ATR(14) son kapali gun: 0.0051214  (100 gunun %8. yuzdeligi)
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

- son kapanis: 1.348  (bar 2026-09-15 19:00:00 UTC)
- dun araligi: 1.3465 → 1.3528
- bugun araligi: 1.3465 → 1.3505
- 200EMA (gunluk): 1.3427  (uzaklik +0.0053059 / %+0.40)
- ATR(14) son kapali gun: 0.0062475  (100 gunun %3. yuzdeligi)
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
| NASDAQ100 | endeks | ustunde | %+5.7 | 12.8 | %-3.3 | %-1.4 |
| SP500 | endeks | ustunde | %+5.3 | 12.9 | %-2.3 | %+1.3 |
| US30 | endeks | ustunde | %+4.2 | 16.9 | %-2.5 | %-1.4 |
| US2000 | endeks | ustunde | %+4.0 | 27.6 | %-5.9 | %-4.0 |
| GER40 | endeks | ustunde | %+2.3 | 20.1 | %-3.4 | %-1.5 |
| UK100 | endeks | ustunde | %+3.5 | 17.0 | %-0.5 | %+0.2 |
| FRA40 | endeks | altinda | %-1.6 | 38.5 | %-5.4 | %-4.3 |
| JAP225 | endeks | ustunde | %+5.3 | 12.6 | %-8.1 | %-7.4 |
| EURUSD | fx | ustunde | %+0.2 | 23.7 | %+0.2 | %+1.4 |
| GBPUSD | fx | ustunde | %+0.7 | 18.1 | %-0.2 | %+1.3 |
| USDJPY | fx | altinda | %-2.7 | 48.0 | %-3.6 | %-5.0 |
| AUDUSD | fx | ustunde | %+2.6 | 17.9 | %+0.9 | %+3.1 |
| USDCAD | fx | altinda | %-0.2 | 21.1 | %-0.0 | %-2.4 |
| USDCHF | fx | ustunde | %+1.9 | 14.0 | %+0.5 | %+1.6 |
| NZDUSD | fx | altinda | %-0.6 | 27.6 | %-1.3 | %+1.9 |
| EURJPY | fx | altinda | %-2.5 | 37.0 | %-3.5 | %-3.7 |
| GBPJPY | fx | altinda | %-2.0 | 37.1 | %-3.8 | %-3.7 |
| XAUUSD | emtia | altinda | %-0.1 | 20.4 | %-1.9 | %+5.5 |
| XAGUSD | emtia | altinda | %-3.0 | 17.5 | %-2.3 | %+4.7 |
| WTI | emtia | ustunde | %+25.5 | 27.8 | %+23.0 | %+47.6 |
| BTCUSDT | kripto | ustunde | %+6.5 | 43.6 | %-0.4 | %+19.6 |

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
