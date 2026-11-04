# Video karşılaştırması — 17 Ekim 2026

Kaynak: Ziya BAYSAL, Kârlı Bir Trade Modeli Nasıl Kurulur? Fikirden İstatistiğe, https://youtu.be/aFZc5SUbi-k (22:13).
Yerel HEAD: ea74970b2d6126176f2333bb3ff2355a98856eb1. Çalışma ağacı değişiklikler içeriyor; hash bütün yerel uygulamanın teslim kimliği değildir. git pull yerel çakışmalar nedeniyle tamamlanmadı. Bu çalışma kod/risk/LIVE yetkisi değişikliği veya Hermes denetimi değildir.

## Gözlenen içerik

Video modeli avantaj/mekanizma, giriş kuralları, risk/çıkış ve veriyle test bileşenleriyle anlatıyor. Koşul/tetik ayrımı, geleceği geçmişte kullanma hatası, komisyon/spread/kayma, beklenen değer, geliştirme-doğrulama-son test ayrımı ve walk-forward görsellerde yer alıyor. Test verisine tekrar tekrar bakıp model değiştirmeme ve iyi backtestin aynı canlı sonuç anlamına gelmemesi vurgulanıyor. Order flow/AMT örnekleri yeni gösterge eklemenin zorunlu olduğu anlamına gelmez.

## Mevcut sistemle karşılaştırma

| Ölçüt | Yerel kanıt | Değerlendirme |
|---|---|---|
| Açık model ve kurallar | default_modules: yalnız SWEEP_CORE_AVOID_MID_VWAP; risk.py ayrı yetki kaynağı | Mekanik tanım var; tanım kârlılık kanıtı değil. |
| Veri ve sürüm kimliği | 15 Ekim tek ana kaynak kararı; Maven broker/server ve kapalı mum; veri/kod/config SHA256 | Panel/yeni backtest için var; eski akışların tümünün dönüştüğü varsayılmaz. |
| Gerçekçi dolum ve maliyet | honest_engine, aynı barda SL önce, gidiş dönüş maliyet; README OHLC/tick sınırını açıklıyor | Model var; gerçek gerçekleşme maliyetiyle doğrulanmış eşitlik yok. |
| Net beklenen değer ve düşüş | Kaydedilmiş backtest job metrikleri; forward ayrı | Ölçüm var, olumlu sonuç garantisi yok. |
| Gerçek görülmemiş test | README iki tarihsel yarının gerçek OOS olmadığını söylüyor | Belgelerden tamamlandığı doğrulanamadı. |
| Walk-forward/parametre dayanıklılığı | Bu denetimde mevcut LIVE sürümüne ait tamamlanmış kabul paketi doğrulanmadı | Yokluğu kesinleştirilmedi; geçmiş raporu sonradan OOS ilan etme. |
| İleriye dönük kayıt | MT5 sanal forward, normal/backfill ayrımı, kaynak sağlığı | Sanal kayıt gerçek emir veya Telegram teslim makbuzu değildir. |
| Başarısızlık ve durma | Emekli modüller korunuyor; mekanik DEMOTION_MIN_N=25, diskresyoner n>=20 ve exp_R<0 | İki farklı taahhüt birbirine karıştırılmaz. |

## Sayısal örnekler ve sınırları

15 Ekimde kaydedilmiş Maven Sweep testi: 2026-07-01–2026-10-14 istenen aralık, maliyet 1x, n=13, toplam -3.087555882R, ortalama -0.237504299R, kazanma %15.3846, kapanmış işlem R eğrisi maksimum düşüşü 9.482055R. Bu entegrasyon/tarihsel ölçümdür; bağımsız yeni OOS kanıtı veya gerçek hesap drawdown'u değildir.
Dosya: strategy-lab/outputs/intraday/research_panel/jobs/e8f70e2e-d69f-4321-912c-a9d02cb2bd37.json.

15 Ekim denetim belgesindeki normal MT5 Sweep sanal forward özeti n=15, toplam +0.136R (ortalama yaklaşık +0.009R). Bu 17 Ekimde yeniden hesaplanmış güncel sayı değildir. Backtest ile farklı dönem/kayıt kapsamıdır; iki örneklem toplanmaz. Küçük örneklem güçlü pozitif beklenti kanıtı değildir.

