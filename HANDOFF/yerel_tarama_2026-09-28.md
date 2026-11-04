# Yerel tarama doğrulaması — 2026-09-28

## 29 Eylül son kontrol

Kullanıcı konsol açılıp kapanmasını bildirdi. Görevlerin doğrudan powershell.exe başlatması yerine GUI host wscript.exe üzerinden run-borsa-hidden.vbs kullanıldı; Shell.Run pencere stili0, wait=True ve gerçek alt işlem çıkış kodu korunur. Üç Borsa görevi yeniden kaydedildi. Tarama/strateji/risk/emir yolu değiştirilmedi.

London görevinde LastTaskResult=1 görüldü. Windows PowerShell 5 Türkçe kültüründe ASCII I içeren `TELEGRAM_CHAT_ID` değişkeni case-insensitive regex aralığından geçmiyordu. Sentetik `TELEGRAM_CHAT_ID=test` ile `-match=False`, `-cmatch=True` doğrulandı. Runner `-cnotmatch` ve açık UTF-8 dosya I/O kullanacak şekilde düzeltildi. Gerçek Windows Task Scheduler'dan başlatılan NQ-Mobile 29 Eylül 15:35:54 koşusunda LastTaskResult=0; log scan=0/mobile=0/makro=0. Pencere öncesinde aktif modül0; bu tam seans kapsamı kanıtı değildir. Sıradaki otomatik koşu 29 Eylül16:00; mobil18:15. 116 passed, 2 skipped. GitHub brifing hâlâ disabled_manually. Önceki günün logundaki UTF-16 satırlar tarihsel olarak korunur; yeni log satırları UTF-8.

Çalışma ağacı korunarak mevcut untracked yerel scriptler tamamlandı. `git pull --ff-only` yerel değişiklikler nedeniyle birleşemedi; origin/main fetch edildi. HEAD d961bf0, fetch sırasında origin/main 2b5042b. Commit/push yok; başkalarının değişiklikleri geri alınmadı.

Windows görevleri Interactive kullanıcı oturumu, gizli PowerShell: London 10:00–14:00; NQ-Mobile 16:00–20:00; her beş dk. Günlük trigger hafta sonunda runner tarafından atlanır. Maksimum koşu dört dk, eşzamanlı kopya IgnoreNew. Bir sonraki koşular 29 Eylül 10:00 ve 16:00 TR.

Yerel tarama 28 Eylül 21:41: aktif modül 1 / yeni setup 0 / hata 0; mobil karar penceresi dışında işlem yapmadı. Emir yolu çağrılmadı, yalnız `run_bot.py` sinyal tarayıcı kullanıldı. LIVE modül/parametre/risk değişmedi.

Mobil ek bildirim eşikleri (edge değildir): mutlak 1 saat hareket≥%1; veya EMA sıralaması + ADX≥25 + mutlak hareket≥%0,5 + aynı-saat hacmi≥1,3x. Eski seviye/VWAP bildirimleri korunur. Başarılı PNG/API kaydı görünür; >1024 açıklama halinde tam metin ayrıca gönderilir. Gönderim başarısızsa olay gönderilmiş sayılmaz.

Makro BLS/Fed/BEA + ücretsiz BBC Business RSS; BBC erişimi HTTP200. CNBC403 olduğundan eklenmedi. Yerelde Finnhub haber anahtarı yok. −15/+60 dk takvim ve son20dk başlıklar seçilir. Yalnız kaynak olguları; beklenti/gerçekleşen olmayan yerde açık eksik veri ifadesi. Haber kapsamı tam veya anlık garanti değil.

Bağlantı testi etiketli NQ PNG Telegram API kabul edildi; telefonda görünmesi doğrulanmadı. Test grafiği gerçek kapanmış Yahoo NQ=F verisi; son kapanış 28 Eylül 21:30 TR. Test fırsat bildirimi değildir.

Bulut signalbot 36453245212 koşusu 19:44 TR başladı, NQ kapanmış bar kontrolü ve izleme bildirimi logda var; yeni mekanik setup0. Bu bildirim LIVE Sweep fırsatı değildir. Üç eski barın atlanması üç kaçan işlem anlamına gelmez.

GitHub telefon_brief.yml durumu disabled_manually doğrulandı. Günlük fon/brifing tekrarı durdu; otomatik BRIEF repo yenilemesi de durdu. Signalbot bulut workflow'u açık; yerel/bulut aynı adayı iki kez bildirebilir. Değişiklikler bulut koduna push edilmedi.

Kapsam alarmı artık `.signalbot/mobile_health.jsonl` içindeki taze veri kayıtlarından 18:15–20:00 için 21 ayrı beş dk dilimini sayar; tek bulut başarısı tam kapsam değildir. `.signalbot/local_scanner.log` koşu sonuçlarını tutar. İlk tam yerel seans henüz gözlenmedi. PC/uygulama/oturum/internet açık kalmalı; bu kurulum piyasa fırsatı garanti etmez.

Doğrulama: signalbot testleri ve telegram_brief testleri 116 passed, 2 skipped (bu not yazılırken); Windows görev tanımları ve ilk yerel koşu ayrıca kontrol edildi. Obsidian: [[Borsa - Yerel Tarayici ve Olay Bildirimleri 2026-09-28]].
