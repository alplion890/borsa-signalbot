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

Workflow private repository ücretsiz kotasına uygun şekilde aktif seanslarda
15 dakikada bir çalışır. Tarayıcı arada kapanan tüm 5 dakikalık barları sırayla
kontrol eder. Aynı bardaki aynı sinyal ikinci kez gönderilmez.

## Lokal test

```powershell
python -m pytest strategy-lab/intraday/signalbot -q
python run_bot.py --dry-run
```
