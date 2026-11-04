# Ücretsiz sürekli sunucu taşıma hazırlığı — 7 Ekim 2026

Kullanıcı kararı: ücretli sunucu yok; 10–15dk veri gecikmesini kabul ediyor. Sürekli tarama, PC kapalıyken de ölçüm/bildirim isteniyor. Yeni strateji veya risk kararı yok.

Hazırlanan dosyalar: deploy/always-on/README.md, borsa-scan.service/timer, secrets.env.example; intraday.signalbot.production_cycle ve üç test. systemd beş dakika tetikler, kalıcı /var/lib/borsa state, 240sn koşu sınırı. Açık takvim kapısı + kapanmış15dk NQ barının kapanıştan veri yaşı >15dk hata, stage/forward skip hataları exit1. Dış heartbeat yalnız başarılı açık-piyasa turunda. Anahtarlar dosyada yok.

Altı odak testi geçti. Yerel gerçek veriyle dry-run 7 Ekim 22:27TR: veri yaşı12,05dk, yeni Sweep/mobil adayı0. Bu Telegram gerçek teslim testi veya sunucu canlı çalışma kanıtı değil. Gölge süreç ve cache/state aktarımı tamamlanmadan GitHub kapatılmayacak.

Oracle Always Free incelendi: yeni resmî A1 sınırı toplam2OCPU/12GB; home region, konsolda0 maliyet ve Always Free etiketi şart. Kapasite yokluğu ve idle reclaim koşulları var, kesintisizlik garantisi yok. Ücretsiz Render15dk hareketsizlikte uyuyor ve bu iş için sürekli worker yerini tutmaz.

Henüz Oracle hesabı/SSH hedefi yok; deploy yapılmadı. Paket ilk host taşıma katmanı. Ledger ve sinyal-event aynı üretim olayına bağlanması, kalıcı Telegram outbox/teslim makbuzu ve dış monitör entegrasyonu tamamlanmadan tüm bildirim eksikliği çözüldü denmeyecek. Seyrek sinyal/source paritesi altyapı taşımasından ayrı ölçülür.

Kaynaklar: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm ; https://render.com/docs/free
