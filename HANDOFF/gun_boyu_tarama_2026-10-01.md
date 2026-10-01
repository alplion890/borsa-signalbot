# Gündüz tarama

Denetlenen commit: b1ca9a66181b99cdadd6fa94ee5ff552b8efe779

Yerel görev hafta içi 09:00 TR + 15 saat / 5dk tekrar; takvim kapısı NY kapanışında, tatilde ve hafta sonunda gerçek taramayı engeller. Bulut: gündüz bootstrap + 330dk işçi; beş dakikalık duvar saati dilimlerinde Sweep, mobil, EMA12 PAPER ve Finnhub bağımsız kontrol edilir. İşçi dönüşünden sonra cache kaydı ve workflow_dispatch devir adımı vardır.

Sinyal tanımları, LIVE whitelist, risk ve manuel emir yetkisi korunur. İlk başlangıç ve işçi değişiminde GitHub kuyruk gecikmesi mümkündür.

Odak testleri: 126 passed, 2 skipped.
