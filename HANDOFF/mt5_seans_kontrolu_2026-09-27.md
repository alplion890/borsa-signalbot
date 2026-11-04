# Maven MT5 / 21–25 Eylül seans kontrolü

27 Eylül 2026'da açık MavenTrade terminalinden US100 15m, EURUSD/GBPUSD 5m
mumları okundu. `default_modules()` kuralları değiştirilmeden, izole `Book`
ve mevcut `engine.cycle` üzerinde 21 Eylül 00:00–26 Eylül 00:00 UTC aralığı
yeniden oynatıldı. Isınma için önceki 40 günlük mumlar kullanıldı.
Başlangıçta açık sanal pozisyon yoktu; gerçek emir/Telegram setup gönderimi
yapılmadı, forward defteri değiştirilmedi. Sonuçlar broker mumları üzerinde
sanal SL/TP/timeout ve mevcut maliyet modeliyle hesaplanmıştır.

| Modül | Giriş UTC | Sonuç | R |
|---|---|---|---:|
| Sweep LIVE | 24 Eylül 13:15 | SL | -1.295787 |
| Sweep LIVE | 24 Eylül 13:45 | SL | -1.096244 |
| EUR PAPER | 21 Eylül 08:30 | timeout | +0.091009 |
| EUR PAPER | 24 Eylül 07:25 | SL | -1.069042 |
| GBP PAPER | 21 Eylül 07:00 | timeout | -0.636261 |
| GBP PAPER | 22 Eylül 07:30 | timeout | +0.146524 |
| GBP PAPER | 24 Eylül 07:45 | SL | -1.077962 |
| GBP PAPER | 24 Eylül 10:15 | timeout | -0.073498 |

Sweep: 2 setup, %0 pozitif sonuç, -2.392R.
EUR: 2 setup, %50 pozitif sonuç, -0.978R.
GBP: 4 setup, %25 pozitif sonuç, -1.641R.
Kalan açık sanal pozisyon yok. Başlangıç defterindeki aynı haftanın iki
21 Eylül FX kaydıyla örtüşüyor; altı ek mekanik setup belirlendi.
Yahoo ve Maven feed farklı olduğu için bunların tamamı Telegram'ın kaçırdığı
aynı adaylar kabul edilemez. Sweep girişleri 16:15/16:45 TR olup ayrı mobil
izleme penceresi 18:15–20:00 TR'nin dışındadır.

Bağımsız Windows görevi `Borsa-Seans-Tarama-Alarmi`: hafta içi 20:10 TR.
Bilgisayar ve kullanıcı oturumu açık olmalı; GitHub'ın çalıştırmasına bağlı
değildir. O gün seans içinde başarılı NQ bar değerlendirmesi yoksa Telegram
uyarısı gönderir. 25 Eylül kontrolünün Telegram gönderimi başarılı oldu.
Bu görev uyarı kontrolüdür; eksik taramaları kendiliğinden yerine getirmez.
