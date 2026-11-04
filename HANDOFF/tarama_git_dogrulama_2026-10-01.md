# 1 Ekim 2026 operasyon doğrulaması

Temel commit: ea74970. Yerel düzeltmeler henüz commit edilmedi.

# 1 Ekim 2026 yerel tarama kesintisi

Windows System / Kernel-General olayları: PC 00:12:55 TR kapandı (ID13), 18:20:51 TR açıldı (ID12). Oturum kilidi 18:22:15 TR açıldı (Kernel-Power 566). Dolayısıyla EMA12 16:35–17:10 edinim penceresi boyunca PC kapalıydı. Mobil ilk dilim 18:15 de PC kapalıyken geçti. Bu ilk boşluğu yalnız günlük dosyası hatasına bağlamak yanlış olur.

Açıldıktan sonra NQ-Mobile 18:25 ve 18:30 sonucu1 görüldü. İlk başarılı elle koşu 18:29:44. 18:45 otomatik koşuda hata sarmalayıcısı IOException / run-signalbot-local.ps1:59 yakaladı. MT5 çıktısı ve her dakika gelen-kutusu görevi aynı local_scanner.log dosyasına yazıyordu. Çıktılar mt5_context.log ve telegram_inbox.log dosyalarına ayrıldı. 18:50,18:55,19:00,19:05,19:10,19:15 gerçek planlı koşular başarı0 ve taze mobil sağlık kaydı verdi. Kurulum scripti de hata sarmalayıcısını kullanacak biçimde güncellendi.

1 Ekim bulut signalbot schedule koşuları 03:06,09:07,17:23,18:30 TR. EMA12 16:35–17:10 penceresinde koşu yok; 17:24 adım logu pencere dışı/açık kayıt yok dedi. PC kapalı olduğunda GitHub cron eksiksiz telafi sağlamadı. Yerel EMA state yok; bu gün gerçek ileriye dönük gözlem sayılmaz.

Windows güç planında AC ve pil uyku zaman aşımı0 (otomatik uyku kapalı). Sorun uyku ayarı değil, işletim sistemi kapanışı. Kapalı PC’de Interactive görev çalışmaz; ölçüm saatinden önce PC/oturum/internet açık olmalı. Bu koşul değişecekse sürekli çalışan bağımsız tarayıcı gerekir; yeni hizmet kurulmadı. Kaçmış EMA günü yeniden forward yapılmaz.

Temel repo commit ea74970; düzeltmeler yerel çalışma ağacında. [[Borsa - Forward Kapsam Denetimi 2026-09-30]]

# Git yerel/bulut uzlaştırması — 1 Ekim 2026

Yerel main d961bf0, origin/main ea74970 idi. Önceki API yayımlamaları yerel çalışma ağacındaydı fakat yerel Git HEAD ilerlememişti; güncelleme aynı dosyalara yazacağı için pull duruyordu.

46 uzak değişiklik yolu yerel/eski temel/uzak/son birleşik içerikleriyle C:\Users\quantum\.codex\backups\borsa-reconcile-2026-10-01 altında yedeklendi; manifest.json kararları kaydeder. İlgili dosyalar seçili pathspec ile güvenlik stash’ine alındı; stash’ler tutuluyor. İlgisiz yerel değişiklikler korunarak main ea74970’e fast-forward edildi ve yerel eklemeler/uzlaştırılmış dosyalar geri yerleştirildi. git pull --ff-only artık Already up to date döndü. Zorla push, toplu commit veya uzak yayın yapılmadı.

Telefon Telegram kodu/testlerinde otomatik parça birleştirme çalışma zamanı NameError üretti; birleştirme sonrası test yakaladı. Bu çiftin önceki çalışan yerel sürümleri yedekten korundu. Uzak telefon-talimat testleri güncel kullanıcı olgu/manuel karar kuralıyla çelişiyordu; test sözleşmesi güncel talimata uyarlandı. Katalogdaki eski Sweep n9/+0.804 kapsam metni güncel sonuç gibi görünmesin diye dinamik ölçümün sistem durumu bölümünde olduğu yazıldı.

Çalışma ağacı hâlâ yerel değişiklik içeriyor; bu git pull hatasının devamı değildir. Gelecekte aynı dosyalara yeni uzak değişiklik gelirse yeniden birleştirme gerekir. [[Borsa - 1 Ekim Yerel Tarama Kesintisi]]

Son doğrulama: tam intraday testleri 562 passed, 3 skipped. git pull --ff-only başarılı / Already up to date; HEAD ve origin/main ea74970. Güvenlik yedekleri ve stash korundu.
