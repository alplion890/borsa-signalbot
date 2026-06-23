# Maven 5K Telegram Sinyal Botu

Yedi stratejiyi ucretsiz veriden tarar ve uygun setup'lari Telegram'a yollar.
Emir acmaz. Son karar ve manuel emir kullanicidadir.

## Stratejiler

- Gold NY ORB
- NQ ORB
- NQ liquidity sweep
- EUR London fade
- GBP London trend
- NQ/ES divergence
- BTCUSDT absorption

## GitHub kurulumu

Repository `Settings > Secrets and variables > Actions` bolumune:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `FINNHUB_API_KEY`
- `DEEPSEEK_API_KEY`

eklenir. Ardindan Actions sekmesindeki `borsa-signalbot` workflow'u `Run workflow`
ile bir kez calistirilir.

Ilk canliya alma sirasi:

1. `test_finnhub` secilerek ikincil anlik fiyat kaynagi test edilir.
2. `test_telegram` secilerek telefona test mesaji gonderilir.
3. Testler basariliysa normal zamanlanmis tarama acik birakilir.

Workflow private repository ucretsiz kotasina uygun sekilde Gold/NQ ana
penceresinde 5 dakikada, diger aktif seanslarda 15-30 dakikada bir calisir.
Tarayici arada kapanan tum barlari sirayla kontrol eder.

Ayni bardaki ayni sinyal ikinci kez gonderilmez. Ayrica ayni modul, yon, giris,
stop ve hedef yapisindaki kucuk veri revizyonlari 24 saat icinde ayni fikir
sayilir. Son kapanmis fiyat setup yonunde 1R'den fazla ilerlemisse veya setup
tersine 0.5R gitmisse gecikmis aday Telegram'a gonderilmez.

Gold, NQ, ES, EUR ve GBP icin mum kaynagi Yahoo Finance, BTC icin Binance public
API'dir. Finnhub ikincil anlik fiyat destegi olarak kalir; fakat futures kontrat
seviyeleri spot/CFD proxy fiyatlariyla karismasin diye Gold, NQ ve ES
sinyallerinde Finnhub fiyati kullanilmaz. Bu sinyallerde Maven grafigindeki
guncel fiyat manuel kontrol edilmelidir.

## Lokal test

```powershell
python -m pytest strategy-lab/intraday/signalbot -q --basetemp .pytest_tmp
python run_bot.py --dry-run
python run_bot.py --test-finnhub
```

## DeepSeek AI scout

AI scout ana strateji botundan bagimsiz calisir. Ana bot setup mesajini once
gonderir; ardindan DeepSeek piyasayi tarar ve ayni Telegram sohbetine yalnizca
Pro tarafindan onaylanmis `AI FIRSAT` mesaji yollar.

Varsayilan aylik API butcesi 2 dolardir. Gunluk firsat adedi veya sabit saat
cooldown'u yoktur. Flash model butun aktif piyasalari tek istekte tarar.
Yalnizca 80 ve uzeri guven, minimum 2R ve en az uc bagimsiz kanit kategorisi
olan firsat adaylari Pro model tarafindan ikinci kez kontrol edilir.
Watch/risk adaylari Telegram'a gonderilmez; audit kaydinda kalir.
VWAP reclaim/rejection tek basina setup kabul edilmez.

Ayni sembol ve yonde neredeyse ayni giris, stop ve yapisal seviye model setup
adini degistirse bile tekrar gonderilmez. Daha genis eslesmede ayni seans ve
setup ailesindeki acik fikir; giris ve stop yapisi onceki fikre bir ATR'den daha
yakin ise bastirilir. Seans etiketi modelden alinmaz, saatten hesaplanir.
Bayat mum verisinden AI firsati uretilmez.

Tarama sikligi Londra seansinda 15 dakika, ana NY penceresinde yaklasik 10
dakika, NY seansinin ikinci yarisinda 30 dakika ve diger zamanlarda dort
saattir. Ana botun 5 dakikalik NY taramasi degismez.

Lokal kuru test:

```powershell
python run_bot.py --ai-scout --dry-run
```

Not: AI dry-run Telegram'a mesaj yollamaz ama gercek DeepSeek API tokeni
kullanir; bu nedenle harcama state dosyasina yine kaydedilir.

### Ucretsiz haber, takvim ve performans hafizasi

AI scout mevcut Finnhub anahtariyla son piyasa haberlerini ve ekonomik takvimi
almayi dener. Ucretsiz plan bu endpointleri vermezse Fed ve BEA resmi RSS
akislarina, ekonomik takvim icin BLS iCalendar kaynagina duser. Veri kaynaklari
gecici olarak calismazsa teknik tarama devam eder.

Her `AI FIRSAT` adayi `.signalbot/ai_ledger.jsonl` dosyasina kaydedilir. Sonraki
taramalarda mumlar kullanilarak girisin tetiklenip tetiklenmedigi, TP veya
stopun hangisinin once geldigi, MFE/MAE ve gerceklesen R otomatik hesaplanir.
Ayni mumda hem TP hem stop gorulurse sonuc iyimser varsayilmaz ve `ambiguous`
olarak isaretlenir. Olculen sembol/setup istatistikleri sonraki DeepSeek
isteklerine performans hafizasi olarak eklenir; sekizden az ornek zayif kanit
sayilir.

Dry-run adaylari gercek performans defterine yazilmaz. Tum ham, reddedilen ve
ayni acik yapinin tekrari oldugu icin bastirilan AI adaylari
`.signalbot/ai_audit.jsonl` dosyasina yazilir. Her workflow sonunda
`python run_bot.py --ai-report` ile gercek firsatlarin win rate, ortalama R, MFE
ve MAE ozeti GitHub loguna basilir.

## Kilitli Maven BNPL risk profilleri

GitHub repository variable `ACCOUNT_PHASE` yalnizca su iki degeri kabul eder:

- `bnpl_challenge`: Gold ve NQ normal yuzde 1.5, onceki kapanan islem
  kazandiysa yuzde 3. Ayni anda tek islem. Paper moduller sabit ve en fazla
  yuzde 0.75 risk alir; kazanc sonrasi artmaz. Gunluk yumusak stop yuzde 4.5,
  haftalik stop yuzde 7.5.
- `bnpl_funded`: Gold ve NQ yuzde 0.35, modul agirligiyla dahi tek islem ve
  toplam acik risk en fazla yuzde 0.50. Kazanc sonrasi risk artisi yok. Gunluk
  zarar stopu yuzde 1, haftalik zarar stopu yuzde 2, gunluk kar tavani yuzde
  0.50. Paper moduller gercek para icin sifir lot gosterir.

Funded profili Maven BNPL funded kurallarindaki yuzde 4 gunluk DD, yuzde 8
trailing DD ve yuzde 20 consistency sinirlarinin icinde guvenlik tamponu
birakir. Payout istemeden once en az yuzde 2.5 toplam kar tamponu ve Maven
panelinde consistency degeri yuzde 20 veya altinda olmalidir.

Challenge gecince GitHub `Settings > Secrets and variables > Actions >
Variables` bolumundeki `ACCOUNT_PHASE` degerini `bnpl_funded` yap. Bot Maven
hesabini okuyamadigi icin bu tek asama degisikligi kullanici tarafindan
yapilmalidir.
