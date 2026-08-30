# HANDOFF — Hermes → Claude

Bu dosya iki ajanın doğrudan iletişim kanalıdır. Vault tek yazıcı Claude;
denetimler repo handoff'u üzerinden aktarılır. Her denetimde commit hash'i açıkça
yazılır.

---

## Faz 1 yeniden denetimi — DEĞİŞİKLİK GEREKLİ

**Denetlenen kod commit'i:** `7193ca6651f0e995f6c39481472ed9c0d46734a0`

**Not:** Güncel HEAD `3f90eeb91556d558c13adf559ef7d7cb75f57a39`; bu sonraki
commit yalnız `.lnk`, CSV ve indirme logları ekledi. Denetlenen Python kodu
`7193ca6` ile aynı.

### Kısa karar

Ana düzeltmelerin yönü doğru ve bugünkü gerçek defter sonucu bozulmamış:

- bulut `backfill` şeması birleşik sayımda fail-closed,
- kimlik `module + symbol + dir`, tolerans 15 dakika,
- aynı MT5 satırı bir kez kullanılıyor,
- iki defter yok / boş bulut dosyası şemalı boş sonuç veriyor,
- GOLD challenge portföyü artık dinamik live kümesini kullanıyor,
- tam intraday paketi bağımsız koşuda **417 passed, 3 skipped**.

Ancak "beş bulgunun beşi tamamen kapandı" hükmü erken. Aşağıdaki kanıt kapısı
uçları ve yeni elenenler kataloğu düzeltilmeden onay vermiyorum.

## Bloklayan / düzeltilecek bulgular

### 1. ORTA — sıfır bayt MT5 defteri hâlâ kırılıyor

**Yer:** `strategy-lab/intraday/forward_ea/ledger.py:24-46, 77-110`

`_oku_bulut()` `EmptyDataError` yakalıyor; `load_forward()` yakalamıyor. Sıfır
bayt MT5 + olmayan bulut sentetik yeniden üretiminde sonuç:

```text
EmptyDataError: No columns to parse from file
```

Önceki BULGU 3 "boş/eksik kaynakların kararlı davranışı" idi; yalnız bulut
tarafı kapandı.

**İstenen:** MT5 ve bulut için ortak `_oku_defter()`/public loader; dosya yokluğu,
sıfır bayt, tarih parse'ı ve şema doğrulaması aynı sözleşmeden geçsin. Sıfır
bayt MT5 regresyon testi ekle.

### 2. YÜKSEK — aynı kimlikteki çelişki yalnız `r` ile ölçülüyor

**Yer:** `ledger.py:113-133`

Aynı kimlik + aynı `r`, fakat farklı `backfill`, `status`, exit zamanı/fiyatı
olan iki kayıt çelişki sayılmıyor; `keep="first"` ile dosya sırası gerçeği
belirliyor. Tekilleştirme backfill filtresinden önce olduğundan ilk satır
`backfill=1`, ikinci satır `backfill=0` ise gerçek forward satırı tamamen
kaybolabiliyor. Sentetik yeniden üretimde iki satırdan **0 kanıt** kaldı ve hata
çıkmadı.

**İstenen:** yalnız tam birebir kopyayı sessizce düşür; aynı kimlikte herhangi
bir immutable/evidence alanı farklıysa fail-closed hata/karantina. En az
`backfill`, `status`, `r`, `exit_time`, `exit` karşılaştırılmalı.

### 3. YÜKSEK — açgözlü matcher maksimum bire-bir eşleşmeyi garanti etmiyor

**Yer:** `ledger.py:136-175`

Algoritma `sol` satır sırasına bağlı biçimde o anda en yakın kullanılmamış
sağı seçiyor. Bu maksimum eşleşme sayısını garanti etmiyor. Karşı örnek:

- sol: `00:00`, `00:01`
- sağ: önceki gün `23:56`, aynı gün `00:00`
- tolerans: 4 dakika

Mevcut algoritma yalnız `00:00↔00:00` çiftini alıyor. Oysa
`00:00↔23:56` ve `00:01↔00:00` ile iki geçerli çift var. Birleşimde fazladan
bulut kanıtı oluşabiliyor.

Bugünkü defter küçük ve gerçek eşleşme farkları en fazla 5 dakika olduğu için
bugünkü `NQ n=22` etkilenmiyor. Fakat amaç gelecekte güvenli kanıt kapısıysa
satır-sırası bağımlılığı kalmamalı.

**İstenen:** anahtar grubu içinde önce maksimum kardinalite, sonra minimum toplam
zaman farkı; uzun vadede writer'da deterministik `signal_id/trade_id`.

### 4. ORTA — `cloud_parity` merkezi kanıt okuyucusunu hâlâ atlıyor

**Yer:** `cloud_parity.py:27-29, 91-128`

Matcher ortaklaştırılmış, fakat CSV path/okuma ve backfill ayrımı kopya.
`backfill` kolonu yoksa `cloud_parity` hâlâ tüm satırları forward kabul ediyor.
Aynı dosya birleşik sayımda reddedilip parite raporunda kanıt sayılabilir.

**İstenen:** doğrulanmış MT5/bulut loader'larını `ledger.py` public API yap ve
pariteyi bu API üzerinden besle. Writer/reader için ortak `LEDGER_COLUMNS` ve
`TRADE_ID_COLUMNS` sözleşmesi oluştur.

### 5. ORTA — üç kritik regresyon testi iddia ettiği davranışı sınamıyor

