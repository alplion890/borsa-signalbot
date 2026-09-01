# HANDOFF — Hermes → Claude

Vault tek yazıcı Claude; bu dosya repo içi denetim kanalıdır.

---

## `9a06c24` bağımsız yeniden denetimi — DEĞİŞİKLİK GEREKLİ

**Denetlenen commit:** `9a06c24a8b15a50609e920f5f62412aa5a61843e`

**Parent:** `fccdfb871171fa812a62c589fbc6310a59c71791`

**Asıl kod commitleri:** `ef5f6ae5d8eb8d52203f4cf67df86843b84b2c41` ve `fccdfb871171fa812a62c589fbc6310a59c71791`.

### Kısa hüküm

Önceki beş ledger bulgusunun hedeflenen mekanizmaları büyük ölçüde doğru
kapatılmış; katalogdaki blanket-veto kategori hatası da mevcut kayıtların CLI
sunumunda çözülmüş. Fakat kanıt kapısında dört açık kaldığından tam onay vermiyorum:

1. çelişki kapısı `load_forward/load_cloud` çağrılarında hiç çalışmıyor,
2. demotion tripwire kanıt kapısı hatalarını yutup "kanıt yok" skip'ine çeviriyor,
3. zorunlu kolonların **değerleri** doğrulanmıyor; null kimlik/zaman/R kabul
   ediliyor ve birleşik kanıtı bozabiliyor,
4. maksimum-kardinalite matcher eşit maliyetli optimumlarda hâlâ satır sırasına
   bağlı; hangi bulut kaydının fazladan kanıt sayıldığı ve toplam R değişebiliyor.

### Geçen düzeltmeler

- Sıfır bayt MT5 ve bulut CSV: şemalı boş sonuç.
- Eksik `backfill`: fail-closed `ValueError`.
- Birleşik union yolunda aynı trade kimliğindeki `backfill/status/r/exit_time/exit`
  çelişkileri hata veriyor; yalnız tam kopya düşüyor. Bu düzeltme aşağıda açıklandığı
  üzere genel loader yollarına uygulanmamış.
- Önce maksimum kardinalite, sonra minimum toplam zaman farkı hedefi: 500 rastgele
  küçük matris için exhaustive oracle ile **500/500** doğru.
- Önceki greedy karşı örneği artık iki eşleşme veriyor.
- Üç zayıf regresyon testi gerçekten tolerans içindeki adayları zorluyor.
- `cloud_parity` yol/okuyucu/matcher kopyalarını kaldırmış; gerçek forward raporu
  **14 eşleşme, %100 aynı sonuç, R korelasyonu 1.00**.
- `live_only`, `_gold_orb_detector`, `_es_div_detector`, `_ESDIV_CACHE` kaldırılmış;
  GOLD tarihsel ledger kayıtları korunmuş.
- Challenge testi kaynak metni yerine davranış test ediyor.
- Katalog `rejected / standalone_rejected / not_adopted / retired` ayrımını yapıyor;
  Donchian veto değil, FVG/EMA yalnız standalone reddedilmiş, SWEEP/NQ_ORB kapsam
  satırları canlı modülleri açıkça hariç tutuyor.

## Bloklayan bulgular

### 1. YÜKSEK — çelişki kapısı normal loader çağrılarında atlanıyor

**Yer:** `strategy-lab/intraday/forward_ea/ledger.py:107-155,232-244`

`tekillestir()` doğru çelişki denetimini yapıyor, fakat yalnız
`birlesik_forward()` onu çağırıyor. `load_forward()` ve `load_cloud()` doğrudan
`_filtrele(oku_defter(...))` döndürüyor. Aynı kimlik/zaman/R ile `status=tp` ve
`status=sl` iki sentetik satırda:

- `load_forward()` iki satırı da kabul etti,
- `tekillestir()` aynı veri için beklendiği gibi `ValueError` verdi.

`funded_sim.py`, `overfit_audit.py`, `portfolio_ab.py` ve `search_budget.py`
`load_forward()` kullanıyor; bu çağrı yollarında bozuk tekrar hem `n` şişirebilir
hem de çelişkili sonucu kanıt sayabilir.

**İstenen:** `tekillestir()` ortak public loader sözleşmesinin içinde çalışmalı;
`load_forward`, `load_cloud`, union ve parity aynı doğrulanmış+tekilleştirilmiş
çıktıyı tüketmeli. Her public loader için çelişkili tekrar regresyon testi ekle.

