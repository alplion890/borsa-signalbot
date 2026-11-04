# Yerel araştırma paneli — 15 Ekim 2026

Temel HEAD: ea74970; uygulama henüz commit edilmedi. Yerel çok sayıda mevcut değişiklik korundu; pull çakışmalar nedeniyle tamamlanmadı. Bu not Hermes denetimi değildir.

Kullanıcı sırası: plan.md → dönüşüm öncesi yedek → panel → farklar. Plan önce oluşturuldu. Yedek `../borsa-backups/20261015-175350-before-research-panel`: 724 dosya kopyalandı ve SHA256 eşitliği doğrulandı; Git bundle başarılı. 172 büyük veri/cache/sır dosyası hariç tutuldu ve manifestte listelendi. Sırlar/cache orijinal konumunda; makine/MT5/Scheduler felaket kurtarma yedeği değil. Özellik listesi ve geri dönüş yönergesi yedekte FEATURES_AND_RESTORE.md içinde.

Graph query: dashboard/report viewer ve oku_defter/load_forward/load_cloud. Obsidian: Borsa MOC → Araştırma ve Diskresyoner Yol Haritası 2026-09-16; Honest Engine Fill Modeli. Kök MOC yeniden okunmadı.

Yeni paket: strategy-lab/intraday/research_panel. Standart Python loopback HTTP, bağımlılıksız HTML/CSS/JS, pandas ve mevcut canonical ledger okuyucusu. Veri/emir çağrısı ve runner importu yok. GET defter/rapor/state/audit; POST yalnız ayrı deney ön kayıt JSON'u. Host+origin+oturum token kontrolü, CSP, dosya allowlist ve textContent ile rapor gösterimi.

Başlangıç: 55 mevcut sözleşme/yetki testi geçti. Yeni paketle odaklı koşu ilk 65 test geçti; karantina eklenince yeni 10 test tekrar geçti. Son doğrulama sonucu ayrıca aşağıya eklenecek.

Bulgu: MT5 3 eski kayıtta exit_time < entry_time (CAND_NQ_DUAL_THRUST ve NQ_ORB_STRONG_TREND); bulut 3 eski kayıtta aynı sorun (CAND_SP500_ORB ve NQ_ORB_STRONG_TREND). Panel bu kaynaktaki ilgili modüllerin bütün kayıtlarını metrik dışında tutar; CSV'ler değiştirilmedi. Sweep kayıtları bundan etkilenmez. Bu panel koruması geçmiş raporları geriye dönük düzeltmez.

Tarayıcıda gerçek MT5 Sweep n15, toplam +0,136R ve bulut n3, toplam -3,820R ayrı doğrulandı. Bunlar disk snapshot'ıdır; bugün yeniden piyasa ölçümü yapılmadı. Rapor kataloğunda 7 REPORT.md bulundu; makro/COT raporu açıldı. Ön kayıt formu görüntülendi; kalıcı test deneyi oluşturulmadı (yazma testi geçici dizinde HTTP üzerinden).

Kalan yetenek sınırı: tick/AI strateji üretimi/replay/yeni backtest çalıştırma/sürekli sunucu yok. Bu ilk platform katmanıdır. Çalışan strateji, risk, zamanlanmış görev ve bildirim kodu değişmedi.

Son doğrulama: 73 odaklı test geçti (18 yeni panel vakası + 55 mevcut sözleşme/yetki testi); JS sözdizimi kontrolü geçti. Bağımsız incelemedeki 4 orta önem dayanıklılık bulgusu düzeltildi ve regresyon testleri eklendi. Yedekle karşılaştırmada mevcut kaynak/defter/görev dosyaları değişmedi; MEMORY.md/plan.md ve arka planda çalışan tarayıcı log/state dosyalarında zamanla değişim var. Tarayıcı önizlemesi .tmp/research-panel-preview.png. Yerel panel 8766 portunda; yeniden başlatma komutu paket README içinde.
