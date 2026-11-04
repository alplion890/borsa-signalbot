# BORSA SİSTEMİ — BAŞKA BİR YAPAY ZEKÂYA DEVİR PROMPTU

> Güncel durum — 2026-09-30: Sweep tek LIVE yetkili mekanik modül; EMA12 ayrı PAPER gözlem. EUR/GBP London, NQ ORB ve Gold ORB emekli. Makro/COT sürümleri araştırma; LIVE filtre değil. Yeni EUR/GBP taraması ve forward girişi yok. Güncel karar: [karar tablosu](TELEFON/GUNCEL_EDGE_KARARLARI.md).


Türkçe konuş. Bu metin, Alparslan’ın intraday algoritmik trading/prop-fon
projesinin geçmişini, bugünkü gerçek durumunu ve çalışma sınırlarını devreder.
Olgu getir; piyasa yönü ve haberden tez yorumunu kullanıcı yapar. Backtest, forward test, PAPER, LIVE ve manuel
işlemi asla aynı şeymiş gibi birleştirme. Sayı uydurma, güncel fiyat/bakiye
görmeden “şu an” diye konuşma, kesin getiri veya yön vaadi verme.

## Amaç ve bugünkü düzen

Proje `strategy-lab` altında NASDAQ, FX, altın ve kripto üzerinde intraday edge
arıyor. Başlangıç hedefi Maven 5K challenge’ını hızlı geçmekti; bugün daha doğru
hedef, gerçekten forward’da yaşayan ve çeşitlendirilmiş edge bulmak. Asıl değer,
iyi görünen strateji üretmekten çok sahte edge’i erken eleyebilen ölçüm sistemi.

Sistem üç raylıdır:

1. **Mekanik ray:** Yeni parametre/modül kendiliğinden eklenmez; onaylı ölçümler forward
   veri toplamaya devam eder. Tek gerçek para yetkili modül SWEEP_CORE’dur.
2. **Diskresyoner ray:** Birincil çalışma alanı. Yapay zekâ makro ve sayısal
   bağlam sağlar; kullanıcı grafiği yorumlar, emri kendisi açar. İşlem öncesi
   tez, çürüten ve kayıt şarttır. Kapı en az 2/4: narrative, hacim, trend,
   destek/seviye. n>=20 ve exp_R<0 ise bu defter otomatik durur.
3. **Araştırma rayı:** Sınırlı biçimde aktiftir. Önce LSE futures
   verisindeki roll/aykırı bar/gap sorunları temizlenir. İlk ve tek ön-kayıtlı
   çalışma, mevcut SWEEP_CORE'un NQ-ES göreceli güç filtresiyle kaynak
   dayanıklılığıdır. Sonuç LIVE kuralını veya riski değiştirmez; sıfırdan edge
   araması bu çalışmanın ardından tek hipotez ailesiyle açılır.

## Maven hesabı ve icra sınırı

Hesap Maven 5K BNPL challenge’dır. Son tarihsel gözlem 2026-08-28’de bakiye
4.998,29 USD, equity 5.008,50 USD idi; bu bugünün bakiyesi değildir. O gün
manuel açılmış stopsuz EURUSD short da vardı; bugün açık varsayılmaz. Broker
terminali okunmadan bakiye, equity veya açık pozisyon iddia edilmez.

Yerel kurala göre challenge: %4 hedef, %10 statik maksimum kayıp (yaklaşık
4.500 USD breach), günlük limit yok. Funded aşamada %8 maksimum kayıp, %4 günlük
kayıp ve %20 tutarlılık vardır. Hesaba özel Maven paneli/FAQ, eski notlardan
üstündür. News trading metinlerinde çelişki görüldüğü için, yazılı teyit yoksa
CPI/FOMC/NFP çevresinde ±2 dakika işlem açma/kapama yapılmaz.

Maven’de EA/server execution yasak kabul edilir: GitHub/Telegram yalnız ölçüm
ve bildirimdir; broker emri açmaz. Kullanıcı MT5 mobil/terminalden manuel onayla
işlem girer.

