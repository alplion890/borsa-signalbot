# Signalbot Current Status - 2026-06-24

Bu dosya botun Capital.com sonrasi son pratik durumunu ozetler. Amac: bir ay
sonra bile "biz nerede kalmistik?" sorusuna hizli ve net cevap vermek.

## Ana karar

Capital.com Turkiye'de kullanilamadigi icin Capital demo/API yolu tamamen terk
edildi. Capital primary feed, Capital secret'lari, `test_capital` workflow
secenegi ve ilgili kod/test yolu kaldirildi.

Bu karar sonrasi bot cop olmadı; rolu degisti:

```text
Bot = setup radari
Kullanici = execution pilotu
```

Sifir maliyet + PC kapali + TradingView/VPS yok + Capital yok kosulunda,
5m/15m futures icin kusursuz real-time otomatik sinyal mumkun degil. En guvenli
ucretsiz kurulum GitHub radar + manuel Maven teyididir.

## Aktif mimari

```text
Normal strateji botu:
  - GitHub Actions uzerinden calisir.
  - Telegram'a sinyal yollar.
  - Emir acmaz.
  - Gold/NQ ana penceresinde 5 dakikada bir tarama yapar.
  - Londra penceresinde 15 dakikada bir, NY ikinci yarida 30 dakikada bir calisir.

Veri kaynaklari:
  - XAUUSD / NASDAQ100 / SP500 / EURUSD / GBPUSD: Yahoo Finance mum verisi.
  - BTCUSDT: Binance public API.
  - Finnhub: sadece uyumlu sembollerde ikincil anlik fiyat.

Futures karari:
  - Gold, NQ ve ES futures seviyeleri spot/CFD proxy ile karistirilmiyor.
  - Bu yuzden Gold/NQ/ES icin Finnhub anlik fiyat karsilastirmasi kapali.
  - Bu sinyallerde Maven/prop grafiginden guncel fiyat manuel kontrol edilmeli.
```

## Normal bot korumalari

```text
Tekrar-spam korumasi:
  - Ayni bardaki ayni sinyal ikinci kez gonderilmez.
  - Ayni modul/yon/giris/stop/hedef yapisindaki kucuk revizyonlar 24 saat icinde
    ayni fikir kabul edilir.
  - Eski NQ ORB gibi 18:01 ve 18:11'de ayni setup'in tekrar gelmesi engellenir.

Gecikme filtresi:
  - Fiyat setup yonunde +1.0R'den fazla ilerlemisse aday gonderilmez.
  - Fiyat setup tersine -0.5R gitmisse aday gonderilmez.
  - Bu filtre en son kapanmis mum fiyatina gore calisir.
  - Futures'ta sahte CFD/spot proxy fiyati kullanmaz.
```

## DeepSeek AI scout

AI scout ana bottan bagimsizdir. Ana bot setup mesajini once yollar; DeepSeek
ana botu bekletmez.

```text
Kurallar:
  - Ayni Telegram sohbetine "AI FIRSAT" mesaji yollar.
  - Minimum 2R altindaki firsatlar Telegram'a cikmaz.
  - Minimum guven: 80.
  - VWAP reclaim/rejection tek basina setup sayilmaz.
  - Flash model once tum aktif piyasalari tarar.
  - Sadece kaliteli adaylar Pro modelden ikinci teyit alir.
  - Watch/risk/ham model cevaplari Telegram'a cikmaz, audit dosyasina yazilir.
  - Gercek AI FIRSAT adaylari ledger'a yazilir; TP/SL/MFE/MAE sonradan izlenir.
```

## Risk yonetimi

```text
Challenge fazi:
  - Gold ve NQ normal risk: %1.5.
  - Onceki kapanan islem kazandiysa maksimum %3.
  - Ayni anda tek islem.
  - Toplam acik risk maksimum %3.
  - Gunluk zarar %4.5'e gelirse dur.

Funded fazi:
  - ACCOUNT_PHASE = bnpl_funded yapilinca devreye girer.
  - Gold/NQ risk yaklasik %0.35.
  - Toplam acik risk maksimum %0.50.
  - Gunluk zarar stopu %1.
  - Haftalik zarar stopu %2.
  - Gunluk kar tavani %0.50.
  - Paper moduller gercek para icin sifir risk gosterir.
```

## Aktif kullanim kurali

Telegram sinyali gelirse:

1. Acik islem var mi kontrol et.
2. Maven grafiginde guncel fiyati kontrol et.
3. Fiyat giris bolgesine yakin degilse alma.
4. +0.5R'den fazla kacmis hareketi kovalamama.
5. Sadece Gold/NQ ana saatlerinde ve ekrana bakabiliyorsan gercek hesaba dokun.

## Test ve deploy notu

```text
Local test:
  python -m pytest strategy-lab/intraday/signalbot -q --basetemp .pytest_tmp

Sonuc:
  71 passed

Dry-run:
  python run_bot.py --dry-run

Sonuc:
  Kod calisti. Local sandbox dis internete/Binance'a izin vermedigi icin BTC
  veri istegi ConnectionError verdi; bu GitHub Actions icin kod hatasi olarak
  okunmadi.

Hazir commitler:
  Local normal commit: 09ea6f2 fix: remove unavailable capital feed path
  Remote origin/main parent'li deploy commit: face0778 fix: remove unavailable capital feed path
```

## Son acik risk

GitHub baglantisi bu oturumda ara ara `github.com port 443` hatasi verdi. Baglanti
geldigi anda `face0778` commit'i `origin/main` uzerine fast-forward pushlanacak.
Push tamamlandiktan sonra GitHub Actions uzerinden dry-run/test calistirilip bot
aktif halde birakilacak.
