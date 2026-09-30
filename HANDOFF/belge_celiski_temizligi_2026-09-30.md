# Güncel belgeler ve çelişki temizliği — 2026-09-30

İkinci denetimde kalan çelişkiler bulundu ve düzeltildi. Kapsam: aktif repo kullanım/talimat sayfaları, telefon akışı, kod kayıt listeleri, GitHub karşılıkları ve Borsa MOC üzerinden bağlanan güncel/historik detay notları. Tüm vault’un bütün konuları yeniden yazılmadı.

- Aktif listeler: Sweep LIVE, ayrı EMA12 PAPER. EUR/GBP London ve eski NQ ORB/Gold emekli. Yeni London girişleri yok; açık eski sanal pozisyon varsa yalnız sonuçlandırma yolu var.
- EUR güncel sürüm n14/+3,812R (7 Ağustos–24 Eylül); n16 iki eski-konfig Temmuz satırı içeriyordu. Emeklilik gerekçesi negatif EUR forward değildir.
- Repo SIGNALBOT_STATUS eski beş/yedi modüllü metni HANDOFF/archive/signalbot_status_before_2026-09-30.md içine taşındı; kısa güncel sayfayla değiştirildi. Eski aktif London dedektörü runtime’dan çıktı, araştırma aynası ve ham CSV kanıtı korundu.
- AGENTS/CLAUDE, telefon kısa/tam/master talimatları ve mobil aç/kapa akışı güncel statüye bağlandı. EMA12 kullanıcı onaylı ayrı PAPER istisnası belirtildi.
- Üç ray güncel özetindeki EUR/GBP PAPER ifadesi düzeltildi. Eski SignalBot/Forward EA/Canlı Plan/Pano notları tarihsel etiket aldı. Panonun “her sabah güncel” iddiası kaldırıldı. MOC güncel karar ve kapsam denetimine yönlendirildi.
- London Windows görevi yok. Kayıtlı NQ-Mobile 16:00–20:00/5dk, Telegram-Defter her dakika, kapsam alarmı 20:10. Sabah 10:00–14:00 RSS kapsamı artık varsayılmaz. Eski görev anlatımları güncel talimat olarak kullanılmaz.
- 9 CAND_ sessiz deney hâlâ arka planda; EUR/GBP emekliliği onları kaldırmadı. Gold makro+COT veya Sweep makro+COT sonucu yeni LIVE kurala dönüşmedi.
- Dokümantasyon GitHub commit: 1bd2b473283c903185efd49b1cc0b9c0089b44a8. Remote içerik üzerinde sınırlı dönüşüm uygulandı; diğer kullanıcı değişiklikleri ezilmedi.

Doğrulama: aktif kullanım sayfalarında eski EUR/GBP PAPER/London görevi tanımları arandı; kalan eşleşmeler emeklilik/tarihsel açıklamadır. default_modules yalnız Sweep; forward_test_modules içinde EUR/GBP yok; London detector runtime dosyasında yok; emekli pozisyon yöneticileri yeni sinyal üretmez. Önceki emeklilik tam testleri 556 passed/3 skipped; son tur belgesel açıklama değişiklikleri ve kayıt kontrolleridir. Bu doğrulama gün içi tarama/Telegram teslim sorununu çözülmüş saymaz.

Açık operasyon sorunları: 30 Eylül 3/21 yerel mobil kapsam, 0 pencere içi bulut koşusu; EMA12 ilk gerçek forward/teslim henüz doğrulanmadı; NQ-Mobile Windows hata kodu 1’in nedeni çözülmedi.

İlgili: [[Borsa - Guncel Edge ve Filtre Kararlari 2026-09-27]], [[Borsa - EUR GBP London Emeklilik Karari 2026-09-30]], [[Borsa - Forward Kapsam Denetimi 2026-09-30]].