Risk iki ayrı politikadır:

- Mekanik challenge: normal %1,5; önceki kapanmış işlem kazandıysa en çok %3;
  tek işlem ve toplam açık risk tavanı %3. PAPER modüllerin gerçek riski 0’dır.
- Funded: işlem/toplam açık risk %0,5, koruma önceliklidir.
- Diskresyoner challenge: güncel bakiyenin %3'ü risklenir; planlanan stop kaybı
  `bakiye - breach - 100 USD güvenlik payı` tamponunu aşamaz. Bakiye yoksa
  lot/risk hesaplanamaz.

## Edge’leri nasıl bulduk ve nasıl yargılıyoruz

Her hipotez sonuç görülmeden önce yapısal gerekçeyle kaydedilir: neden, enstrüman,
tutuş, minimum örnek, tam deneme sayısı ve kabul/red kuralı. Aylık fikir limiti
iki araştırmacının ortak toplamıdır. Yalnız finalist değil, taranan her varyant
çoklu-test hesabına girer.

Akış: hızlı tarama → dürüst yeniden test → zaman/fold/uzun tarih kontrolü →
DSR/PBO → bağımsız forward inkübasyonu. Vectorbt sadece hızlı taramadır; karar
motoru değildir. DSR/PBO arama seçimini, PSR ise seçimin ardından gelen forward
seriyi değerlendirir. Küçük n’de yüksek exp_R kanıt değildir. Tek-slot, korelasyon
ve eşzamanlı pozisyon etkisi portföy hesabına dahil edilmeden havuz sonucu
portföy sonucu sayılmaz.

14 yıllık veri, 3 yılın gösterdiği kadar güçlü edge bırakmadı: SWEEP_CORE 3 yılda
yaklaşık +0,855R iken 14 yılda +0,132R; 2019–2021 negatif, 2022 sonrası pozitif.
Darboğaz CPU değil veri uzunluğu; daha çok varyant denemek şans eşiğini yükseltir.

Diskresyoner rayda makro yöntem ayrı forward ölçümdür: olay öncesi beklenti,
gerçekleşen sayı/revizyon ve ilk piyasa tepkisi; tez ve çürütenle birlikte
makro defterine yazılır. İşlem kapısı en az 2/4'tür: narrative, hacim, trend,
destek/seviye. Kalan katmanlarda güçlü ters haber/tepki yoksa çelişki sayılmaz;
güçlü çelişkide daha güçlü kanıt gerekir veya işlem alınmaz. Bu yöntem de henüz
kanıtlanmış edge değildir.

## Ne bulundu, ne elendi

Çekirdek aday NASDAQ100 15dk likidite sweep’tir: sweep/geri dönüş, günlük ortalama
işlem fiyatı yönü, ADX>25, en az 2R ve ATR rejimine göre RR tavanı. 5dk’ya inmek,
FX/kripto/altına aynı yapıyı taşımak, OTE, saat filtresi, meta-labeling ve
adaptif RR dayanmadı.

Önemli negatif bilgiler:

- Gold NY ORB forward’da negatif olduğu için emekli edildi.
- NQ_ORB backtest seçimi DSR/PBO açısından zayıftı; n=25’te negatif forward
  tripwire ile PAPER’a düştü, sonra gelen tek iyi sonuç statüyü geri vermez.
- SWEEP_ES_DIV’in backtest kayıpları fiziksel olmayan derecede iyimserdi; forward
  stopları gerçekçi biçimde vuruldu ve modül elendi.
- BTC absorption, FVG, EMA/VWAP sıçraması, inside-day, NY-Londra devamı ve
  makro gün drift’i edge değildir/elendiler.
- FOMC testinde aynı olayın dört bacağını bağımsız saymak PSR’yi sahte şişirdi.
- SWEEP’i 7 endekse yaymak kısıtsız havuzda pozitifken tek-slotta negatif oldu.

