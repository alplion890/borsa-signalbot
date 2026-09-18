# Android'de makro + çapraz piyasa + teknik karar akışı

Güncelleme: 2026-09-18. TradingView açılmasa da kullanılacak düzen.

## Uygulamalar

| Görev | Ücretsiz tercih | Kullanım sınırı |
|---|---|---|
| Broker fiyatı, teknik çizim, emir | **MT5 Android** | US100 için gerçek emir fiyatı burada. 15dk ve 5dk grafik; EMA20/50, ADX14, RSI14, ATR14, yatay seviyeler. MT5 Android'in 30 standart göstergesi arasında VWAP yok; Telegram'daki NQ VWAP'ı aynı broker seviyesi sanma. [MT5 göstergeler](https://www.metatrader5.com/en/mobile-trading/android/help/chart/indicators), [grafik](https://www.metatrader5.com/en/mobile-trading/android/help/chart) |
| Takvim ve çapraz piyasa listesi | **Investing.com Android** | ABD 2Y, 10Y, DXY, EUR/USD, altın, Nasdaq ve S&P 500 vadeli, VIX izle. Takvimde beklenti, açıklanan, önceki ve revizyonu ayrı oku; haber bildirimini aç. Her enstrümanın veri saatini kontrol et. [Uygulama](https://www.investing.com/mobile/), [takvim](https://www.investing.com/academy/trading/how-to-read-an-economic-calendar/) |
| Opsiyonel ikinci grafik | **GoCharting Android ücretsiz plan** | Seans VWAP ve daha geniş grafik araçları için dene; kendi Android cihazında akıcılığını sınamak gerekir. Ücretsiz CME/NQ vadeli verisini anlık varsayma: [fiyat planı](https://gocharting.com/pricing) ile [CME veri sayfası](https://gocharting.com/trading/market-data/cme) farklı ifadeler kullanıyor. NQ işlem girişini MT5 US100 fiyatından teyit et. [Android uygulaması](https://play.google.com/store/apps/details?id=com.gocharting.gocharting) |
| 10 yıllık reel faiz / enflasyon beklentisi | **FRED mobil tarayıcı** | [DFII10](https://fred.stlouisfed.org/series/DFII10) ve [T10YIE](https://fred.stlouisfed.org/series/T10YIE) günlük serilerdir; 5–15 dakikalık giriş teyidi değildir. |

**Telefon ayarı:** Telegram ve Investing bildirimlerine izin ver. MT5'te brokerin US100 sembolünü favorilere al; 1s/15dk/5dk grafikler arasında geç. GoCharting ağır çalışırsa onu çıkar, MT5 + Investing + Telegram yeterlidir. TradingView'i sonradan düzeltmek istersen Android System WebView ve Chrome'u güncellemek [TradingView'in resmi önerisi](https://www.tradingview.com/support/solutions/43000616728-android-my-chart-is-not-displayed-correctly-buttons-on-the-chart-do-not-work/).

**GitHub taramasına yedek:** Investing'de US100/NQ için kendi veri akışındaki önceki gün yüksek/düşük fiyatına yakın fiyat alarmı ve önemli takvim olayları için uyarı kur. [Investing fiyat ve olay alarmları](https://www.investing.com/alerts/) mobil bildirim verebilir. NQ akışı gecikmeliyse bu alarm da gecikmelidir; gerçek giriş teyidi MT5'te kalır.

## Telefonda karar formülü

1. **Olay:** Investing takviminden olay saatini, açıklama öncesi beklentiyi ve açıklanan/revize sayıyı al. Haber yoksa bunu yaz; haber üretme.
2. **Tepki:** 2Y/10Y, DXY, ES/NQ, altın ve EUR/USD'yi olay *öncesi* düzeye göre karşılaştır. DXY ile EUR/USD aynı dolar hareketini kısmen tekrar eder; iki bağımsız oy sayma. Nominal faizi gerçek zamanlı reel faiz diye sunma. Uyumsuzluk gelecekte zorunlu yakınsama değildir.
3. **Seviye:** Telegram izleme uyarısı geldiyse NQ'daki seviyenin **Maven US100 fiyatına birebir taşınamayacağını** hatırla. MT5 15dk/1s US100 grafiğinde kendi önceki gün yüksek/düşüğünü ve desteği/direnci çiz. Veri saati 35 dakikadan eskiyse uyarıyı güncel işlem gerekçesi yapma.
4. **Tetik:** MT5 15dk trend/EMA20-50 ve 5dk kapanmış mumla kabul/ret ara. Telegram'daki VWAP yalnız NQ bağlamıdır. ADX hareketin gücünü, RSI aşırılığı, ATR stop genişliğini anlatır; bunlar ayrı ayrı oy vererek işlem açtırmaz.
5. **Karar:** Mevcut kapıdan en az 2/4 (makro anlatı, hacim, trend, seviye) dolu olmalı; güçlü zıt tepkiyi ayrıca açıkla. Giriş, stop, hedef, tez, çürüten, güncel bakiye/hesap güvenliği yaz. **AL / PAS / BEKLE** kararını sen ver, emri yalnız MT5 Android'de elle aç. Adayı girişten önce diskresyoner deftere kaydet; kayıt yapılamıyorsa yapılmış gibi davranma.

Bu akışın kayıtlı NQ karar penceresi hafta içi **18:15–20:00 Türkiye saati**. Bu pencere dışındaki seanslar için ayrı ölçülmüş kural gerekir. Mevcut mekanik LIVE sinyali, yeni diskresyoner izleme mesajından ayrıdır.

## Telegram mesajları ne demek?

- **Planlı brifing:** 16:20 ve 18:15 hedefli durum, makro takvim ve NQ özeti. GitHub Actions gecikebilir; üretim/bar saatine bak.
- **Mekanik LIVE/PAPER sinyali:** `signalbot` kendi ölçülmüş modüllerini tarar; sadece geçerli yeni setup oluşunca yazar. LIVE ile PAPER etiketi kesinlikle karıştırılmaz.
- **DİSKRESYONER İZLEME:** NQ 15dk kapanmış barda önceki NY günü yüksek/düşüğüne en fazla 0,5 ATR yaklaşır **veya** aynı New York 15dk saatindeki hacim önceki en az 10 gözlemin medyanının ≥1,3 katıyken EMA yönünde NY nakit seansı VWAP'ını geri geçer. Her gün ve seviye/tür için en çok bir kez bildirilir. Bu yalnız **birinci aşama**, yani telefonu açıp kontrol et çağrısıdır.
- **İkinci aşama:** Investing'de olay/çapraz piyasa, MT5'te broker grafiği, 2/4 kapısı ve risk insan tarafından doğrulanır. Bildirimde AL yazmaması bilinçlidir; izleme fırsatının kârlılığı henüz ölçülmemiştir.

Tarayıcı Yahoo `NQ=F` verisini kullanır; NQ vadeli ile Maven US100 farklı fiyat akışlarıdır. Watch mesajı, 35 dakikadan eski kapanmış barı veya pencere dışını göndermez. GitHub'ın [zamanlanmış işlerindeki gecikme/atlama olasılığı](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows) nedeniyle mesaj gelmemesi otomatik olarak “piyasada fırsat yok” anlamına gelmez. Mekanik tarayıcının logu ile ayrı izleme adayı logu kontrol edilmelidir.
