# Borsa Canlı Sinyal Botu — Operating Model & Tasarım

Tarih: 2026-06-18
Durum: Onaylandı (kullanıcı), implementation plan bekliyor

## Bağlam

Maven $5k 1-step prop fonu. EA/bot YASAK → sistem yalnızca sinyal/alarm üretir, emri
kullanıcı elle girer (diskresyoner, uygun). Şifre/login hiçbir yere yazılmaz.

Kullanıcı müsaitliği: **düzensiz / sadece telefon.** Bu yüzden:
- **Telegram bot ana sistemdir** (7/24, bedava-bulut).
- **TradingView MCP co-pilot ikincildir** — sadece kullanıcı masadayken derin teyit için.

İlgili memory: borsa-live-trading-plan, borsa-maven-fund, borsa-fill-model-lesson.

## A. Mimari

```
GitHub Actions cron (bedava, 7/24)
   -> free_data.py: yfinance (futures/FX/gold) + Binance (BTC)
   -> 7 strateji modülü, her biri Signal | None döner
   -> signal_scan.py: tüm modülleri kontrol eder, tier etiketler
   -> telegram_notify.py: telefona mesaj (token/chat_id = env var, ASLA hardcode)
```

Provider-agnostic: `free_data.py` her enstrümanı doğru kaynağa yönlendirir. Bir kaynak
bloklanırsa tek dosyada değişir.

- BTC -> Binance API (key yok, gerçek-zamanlı)
- NQ, ES (futures) -> yfinance (bedava futures veren neredeyse tek kaynak)
- Gold, EUR, GBP -> yfinance (yeterli; gelecekte OANDA demo ile real-time upgrade opsiyonu)

yfinance ~15dk gecikme: LIVE tier yalnızca **retest** girişi kullanır (breakout chase yok),
gecikmeye toleranslı. Cron 5dk olduğu için sub-saniye hız gereksiz.

## B. İki Tier

Her iki tier de kullanıcıya sinyal yollar. Fark: mesaj tonu + hazır-emir seviyesi.

- **LIVE**: Gold NY ORB, NQ ORB. Forward-parity kanıtlı (30g forward'da tuttu). Tam emir
  hazır gelir; kullanıcı kör girebilir.
- **PAPER**: NQ Sweep, EUR London, GBP London, ES-Div, BTC Absorption. Overfit şüpheli veya
  test edilmemiş. "Kalite kontrol et" etiketli gelir; kullanıcı kendi vetiyle funded
  hesabına alabilir.

Kullanıcı her setup'ta sinyal alır ve gatekeeper'dır. Terfi (paper -> live) elle, işlem
kalitesine göre yapılır (bkz. E).

## C. Günlük Takvim

Türkiye UTC+3 sabit (DST yok); NY/Londra DST ile kayar. Bot seansı **UTC'den hesaplar**,
kullanıcıya TRT gösterir. TRT saatleri yaz/kış 1 saat kayar — aşağıdaki TRT değerleri yaz
referansıdır, hardcode EDİLMEZ.

| Modül | TF | Seans (TRT yaz) | Tier | Tarama cadence |
|---|---|---|---|---|
| Gold NY ORB | 5m | NY açılış ~16:30 | LIVE | 16:30-18:00, 5dk |
| NQ ORB | 5m | ~17:45 | LIVE | 17:00-19:00, 5dk |
| NQ Sweep | 15m | NY seansı | PAPER | 16:30-23:00, 15dk |
| ES-Div | 15m | NY seansı | PAPER | 16:30-23:00, 15dk |
| EUR London | 5m | ~10:00-12:00 | PAPER | 5dk |
| GBP London | 5m | ~10:00-12:00 | PAPER | 5dk |
| BTC Absorption | 1H | 7/24 | PAPER | saatlik |

Seans-gated tarama GitHub Actions dakikalarını korur.

## D. Alarm Mesaj Formatı

KRİTİK kullanıcı gereksinimi: **insan gibi düz yazı, sade, minimum noktalama, emoji/sembol
yok.** Kafa karıştırıcı tablo/işaret yığını YASAK.

LIVE örnek:

> Gold ORB long sinyali geldi. Fiyat NY açılış aralığının üstünü retest etti. Yaklaşık
> 4225 ten gir, stop 4214, hedef 4247. Risk yüzde 1.5 yani lot 0.XX. ADX 24 ve fiyat VWAP
> üstünde, ikisi de uygun. Saat 16 42. Retest girişi bekle, kırılımı kovalama.

PAPER örnek:

> Paper sinyali, BTC absorption. Önce chart aç ve OBV ile hacmi teyit et. Kalite iyiyse
> funded hesabında değerlendir. Yaklaşık giriş, stop ve hedef şu seviyelerde ... .

Mesaj her zaman içerir: modül adı, yön, giriş, stop, hedef, lot/risk, teyit göstergeleri,
saat (TRT), giriş notu. Düz cümlelerle.

## E. Terfi Akışı (kullanıcı kararı)

Bot her modül için **parity skorkartı** tutar: forward sinyal sayısı, gerçekleşen R vs
beklenen R. Periyodik özet yollar. Bir paper modül kaliteli görününce sistem "terfi düşün"
önerir; kullanıcı funded hesabında gerçek-para deneyip nihai kararı verir. Otomatik terfi yok.

## F. Faz Ayarı (Funded geçişi)

Bot, `PHASE` config flag'inden aşamayı okur (challenge | funded) ve lot/uyarıları ayarlar.

| | Challenge (şu an) | Funded |
|---|---|---|
| Risk | %1.5 ($75) | %0.5-0.75 |
| İşlem temposu | günde max 2 | kârı 5+ güne yay |
| Tutarlılık | yok | %20 kuralı |
| Mod | vur-çık | koru + yay |

## Güvenlik Kısıtları (değişmez)

- EA/order_send KULLANILMAZ — yalnızca sinyal. Maven kuralı.
- Telegram token + chat_id yalnızca env var; asla repoda/hardcode değil.
- MT5 şifre/login hiçbir yere yazılmaz.
- git add yalnızca cwd-relative spesifik path; asla `git add -A`.

## Kapsam Dışı (YAGNI)

- Otomatik emir icrası (yasak).
- Real-time tick verisi / websocket (cron 5dk yeterli).
- OANDA/Twelve Data/Finnhub entegrasyonu (yfinance + Binance yeterli; ileride opsiyon).
- Web dashboard (Telegram mesajı yeterli).