## Uyum için hazırlanmış denetim sırası — öneri, yeni kural değil

1. Mevcut sürümün mekanizma, koşul, tetik, giriş, stop, çıkış, zaman penceresi ve sürüm kimliğini tek model kartında sabitle; yeni filtre ekleme.
2. Önce mevcut LSE roll/aykırı bar/gap temizliği ve veri sağlığı taahhüdünü tamamla. Panelin Maven tek kaynak kararını koru; LSE araştırması ana broker sonucu gibi sunulmasın.
3. Daha önce geliştirmede kullanılan dönemleri listele. Gerçekten görülmemiş bir dönem yoksa geçmişi OOS diye adlandırma; yeni ileriye dönük veriyi önceden belirlenmiş protokolle biriktir.
4. Yeni araştırma açmadan mevcut sürümün maliyet varsayımı ile ölçülmüş broker spread/komisyon/kayma kayıtlarını karşılaştır. Maliyet stresini sonuç seçme aracı yapma; senaryoları önce kaydet.
5. Her raporda n, toplam/ortalama net R, kazanma oranı, PF, düşüş, veri/kod/config kimliği ve kapsam/eksik veri sınırını birlikte göster. Belirsizliği ve bağımlı/örtüşen gözlemleri açıkla.
6. Tek ön-kayıtlı NQ–ES göreceli güç çalışmasını mevcut araştırma kapsamı içinde tut. Walk-forward veya komşu parametre incelemesi gerekiyorsa bu ailenin önceden yazılmış planının parçası olsun; yeni edge taramasına dönüşmesin.
7. Mevcut forward ve durma taahhütlerini koru. n=20/25 durma eşikleri otomatik olarak istatistiksel kanıt yeterliliği eşiği değildir. Olumlu backtest LIVE/risk yetkisini değiştirmez.

Kaynak belgeler: TELEFON/GUNCEL_EDGE_KARARLARI.md; strategy-lab/intraday/research_panel/README.md; HANDOFF/tek_ana_kaynak_2026-10-15.md; HANDOFF/panel_guncellik_2026-10-15.md; HANDOFF/forward_kontrol_2026-10-07.md.

## Video erişimi ve zamanlı başvuru

YouTube İngilizce altyazı isteği HTTP429 verdi. Watch ile yerel 12 kare incelendi; ayrıca kurulu Gemini motoruyla indirilen videonun ses+görüntü çözümlemesi tamamlandı. Tam insan doğrulamalı kelimesi kelimesine transkript değildir; 22 dakikalık videoda ilk kare taraması seyrektir. Aşağıdaki zamanlar native çözümlemenin bölüm referanslarıdır:
- 02:32–02:57: avantaj/mekanizma, giriş, risk/çıkış ve veriyle test.
- 08:18 civarı: look-ahead bias ve o anda bilinemeyen fiyatla giriş sorunu.
- 11:57 civarı: beklenen değer; kazanma oranı tek başına yeterli değil.
- 14:33–15:47: çok deneme, aşırı uyum, kronolojik geliştirme/doğrulama/son test ve son testi kirletme.
- 16:46–17:21: alt grupları sonuçtan sonra seçme riski; önceden tanımlı sorular ve belirsizlik.
- 17:26–17:46: walk-forward; kazanç garantisi değil.
- 18:38–19:17: paper/gerçek zaman uygulanabilirlik; sinyal zamanı, giriş fiyatı, stop/hedef ve işlem sıklığı.

Diskresyoner rayda 2/4 kapısı tek başına tam tekrarlanabilir mekanik model değildir. Kullanıcının tez/çürüten/katman/PAS kayıtları ve gerçek gerçekleşme verileri bu rayın ayrı ölçümünü oluşturur; mekanik Sweep sonuçları kullanıcı yorumunun başarısının yerine geçmez.

Order flow örneğini uygulamak ayrı veri ve hipotez gerektirir. Mevcut OHLCV veya broker hacmi, videodaki gerçekleşmiş bid/ask işlemlerinin ve footprint deltasının eşdeğeri olarak adlandırılamaz. Böyle bir modül bu çalışmada eklenmedi.
