# EUR/GBP London emeklilik kararı — 2026-09-30

Kullanıcı seyrek sinyal, sınırlı zamanı ve zayıf uzun dönem kanıtı nedeniyle mevcut EUR/GBP mekanik London sürümlerini rafa kaldırdı.

EUR: 16 satırlık birleşik sayımda 16 Temmuz eski sürümüne ait iki işlem vardı. 5 Ağustos gün filtresi değişiminden sonraki sürüm: 7 Ağustos–24 Eylül 14 sonuçlandırılmış gözlem, +3,812R / +0,272R ortalama. EUR negatif forward nedeniyle elenmedi; küçük örneklem uzun dönem negatifini doğrulamıyor veya gidermiyor. Eski +4,022R/n16 raporu güncel sürüm kanıtı diye kullanılmamalı.

GBP: 29 Eylül temiz birleşik sayım n23, −8,379R / −0,364R. Bu sayı raporlanan toplamdır; tümü tek sabit sürüm sayılmamalı. Uzun tarih negatif, makro 2022+ başlangıçtan kötü. İstatistiksel kesin başarısızlık iddiası değil; araştırma önceliği ve kullanıcı emeklilik kararıdır.

Aktif yerel ve GitHub default/forward listelerinden iki modül çıkarıldı. Yeniden kayıt yolu olan experimental_modules kaldırıldı. London görev zamanlayıcısı kaldırıldı. Açık sanal pozisyonlar varsa yalnız eski SL/TP/timeout ile sonuçlandırılır; yeni kurulum üretmez, gerçek emir göndermez. Geçmiş CSV/ham test verileri korundu. Eski detector araştırma aynası historical_london_detector.py içine taşındı; runtime kaydı yok. Kodun önceki tam sürümü HANDOFF/archive/london_modules_before_2026-09-30.py.txt içinde tarihsel arşivdir.

Aktif kullanıcıya görünen mekanik liste: Sweep LIVE manuel; EMA12 ayrı PAPER gözlem. NQ ORB/Gold emekli. Sweep makro+COT ve Gold makro+COT ayrı araştırma adaylarıdır; bu karar filtreleri canlıya eklemez. Arka plandaki önceden var olan CAND_ deneyleri bu kararla değiştirilmedi. EUR/GBP paritelerinin piyasa/haber bağlamı veya ayrı diskresyoner tezleri genel olarak yasaklanmadı.

İlgili: [[Borsa - Guncel Edge ve Filtre Kararlari 2026-09-27]], [[Borsa - Edge Secim Sureci Denetimi 2026-09-30]], [[Borsa - Forward Kapsam Denetimi 2026-09-30]].

Doğrulama: yerel intraday testleri 556 passed, 3 skipped. GitHub son düzeltme commit c4375444d04c29c48d00853107465b058816c269; kuru deneme 36772166782 başarılı (https://github.com/alplion890/borsa-signalbot/actions/runs/36772166782). EMA12 adımı çalıştı; pencere dışı kuru koşu gerçek aday/Telegram teslimini kanıtlamaz. Yerel London görevi kaldırıldı. Graphify yapı haritası güncellendi. Diğer kullanıcı değişiklikleri korunarak yalnız emeklilik dosyaları GitHub API üzerinden yayımlandı; dirty çalışma ağacı nedeniyle git pull birleştirmesi yapılamadı.

Sonraki kullanıcı kararı: eski durum/arşiv kopyaları ve historical_london_detector.py silindi; ham deney raporları/CSV kanıtı korundu. Önceki arşivleme anlatımı artık dosyanın bulunduğu anlamına gelmez.
