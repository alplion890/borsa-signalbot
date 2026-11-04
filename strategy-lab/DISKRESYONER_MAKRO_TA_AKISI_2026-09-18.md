# Diskresyoner makro + çapraz piyasa + teknik karar akışı

Tarih: 2026-09-18. Bu not kullanıcının anlattığı **mevcut araştırma/karar yöntemini** kaydeder; yeni mekanik edge veya canlı kural ilan etmez. Kullanıcının son mesajı “bide” ile bittiği için ek koşul henüz açıklanmadı.

## Kullanıcının kastettiği sıra

1. **Olay ve temel tez:** Faiz artırımı/indirimi, CPI ve istihdam gibi makro açıklamalar; merkez bankası/devlet kararları; şirket bilançosu, sermaye artırımı, ürün ve sektör haberleri. Olayın önceden beklenen kısmı, yeni bilgi, yayın saati ve olası alternatif yorum ayrılır.
2. **Çapraz piyasa tepkisi:** NQ/ES, DXY, nominal ve reel tahvil getirisi, enflasyon beklentisi, EUR/USD ve altın gibi *ilgili* serilerin olaydan sonra ters/paralel tepkisi izlenir. Fiyatın teze uyumu veya uyumsuzluğu karar bağlamıdır; tek başına al/sat sinyali değildir.
3. **Zaman ve likidite:** Aday işlem enstrümanına uygun Londra/New York gibi etkin seanslarda ve ilan edilen haber saatine dikkat edilerek değerlendirilir; olağan dışı sığ saatlerde sırf gösterge kesişti diye işlem açılmaz.
4. **Fiyat yapısı ve giriş:** Destek/direnç, gün/hafta seviyeleri ve fiyatın bu seviyelerdeki tepkisi okunur. VWAP/EMA ile trend, kabul/ret ve geri çekilme değerlendirilir; diğer göstergeler ancak tanımlı işlevleri varsa kullanılır. Giriş için gözlenebilir tetik, tezi yanlışlayan seviye, stop ve çıkış planı önceden yazılır.
5. **Karar ve ölçüm:** Temel olay + çapraz piyasa + teknik yapı birlikte değerlendirilir; güçlü çelişki ayrıca açıklanır. İşlem açılırsa tez/çürüten alanları ayrı diskresyoner forward deftere **girişten önce** girilir. Mevcut 2/4 kapı ve durma kuralı için `Borsa - Arastirma ve Diskresyoner Yol Haritasi 2026-09-16` notu esastır.

Bu akış tek tek EMA, RSI, ADX, ATR sinyallerinin üst üste oy kullanması değildir. Teknik göstergeler girişin *nerede/ne zaman* olacağını açıklamak için kullanılır. Makro yorum, gelecekteki yönün otomatik kanıtı değildir. İşlem süresi bazı adaylarda intraday, bazı adaylarda swing olabilir; kullanıcı son mesajında Londra/New York seanslarında işlem seçimini özellikle vurgulamıştır. Önceki 2026-08-23 diskresyoner notu swing ağırlıklı başlangıcı anlatır; bu mesaj intraday seans seçimini de içerir, eski taahhüt veya risk kurallarını kendiliğinden değiştirmez.

## Analitik sınırlar

- **Reel 10Y / enflasyon beklentisi:** [FRED T10YIE](https://fred.stlouisfed.org/series/T10YIE), 10 yıllık nominal getiri `DGS10` ile enflasyona endeksli getiri `DFII10` farkından türetilir. Bu piyasa fiyatına dayalı *breakeven* ölçüdür; gerçekleşecek enflasyonun kesin tahmini değildir. Günlük FRED serisinin yayın/gecikme niteliği intraday teyit için ayrıca denetlenir.
- **DXY ve EUR/USD bağımsız teyit değildir:** [ICE USDX metodolojisinde](https://www.ice.com/publicdocs/futures_us/ICE_Dollar_Index_FAQ.pdf) euronun ağırlığı %57,6'dır. DXY yükseliyor, EUR/USD düşüyor görüntüsü kısmen aynı hareketin iki ölçümü olabilir.
- **Altın–dolar–reel faiz ilişkisi rejime bağlıdır:** [CME'nin 2026 değerlendirmesi](https://www.cmegroup.com/articles/2026/precious-metals-outlook-2026-market-dynamics-following-a-record-breaking-year.html), altının yüksek reel getiri döneminde de yükseldiği 2025 ayrışmasına dikkat çeker. Uyumsuzluk görüldüğünde otomatik “geciken varlık yetişecek” kararı verilmez.
- **Beklenti farkı ve gerçekleşen tepki:** [CME araştırmasında](https://www.cmegroup.com/insights/economic-research/2025/how-fx-equities-trade-economic-data-sets.html) piyasa katılımcıları açıklanan veriyi konsensüs beklentisiyle karşılaştırır; fark işlem hacmini etkiler. Sürprizin yönü, enstrümanın son yönünü tek başına belirlemez.

## Meslektaş yöntemleriyle ilişki

[SMB'den Ryan Hasson](https://www.smbtraining.com/blog/the-weekly-trade-plan-top-stock-ideas-in-depth-execution-strategy-week-of-july-15-2024), enflasyon açıklaması sonrasında güçlenen IWM/IBB'de önce kırılımı, sonra eski dirence geri çekilme ve desteğe dönüşü izlediğini anlatıyor. [Başka bir planında](https://www.smbtraining.com/blog/the-weekly-trade-plan-top-stock-ideas-week-of-september-14-2026) CPI/Fed bağlamıyla VWAP, göreceli güç ve destek/direnç tetiklerini birleştiriyor. Bu, kullanıcının **olay → çapraz piyasa → fiyat teyidi → giriş** düzenine en yakın açık örnek. SMB içerikleri, bu tam akışın tekil trader bazında doğrulanmış getirisini yayımlamaz.

Önceki makro A/B testi yalnız mekanik modüllere basit günlük yön filtresi ekliyordu; bu diskresyoner, olay ve piyasa tepkisi merkezli karar akışını test etmedi. O testin zayıf sonucu, bu akışın işe yaramadığını ispatlamaz; bu akışın kârlılığını da kanıtlamaz. Ayrı forward ölçüm gerekir.
