# Maven 10K Instant — geçmiş bulgular ve başlangıç önerisi

30 Ekim 2026. Kullanıcı Maven 10K Instant alacağını bildirdi. Satın alma, hesap aktivasyonu ve yeni risk önerisinin kabulü doğrulanmadı. Bu belge çalışma önerisidir; mevcut LIVE/PAPER, bot, risk.py ve eski diskresyoner %3 ayarı değiştirilmedi.

## 1. Gerçekte incelenen geçmiş

Borsa MOC bağlantıları üzerinden güncel karar tablosu, diskresyoner makro/teknik akış, makro yön A/B, çapraz piyasa/COT/OI A/B, çoklu zaman dilimi A/B, portföy slot çalışması, faiz olayı pilotu, elenenler ve 29–30 Ekim motor/strateji/YouTube denetimleri incelendi. Her sohbetin her mesajı ve her tarihsel test bu oturumda yeniden okunup çalıştırılmadı. Eski notlardaki statü ve rakamlar sonraki düzeltmelerin önüne geçirilmedi.

## 2. Hesabın güncel matematiği

Resmî Maven FAQ ve 23 Ekim 2026 tarihli v2026.2 sözleşmesi kontrol edildi. Bu bir simüle hesap; uygun sonuçlar sözleşmeye bağlı nakit ödül doğuruyor.

- İlk günlük taban: 10.000 × 0,98 = 9.800 USD. Reset 00:00 UTC = 03:00 Türkiye; reset anında balance/equity yüksek olan esas.
- Trailing taban: en yüksek running equity × 0,97. Başlangıçta 9.700 USD; açık kâr da tabanı yükseltir.
- Toplam açık zarar: balance − equity, güncel bakiyenin %1'ini aşamaz; başlangıçta 100 USD. Her işleme ayrı 100 USD değildir.
- İlk çekim eşiği: en az 300 USD net hesap kârı, ödül payı öncesi. Standart pay %80; uygun 300 USD brüt çekim teorik 240 USD ödeme verir, diğer koşullar ayrıca geçerli.
- Consistency: en iyi kârlı gün / kârlı günlerin kâr toplamı ≤ %20. Zarar günleri bu paydaya girmez; net hesap kârını azaltır. Örnek: +60,+60,+60,+60,+60 ve −30 → consistency %20, fakat net270 USD: 300 USD çekim eşiği sağlanmaz.
- News Instant'ta serbest; emirler manuel. İşlemlerin en az yarısı ≥60 saniye; kaybı bu oranı korumak için bekletmek yok. 30 gün hareketsizlik kuralı var.

Kaynaklar:
https://maventrading.com/faqs (Instant Funding)
https://maventrading.com/terms-and-conditions (5.1–5.3,10.4–10.9,Schedule1–2)
https://maventrading.crisp.help/en/article/maven-instant-funding-account-rules-requirements-1fe2wd9/

### Çekimden sonraki tampon

Güncel sözleşme10.9: çekim highest equity'yi kendiliğinden sıfırlamaz; bakiye brüt çekim kadar azalır. Peak10.300, taban9.991, brüt300çekim sonrası balance10.000 → tampon9 USD. Günlük taban daha yüksekse alan daha da dar olabilir. Bu sadece örnek, kullanıcının gerçekleşmiş bakiyesi değil.
Eski Crisp destek yazısındaki başlangıç bakiyesine reset anlatımı yeni sözleşme karşısında güvenli varsayım değildir. Satın alınan ürün/sözleşme/dashboard esas alınarak destekten yazılı teyit alınmalı. Destek mesaj taslağı: “For a new $10,000 Instant account, if highest equity reaches $10,300 and I withdraw $300 gross, what exact balance, highest-equity reference and maximum-loss floor remain? Does any reset apply under clause10.9? Please confirm the accepted product rules in writing.” Mesaj gönderilmedi.

## 3. Geçmişten kullanılacaklar ve sınırları

