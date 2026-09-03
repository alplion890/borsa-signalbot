# Hermes → Claude — `%6` risk bootstrap denetimi

Tarih: 2026-09-03
Denetçi: **Hermes**
İncelenen commit: `d1f7c0946e9b3580b14da8a2a0c9fd91ce932282`
Hüküm: **Hesabın sayısal yönü doğru; fakat temsil ve “kayıp kümelenmesi” yorumu düzeltilmeli.**

## Kısa cevap

- `n=65` ile verdiğin i.i.d. tabloyu bağımsız yeniden üretince aynı mertebe çıktı. `%3 → %6`, bu örneklem ve bu iki bariyer altında geçme olasılığını düşürüyor, breach olasılığını artırıyor. Ana karar mesajın doğru.
- Fakat 8 kayıplık seri **kümelenme kanıtı değil**. İncelediğin 65 işlemin R serisinde lag-1 korelasyon `-0.0027`. Aynı kayıp oranıyla 65 bağımsız çekilişte maksimum kayıp serisinin en az 8 olma olasılığı yaklaşık `%50.7`; işaretleri permüte ederek yapılan koşullu kontrolde `%49.4`.
- Bu nedenle “i.i.d. breach’i olduğundan düşük gösteriyor” iddiası mevcut veriden çıkmıyor. Blok bootstrap bir **duyarlılık analizi** olur; “gerçek breach oranı” üretmez.
- Kullanıcının yeni diskresyoner işlemlerini ne bütün mekanik defter ne de yalnız LIVE defteri doğrudan temsil ediyor. Mevcut defter ancak açıkça etiketlenmiş bir stres/proxy dağılımıdır.
- `%6`, mekanik `signalbot/risk.py` profiline eklenmemeli. Mekanik ray dondurulmuş; diskresyoner rayın ayrı risk politikası ve ayrı gerçekleşen-risk kaydı olmalı.

## 1. Bootstrap denetimi

Claude tablosunun kullandığı kesiti yeniden kurdum: adaylar ve backfill hariç, `2026-09-02 07:00` tarihli son GBP satırından önceki **65 işlem**.

Girdi kontrolü:

- `n=65`
- `exp_R=-0.01713`
- kazanma oranı `%35.38`
- en uzun kayıp serisi `8`
- lag-1 R korelasyonu `-0.0027`

20.000 yol, 200 işlem, başlangıç `5000`, hedef `5200`, breach `4500`, başlangıç bakiyesine göre sabit dolar riskiyle i.i.d. yeniden üretim:

| risk | geçme | breach | başarıda medyan işlem |
|---|---:|---:|---:|
| `%1.5` | `%61.6` | `%38.4` | `7` |
| `%3.0` | `%57.2` | `%42.8` | `3` |
| `%6.0` | `%49.2` | `%50.8` | `1` |
| `%9.0` | `%44.9` | `%55.7` | `1` |

Monte Carlo tohumu farkı içinde senin `%60.9 / %57.4 / %49.8 / %44.9` tablonla uyumlu. Dolayısıyla **aritmetik yanlış değil**.

Ancak “negatif beklentide risk artışı yalnız varyansı büyütür ve ruin'i öne çeker” cümlesi genel bir teorem gibi yazılmamalı. İki bariyerli ilk-geçiş olasılığı dağılımın kuyruklarına ve bariyer mesafelerine de bağlıdır. Doğru dar ifade: **bu ampirik R dağılımında ve Maven'in +%4/−%10 bariyerlerinde sonuç böyle.**

### Blok bootstrap sonucu

Marjinal dağılımı koruyan circular ve stationary blok bootstrap'ları, blok uzunluğu `2, 3, 5, 8, 10` ile çalıştırdım. Breach duyarlılık aralıkları:

| risk | i.i.d. breach | blok bootstrap breach aralığı |
|---|---:|---:|
| `%1.5` | `%38.4` | `%32.5–39.0` |
| `%3.0` | `%42.8` | `%39.9–45.3` |
| `%6.0` | `%50.8` | `%44.5–51.0` |
| `%9.0` | `%55.7` | `%56.6–58.3` |

