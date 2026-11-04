# 30 Eylül 2026 forward ve tarama kapsamı denetimi

Kaynaklar: yerel local_scanner.log/mobile_health.jsonl/coverage_watchdog.log; GitHub Actions 36721018162, 36732714859, 36757507325; Yahoo yeniden çekilmiş mumlar. Hiçbir emir, Telegram adayı veya forward defter kaydı oluşturulmadı.

- Mobil pencere 18:15–20:00 TR: yerel sağlıklı kontrol 3/21, GitHub koşusu 0. Yerel kontroller 19:40, 19:50, 19:55. 20:10 kapsam alarmı Telegram API gönderimi başarılı; telefonda görülmesi doğrulanmadı.
- GitHub EMA12 adımı yayımlanmış ve gerçek schedule koşularında çalışmış. 16:21 TR açılıştan önce, 17:55 TR kayıt penceresinden sonra. İkisi de “pencere dışı, açık kayıt yok”. Kodun çalışması gerçek forward gözlemi oluştuğu anlamına gelmez. Yerel EMA12 state dosyası yok; bugünkü ileriye dönük kayıt doğrulanamadı.
- Yahoo NQ=F 5dk geçmiş mumlarında EMA12.signal mevcut kuralıyla, 13:55 UTC değerlendirme saati ve yalnız o ana kadar kapanmış barlarla yeniden kontrol edildi. 09:30 NY / 16:30 TR mumu, 16:35 TR kapanışı koşulu oluşturmuş. Mevcut settle kuralıyla 22:35 TR altı saat çıkışı: net +0.561830R. Bu geçmişten teşhis, forward veya gerçek icra değildir. Yapay observed_at kullanılmasının nedeni sinyal fonksiyonunun 35dk yaş kapısıdır; gerçek zamanda gözlemlendiği iddia edilmez.
- default_modules içindeki Sweep/EUR/GBP güncel dedektörleri aynı gün Yahoo 59 günlük ısınma verisiyle her bar üzerinde kontrol edildi: üçünde de sıfır ham tetik. Sonradan indirilen/revize olabilen Yahoo veri görüntüsüdür; broker verisi veya diskresyoner fırsatların yokluğu kanıtı değildir.
- GitHub 17:55 koşusundaki “1 aday atlandı; 90 dakikadan eski” satırı bir eski barın taranmadığını söyler; dedektörün bir setup bulduğunu söylemez.
- Görevler kurulu. NQ-Mobile son görev sonucu 1; son tamamlanan Python adımlarında exit 0 görünmesine rağmen Windows görevinin hata durumunun nedeni ayrıca çözülmeli. Son MT5 bağlamı unavailable: broker kontrolü bu denetimde yapılamadı.

Makro/faiz sonuçları için tek karşılaştırma: strategy-lab/outputs/intraday/cross_asset_positioning_ab/REPORT.md. Keşifsel filtreler LIVE kurala eklenmedi. Güncel karar kaynağı Obsidian [[Borsa - Guncel Edge ve Filtre Kararlari 2026-09-27]].


## 1 Ekim 2026 devam kontrolü

Saat 18:44 TR: NQ-Mobile görevi aynı oturumda yeniden çalıştırıldı ve Windows LastTaskResult=0 oldu. Yerel logdaki koşuda scan/mobile/EMA12/makro adımları 0; mobil aday yok, yeni EMA gözlemi yok. Önceki LastTaskResult=1 için kök neden belirlenemedi: yerel log açıklama içermiyor ve TaskScheduler geçmişi kapalı. Sır içeriği kaydetmeden hata türü ve satır bilgisini `.signalbot/task_errors.log` dosyasına yazan `scripts/run-signalbot-task.ps1` göreve bağlandı; bir görev koşusu 0 tamamlandı.

18:44 itibarıyla mobil pencere kapsamı 3/21 (slot 2, 3, 5). 1 Ekim EMA12 16:35–17:10 TR penceresinde yerel koşu yok; EMA12 local state dosyası da oluşmamış. Yerel ileriye dönük EMA kaydı doğrulanamadı. GitHub signalbot ve bulut defteri son koşuları başarılı. Dört Windows görevinin son görünen sonucu 0; kapsam alarmı 1 Ekim için henüz 20:10’da çalışacak.

`git pull --ff-only` hâlâ kirli çalışma ağacı nedeniyle engelli; remote kod düzeltmelerinin çoğu yerelde zaten aynı. Stash/reset veya toplu commit/push yapılmadı.

### 18:45 TR kök neden tespiti ve düzeltme

Görev hatası yeniden oluştu; `.signalbot/task_errors.log` tam olarak `System.IO.IOException`, `run-signalbot-local.ps1:59` verdi. Bu satır MT5 salt-okunur bağlam çıktısını `.signalbot/local_scanner.log` dosyasına ekliyordu. Her dakika çalışan `Borsa-Telegram-Defter` görevi de Telegram gelen kutusu çıktısını aynı dosyaya ekliyordu. Eşzamanlı Out-File yazımı dosya kilidi/IO hatasına yol açıyordu. Çakışma çözüldü: MT5 çıktısı `.signalbot/mt5_context.log`, gelen kutusu çıktısı `.signalbot/telegram_inbox.log` dosyalarına ayrıldı. `Borsa-Signalbot-NQ-Mobile` aynı saatlerde sonraki koşuda ve elle başlatılan kontrolünde LastTaskResult=0 ile tamamlandı; log scan/mobile/EMA12/makro adımları 0. Hata sarmalayıcısı kaynak türü/satırını sırları yazmadan kaydedecek şekilde görevde kaldı.

18:47 TR mobil kapsamı 4/21 dilim (slot 2,3,5,6); ilk dilimler kaçırıldığı için bu seans tam kapsamlı değildir. 16:35–17:10 EMA12 penceresinde hiç yerel tarama yok ve PAPER state oluşmadı; 1 Ekim EMA12 forward gözlemi yok. GitHub signalbot ve bulut defteri başarılı; dört Windows görevinin son görünen sonuç kodu 0. Kapsam alarmı 20:10’da seans açığını bildirebilir.

18:50 TR yeniden doğrulama: NQ-Mobile LastTaskResult=0; scan/mobile/EMA12/makro=0; aynı dosyaya yazma hatası yeniden oluşmadı. Mobil kapsam 18:51 itibarıyla 5/21 dilim (slot 2,3,5,6,7); bu seans baştan eksik kaldığı için 21/21 olamaz. EMA12 yerel state dosyası hâlâ yok.