**Yer:** `test_ledger.py:202-259`

- Zıt yön testi 30 dakika aralık kullanıyor; tolerans 15 dakika olduğu için
  `dir` kontrolü silinse de test geçer.
- "Bir MT5 bir kez" testindeki ikinci bulut satırı 20 dakika uzakta; `used`
  kümesi silinse de test geçer.
- "En yakın" testinde 14:55 bulut için 15:00 tek tolerans-içi aday; hangi adayın
  seçildiği union uzunluğundan görülemiyor.

**İstenen:** tüm adayları tolerans içine koy ve doğrudan `eslestir_bir_bir()`
çiftlerini/assert edilen MT5 satırını kontrol et. Örn. yön testi 5 dk; used testi
5 ve 10 dk; nearest testi iki tolerans-içi aday + eşleşen index doğrulaması.

## Yeni `elenenler.py` — bu haliyle veto aracı olarak güvenli değil

### Semantik hata

`intraday/elenenler.py:173-182` içindeki Donchian maddesi açıkça "Elenmis degil"
diyor fakat `KATALOG` içinde olduğu için CLI şu başlıkla gösteriyor:

```text
ELENMIS — BU TEZI KULLANMA
```

Ayrıca genel arama anahtarları kapsamı fazla geniş:

- `--kontrol sweep` → çalışan `SWEEP_CORE` ile isim çakışan elenmiş sweep
  varyantlarını blanket veto ediyor.
- `--kontrol orb` → emekli GOLD ORB yüzünden genel ORB tezini veto ediyor;
  çalışan NQ ORB ile kapsam ayrımı yok.
- FVG/EMA/VWAP gibi "tek başına edge değil" sonuçları, diskresyoner confluence
  olarak kullanımından ayrılmıyor.

Bu, araştırma sonucunu "standalone reddedildi"den "hiçbir bağlamda kullanma"ya
çeviren kategori hatasıdır.

### Gereksiz/tekrarlı kısım

- `elenenler.py` + testleri **432 satır** ve ledger fix commit'inin yaklaşık
  `%45.5`'i; ilgisiz feature aynı commit'e karışmış.
- `test_elenenler.py` tek başına **73 parametrik test** topluyor. 333→417 test
  artışının çoğu ledger güvenliği değil, statik metinde sayı/kelime varlığı.
- FOMC/Donchian sonuçları `hypotheses.json`/registry/vault bilgisinin ikinci
  elle yazılmış kopyası; şimdiden Donchian statüsü ayrışmış.
- Katalog şu an `seans_brief` veya diskresyoner akışa bağlı değil; yalnız manuel
  CLI. Bu yüzden 432 satırlık özellik aktif iş akışında otomatik koruma sağlamıyor.

**İstenen karar:** Bu feature'ı ledger fix'ten ayrı commit/konu olarak ele al.
`rejected`, `standalone_rejected`, `not_adopted`, `retired`, `structural`
statülerini ayır; yalnız gerçekten veto statüsündekileri "KULLANMA" olarak
göster. Mümkünse tek evidence registry'den türetilen salt-okunur görünüm olsun.
Bu yapılana kadar blanket veto olarak kullanılmamalı.

## Yüksek güvenli dead code / sadeleştirme adayları

1. `forward_ea/ledger.py:49-55` — `live_only()` üretim kodunda çağrılmıyor;
   yalnız kendi testi kullanıyor. Silinip test `load_forward(...,
   include_candidates=False)` üzerinden yazılabilir. **SAFE.**
2. `forward_ea/modules.py:46-86` — `_gold_orb_detector()` emeklilik sonrası
   çağrısız.
3. `forward_ea/modules.py:263-320` — `_es_div_detector()` ve `_ESDIV_CACHE`
   çağrısız. Gold/ES_DIV geçmişi git ve katalogda korunuyor; üretim modülünde
   yaklaşık 100 satır hareketsiz kod kalmış. Silmek veya açık bir `retired/`
   arşivine taşımak **CAREFUL**, fakat aktif dosyada tutmak gereksiz.
4. `modules.py:323-379` — emeklilik tarihçesi README+katalog+git'te tekrar;
   aktif dört modül uzun geçmiş metnine gömülmüş. Kısa katalog ID referansı yeter.
5. `test_challenge_sim.py:91-110` — davranış yerine `inspect.getsource()` ile
   kaynak metni test ediyor; monkeypatch + çıktı davranışı testiyle değiştirilmeli.

## Performans notu — acil değil

`eslestir_bir_bir()` O(sol×sağ). Ölçüm:

- bugünkü 53/146 satır: yaklaşık `0.04s`
- 1,000 çift: `1.16s`
- 4,000 çift: `5.10s`
- 8,000 çift: `14.97s`

Bugün bloklayıcı değil; append-only defter büyürken anahtar bazında gruplayıp
zaman sıralı eşleştirmeye geçilmeli.

## Son hüküm

- **Bugünkü sayıların doğruluğu:** geçti.
- **GOLD emekliliği/challenge düzeltmesi:** geçti.
- **İlk audit'in ana yönü:** büyük ölçüde düzeldi.
- **Geleceğe güvenli kanıt kapısı:** henüz tam geçmedi.
- **Gereksiz kod:** evet; en netleri `live_only`, emekli GOLD/ES_DIV dedektörleri
  ve mevcut haliyle aşırı/çift-kaynaklı `elenenler` feature'ı.

Kod değiştirmedim; yalnız yeniden denetim ve handoff yazdım.
