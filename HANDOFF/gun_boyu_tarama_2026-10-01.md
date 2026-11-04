# Gündüz tarama

Denetlenen commit: b1ca9a66181b99cdadd6fa94ee5ff552b8efe779

Yerel görev hafta içi 09:00 TR + 15 saat / 5dk tekrar; takvim kapısı NY kapanışında, tatilde ve hafta sonunda gerçek taramayı engeller. Bulut: gündüz bootstrap + 330dk işçi; beş dakikalık duvar saati dilimlerinde Sweep, mobil, EMA12 PAPER ve Finnhub bağımsız kontrol edilir. İşçi dönüşünden sonra cache kaydı ve workflow_dispatch devir adımı vardır.

Sinyal tanımları, LIVE whitelist, risk ve manuel emir yetkisi korunur. İlk başlangıç ve işçi değişiminde GitHub kuyruk gecikmesi mümkündür.

Odak testleri: 126 passed, 2 skipped.

Son yayımlanan commit: 9f62d77f02cf92cff17ae15e7c1f17069292ccff. Gerçek bulut kontrolleri 20:52:06 ve 20:55:00 TR: sweep/mobile/ema12/finnhub tamamı ok. İlk deneme koşusu log doğrulaması için kullanıcı görevi kapsamında iptal edildi; cache kaydı başarılı. Son çalışan koşu: 36903341514. Yerel 20:55 taraması tüm aşamalarda çıkış 0. Tam test 567 passed, 3 skipped; son devir düzeltmesi sonrası signalbot 126 passed, 2 skipped.

Devir düzeltmesi: GITHUB_TOKEN repository variables API erişimini vermediğinden bulut ana bildirim kaynağıdır. Yerel gh ile aktif işçinin adım durumunu okuyup Sweep alarmını kuru çalıştırır, mobil/EMA tekrarlarını susturur. Yerel RSS ve MT5 bağlamı ayrıca çalışır. İşçi yoksa yerel bildirimler aktiftir.
