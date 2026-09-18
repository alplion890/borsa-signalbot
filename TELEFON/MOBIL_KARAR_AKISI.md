# Android'de makro + çapraz piyasa + teknik karar akışı

Güncelleme: 2026-09-18. TradingView açılmasa da kullanılacak düzen.

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

**PC olmadan ön kayıt:** Telegram **Kaydedilen Mesajlar**'a emirden önce `ADAY | tarih-saat TR | US100 | long/short | tetik | stop | hedef | tez | çürüten | hangi 2/4 katman | veri saati` satırını gönder. Ardından `AL`, `PAS` veya `BEKLE` kararını ve nedenini ayrı satıra yaz. Bu zaman damgalı kişisel not, mevcut CSV diskresyoner defterine **otomatik aktarılmaz**; eve dönünce veya deftere erişen bir yardımcıyla aktarılınca ölçüme girer. Botun Telegram sohbetine cevap yazmak da şu an CSV'ye kayıt yapmaz.

Bu akışın kayıtlı NQ karar penceresi hafta içi **18:15–20:00 Türkiye saati**. Bu pencere dışındaki seanslar için ayrı ölçülmüş kural gerekir. Mevcut mekanik LIVE sinyali, yeni diskresyoner izleme mesajından ayrıdır.

## Telegram mesajları ne demek?

- **Planlı brifing:** 16:20 ve 18:15 hedefli durum, makro takvim ve NQ özeti. GitHub Actions gecikebilir; üretim/bar saatine bak.
- **Mekanik LIVE/PAPER sinyali:** `signalbot` kendi ölçülmüş modüllerini tarar; sadece geçerli yeni setup oluşunca yazar. LIVE ile PAPER etiketi kesinlikle karıştırılmaz.
- **DİSKRESYONER İZLEME:** NQ 15dk kapanmış barda önceki NY günü yüksek/düşüğüne en fazla 0,5 ATR yaklaşır **veya** aynı New York 15dk saatindeki hacim önceki en az 10 gözlemin medyanının ≥1,3 katıyken EMA yönünde NY nakit seansı VWAP'ını geri geçer. Her gün ve seviye/tür için en çok bir kez bildirilir. Bu yalnız **birinci aşama**, yani telefonu açıp kontrol et çağrısıdır.
- **Grafik eki:** İzleme kartı resimle gönderilir; resim üretimi/teslimi başarısızsa aynı bilgi metin olarak gelir. Görsel NQ 15dk geçmiş kapanmış mumlardan üretildiği için US100 broker grafiği veya anlık NQ verisi değildir.
- **İkinci aşama:** Investing'de olay/çapraz piyasa, MT5'te broker grafiği, 2/4 kapısı ve risk insan tarafından doğrulanır. Bildirimde AL yazmaması bilinçlidir; izleme fırsatının kârlılığı henüz ölçülmemiştir.

Tarayıcı Yahoo `NQ=F` verisini kullanır; NQ vadeli ile Maven US100 farklı fiyat akışlarıdır. Watch mesajı, 35 dakikadan eski kapanmış barı veya pencere dışını göndermez. GitHub'ın [zamanlanmış işlerindeki gecikme/atlama olasılığı](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows) nedeniyle mesaj gelmemesi otomatik olarak “piyasada fırsat yok” anlamına gelmez. Mekanik tarayıcının logu ile ayrı izleme adayı logu kontrol edilmelidir.
