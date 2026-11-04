# Bizim backtest sistemi nasıl çalışıyor?

**Kural işlemi seçer. Motor sonucu hesaplar. Backtest geçmişte tekrarlar. Edge araştırması avantajın güvenilir olup olmadığını sınar.**

## 1. Veri: geçmişin fiyat kaydı

Maven MT5'ten her mumun başlangıç, en yüksek, en düşük ve kapanış fiyatını alıyoruz. Yeni ana testler bu broker verisini kullanıyor. Veriyi bir fotoğraf gibi saklıyoruz: aynı dosyayla tekrar hesaplayınca aynı geçmişi kullanıyoruz.

Bu denetimdeki NQ dosyası 40.000 adet 15 dakikalık mum içeriyor ve 15 Ekim 2026'da bitiyor. Formda 2020 seçmek, dosyada 2020 verisi olduğu anlamına gelmiyor; dosyanın başlangıcı Şubat 2025.

## 2. Strateji: hangi durumda işlem seçilecek?

Sweep kuralı kabaca şunu arıyor: fiyat son 20 mumun bir ucunu aşıp tekrar içeri kapanıyor mu? Buna VWAP'a göre fiyatın konumu ve ADX ölçümü eşlik ediyor. Mevcut tanımda çarşamba dışarıda. Stop, mumun uç noktası ve ATR tamponundan; hedef geçmiş swing seviyesinden hesaplanıyor. Risk/ödül eşiği ve oynaklığa göre hedef tavanı var.

Bunlar bilgisayarın kendi fikri değil; koda yazılmış seçim koşulları. Koşulların var olması çalıştıklarını kanıtlamıyor. Güncel modül adı tarihsel olarak AVOID_MID_VWAP içeriyor; dedektörde ayrıca mid-VWAP veto filtresi yok.

## 3. Motor: seçilen işlem nasıl sonuçlanırdı?

Aşağıdaki sayılar yalnız eğitim örneği; piyasa fiyatı veya işlem önerisi değil:

- Giriş 100, stop 99, hedef 102.
- Giriş ile stop arasındaki 1 puan, başlangıç riski: **1R**.
- Önce 102'ye ulaşırsa +2R, önce 99'a ulaşırsa -1R.
- Maliyet 0,1R ise sonuçlar +1,9R veya -1,1R.
- Pozisyon açıkken fiyat 97'ye boşlukla açılırsa model artık -3R brüt hesaplıyor. Gerçek broker dolumu ayrıca doğrulanmalı.
- Aynı mumda hem stop hem hedef görülür ve sıra bilinmezse stop önce sayılıyor. Mumun açılışında zaten ulaşılmış hedef varsa önce o bilinen olay dikkate alınıyor.

Motorun işi bu hesabı her mumda yapmak. Varsayılan giriş sinyal mumunun kapanışı; alternatif kontrolde sonraki mumun açılışı. Pozisyon açıkken yeni işlem biriktirilmiyor. Belirlenen sürede hedef/stop olmazsa zaman çıkışı var.

**R, hesap bakiyesi getirisi değil.** Bir işlemde gerçekten 10 USD başlangıç riski kullanılsaydı 2R brüt = 20 USD olurdu. Tarihsel toplam R'yi doğrudan hesabın dolar kârı veya yüzdesi diye okumayız.

## 4. Backtest: aynı kuralı geçmiş boyunca yürütmek

Program geçmişi tarıyor, koşul oluştuğunda motor bir sanal işlem hesaplıyor. Sonunda işlem listesi, ortalama net R ve en büyük kapanmış-işlem R düşüşü çıkıyor.

Bugünkü düzeltme sonrası aynı kayıtlı NQ örneği: **52 işlem, toplam +25,175R, işlem başına +0,484R**. Eski motor +25,764R yazıyordu. Stop boşluğu yüzünden bir işlem daha fazla kayıp yazdı. Önceki sonuç ayrı saklandı.

Bu sonuç, geçmişte bu varsayımlarla ne çıktığını gösteriyor. Gelecek kazanç sözü değil.

