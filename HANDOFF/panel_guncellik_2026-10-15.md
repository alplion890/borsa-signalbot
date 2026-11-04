# Panel güncelliği ve kayıt türü açıklaması — 15 Ekim 2026

Temel HEAD ea74970, remote 359dded; yerel kod henüz commit edilmedi. Hermes denetimi değildir. Pull dirty/untracked çakışmalar nedeniyle uygulanmadı.

Kullanıcı backfill boşluğunu, ekranın anlamını ve yerel/bulut güncelliğini sordu; güncelleme ve kalıcı bağlantı istedi. Tarayıcıda MT5+CAND_SWEEP_FRA40+backfill seçiliydi: 6 normal, 0 tarihsel kapalı kayıt. Backfill bir test başlatıcısı değil, etiket filtresidir. Açıklama, kayıt sayıları, tarih temizleme ve alan sözlüğü eklendi.

Başlangıçta MT5 Sweep son barı 7 Ekim, yereldeki bulut kopyası 1 Ekim idi. GitHub workflow 38757047188 15 Ekim 18:04 TR başarılı; remote state updated_at 15:04:48Z, Sweep son bar açılışı14:30Z. İlk indirilen remote bulut CSV139 satır; yerel eski bulut CSV120 satır. Yerel dirty dosyalar ezilmedi.

Ön yedek: .tmp/forward-before-refresh-20261015-185014. MT5 terminale salt okunur erişim C:/Users/quantum/vectorbt-lab/.venv/Scripts/python.exe (3.11) ile doğrulandı. Varsayılan Python3.14'te MT5 paketi yok; gerçek ölçüm için mevcut görevdeki venv kullanıldı. Terminal bağlı, yeni US100 15dk mumları okunabildi.

Görev geçici durdurulup `live_runner --once --warmup 1 --no-notify` PAPER çalıştırıldı; finally içinde ForwardEA-5dk yeniden etkinleştirildi. Gerçek emir ve Telegram gönderilmedi. Yerel Sweep son işlenen mum açılışı15:30Z/kapanışı15:45Z, state15:53:31Z. Aynı Sweep kapalı gözlem sayısının değişmemesi güncellenmediği anlamına gelmez; yeni kapanmış Sweep işlemi yoktu. Yeni telafi gözlemleri backfill olarak korunur; daha eski kayıtlar yeniden etiketlenmedi.

Yeni cloud mirror: research_panel.sync git fetch yapar, aynı SHA'dan CSV/state indirir; canonical ledger ve tam state sözleşmesiyle doğrular; hash + atomik manifest pointer ile yayınlar. Hata yeni generation'ı yayınlamaz. Yerel panel bu kopyayı okur; kaynaklar birleşmez. Nested hatalı state'in sağlam kopyayı bozma riski bağımsız incelemede bulundu, ortak validate_state ile düzeltildi.

Kurulan görevler: Borsa-ResearchPanel-Sync (oturum açma +5dk, gizli pythonw, IgnoreNew,3dk timeout), Borsa-ResearchPanel-Dashboard (oturum açma, localhost8766, gizli pythonw). ForwardEA-5dk mevcut5dk ölçüm görevinde kaldı; VBS artık süreç sonucunu bekler/aktarır. Panel30sn otomatik okur, arka plandaki sekmeye geri dönüşte yeniler. Yenile butonu yalnız ekranı okur.

Güncellik kartları gerçek işlenen Sweep mum kapanışı/yaşı ile ölçüm state ve Git indirme saatini ayrı gösterir. TR saatleri; MT5≤30dk, bulut≤120dk operasyon eşiği. Bunlar yeni edge veya canlı giriş filtresi değil. PC/oturum/internet/MT5 koşulları ve saatlik GitHub cron gecikmesi nedeniyle kesintisizlik garantisi yok; PC kapalıyken yalnız uzak workflow çalışabilir.

Doğrulama: panel+forward_ea testleri 297 passed,1 skipped (ortak state doğrulama düzeltmesinden önce); son odaklı panel+runner32 passed, JS sözdizimi kontrolü geçti. Tarayıcı boş backfill açıklaması ve gerçek mum saatleri doğrulandı. Sync Scheduler gerçek çıkış0 ve sonraki5dk tetikleme doğrulandı. Son tekrar denetim sonucu eklenecek.

Son doğrulama: GitHub cloud workflow 38765219569 manuel warmup0 çalıştırıldı ve başarıyla tamamlandı. Commit 7c44c842b228e6797aaa0be9df7e048ff1ac74c7 mirror'a alındı; bulut state 19:00:27 TR, Sweep kapanış 18:45 TR. Yerel görev 18:59:53'te gerçek çıkış0; state18:59:57 TR ve aynı kapanış18:45 TR. Normal Sweep MT5 n15/+0,136R, bulut n3/-3,820R; tarihsel Sweep her kaynakta1 kayıt (MT5+2,424R/bulut-1,189R), birbirine eklenmez.

Ortak tam state doğrulama sonrası panel30testi ve runner2testi geçti; bağımsız son incelemede yeni bulgu yok. UI boş FRA40 backfill açıklaması, Sweep her iki kaynakta tarihsel1 kayıt ve TR mum/ölçüm/indirme zamanları doğrulandı. Yeni strateji/backtest taraması veya gerçek emir çalıştırılmadı.

Otomatik ekran yenilemesi de gözlendi: kullanıcı yenile düğmesine basılmadan 19:01:35 TR →19:02:05 TR; filtreler korundu, otomatik checkbox seçili. Güncel önizleme .tmp/research-panel-current.png. Panel logon görevi çalışır durumda, cloud sync IgnoreNew/StartWhenAvailable/PT3M doğrulandı.