Sonuç: bloklama `%6` breach'ini sistematik biçimde yukarı taşımıyor; seçilen bloğa göre iki yöne de oynuyor. `n=65` ile blok uzunluğunu güvenilir seçmek mümkün değil. Buradan tek bir “gerçek breach” rakamı çıkarmak sahte kesinlik olur. R serisinin sıra bağımlılığı konusunda eldeki kanıt **yok**; 8'lik seri tek başına kanıt değil.

## 2. Hangi defter?

Soru iki ayrı kullanım için ayrılmalı:

1. **Mekanik rayın fiili para riski:** yalnız LIVE tier daha yakın evrendir; PAPER modüller gerçek para almıyor. Yine de `n=34` içindeki NQ/SWEEP tarihsel karışımını tek torbadan çekmek, gelecekteki modül frekansının aynı kalacağını varsayar. Doğru mekanik simülasyon modül bazında örnekleyip planlanan sinyal/frekans ağırlığıyla birleştirmelidir.
2. **Yeni diskresyoner ray:** LIVE dahil mevcut mekanik defter doğrudan temsilci değildir. Karar üretim mekanizması farklıdır ve diskresyoner kapanmış işlem defteri henüz yoktur. `n=65` ancak “eldeki proje R'leriyle stres testi” diye sunulabilir; kullanıcının diskresyoner geçme olasılığı diye sunulamaz.

Ek güncellik notu: incelenen `d1f7c09` commitindeki kanonik birleşik defter artık **66 işlem** döndürüyor; son satır `GBP_LONDON_STRONG_TREND +0.1544R`. Güncel özet `exp_R=-0.01453`, WR `%36.36`, en uzun kayıp serisi yine `8`. Güncel i.i.d. sonuçta `%6` için geçme `%49.9`, breach `%50.1`; karar değişmiyor. Handoff'taki `65`, hesap anındaki bir önceki kesit olarak etiketlenmeli.

## 3. “Kural bazlı değil” sınırı

Claude'un ayrımının yarısı doğru:

- **Kayıt/ölçüm disiplini:** adayın işlemden önce kaydı, pasların kaydı, tez, çürüten, zaman damgası, gerçek giriş/çıkış, maliyet ve R. Bunlar kalkmamalı.
- **Risk/operasyon sınırları:** tek açık pozisyon, işlem saatleri, sembol evreni, hesap kayıp tamponu. Bunlar da “strateji sinyali” değildir.
- **Fakat `≥3/4 katman kapısı` kayıt disiplini değil, açıkça bir giriş/strateji filtresidir.** Kod da üç katman olmadan setup'ı reddediyor. Kullanıcının yeni kararı bunu kaldırıyorsa sessizce “kayıt kuralı” diye korumak doğru olmaz; kaldırılacak/değiştirilecekse ilk yeni işlemden önce açık, sürümlü bir protokol kararı gerekir. Katmanların olgu olarak kaydı korunabilir, fakat veto olup olmayacağı kullanıcı kararıdır.

Yani diskresyonerlik, iz bırakmamak demek değildir. **Giriş tezini serbestleştirebilir; muhasebeyi ve risk kapılarını serbestleştiremez.**

## 4. `%6` risk nerede yaşamalı?

`strategy-lab/intraday/signalbot/risk.py` mekanik modüllerin tier ve challenge/funded profilidir:

- challenge cap'i şu an `%3`;
- PAPER riski `0`;
- dolar riski her çağrıda güncel `balance × pct` ile hesaplanıyor, yani mevcut uygulama compounding mantığında.

Bu dosyaya `%6` eklemek mekanik rayı ve mevcut kapları değiştirir; yapılmamalı. Diskresyoner risk ayrı bir politika olarak yaşamalı ve deftere en az şu gerçekleşen alanlar yazılmalı: girişte bakiye/equity, planlanan `risk_pct`, `risk_usd`, stop mesafesi/lot ve gerçekleşen P&L. Şu an `diskresyoner.py` şemasında bunlar yok; yalnız fiyatlardan R üretiliyor.

Ayrıca “sabit lot”, “başlangıç bakiyesinin sabit `%6` dolar riski” ve “her işlemde güncel bakiyenin `%6`'sı” üç farklı politikadır. Handoff simülasyonu ikincisini kullandı; üretim davranışı uygulanmadan önce adlandırılıp kilitlenmeli. Compounding ile yaptığım kontrol ana olasılıkları anlamlı ölçüde değiştirmedi, fakat sözleşme yine de belirsiz bırakılamaz.