## 5. Edge aramak: ölçülebilir bir fikri sınamak

Örnek soru: “Bu koşulu önceden yazıp her oluştuğunda aynı şekilde uygularsak, masraflar sonrasında bir avantaj kalıyor mu?”

Önce kural yazılır; sonra geçmişte denenir. Başarı yalnız kazanma oranıyla ölçülmez. Tamamen varsayımsal 10 işlem düşün: 4 tanesi +2R, 6 tanesi -1R olsun. Toplam +2R brüt. Maliyetler bunu azaltır; küçük bir örnek tek başına avantaj kanıtı değildir.

Bin farklı kural deneyip en kârlısını göstermek kolaydır. Bu yüzden deneme sayısı, farklı dönemler, maliyetler ve daha önce bakılmamış veri önemlidir. Elenen fikirler de katalogda tutulur; aynı zayıf fikri yeni isimle tekrar kazanan ilan etmeyiz.

Bu projede geniş yeni edge taraması şu an açık değil. Araştırma sırası veri temizliği ve ön-kayıtlı NQ–ES çalışmasıyla sınırlı. Şu anda yaptığımız iş mevcut motorun hesabını denetlemek.

## 6. Forward: geçmiş bitti, yeni mumları bekliyoruz

Sabit kural yeni gelen mumlarda izlenir. Sanal forward kaydı ile kullanıcının gerçekten açtığı broker emri ayrı şeylerdir. Yeni kayıt gelmesi, geçmiş testten daha bağımsız kanıt toplamaya yarar; gözlem kesintileri de ölçülmeli.

## 25 Ekim'de neleri yaptık?

| Kontrol | Sonuç |
|---|---|
| Stop boşluğu düzeltmesi | Normal, hızlı ve isteğe bağlı sonraki açılış yoluna eklendi |
| Alt zaman verisinde eksik başlangıç | Sonraki hedef dokunuşu yanlışlıkla ilk dokunuş sayılmıyor |
| Motor ve ilgili odak testleri | 68 geçti |
| Panel, forward ve uzun-geçmiş test grubu | 329 geçti, 1 atlandı; gruplar kısmen örtüşüyor |
| Ayrı durum makinesiyle işlem hesabı | Dört senaryoda zaman/net R eşliği sağlandı |
| Canlı dedektör ile tarihsel sinyal hesabı | 114 ham aday ve 64 ek mumda fark yok; tam runner/icra eşliği değildir |
| Gelecek mumları kaldırıp yeniden hesaplama | Altı kesitte geçmiş sinyal/seviye/ATR sıralaması değişmedi |

| Aynı 52 işlem üzerinde kontrol | Toplam net R |
|---|---:|
| Düzeltilmiş model, mevcut maliyet | +25,175 |
| Model maliyeti 2 kat | +16,144 |
| Model maliyeti 3 kat | +7,113 |
| Sonraki mumun açılışından giriş, mevcut maliyet | +25,105 |

Son satırda 1 dakikalık veri yok; mum içi belirsizlik stop önce varsayımıyla çözüldü. Maliyet çarpanları ölçülmüş gerçek broker komisyonu değildir. Bu kontroller aynı eski veri üzerinde yapıldı; yeni OOS sayılmaz.

**Açık kalanlar:** gerçek broker tick/bid-ask dolum eşliği, gerçekleşen maliyet ölçümü ve sabit sürümle yeni görülmemiş dönem. Bilinen MT5 hesap engeli çözülmüş kabul edilmedi. Panel kod değişikliği sonrası yeni test için yeniden başlatılmalıdır; eski raporlar eski sürümün kaydıdır.

Ayrıntılı kanıt: strategy-lab/outputs/intraday/execution_audit/20261025-gap-v2/ içinde audit.json, trades.csv, examples.md ve live_signal_parity.json. Kalıcı not: [[Borsa - Motor Dolum Duzeltmesi ve Bagimsiz Denetim 2026-10-25]].