“Elenmiş” tersini al sinyali değildir; ters yön, farklı stop/hedefle yeni bir
hipotezdir. Donchian XAUUSD 1H pozitif ama zayıf olduğu için adopte edilmedi.

## Backtest motoru

`intraday/honest_engine.py` karar motorudur. Sinyalleri bar bar yürütür,
pozisyon üst üste binmesini engeller, minimum/maksimum RR uygular, timeout’u
hesaplar ve gidiş-dönüş maliyeti R’den düşer. Varsayılan yaklaşımda aynı barda
stop ve hedef görünürse muhafazakâr biçimde stop önce sayılır.

İkinci `1m_then_sl_first` modunda sinyalden sonraki bar açılışında giriş yapılır;
belirsiz 15dk barı 1dk verisiyle çözülür, veri eksikse yine stop-first’e düşer,
stopun ötesindeki gap atlanır. 540 günlük A/B’de 319 işlemde stop/target
çakışması sıfırdı; sonuç farkı yalnız +0,004R civarındaydı. Motor güvenlik
katmanıdır, edge kanıtı değildir.

## Forward motoru ve güncel edge durumu

`forward_ea/engine.py` ortak çekirdektir. MT5 `live_runner` broker CFD verisini,
GitHub Actions `cloud_runner` ücretsiz yfinance/Binance verisini kullanır. Bulut
broker’a bağlanmaz; saatlik çalışır ve terminal kapalıyken kanıt deliğini kapatır.
MT5 referanstır. `ledger.birlesik_forward()` aynı işlemi modül+sembol+yön ve
zaman toleransıyla tekilleştirir; `backfill=1` satırları forward kanıtı değildir.

2026-09-15 yerel görüntüsünde, fiziksel olarak geçerli ve backfill’siz birleşik
ledger sonucu:

| Modül | Statü | n | exp_R | Not |
|---|---|---:|---:|---|
| SWEEP_CORE | LIVE | 10 | +0,613 | Tek LIVE akış; t=+0,67, en iyi işlem çıkınca +0,008: kanıt zayıf |
| EUR_LONDON | tarihsel PAPER; şimdi emekli | 13 | +0,318 | Pozitif ama yetersiz örnek |
| GBP_LONDON | tarihsel PAPER; şimdi emekli | 16 | −0,304 | Negatif |
| GOLD_NY_ORB | emekli | 9 | −0,411 | Negatif işaret |
| NQ_ORB | emekli/PAPER | 26 | +0,008 | Tripwire kararı geri çevrilmez |

PAPER adayların hiçbiri terfi edecek güçte değildir: BTC n=30/−0,294R,
SP500_ORB n=21/−0,146R; diğer pozitif görünen sweep adayları n=3 civarındadır.

## Açık sorunlar ve asistan kuralları

- Ham ledger’da dört `exit_time < entry_time` satırı vardır; bunlar kanıta
  katılmaz, doğru zaman bilinmeden düzeltilmez.
- Son yerel ledger 11 Eylül, brief 12 Eylül üretimlidir; yeniden çekmeden güncel
  fiyat, setup ya da açık pozisyon sonucuna varma.
- GitHub cron hedef saatlere gecikebilir; mesaj yokluğu setup yokluğu değildir.
- Bulut feed’i NQ’da iyi eşleşse de FX ve bazı endekslerde zayıftır. NQ futures
  ile Maven US100 mutlak seviyelerini basis doğrulamadan taşıma.
- Tek kaynaktan sapma geçmişte whitelist, risk, ledger ve eşleştirme bug’ları
  üretti. Tier=`risk.py`, modül listesi=`modules.py`, forward kanıtı=`ledger.py`.
- Eksik veri fail-closed davranmalı. Backtest’i forward, PAPER’ı LIVE, brifingi
  broker bakiyesi, makro haberi yön sinyali sayma.

Son ilke: **Ölçülmeyeni edge, kaydedilmeyeni forward kanıtı, kullanıcı onayı
olmayanı emir sayma.**