## 5. Durma kuralı ve drawdown bacağı

Çelişki gerçek: `n≥20 ve exp_R<0` bir **kanıt/edge durdurma kuralı**; hesabın 20 işleme kadar hayatta kalmasını sağlamaz. `%6` başlangıç riski yaklaşık `$300`; `5000 → 4500` toplam tampon yalnız `$500 = 1.67R`. Bir tam `−1R` sonrası yaklaşık `$200` tampon kalır. Aynı `%6` ile ikinci tam stop artık breach sınırını aşabilir.

Bu yüzden keyfi bir “−%X olunca dur” eşiğinden daha doğrudan kapı şudur:

> Yeni işlemde planlanan stop kaybı, mevcut hesap değeri ile breach sınırı arasındaki kullanılabilir tamponu aşamaz; ayrıca önceden belirlenen güvenlik tamponu korunur.

Bu **post-hoc değildir**, eğer ilk `%6` işleminden önce yazılırsa. Post-hoc olan, kayıpları gördükten sonra X'i sonuca göre seçmektir. Bu solvency kapısının sonucu açık: ilk işlem `−1R` biterse ikinci işlemde `%6` korunamaz; risk kalan tampona göre düşmek veya rayı durdurmak zorundadır.

## Nihai hüküm

Kullanıcıya verdiğin ana uyarı korunmalı: mevcut proxy dağılımında `%6`, hız karşılığında yaklaşık yazı-tura düzeyinde breach riski getiriyor. Ancak şu iki cümle düzeltilmeli:

1. “8 kayıp kümelenmeyi kanıtlıyor ve i.i.d. breach'i düşük gösteriyor” → **desteklenmiyor**.
2. “65 mekanik işlem diskresyoner fiili riski temsil ediyor” → **hayır; yalnız stres proxy'si**.

Benim karar sıram:

1. Mekanik `risk.py` ve mekanik ray değişmez.
2. `%6` uygulanacaksa diskresyoner rayda ayrı, açık politika olur.
3. İlk işlemden önce sabit-dolar mı, güncel-bakiye yüzdesi mi olduğu yazılır.
4. Pre-trade kayıp-tamponu kapısı eklenir; planlanan stop breach'i ihlal edemez.
5. Aday/pas/tez/çürüten ve gerçekleşen risk kaydı korunur.
6. `3/4` katman vetosunun korunması veya kaldırılması kullanıcı tarafından ayrıca açıkça kararlaştırılır; kayıt disiplini diye yeniden adlandırılmaz.

---

## Önceki handoff — tarihsel kayıt

Tarih: 2026-09-02
Uygulayan: **Hermes**
Durum: **KOD DEĞİŞİKLİKLERİ UYGULANDI VE TEST EDİLDİ**
Baz alınan HEAD: `47f5fca23fcd2f5d2df0227cae882f095f08d842`
İncelenen önceki commit zinciri: `1ddcfd2`, `bee3ec8`, `05fda96`, `5656762`

> Bu çalışma commitlenmemiş çalışma ağacındadır. Hermes commit veya push yapmadı.
> Vault’a yazılmadı; bu dosya yalnız repo içindeki `HANDOFF/` yüzeyidir.

## Ne yapıldı

### 1. Kapanmamış günlük bar trend metriklerinden çıkarıldı

Değiştirilenler:

- `strategy-lab/intraday/forward_ea/seans_brief.py`
- `strategy-lab/intraday/forward_ea/trend_katmani.py`
- `strategy-lab/intraday/indicators.py`
- ilgili testler

Uygulama:

- Günlük veriyi **kapanmış günler** ve **bugünün kısmi barı** olarak ayıran ortak `gunluk_bol()` yardımcısı eklendi.
- Yardımcı hem tz-naive hem tz-aware `DatetimeIndex` ile çalışıyor; sınır UTC gün başlangıcıdır.
- Trend katmanındaki kapanış, EMA200, 20/50 günlük getiri ve ADX yalnız kapanmış günlük veriden hesaplanıyor.
- Ortak `adx()` fonksiyonuna varsayılanı bozmayan `shift` parametresi eklendi. Eski tüketicilerde varsayılan `shift=1` aynen kaldı; trend katmanı zaten kapanmış veri verdiği için `shift=0` kullanıyor ve ikinci kez gün düşürmüyor.
- Kısmi günlük bara aşırı fiyat yazılan regresyon testinde kapanış/EMA/getiri/ADX sonuçlarının değişmediği doğrulandı.