### 2. YÜKSEK — demotion tripwire fail-closed hatalarını skip'e çeviriyor

**Yer:** `strategy-lab/intraday/signalbot/test_demotion_tripwire.py:29-50`

`_forward_ozet()` `birlesik_forward()` kaynaklı `ValueError` ve
`FileNotFoundError` hatalarını yakalayıp `{}` döndürüyor. Sentetik olarak
`ValueError("CELISEN")` üretildiğinde özet boş kaldı; parametrik test bunu
"forward kaydı yok" diyerek skip ediyor. Yani eksik şema veya çelişkili duplicate
tam da fail-closed kapısını tetiklediğinde güvenlik taahhüdü kırılmak yerine devreden
çıkıyor; LIVE modülün düşürülmesi süresiz ertelenebilir.

**İstenen:** Kanıt bütünlüğü hatalarını yakalama; test açıkça fail etmeli. Gerçekten
opsiyonel veri-yok durumu gerekiyorsa yalnız açık, doğrulanmış boş defter sonucu skip
edilmeli ve bunun ayrı regresyon testi bulunmalı.

### 3. YÜKSEK — şema kapısı yalnız kolon varlığını doğruluyor

**Yer:** `strategy-lab/intraday/forward_ea/ledger.py:47-73,76-104,193-209`

`_dogrula_sema()` kolonların varlığını kontrol ediyor; zorunlu değerlerin null,
boş, sonlu veya geçerli domain içinde olmasını kontrol etmiyor. Sentetik iki-feed
sonucu:

- `module=None` → kabul, birleşimde `n=2`;
- `symbol=None` → kabul, `n=2`;
- `dir=None` → kabul, `n=2`;
- `entry_time=None` → kabul, `n=2`;
- `r=None` → kabul, `n=1`, `r=[NaN]`.

Ek olarak `backfill=2` okuyucudan geçiyor. `load_forward` bunu sessizce dışlarken
`cloud_parity` içindeki `~(backfill == 1)` maskesi satırı **forward** kabul ediyor.
Yalnız `entry_time,module` başlıklarını taşıyan sıfır satırlı CSV de şema
doğrulanmadan şemalı boş deftere çevriliyor; eksik başlık sessizce gizleniyor.

Aynı null kimlik iki tarafta olduğu halde `groupby(..., dropna=False)` anahtarları
sözlük lookup'ında eşleşmiyor; aynı işlem iki kanıt oluyor. NaN R de kanıt satırı
olarak geçiyor. Bu, fail-closed sözleşmesine aykırı ve ileride n/exp_R/PSR eşiklerini
bozabilir.

**İstenen:** okuyucuda en az şu invariantları doğrula: `module/symbol` boş değil,
`dir` izinli ve null değil, `entry_time` parse edilmiş ve NaT değil, `r` sayısal ve
sonlu, `backfill ∈ {0,1}`. Geçersiz satır sessiz filtrelenmemeli; kaynak+satır
numarasıyla `ValueError`/karantina olmalı. `df.empty` dönüşünden önce de header
şeması doğrulanmalı. Her alan için sentetik regresyon testi ekle.

### 4. YÜKSEK — eşit maliyetli optimumda birleşik kanıt satır sırasına bağlı

**Yer:** `ledger.py:158-215,218-259`

Atama maksimum kardinaliteyi ve minimum toplam zamanı sağlıyor; ancak eşit maliyet
bağında karar SciPy'nin giriş sırasına kalıyor. Sentetik örnek:

- MT5: `00:01, r=+1`;
- bulut: `00:00, r=+10` ve `00:02, r=-10`.

İki bulut adayı da MT5'e 1 dakika. Bulut satır sırası `[00:00,00:02]` iken birleşik
R toplamı **-9**; sıra ters çevrilince **+11**. Maksimum kardinalite her iki durumda
1 ve toplam mesafe aynı, fakat hangi bulut satırının unmatched kanıt sayıldığı
kanıt sonucunu değiştiriyor.

Bugünkü gerçek defterde 100 bulut satır permütasyonunun tamamı aynı `n=122` ve aynı
modül toplamlarını verdi; güncel NQ sonucu etkilenmiyor. Yine de append-only kanıt
kapısı dosya sırasından bağımsız olmalı.

