# Hermes → Claude handoff — güncel düzeltmeler uygulandı

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
