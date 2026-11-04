# Borsa araştırma platformuna dönüşüm planı

Tarih: 2026-10-15. Kullanıcı sırası: plan → mevcut hâli ve özellikleri yedekle → dönüştür → farkları bildir.

## Amaç ve sınır

Mevcut Python araştırma altyapısının üzerine yerel tarayıcıdan kullanılan bir araştırma paneli kurulacak. İlk teslim: gerçek forward defterleri, kaynak bazında sonuçlar, veri/operasyon sağlığı, araştırma raporları ve deney kaydı. Panel mevcut çalışan tarayıcıyı değiştirmeyecek. Tick verisi veya yapay zekâ servisi varmış gibi gösterilmeyecek.

Emir işlemleri yok. Sweep LIVE yetkisi manuel emir anlamındadır. EMA12 PAPER, CAND sessiz ölçüm ve emekli stratejiler ayrı gösterilir. MT5/bulut kayıtları toplanmaz; backfill gerçek zamanlı gözlemden ayrılır. Olumlu backtest LIVE yetkisini değiştirmez. Yeni hipotez/parametre taraması başlatılmaz.

## Sıralı çalışma

1. [x] Bu planı oluştur.
2. [ ] Graphify scoped sorguları ile defter, metrik, rapor ve veri adaptörlerini bul. Obsidian'da Borsa alt-MOC üzerinden ilgili tekil notlara git; kök MOC'u yeniden okuma.
3. [ ] Kod değişikliğinden önce mevcut tracked/untracked kaynakları, görev betiklerini, dokümanları ve küçük state/ledger dosyalarını zaman damgalı dış klasöre kopyala. Git HEAD/diff/status ve dosya SHA256 envanteri kaydet. Büyük veri cache'lerini ayrıca listele; hariç tutulanları açıkla. Sırları ekrana/loga basma. Özellik envanteri ve geri dönüş talimatı yaz. Hash ile kopyaları doğrula. Mevcut çalışma için test başlangıcını kaydet; mevcut hataları saklama.
4. [ ] Mevcut Python kalıplarıyla ayrı bir panel paketi kur. Ağdan veri/emir çekmeyen salt okunur adaptör; dosyaların eksik/bozuk/bayat oluşunu açık göster.
5. [ ] Kaynak/modül/provenans filtreli forward tablosu ve R eğrisi, açık sanal pozisyonlar, rapor kataloğu, veri sağlığı ve ön kayıtlı deney notu oluşturma ekle. Deney kaydı yalnız kendi panel klasörüne yazılır; yürütme otomatik başlamaz.
6. [ ] Gerekirse kayıtlı backtest çıktılarının detay görünümünü ekle. Genel amaçlı serbest kod çalıştırma veya yeni optimizasyon yok; yeni motor özelliği taklidi yok.
7. [ ] Hesap/provenans/path güvenliği testleri, yerel HTTP kontrolü ve tarayıcıyla kullanıcı akışı doğrulaması yap. Kod incelemesi uygula. Görevleri veya defterleri değiştirmediğini kontrol et.
8. [ ] Graphify update ile haritayı yenile. Kullanım kılavuzu, eski-yeni farkları ve bilinen sınırları yaz. Kalıcı kararı Obsidian tek konu notu + alt-MOC linki + MEMORY pointer olarak kaydet.

## Tasarım kararı

İlk aşamada yerel Python servis + hafif tarayıcı arayüzü tercih edilir: mevcut ortamla çalışır, abonelik veya ayrı sunucu gerektirmez. Streamlit hızlı alternatif; React/ayrı API daha kapsamlı ama bağımlılık ve bakım yükü daha fazla. Mevcut depo incelendikten sonra en az bağımlılıklı seçenek kesinleştirilecek.

Panelde araştırma sonucu, gerçek zamanlı sanal forward ve gerçek broker gerçekleşmesi birbirine karıştırılmaz. Veri zaman damgası yalnız ilgili dosyanın söylediği ölçüde gösterilir; dosya değiştirilme zamanı canlı piyasa kapsaması sayılmaz. Birleşik portföy getirisi hesaplanmaz.

## Kabul ölçütleri

- Yedek konumu ve doğrulama sonucu kayıtlı; kaynaklar geri yüklenebilir.
- Ekrandaki sayılar dosyadan gelir; örnek veri gerçek veri görünümünde kullanılmaz.
- Kaynaklar ve backfill ayrılır; bozuk R/eksik kolon sessizce başarılı sayılmaz.
- Panel başlatma komutu çalışır; filtreleme, rapor açma ve deney kaydı doğrulanır.
- Eski çalışan bileşenlerin yetkisi/risk/planlanmış görevleri değiştirilmez.
- Bu teslimin tick motoru, lisanslı veri veya AI strateji üretimi içermediği açıkça yazılır.

## İlerleme / kanıt

- Yerel HEAD: ea74970 (önceki inceleme). Git pull yerel değişiklikler ve untracked çakışmaları yüzünden tamamlanmadı; zorla temizleme/stash yapılmayacak.
- Uygulama ve yedek tamamlandı. Ayrıntı: HANDOFF/arastirma_paneli_2026-10-15.md.