**İstenen:** kısa vadede identity gruplarını stabil biçimde zaman/kalıcı sıra anahtarı
ile sırala ve eşit-optimum belirsizliği için fail-closed test ekle. Doğru kalıcı çözüm
writer'dan taşınan deterministik `signal_id/trade_id`; farklı R taşıyan birden çok
optimal uzlaştırma varsa keyfi seçim yerine hata/karantina.

## Orta/ikincil bulgular

1. `cloud_parity.py:127-139` forward bulut bloğunu **tüm** MT5 satırlarıyla
   eşleştiriyor. Bugünkü gerçek forward çiftlerde MT5-backfill çapraz eşleşmesi yok,
   fakat sentetik durumda forward kapsama bir MT5 backfill kaydıyla sahte biçimde
   kapanabilir. Forward blokta `mt5[backfill == 0]` kullanılmalı. Backfill bloğunun
   cross-mode karşılaştırma niyeti ayrıca açıkça belgelenmeli.
2. `LEDGER_KOLONLARI` `status` içermiyor, fakat `cloud_parity.match()` status'u
   zorunlu kullanıyor. Status'suz ama diğer kolonları tam CSV okuyucudan geçiyor,
   sonra parite `KeyError: 'status'` ile kırılıyor. Kanıt uydurmuyor ama ortak loader
   sözleşmesi tüketici ihtiyacını tam ifade etmiyor; pariteye özel şema kapısı ekle.
3. Katalog hâlâ manuel ikinci source-of-truth ve koruma testleri mekanizmayı tam
   zorlamıyor. Sentetik mutation'da registry'de `tamamlandi` olan Donchian katalogda
   veto statüsü `retired` yapılınca tutarlılık testi yanlışlıkla geçti; test yalnız
   `rejected` statüsünü yasaklıyor. Ayrıca boş kapsamlı yeni bir genel `rejected ORB`
   maddesi üç canlı-modül/kapsam testinden de geçti; kontroller yalnız önceden seçilmiş
   ID'leri ve tam modül adını arıyor. Mevcut kayıtların CLI çıktısı doğru, bu nedenle
   bugünkü karar açısından orta; fakat commit'in blanket-veto regresyon güvencesi
   iddia edilenden zayıf. Veto statülerinin tamamını registry durumuna karşı kontrol
   et ve `ara()`/CLI çıktısını `capsys` ile sweep/orb/donchian/fvg sorgularında sınat.
4. SciPy ana `strategy-lab/requirements.txt` dosyasına doğru eklenmiş ve gerçek
   `cloud_runner`/signalbot üretim import yolu ledger'ı import etmiyor. Ancak
   `intraday/signalbot/test_demotion_tripwire.py` ledger'ı import ediyor;
   yalnız `intraday/signalbot/requirements.txt` kurulu ortamda test collection
   `ModuleNotFoundError: scipy` ile kırılıyor. Bu requirements dosyası `pytest` de
   içerdiği için test ortamı sözleşmesi belirsiz. SciPy'yi buraya da ekle veya testi
   SciPy gerektirmeyen sınırdan besle; üretim deploy için şu an bloklayıcı değil.

## Bağımsız doğrulama

- Hedefli: **57 passed, 2 skipped**.
- Tam `intraday`: **369 passed, 3 skipped**, 8 mevcut `FutureWarning`.
- Matcher oracle: **500/500**.
- Gerçek birleşik ledger: `n=122` toplam; NQ `n=22`, `exp_R=-0.0899906041`.
- Gerçek forward parity: 14 eşleşme; 100 satır permütasyonunda güncel sonuç sabit.
- `git diff --check`: temiz.

## Son karar

| Alan | Karar |
|---|---|
| Önceki 5 ledger bulgusu | **Kısmen — union yolu düzeldi, public loader sözleşmesi tam değil** |
| Demotion tripwire fail-closed davranışı | **Çözülmedi — bütünlük hatası skip oluyor** |
| Dead code / davranış testi | **Çözüldü** |
| Katalog blanket-veto semantiği | **Mevcut kayıtlar çözüldü; regresyon testleri kısmen** |
| Katalog tek source-of-truth | **Kısmen** |
| Geleceğe güvenli kanıt kapısı | **Çözülmedi — değişiklik gerekli** |
| Bugünkü gerçek NQ sayısı | **Doğru ve değişmedi** |

Kod değiştirmedim; yalnız bağımsız denetim, sentetik doğrulama ve bu handoff'u yazdım.
