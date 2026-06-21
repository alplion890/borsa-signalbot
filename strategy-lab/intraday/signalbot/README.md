# Maven 5K Telegram Sinyal Botu

Yedi stratejiyi ücretsiz veriden tarar ve uygun her setup'ı Telegram'a yollar.
Emir açmaz. Son karar ve manuel emir kullanıcıdadır.

## Stratejiler

- Gold NY ORB
- NQ ORB
- NQ liquidity sweep
- EUR London fade
- GBP London trend
- NQ/ES divergence
- BTCUSDT absorption

## Risk mesajı

Challenge modu normalde yüzde 1.5 risk gösterir. Bir önceki kapanan işlemin
kazandığını kullanıcı biliyorsa yüzde 3 lotunu seçebilir. Portföy ağırlıkları
ve tek işlem yüzde 3 tavanı otomatik uygulanır.

## GitHub kurulumu

Repository `Settings > Secrets and variables > Actions` bölümüne:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `FINNHUB_API_KEY`

eklenir. Ardından Actions sekmesindeki `borsa-signalbot` workflow'u
`Run workflow` ile bir kez çalıştırılır.

İlk canlıya alma sırası:

1. `test_finnhub` seçilerek XAU, NAS100, SP500, EUR, GBP ve BTC sembolleri test edilir.
2. Çalışmayan Finnhub proxy sembolü varsa `FINNHUB_SYMBOL_*` eşlemesi düzeltilir.
3. `test_telegram` seçilerek telefona test mesajı gönderilir.
4. İkisi de başarılıysa normal zamanlanmış tarama açık bırakılır.

Workflow private repository ücretsiz kotasına uygun şekilde Gold/NQ ana
penceresinde 5 dakikada, diğer aktif seanslarda 15 dakikada bir çalışır.
Tarayıcı arada kapanan tüm 5 dakikalık barları sırayla kontrol eder.
Aynı bardaki aynı sinyal ikinci kez gönderilmez.

Yahoo, GC/NQ/ES futures verisini yaklaşık 10 dakika gecikmeli verir. Bu
modüllerin Telegram mesajı eski mum fiyatını her koşulda bildirir. Finnhub
anlık fiyat geldiyse ayrıca girişten fiyat farkını ve R cinsinden hareketi
yazar. Finnhub çalışmazsa sinyal yine gönderilir ve Maven grafiğinden kontrol
istenir. EUR/GBP Yahoo metadata gecikmesi 0 dakika, BTC geçmiş mumları Binance
public API üzerinden gelir.

## Lokal test

```powershell
python -m pytest strategy-lab/intraday/signalbot -q
python run_bot.py --dry-run
```

## DeepSeek AI scout

AI scout ana strateji botundan bagimsiz calisir. Ana bot setup mesajini once
gonderir; ardindan DeepSeek piyasayi tarar ve ayni Telegram sohbetine yalnizca
`AI FIRSAT` veya `AI RISK` etiketiyle ayri mesaj yollar.

GitHub Environment secret olarak sunu ekle:

- `DEEPSEEK_API_KEY`

Varsayilan aylik API butcesi 2 dolar, gunluk AI firsat tavani 4'tur. Flash model
butun aktif piyasalari tek istekte tarar. Yalnizca 80 ve uzeri, minimum 2R ve
en az uc bagimsiz kanit kategorisi olan firsat adaylari Pro model tarafindan
ikinci kez kontrol edilir. `AI IZLE` adaylari Telegram'a gonderilmez; audit
kaydinda kalir. Ayni sembol ve yon icin dort saat dolmadan yeni AI firsat
mesaji gonderilmez. VWAP reclaim/rejection tek basina setup kabul edilmez.

Tarama sikligi Londra seansinda 15 dakika, ana NY penceresinde yaklasik
10 dakika, NY seansinin ikinci yarisinda 30 dakika ve diger zamanlarda dort
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

Dry-run adaylari gercek performans defterine yazilmaz.
Tum ham, reddedilen ve cooldown nedeniyle bastirilan AI adaylari
`.signalbot/ai_audit.jsonl` dosyasina yazilir. Her workflow sonunda
`python run_bot.py --ai-report` ile gercek firsatlarin win rate, ortalama R,
MFE ve MAE ozeti GitHub loguna basilir.

## Kilitli Maven BNPL risk profilleri

GitHub repository variable `ACCOUNT_PHASE` yalnizca su iki degeri kabul eder:

- `bnpl_challenge`: Gold ve NQ normal yuzde 1.5, onceki kapanan islem
  kazandiysa yuzde 3. Ayni anda tek islem. PAPER moduller sabit ve en fazla
  yuzde 0.75 risk alir; kazanc sonrasi artmaz. Gunluk yumusak stop yuzde 4.5,
  haftalik stop yuzde 7.5.
- `bnpl_funded`: Gold ve NQ yuzde 0.35, modul agirligiyle dahi tek islem ve
  toplam acik risk en fazla yuzde 0.50. Kazanc sonrasi risk artisi yok.
  Gunluk zarar stopu yuzde 1, haftalik zarar stopu yuzde 2, gunluk kar tavani
  yuzde 0.50. PAPER moduller gercek para icin sifir lot gosterir.

Funded profili Maven BNPL funded kurallarindaki yuzde 4 gunluk DD, yuzde 8
trailing DD ve yuzde 20 consistency sinirlarinin icinde guvenlik tamponu
birakir. Payout istemeden once en az yuzde 2.5 toplam kar tamponu ve Maven
panelinde consistency degeri yuzde 20 veya altinda olmalidir.

Challenge gecince GitHub `Settings > Secrets and variables > Actions >
Variables` bolumundeki `ACCOUNT_PHASE` degerini `bnpl_funded` yap. Bot Maven
hesabini okuyamadigi icin bu tek asama degisikligi kullanici tarafindan
yapilmalidir.