- Yedek: ../borsa-backups/20261015-175350-before-research-panel; 724 doğrulanmış dosya, 172 hariç dosya, Git bundle başarılı.
- İlk panel: bağımlılıksız yerel Python HTTP + HTML/CSS/JS; kullanıcı akışları tarayıcıda kontrol edildi.
- Yeni özellik sınırı: backtest arşivi mevcut; yeni backtest çalıştırma/tick/AI/replay yok.
- Veri bulgusu: iki kaynakta üçer geçersiz çıkış zamanı; ilgili modüller panel metriklerinde karantinada.

## 15 Ekim ek teslim — güncellik

- Backfill kayıt filtresi açıklaması ve modül bazında normal/tarihsel sayıları eklendi.
- MT5 PAPER defteri --warmup 1 --no-notify ile ilerletildi; emir veya Telegram gönderilmedi.
- GitHub bulut defteri commit/hash doğrulamalı ayrı mirror olarak bağlandı; dirty yerel dosyalar korunur.
- Windows sync5dk/logon + panel logon görevleri kuruldu; ekran30sn yenilenir.
- Son işlenen mum, ölçüm ve indirme zamanları ayrı/TR gösterilir; PC kapalıyken yerel ölçüm çalışmaz.
- Kanıt/sınırlar: HANDOFF/panel_guncellik_2026-10-15.md.

## React ve motor bağlantısı — kullanıcı başlama izni 2026-10-15
- [x] Panel yedeği, React siyah/gri arayüz, tek strateji görünümü.
- [x] MT5/bulut ortak dönem ve eşleşen işlem karşılaştırması; backfill ayrıntıda.
- [x] Yetki ve kanıt ayrımı; küçük örneklem/veri uyuşmazlığı gerekçeleri.
- [x] Sabit strateji + yerel önbellek + maliyet/tarih seçimiyle honest_engine iş kuyruğu.
- [x] Sürüm/veri hash'i ve kalıcı iş raporu; test, bağımsız inceleme, tarayıcı kontrolü.


## React teslimi — tamamlandı
- [x] Siyah/gri React sayfa; MT5/bulut ayrı görünür, backfill ayrıntıda.
- [x] Kanonik ortak dönem kaynak eşleme; yetki/kanıt ayrımı ve gerekçeler.
- [x] Sabit strateji, yerel OHLCV, tarih, maliyet -> mevcut honest_engine iş kuyruğu.
- [x] Kalıcı sonuç/config/veri/kod hash'leri; restart ve kaynak değişimi koruması.
- [x] 45 panel testi; geniş grupta339 passed/1 skipped; npm build/node check; bağımsız inceleme APPROVE.
- [x] Tarayıcıdan gerçek sabit Sweep backtest işi tamamlandı. Detay: HANDOFF/react_panel_motor_2026-10-15.md.

## Tek kaynak kararı — 2026-10-15
- Kaynak: Maven MT5. Panel ve yeni backtestlere bulut/Yahoo/Dukascopy karışmaz; eksik veri başka feed ile doldurulmaz.
- Yerel CSV içindeki Binance BTC satırları broker kaydı sayılmaz.
- Kapalı broker mumları hash doğrulamalı ayrı snapshot, 30dk/logon gizli görev.
- MT5 kapalıysa ölçüm yok uyarısı; terminal kendiliğinden açılmaz. Eski durma taahhütleri ve LIVE/risk tablosu değişmez.


## Tek kaynak teslimi tamamlandı
- [x] MT5-only ana panel, bulut ve farklı-feed eski işler arşiv.
- [x] Binance yerel kayıtları Maven diye sayılmaz; eski broker kimliği eksikliği açıklanır.
- [x] Yeni forward Maven connected/server kontrolü ve provenance.
- [x] Hash doğrulamalı broker kapalıbar geçmişi, seçili immutableid pinleme, yeni backtestlere aynı feed.
- [x] Logon/5dk brokerhistory kontrolü; her çift günlük1tamaktarımı. (Önceki30dk ifadesinin yerini alır.)
- [x] Kullanıcı MT5açtı;5gerçekbrokerdatasetalındı; tarayıcıdanMavenbacktesttamamlandı.
- [x]54paneltest,geniş329passed1skipped,bağımsızincelemeAPPROVE. DetayHANDOFF/tek_ana_kaynak_2026-10-15.md.


## Faiz kararı araştırması — 2026-10-15
- Kullanıcı seçimi: PRE/POST ayrı, her birinde 24h/aynı gün kapanışı. Sonuçlara bakıp tüm geçmişten kazanan seçilmez.
- Ön kayıt: strategy-lab/outputs/intraday/rate_event_research/PROTOCOL.md.
- Önce 43 FTMO forex sembolü, fiyat/beklenti/metin erişim zamanı denetimi.
- Ana test eksik konsensüs ile çalıştırılmaz; ayrı FED_MP1_DELAY30 vekil pilotunun kapsamı açıkça yazılır.
- Canlı motor, Maven kaynak politikası, risk, defterler ve emir yetkisi değişmez.

- [x]43 sembol/8 mevcut35eksik fiyat envanteri, üç resmî Excel arşivi, hash manifest ve protokol.
- [x] Ayrı Fed MP1 vekil pilotu tamamlandı;3test,bağımsızinceleme onay,graph güncel.
- [ ] Tam PRE/POST x24h/kapanış: tarihli konsensüs ve ton serisi eksik; henüz kârlılık sonucu yok. Detay REPORT.md.
