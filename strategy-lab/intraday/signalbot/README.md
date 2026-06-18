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
