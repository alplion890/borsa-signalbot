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

eklenir. Ardından Actions sekmesindeki `borsa-signalbot` workflow'u
`Run workflow` ile bir kez çalıştırılır.

Workflow private repository ücretsiz kotasına uygun şekilde Gold/NQ ana
penceresinde 5 dakikada, diğer aktif seanslarda 15 dakikada bir çalışır.
Tarayıcı arada kapanan tüm 5 dakikalık barları sırayla kontrol eder.
Aynı bardaki aynı sinyal ikinci kez gönderilmez.

Yahoo, GC/NQ/ES futures verisini yaklaşık 10 dakika gecikmeli verir. Bu
modüllerin Telegram mesajı gecikmeyi ve izin verilen maksimum fiyat sapmasını
özellikle yazar. Kullanıcı Maven grafiğindeki canlı fiyat sapma sınırını
aşmışsa sinyali almaz. EUR/GBP Yahoo metadata gecikmesi 0 dakika, BTC ise
Binance public API üzerinden gerçek zamana yakındır.

## Lokal test

```powershell
python -m pytest strategy-lab/intraday/signalbot -q
python run_bot.py --dry-run
```
