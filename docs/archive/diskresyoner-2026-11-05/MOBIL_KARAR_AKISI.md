# Android'de makro + çapraz piyasa + teknik karar akışı

> Güncel durum — 2026-09-30: Sweep tek LIVE yetkili mekanik modül; EMA12 ayrı PAPER gözlem. EUR/GBP London, NQ ORB ve Gold ORB emekli. Makro/COT sürümleri araştırma; LIVE filtre değil. Yeni EUR/GBP taraması ve forward girişi yok. Güncel karar: [karar tablosu](GUNCEL_EDGE_KARARLARI.md).


Güncelleme: 2026-09-28. TradingView açılmasa da kullanılacak düzen.

**PC'deki Codex'e telefondan erişim:** Aynı hesapla ChatGPT mobil uygulamasında Remote bölümünü kullan. PC uygulamasında Settings > Connections > Control this Mac or PC üzerinden eşleştirme QR kodunu aç ve telefondan okut. Özelliğin hesabında görünmesi gerekir; PC/uygulama açık ve çevrimiçi kalmalıdır. Normal bir mobil sohbet kendiliğinden bu klasöre erişmez. [Resmî bağlantı rehberi](https://learn.chatgpt.com/docs/remote-connections).

## Uygulamalar

| Görev | Ücretsiz tercih | Kullanım sınırı |
|---|---|---|
| Broker fiyatı ve emir | **MT5 Android** | US100 için gerçek emir fiyatı burada; grafik göstergelerini ana analiz ekranı olarak kullanmak zorunda değilsin. Android'in standart gösterge listesinde VWAP yok. [MT5 göstergeler](https://www.metatrader5.com/en/mobile-trading/android/help/chart/indicators) |
| Ücretsiz teknik özet | **Telegram izleme kartı** | Aday oluştuğunda NQ 15dk mumları, EMA20/50, NY nakit VWAP ve grafik aralığındaysa dünkü ilgili seviye tek resimde gelir; altında sayısal değerler, hacim, ADX/RSI, ES tepkisi ve veri saati vardır. Yahoo NQ vadeli akışı gecikmelidir ve Maven US100 fiyatı değildir. |
| Takvim ve çapraz piyasa listesi | **Investing.com Android ücretsiz sürümü** | Takvim, izleme listesi, temel fiyat/olay uyarıları ve haberler ücretsiz kullanılabilir; reklam ve uygulama içi ücretli seçenekler vardır. **InvestingPro alma**: değerleme, AI analiz ve reklamsız özellikler bu akış için gerekli değil. ABD 2Y/10Y, DXY, EUR/USD, altın, ES/NQ ve VIX'i izle; veri saatini kontrol et. [Android mağaza](https://play.google.com/store/apps/details?id=com.fusionmedia.investing), [takvim ve uyarı anlatımı](https://www.investing.com/academy/trading/how-to-read-an-economic-calendar/), [Pro planı](https://www.investing.com/pro/pricing) |
| İsteğe bağlı interaktif grafik | **GoCharting Android ücretsiz plan** | EMA ve diğer temel göstergeler ücretsiz planda listeleniyor; VWAP'ın seçtiğin sembolde ücretsiz açıldığını uygulamada sınamadan varsayma. Ücretsiz CME/NQ vadeli verisini anlık varsayma; [fiyat planı](https://gocharting.com/pricing) gerçek zamanlı CME verisini ücretli gösteriyor. Cihazda kasarsa kullanma. [Android uygulaması](https://play.google.com/store/apps/details?id=com.gocharting.gocharting) |
| 10 yıllık reel faiz / enflasyon beklentisi | **FRED mobil tarayıcı** | [DFII10](https://fred.stlouisfed.org/series/DFII10) ve [T10YIE](https://fred.stlouisfed.org/series/T10YIE) günlük serilerdir; 5–15 dakikalık giriş teyidi değildir. |

**Telefon ayarı:** Telegram ve Investing bildirimlerine izin ver. MT5'te brokerin US100 sembolünü favorilere al ve emir ekranını kullan. GoCharting ağır çalışırsa onu çıkar; ücretsiz ana düzen Telegram grafiği + Investing takvimi + MT5 emridir. TradingView'i sonradan düzeltmek istersen Android System WebView ve Chrome'u güncellemek [TradingView'in resmi önerisi](https://www.tradingview.com/support/solutions/43000616728-android-my-chart-is-not-displayed-correctly-buttons-on-the-chart-do-not-work/).

**GitHub taramasına yedek:** Investing'de US100/NQ için kendi veri akışındaki önceki gün yüksek/düşük fiyatına yakın fiyat alarmı ve önemli takvim olayları için uyarı kur. [Investing fiyat ve olay alarmları](https://www.investing.com/alerts/) mobil bildirim verebilir. NQ akışı gecikmeliyse bu alarm da gecikmelidir; gerçek giriş teyidi MT5'te kalır.

## Telefonda karar formülü

1. **Olay:** Investing takviminden olay saatini, açıklama öncesi beklentiyi ve açıklanan/revize sayıyı al. Haber yoksa bunu yaz; haber üretme.
2. **Tepki:** 2Y/10Y, DXY, ES/NQ, altın ve EUR/USD'yi olay *öncesi* düzeye göre karşılaştır. DXY ile EUR/USD aynı dolar hareketini kısmen tekrar eder; iki bağımsız oy sayma. Nominal faizi gerçek zamanlı reel faiz diye sunma. Uyumsuzluk gelecekte zorunlu yakınsama değildir.
3. **Seviye:** Telegram grafiğindeki NQ seviyesinin **Maven US100 fiyatına birebir taşınamayacağını** hatırla. Grafikteki veri saati 35 dakikadan eskiyse uyarıyı güncel işlem gerekçesi yapma. Gerçek broker fiyatını MT5'ten kontrol et.
4. **Tetik:** Telegram'daki EMA20/50, VWAP, ADX, RSI ve hacim geçmiş kapanmış NQ barının bağlamıdır. EMA trendi, VWAP seans konumunu, ADX hareketin gücünü, RSI aşırılığı, ATR stop genişliğini anlatır; ayrı ayrı oy vermez. İnteraktif grafik ihtiyacında GoCharting ücretsiz sürümünü deneyebilirsin. **Giriş anındaki US100 fiyatı ve emir koşulu yalnız MT5 broker akışından doğrulanır.**
5. **Karar:** Mevcut kapıdan en az 2/4 (makro anlatı, hacim, trend, seviye) dolu olmalı; güçlü zıt tepkiyi ayrıca açıkla. Giriş, stop, hedef, tez, çürüten, güncel bakiye/hesap güvenliği yaz. **AL / PAS / BEKLE** kararını sen ver, emri yalnız MT5 Android'de elle aç. Adayı girişten önce diskresyoner deftere kaydet; kayıt yapılamıyorsa yapılmış gibi davranma.

**Telefondan ön kayıt:** Botla özel sohbette `YARDIM` yaz; kısa Türkçe açıklama verir. Kopyalanacak ayrıntılı kayıt biçimi için `ORNEK` yaz. Aday için `ADAY|US100|long|tetik=...|stop=...|hedef=...|katmanlar=trend,destek|yontem=SWEEP_CORE_AVOID_MID_VWAP|tez=...|curuten=...` biçimini gerçek seviyelerin ve kendi tezinle doldur. Bot geçerli kaydı mevcut diskresyoner CSV defterine yazar ve `ADAY #id` onayı verir. `PAS|id=...|sebep=...` pas kararını deftere; `BEKLE|id=...|not=...` kararı ayrıca not dosyasına yazar, aday defterde açık kalır. MT5'te emri **kendin açtıktan sonra** `ACILDI|id=...|giris=...|acilis=YYYY-MM-DD HH:MM` ile gerçek açılış saatini TR olarak bildir. Bot sadece defteri günceller; brokerda emir açmaz, kapatmaz veya değiştirmez. `DURUM` sadece isteğe bağlı defter özeti gönderir. Yanıt gelmediyse kaydın yapıldığını varsayma. PC/oturum/internet kapalıyken acil yedek olarak Telegram Kaydedilen Mesajlar'a zaman damgalı ön kayıt bırak; bu yedek otomatik CSV kaydı değildir.

Bu akışın kayıtlı NQ karar penceresi hafta içi **18:15–20:00 Türkiye saati**. Bu pencere dışındaki seanslar için ayrı ölçülmüş kural gerekir. Mevcut mekanik LIVE sinyali, yeni diskresyoner izleme mesajından ayrıdır.

## Telegram mesajları ne demek?

- **Planlı brifing:** Günlük fon özeti ve boş piyasa tekrarı 2026-09-28'de durduruldu; `telefon_brief` GitHub workflow'u devre dışı. BRIEF kendiliğinden güncelleniyor varsayma; tarihine bak veya yeniden üret.
- **Mekanik LIVE/PAPER sinyali:** `signalbot` kendi ölçülmüş modüllerini tarar; sadece geçerli yeni setup oluşunca yazar. LIVE ile PAPER etiketi kesinlikle karıştırılmaz.
- **MT5 teyidi:** PC'de broker terminali açıksa aday kartında güncel broker bid/ask/spread ve istek üzerine bakiye bulunur. Tick 60 sn veya hesap özeti 120 sn üstündeyse teyit geçersiz sayılır; bilgi yokken hesap güvenliği kontrol edilmiş varsayılmaz.
- **DİSKRESYONER İZLEME:** NQ 15dk kapanmış barda önceki NY günü yüksek/düşüğüne en fazla 0,5 ATR yaklaşır **veya** aynı New York 15dk saatindeki hacim önceki en az 10 gözlemin medyanının ≥1,3 katıyken EMA yönünde NY nakit seansı VWAP'ını geri geçer. Her gün ve seviye/tür için en çok bir kez bildirilir. Bu yalnız **birinci aşama**, yani telefonu açıp kontrol et çağrısıdır.
- **Grafik eki:** İzleme kartı resimle gönderilir; resim üretimi/teslimi başarısızsa aynı bilgi metin olarak gelir. Görsel NQ 15dk geçmiş kapanmış mumlardan üretildiği için US100 broker grafiği veya anlık NQ verisi değildir.
- **Ek hareket uyarıları:** NQ'da bir saatte mutlak ≥%1 hareket; veya EMA20/50 sıralaması, ADX≥25, mutlak ≥%0,5 hareket ve aynı-saat hacmi≥1,3x birlikte oluşursa izleme bildirimi. Eşikler bildirim seçimi içindir; ölçülmüş edge veya yeni LIVE filtresi değildir. Gün ve olay türü başına bir kez; daha sonra aynı yönde büyüyen hareket için kademeli tekrar henüz yok.
- **Makro/haber:** Yerelde kayıtlı NQ görevi 16:00–20:00 TR penceresinde çalışır; London görevi 30 Eylül’de kaldırıldı, 10:00–14:00 haber kapsamı artık varsayılmaz; takvim olayı −15/+60 dk aralığında bildirilir. Haber kaynakları Investing.com'un ücretsiz Forex, Ekonomik Veriler ve Borsa RSS kategorileri ile resmî ECB/BoE duyuru RSS'leridir; BBC çıkarıldı. ABD/İngiltere/Avro Bölgesi merkez bankası ve temel veri başlıkları ile piyasa genelinde kesinti/çöküş başlıkları için HTTPS kaynak bağlantısı şarttır. Resmî ECB/BoE akışlarında yalnız faiz/para politikası kararı başlıkları bildirilir. Genel ticaret savaşı, şirket/ürün haberleri ve tahmin yazıları bildirilmez. Türkçe kategori yazılır; ayrıntı kaynak bağlantısında doğrulanır. Takvimde resmî BLS/Fed/BEA kaynakları kalır. Finnhub yalnız GitHub’da ayrı bulut haber adımıyla çalışır; yerel RSS hattına karışmaz. FRED ekonomik seri, LSE fiyat/veri kaynağıdır; canlı haber değildir. Forex Factory takvimi telefonda ücretsiz çapraz kontrol içindir; site koşulları nedeniyle bot tarafından kopyalanmaz. Yahoo tarama/fiyat verisi içindir; haber RSS kaynağı değildir. RSS son dakika terminali değildir, her olay veya beklenti/gerçekleşen kapsanmaz. Kaynakta bulunmayan sayı yazılmaz.
- **İkinci aşama:** Investing'de olay/çapraz piyasa, MT5'te broker grafiği, 2/4 kapısı ve risk insan tarafından doğrulanır. Bildirimde AL yazmaması bilinçlidir; izleme fırsatının kârlılığı henüz ölçülmemiştir.

Tarayıcı Yahoo `NQ=F` verisini kullanır; NQ vadeli ile Maven US100 farklı fiyat akışlarıdır. Watch mesajı, 35 dakikadan eski kapanmış barı veya pencere dışını göndermez. GitHub'ın [zamanlanmış işlerindeki gecikme/atlama olasılığı](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows) nedeniyle mesaj gelmemesi otomatik olarak “piyasada fırsat yok” anlamına gelmez. Mekanik tarayıcının logu ile ayrı izleme adayı logu kontrol edilmelidir.

**Yerel gerçek tarayıcı:** 2026-09-28'de Windows'a kuruldu. Hafta içi NQ 16:00–20:00 TR beş dakikada bir; mobil fiyat izleme 18:15–20:00. PC, kullanıcı oturumu ve internet açık olmalı. `.signalbot/local_scanner.log` koşu sonucunu, `mobile_health.jsonl` taze veri kontrollerini tutar. 20:10 alarmı 21 adet beş dakikalık dilimin yerel kapsamı eksikse bildirir. GitHub yedek tarayıcı olarak kalır; yerel devir geçişinde aynı aday iki kaynaktan gelebilir ve iki bağımsız fırsat sayılmaz. Otomatik MT5 emri yoktur.

**29 Eylül ekleri:** MT5 salt okunur bağlamı ve Telegram komut defteri eklendi. Telegram köprüsü PC açıkken her dakika çalışır. Yerel sağlıklı koşu GitHub'a kısa devir bilgisi yazar; bulut kuru taramaya geçer, PC susarsa yaklaşık 8 dakika içinde tekrar bildirim gönderebilir. Devir anında iki ayrı kaynaktan aynı aday gelmesi hâlâ mümkün; teslim garantisi veya yeni edge iddiası yoktur.

**EMA12 PAPER forward (29 Eylül):** NY açılışının ilk 5dk mumunda kapanışın
EMA12 tarafı ayrı gözlem olarak kaydedilir. Giriş/stop/6 saat çıkış yalnız
varsayımsal R hesabıdır; Yahoo NQ=F verisi Maven US100 emri değildir.
PC ve GitHub aynı kuralı çalıştırır. PC sağlıklıyken bulut ikinci aday
mesajını bastırır; bulut sonuç defterini yine tutar. Bulut gecikmesi veya
devir anı sebebiyle tekrar/eksik mesaj olasılığı vardır. LIVE yetkisi yoktur.
EMA12 PAPER ölçümü 18:15–20:00 diskresyoner giriş saatine bağlı değildir;
NY ilk mum kapanınca izlenir. Gerçek diskresyoner emir protokolü ayrıdır.

**Haber mesajlarını ayır:** `PC HABERİ • RSS` ve `PC TAKVİMİ • RESMÎ KAYNAK` yerel PC'den; `BULUT HABERİ • FINNHUB` GitHub'dan gelir. Finnhub yalnız piyasa genelinde işlem kesintisi/çöküş veya açıkça acil, plan dışı merkez bankası duyurusu başlıklarını seçer; olağan veri haberlerini tekrar etmez. Kartlar yayın saati, Türkçe olay türü, ilgili izleme, kaynak ve bağlantı verir. Özgün İngilizce başlık yalnız Finnhub kartında doğrulama için bulunur. Aynı olay iki kaynakta görünürse tek olay say; hiçbir haber kartı yeni setup veya yön önerisi değildir.

**PC'yi kapatıp açınca:** Windows Görev Zamanlayıcı'daki `Borsa-Signalbot-NQ-Mobile` (16:00–20:00), `Borsa-Telegram-Defter` (her dakika) ve `Borsa-Seans-Tarama-Alarmi` (20:10) kayıtlı kalır. Windows kullanıcı oturumuna tekrar giriş yapınca ve internet varken sonraki planlı tetikte çalışırlar; her açılışta CMD çalıştırma gerekmez. Bilgisayar kapalıyken yerel tarama ve Telegram defter yanıtı yoktur, GitHub bulut taraması/ayrı Finnhub kontrolü devam eder. MT5 broker fiyatı/bakiye bağlamı için terminal ayrıca açık olmalıdır. Görevlerin durumunu Görev Zamanlayıcı Kitaplığı'nda isimleriyle gör; bilerek durdurmak için ilgili görevi `Devre Dışı Bırak`, yeniden açmak için `Etkinleştir`. Yerel görevleri kapatmak GitHub'ı kapatmaz.

MT5 ölçüm telafisi: ayrıca kayıtlı ForwardEA-5dk görevi terminal açıkken her 5dk yalnız sanal defteri ilerletir. Terminal kapanınca state durur; açılınca erişilebilir eksik broker mumlarını sırayla işler. Emir vermez, eski/kapanmış fırsatı güncel Telegram çağrısı yapmaz. Üç Borsa-* görevi + ayrı ForwardEA görevi vardır. Ayrıntı: HANDOFF/mt5_telafi_temizligi_2026-09-30.md.
