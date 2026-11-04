# Ücretsiz sunucuya taşıma hazırlığı — 7 Ekim 2026

DURUM: Hazırlık paketi. Henüz sunucu oluşturulmadı veya canlıya alınmadı.

Tercih: Oracle Always Free Ubuntu VM, home region. Console maliyet tahmini 0 olmalı; trial kredisiyle ücretli kaynak açılmayacak. Mevcut resmî sınır A1 için toplam 2 OCPU/12GB; daha küçük 1 OCPU/2GB ile başlamak yeterlilik testine tabidir. Ücretsiz kapasite bulunmayabilir; Oracle düşük kullanım koşullarında makineyi geri alabilir. Kesintisizlik garantisi yok.

## Somut kurulum

1. Ubuntu sunucu, SSH anahtarı ve giriş IP'si sağlanır; erişim testi yapılır.
2. Repo doğrulanmış commit ile /opt/borsa'ya alınır. python3-venv kurulup /opt/borsa/.venv oluşturulur; signalbot requirements yüklenir. ARM bağımlılıkları önce test edilir.
3. Ayrı `borsa` sistem kullanıcısı oluşturulur. Kalıcı state dizini /var/lib/borsa/.signalbot; secrets /etc/borsa/secrets.env (0600, root).
4. Dosyalar systemd dizinine alınır. Önce gerçek Telegram kapalı tek deneme; sonra kullanıcı tarafından yetkilendirilmiş teslim testi ve 24 saat gölge çalışma.
5. Gölge ölçüm sırasında ikinci Telegram üreticisi açılmaz. VPS doğrulanınca GitHub ana signalbot zamanlayıcısı kapatılır; eski state dosyaları korunur. MT5 emir/broker teyidi ve yerel RSS kaynağı ayrı kalır.
6. Geçiş state'i en son tamamlanmış GitHub cache'inden alınmalıdır. EMA12 state'i eksikse canlı bildirim açılmaz; başlangıçtan eski kayıtları yeni sinyal diye üretmek önlenir.

## Kabul şartları

- Piyasa açıkken her5dk gerçek tarama; 15dk üstü veri gecikmesi hata olarak görünür.
- Veri saati ve başarılı tarama saati ayrı sağlık kayıtları.
- Ayrı dış izleyici 15dk heartbeat yokluğunda alarm üretir. Aynı makinedeki kontrol tam makine kesintisini haber veremez.
- Kalıcı state restart sonrası korunur. Kapalı piyasa takvim kapısı korunur.
- API/Telegram hatası başarılı koşu sayılmaz. Telegram API kabulü telefonda okunma garantisi değildir.
- Host taşıması fiyat kaynağı farkını veya seyrek sinyali gidermez. Tick kaynaklı MT5/bulut paritesi ayrı denetlenir.
- Bu ilk paket existing scan yolunu taşır. Tek sinyal-event/forward ledger + kalıcı outbox/teslim makbuzu bağlantısı ayrıca tamamlanmadan tam teslim güvenilirliği iddia edilmez.

## Çalışma

systemd timer tüm gün tetiklenir; Python takvim kapısı yalnız izinli gündüz penceresinde veri tarar. Oneshot servis çakışan ikinci koşu başlatmaz. 240sn sınırı takılmış işi sonlandırır; sonraki5dk tekrar dener. State cache yerine kalıcı diskte tutulur. Emir executor çağrılmaz.

Kaynak: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