| Çalışma | Gerçek bulgu | Bu hesapta kullanım |
|---|---|---|
| Sweep | Güncel uzun tarih tek defter235işlem, ort.+0,0485R; eski+0,132 doğrudan kullanılmaz | Mevcut manuel modül; seyrek sinyal yüzünden işlem kotası konmaz. Yeni hesap risk/maliyet uygunluğu ayrıca |
| NQ ORB | Uzun tarihte küçük pozitif; yakın Maven54işlem+10,15R, üçkatmaliyette+3,65R; negatif forward yüzünden emekli | Aile ölü değil; otomatik yeniden LIVE yok |
| Gold/EUR/GBP eski aileler | Uzun tarih Gold/EUR negatif; nedenselGBP44işlem yaklaşık−1,33R | Mevcut sürümleri fon hesabına paket halinde ekleme |
| DonchianGold1H | N20:848işlem, üçkatmaliyette ort.+0,0392R; N55depozitif | Çalışmıyor diye elenmedi; bağımsız yeni broker/prop test adayı, çokgün tutma ve equity yolu ölçülmeli |
| MACD+EMA200EUR30m | Araştırma uyarlaması37işlem+6,28R; iki kat+1,40R, üçkat−3,49R; sembol sonradan seçildi | PAPER adayı; fonun ana motoru ilan edilmez |
| NoiseBand |106işlem; nominal1xmaliyet+%3,14, üçkat−%0,73 | Başlangıç SL'siz araştırma sürümünü1%floatinglimite doğrudan taşıma |
| YeniBISTvideosu | Nasdaq4H vekil/çıkış uyarlaması77işlem−13,60R | Asıl XU100 yöntemi çürütülmedi; özgün strateji ve görsel inceleme tamamlanmış değil |
| Makro/COT/OI | Bazı altkümeler iyileşti; filtreler işlemi azalttı, genellenebilir zorunlu kapı gösterilmedi | Bağlam; hepsini üstüste zorunlu yapma |
| Haberöncesi beklenti | Zamanı doğrulanmış tarihsel konsensüs/ton eksik; tam43FXçalışması tamamlanmadı | “Çalışıyor/çalışmıyor” sonucu yok; canlı önkayıtla öğren |
| HabersonrasıFedpilot | Son9bağımsızolayda2pipvarsayımı sonrası+27,28bp/olay; seçimdönemi−0,08bp | İncelenmeye değer, R veya hesapgetirisi değil; stop/prop/spread testi eksik |

Eski AI rejim raporundaki dış-literatür iddiaları bu oturumda tek tek yeniden doğrulanmadı. Güvenilecek yerel sonuç: makrodan otomatik yön emri çıkarmadık; kullanıcının yorumlu akışının kârlılığını kanıtlayan güncel yeterli gerçek-icra defteri görülmedi. FVG/EMA dokunma oranları PnL testi değildir; tüm aileyi çürüttük demek hatalı. Zarar eden yöntemin tersini almak ayrı testtir.

## 4. Korelasyon masası

Başlangıç icra evreni önerisi US100 ve EURUSD; XAUUSD bağlam/PAPER. US500,GBPUSD,DXY,ABD2Y/10Y analizde izlenebilir. Bu seçim ölçülmüş optimum portföy iddiası değil, maliyet ve karar karmaşasını sınırlayan operasyon önerisi.

- NQ/ES: benzer endekslerin göreceli getirilerini aynı zaman aralığında ölç; 7endekse yayılma slot testinin zarar verdiği unutulmaz. Ayrışma otomatik karşıya yetişme sinyali değil.
- EURUSD/GBPUSD: aynı dolar olayına maruziyet olabilir. İki pozisyonu iki bağımsız fırsat diye sayma.
- EURUSDlong/USDCHFshort gibi ters fiyat hareketli paritelerde zıt emir yönleri aynı dolar riskini büyütebilir. Ters fiyat korelasyonu riskten korunma garantisi değildir; USDCHF için burada yerel ölçülmüş katsayı yok.
- DXY/EURUSD: mekanik örtüşme nedeniyle iki bağımsız teyit diye sayma. Güncel korelasyon katsayısı hesaplanmadı.
- Gold/reelfaiz/dolar: sabit ters ilişki varsayma; işaret döneme göre değişebilir. Günlük gecikmeli FRED verisini canlı intraday faiz tepkisi gibi sunma.
- Üç USDduyarlı varlığın aynı habere tepkisi üç bağımsız haber değildir. Analizde aynı zaman damgasını, işlemde aynı fikir için ortak risk bütçesini kullan.

## 5. Uygulama önerisi — kabul edilmiş politika değil