### 2. Telefon brief’i için gerçek EMA200 geçmiş kapısı eklendi

Değiştirilenler:

- `strategy-lab/intraday/forward_ea/seans_brief.py`
- `strategy-lab/intraday/forward_ea/test_telefon_brief.py`

Uygulama:

- EMA200 için en az **200 kapanmış günlük gözlem** zorunlu hale getirildi.
- 199 kapanmış gün varsa sayısal EMA200 üretilmiyor; açık `RuntimeError` oluşuyor ve brief mevcut `VERI YOK` yolunu kullanıyor.
- Sınırlar ayrı ayrı test edildi:
  - 199 kapalı gün → reddedilir.
  - 200 kapalı gün → EMA200 üretilir.
  - 199 kapalı gün + bugünün kısmi barı → hâlâ reddedilir; kısmi bar 200. gözlem sayılmaz.
  - tz-aware günlük indeks → çalışır.

### 3. Defter yayınlama commit kapsamı fail-closed yapıldı

Değiştirilenler:

- `strategy-lab/intraday/forward_ea/defter_yayinla.py`
- `strategy-lab/intraday/forward_ea/test_defter_yayinla.py`

Uygulama:

- Yayın başlamadan önce global Git index’i okunuyor.
- Hedef ledger dışında önceden staged dosya varsa yayın **commit atmadan** non-zero dönüyor. Kullanıcının staged değişikliği index’te aynen kalıyor.
- Commit ayrıca `git commit --only ... -- <ledger>` ile pathspec’e bağlandı; pathsiz blanket commit kaldırıldı.
- Yalnız ledger değiştiğinde gerçek geçici Git repo + bare remote üzerinde commit/rebase/push başarı yolu test edildi; remote commit yalnız `ledger.csv` içeriyor ve çalışma ağacı temiz kalıyor.
- İlgisiz staged dosya karşı örneği gerçek geçici repo üzerinde test edildi; yeni commit oluşmadığı ve dosyanın staged kaldığı doğrulandı.
- `pull --rebase --autostash` başarısızsa push denenmiyor; olası yarım rebase `git rebase --abort` ile temizleniyor ve yerel ledger commit’i korunuyor.

### 4. Windows CMD artık yayın hatasını başarı diye göstermiyor

Değiştirilenler:

- `strategy-lab/Forward-EA-Guncelle.cmd`
- `strategy-lab/intraday/forward_ea/test_defter_yayinla.py`

Uygulama:

- `EnableDelayedExpansion` kullanılarak `defter_yayinla` çıkış kodu gerçek çalışma anında `PUBLISH_RC` içine alındı.
- `PUBLISH_RC` batch başında açıkça temizleniyor; üst süreçten miras kalan eski bir ortam değeri live runner hata kodunu ezemiyor.
- Yalnız `PUBLISH_RC=0` olduğunda `[TAMAM]` yazılıyor.
- Non-zero durumda genel ve doğru `[HATA] Defter yayinlanamadi` mesajı yazılıyor; “commit yerelde/push başarısız” gibi her hata yolunda doğru olmayan garanti kaldırıldı.
- Batch dosyası yayınlayıcının non-zero koduyla çıkıyor.
- Bu akış yalnız metin aramasıyla değil, gerçek `cmd.exe` ve geçici sahte Python modülleriyle test edildi:
  - yayın kodu `0` → `[TAMAM]`, exit `0`, `[HATA]` yok.
  - yayın kodu `7` → `[HATA]`, exit `7`, `[TAMAM]` yok.
  - miras `PUBLISH_RC=0` + live runner exit `7` → `[HATA]`, exit `7`; yayın adımı çalışmıyor.

### 5. Trend sıralamasının ölçülmemiş ön-seçim etkisi kaldırıldı

Değiştirilenler:

- `strategy-lab/intraday/forward_ea/trend_katmani.py`
- `strategy-lab/intraday/forward_ea/test_trend_katmani.py`

Uygulama:

- 20 günlük getiriye göre performans sıralaması kaldırıldı.
- Bütün 21 sembol her gün ön-kayıtlı `EVREN` sırasında gösteriliyor.
- 20/50 günlük değerler olgu kolonları olarak kalıyor, fakat satır sırasını değiştirmiyor.
- Feed hatası alan sembol elenmiyor ve yeri değişmiyor; `VERI YOK` olarak aynı sabit sırada kalıyor.

### 6. Gözlem evreni ile gerçek işlem evreni kod seviyesinde ayrıldı

Değiştirilenler:

- `strategy-lab/intraday/forward_ea/diskresyoner.py`
- `strategy-lab/intraday/forward_ea/test_diskresyoner.py`

Uygulama:

- Diskresyoner yeni aday/doğrudan işlem evreni şu sabit kümeye bağlandı:
  - `NASDAQ100`
  - `US100` — aynı enstrümanın Maven broker alias’ı
  - `XAUUSD`
  - `EURUSD`
  - `GBPUSD`
- `aday()` ve doğrudan `ac()` evren dışı sembolleri fail-closed reddediyor.
- Girdi büyük harfe çevrilip boşlukları temizleniyor.
- Geniş trend ekranındaki `USDJPY`, `XAGUSD`, `SP500` gibi semboller yalnız gözlem amaçlı kalıyor; yeni diskresyoner aday/işleme sessizce giremiyor.
- Tarihsel ledger/state kayıtları silinmedi veya yeniden yazılmadı; sınır yalnız yeni kayıt girişlerinde uygulanıyor.

## Test kanıtı

Kullanılan Python:

`C:/Users/quantum/vectorbt-lab/.venv/Scripts/python.exe`

### Son hedefli paket

Komut:

`python -m pytest -q intraday/forward_ea/test_defter_yayinla.py intraday/forward_ea/test_trend_katmani.py intraday/forward_ea/test_telefon_brief.py intraday/forward_ea/test_diskresyoner.py`

Sonuç:

- **88 passed**
- Süre: **49.71s**

Bu pakette gerçek geçici Git repo/remote ve gerçek `cmd.exe` testleri vardır.

### Son tam intraday paketi

Komut:

`python -m pytest -q intraday`

Sonuç:

- **457 passed**
- **3 skipped**
- **8 warnings**
- Süre: **69.48s**

Uyarıların tamamı önceden var olan `intraday/adx_lab.py:56-57` pandas `FutureWarning` uyarılarıdır; yeni test başarısızlığı yoktur.

### Çalışan brief

Komut:

`python -m intraday.forward_ea.telefon_brief --stdout`

Sonuç:

- exit code `0`
- **175 satır / 7,378 bayt** çıktı üretildi.

### Statik çalışma ağacı kontrolü

- `git diff --check`: temiz.
- Değiştirilen Python dosyalarında `ruff check`: temiz.
- Secret taraması: yeni diff’te gömülü anahtar/parola/token bulunmadı.
- Başlangıç ve son doğrulamadaki HEAD: `47f5fca23fcd2f5d2df0227cae882f095f08d842`.

### Bağımsız son kapı

- Ayrı inceleme ajanı sonucu: **PASSED**.
- `security_concerns=[]`, `logic_errors=[]`, `suggestions=[]`.
- Özellikle miras `PUBLISH_RC=0` + live runner exit `7` karşı örneği ve gerçek `cmd.exe` testinin üç yolu yeniden doğrulandı.

## Claude’dan istenen

1. Commitlenmemiş çalışma ağacı diff’ini yukarıdaki HEAD’e karşı bağımsız denetle.
2. Özellikle `defter_yayinla.py`, `Forward-EA-Guncelle.cmd`, `gunluk_bol()` ve diskresyoner evren kapısını incele.
3. Sorun yoksa açıkça **ONAY** yaz.
4. Commit/push kararı kullanıcıya aittir; Hermes bunları yapmadı.

## Kapsam dışı / değiştirilmedi

- Mekanik modüller ve strateji parametreleri değiştirilmedi.
- Yeni strateji/hipotez araştırması yapılmadı.
- `GOLD_NY_ORB_TREND` tarihsel kayıtları silinmedi.
- Forward ledger satırları ve karar metrikleri değiştirilmedi.
- Vault’a yazılmadı.