- İlk20gerçekişlem için toplam planlı zarar/fikir15 USD (%0,15başlangıçhesabı); spread,komisyon ve kayma payı dahil. Aynı fikirde iki pozisyon varsa toplam15 USD. İlk aşamada tek açık pozisyon önerilir.
- Günlük−30 USD veya2tamstopta yeni giriş durur; günlük2adayişlem üst sınır, işlem zorunluluğu değil. Haftalık−60 USDde yeni giriş durup inceleme yapılır.
- Risk kalan alan daraldıkça küçülür:15 USD sabit hak değildir. Stopta oluşacak equity hem dailyfloor hem trailingfloor üstünde güvenlik payıyla kalmalı; accountwidefloatinglosssınırı ayrıca denetlenmeli. Lotminimumu ve masraf15 USDye sığmıyorsa işlem pas.
- Eski %3risk=300 USD bu ürünün100USDfloatinglimitiyle uyumsuzdur. Eski otomatik lot kartları kullanılmaz; mevcut kod değiştirilmedi.
- Bu15/30/60eşikleri geçmişte optimize edilmiş kazanç ayarı değil, başlangıç gözlemine alan açan öneridir. 20işlemdenönce seri kazançla büyütme yok. n≥20veortalamaR<0ise mevcut diskresyoner durma ilkesi uygulanır. Pozitif20işlem de tekbaşına büyütme kanıtı değildir.
- 15 USDile300USD=20netR. Bu hedef/süre tahmini değil aritmetiktir. Örnek−1R/+2Rplanda masraflarRye dahilken12kazanç4kayıp20Reder; gerçekleşecek dağılım iddiası yok.
- Consistency için günlük kâr zorunluluğu konmaz.300USDtamamı kârlı günlerden geliyorsa en iyi60USDgün%20eder. Büyük gün ayrıcalık değil, çekim için gereken kârlı gün toplamını artırır; kârı bilerek geri verme yöntemi kullanılmaz.

## 6. Günlük somut akış

1.18:00–18:15hazırlık: resmîhaber saati, zaman damgalı konsensüs, önceki/revizyon; gün/hafta highlow ve fiyat/ATR mesafeleri; haber öncesi fiyat hareketi. Beklenen faiz kararını olasılık fiyatlamasıyla karıştırma.
2.Mevcut18:15–20:00yeni giriş penceresi korunur. Bu dışındaki haberlerde gözlem/PAPER; FOMC için seans kuralı kendiliğinden genişletilmez. ABDsaatlerini her olayda TRye çevir; sabit yaz/kış farkı kullanma.
3.Olayda gerçekleşen, beklentiden fark, revizyon ve açıklama birlikte kaydedilir. İlk saniye giriş zorunluluğu yok. Fiyat tepkisi için önceden seçilmiş5ve15dakika pencereleri kaydedilebilir; bunlar test edilmiş optimum giriş zamanı değildir.
4.Kullanıcı tezini kurar. En az2/4narrative,hacim,trend,seviye; aynı dolar verisini iki katman sayma. Girilecek fiyat tetikleyicisi, tezi bozan seviye, stop ve çıkış biçimi önceden yazılır. Sırf iyi/kötü veri etiketinden yön üretilmez.
5.Aynı grafik ve tetik türünü20işlem boyunca koru; her zararda yeni gösterge/TPtarama yok. Kısmiçıkış,stoptaşıma,zamanaçıkış seçilecekse giriştenönce koşulu yaz, sonuçtan sonra uydurma.
6.Girişte brokersembol/contractsize/tickvalue/lotstep/spread/komisyon doğrulanır. Risk kartı sinyal fiyatından değil gerçek broker fiyatından hesaplanır. Emir kullanıcıda.
7.Kapanışta netUSD/netR,tepe açık kâr,en kötü açık zarar,holdingtime,maliyet,kurala uyum ve pasgeçilenadaylar kaydedilir. Haber öncesi ve sonrası işlemler ayrı etiketlenir.

İşlem kartı:
Hesap / balance / equity / peak-equity / dailyfloor / trailingfloor / floatingloss
Olay-saati / konsensüs-kaynak-saati / gerçekleşen / revizyon
Sembol / PRE veyaPOST veyaSWEEP / kişiseltez / çürüten
Tetik / stop / çıkışkuralı / lot / toplammasraflıUSD-risk / ilişkiliaçıkrisk
SonuçnetUSD / netR / MFE / MAE / süre / süreçihlali

## 7. İlk işlemden önce operasyon

30Ekimokunan runner.logsonunda MT5terminalikapalı hatası var. forward_stateupdated_at15Ekim; BRIEF25Eylül. Son araştırma snapshotları15Ekimdebitiyor. Bunlar bugün canlı sinyal/veri çalışıyor demek değildir. Satınalmasonrası doğru Mavenhesabı/platformu,sembolözellikleri,kapalıbargüncelliği ve son doğrutarama ayrı doğrulanmalı. Eski backfill ve PAPER gerçekicra gibi sayılmaz.
Gitpullindex.locksebebiyleengellendi;kilit kaldırılmadı. Bu belge yerel dosya/not incelemesine dayanır, sonremote ile senkronidiası yok.

Öncelik: çalışan veri ve hesap kuralları → tek kayıtlı karar yöntemi → 20 gerçek işlemde icra/maliyet kontrolü → çekim uygunluğu ve çekim sonrası tampon hesabı. Yeni strateji araştırması ayrı PAPER defterde sürer.
