# HANDOFF — Claude → Hermes

## `9a06c24` denetiminin dört bulgusu + YENİ bir yüzey — DENETİME

**Kod commit'leri:**

- `1ddcfd2` — senin dört bloklayan bulgun + katalog regresyon testleri
- `bee3ec8` — MT5 defterini repoya yayınlama
- `05fda96` — brief: hacim yoksa sıfır basma
- `5656762` — trend katmanı (yeni yüzey, aşağıda)

Test: **438 passed, 3 skipped**. Gerçek defter: NQ_ORB **n=22, exp_R −0.089991**
(senin bağımsız hesabınla aynı, değişmedi).

---

## Dört bulgu

### 1. Çelişki kapısı normal loader'larda atlanıyordu → KAPANDI

Doğrulama ve tekilleştirme artık `oku_defter()` içinde, yani `load_forward`,
`load_cloud`, union ve parite hepsi aynı denetlenmiş çıktıyı tüketiyor.
"Kapının bir çağrı yolunda açık olması, kapı olmaması demek" — haklıydın.

Testler: `test_CELISKI_kapisi_HER_public_loaderda_calisir` (parametrik,
load_forward + load_cloud).

### 2. Tripwire bütünlük hatasını skip'e çeviriyordu → KAPANDI

`_forward_ozet()` artık `ValueError`/`FileNotFoundError` yakalamıyor. Gerçekten
boş defter hâlâ `{}` dönüyor ve o ayrı testle korunuyor
(`test_GERCEKTEN_bos_defter_hala_bos_ozet_dondurur`), böylece "veri yok" ile
"veri bozuk" ayrımı duruyor.

Test: `test_kanit_butunlugu_hatasi_SKIP_EDILMEZ`.

### 3. Şema yalnız kolon varlığını doğruluyordu → KAPANDI

`_dogrula_degerler()`: `module`/`symbol` boş değil, `dir ∈ {1,-1}`,
`entry_time` NaT değil, `r` sonlu, `backfill ∈ {0,1}`. Hata mesajı CSV satır
numarası veriyor, sessiz filtre yok. `df.empty` dönüşünden ÖNCE şema
doğrulanıyor (sıfır satırlı ama eksik başlıklı dosya artık gizlenmiyor).

**Senin listende olmayan bir uç:** pandas `entry_time`'daki tek bir bozuk
değeri çözemezse **kolonun tamamını metin bırakıyor**. O zaman `isna()` boş
dönüyor, bozukluk görünmez oluyor ve bütün sıralama/eşleştirme sessizce metin
karşılaştırmasına düşüyor. Ayrı kontrol eklendi.

Testler: 9 parametrik bozuk-değer vakası + eksik başlıklı sıfır satır.

### 4. Eşit maliyetli optimumda satır sırası → KAPANDI

Gruplar eşleştirmeden önce `entry_time`'a göre sıralanıyor. Senin karşı örneğin
(MT5 00:01 r=+1; bulut 00:00 r=+10 ve 00:02 r=−10) doğrudan test:
`test_birlesim_BULUT_SATIR_SIRASINDAN_bagimsiz` — düz ve ters sırada birleşik R
eşit olmalı. Kalıcı çözümün (writer'dan `trade_id`) hâlâ doğru; yapılmadı.

### scipy — GERİ ALINDI

Sen orta bulgu 4'te "SciPy requirements'a doğru eklenmiş" demiştin, ama
`test_cloud_deps` scipy'yi bulutta açıkça yasaklıyor ve telefon brifingi
ledger'ı import ediyor. Yani 2026-08-21'de ölçümü 14 saat durduran hatayı geri
getiriyordum. Matcher saf Python min-cost max-flow'a (SPFA) çevrildi; doğruluk
scipy'ye karşı ölçülüyor (60 rastgele allow-maskeli matris, kardinalite +
toplam maliyet). scipy yalnız dev/test bağımlılığı, `importorskip` ile.

`test_cloud_deps`'e ikinci kapı eklendi: telefon brifingi de ağır bağımlılık
olmadan üretilebiliyor mu.

## Katalog regresyon testleri — senin mutasyonların artık düşüyor

İkisini de kendim tekrarladım, haklıydın:

- Donchian'ı `retired` yapmak eski testten geçiyordu (yalnız `rejected`
  yasaklıydı). Artık `VETO_STATULERI` tek kaynak ve tüm veto statüleri
  registry'ye karşı kontrol ediliyor.
- Kapsamsız yeni bir genel `rejected ORB` maddesi üç testten de geçiyordu
  (kontroller önceden seçilmiş ID'lere bakıyordu). Artık: bir veto maddesi
  canlı modül anahtar kelimesi taşıyorsa kapsam ZORUNLU ve kapsam metni canlı
  modülün adını yazmak zorunda. CLI çıktısı `capsys` ile sweep/orb/donchian/fvg
  sorgularında sınanıyor.

Veto/veto-değil ayrımı üç yerde ayrı hesaplanıyordu (CLI, brifing, testler);
tek kaynağa indirildi (`veto_mu`).

---

## YENİ YÜZEY — burası asıl denetim isteğim

Aşağıdakiler senin denetlediğin commit'ten sonra eklendi ve **kanıt kapısına
değil, karar öncesi bilgiye** dokunuyor. Yeni bir sahte-edge yüzeyi açtım mı,
onu sormak istiyorum.

### 1. Telefon brifingi (`telefon_brief.py`, `TELEFON/`)

Kullanıcı sürekli PC'de olamıyor; diskresyoner ray birincil ray olduğu için
rayın fiilen çalışmaması demekti. GitHub Actions saat başı `TELEFON/BRIEF.md`
üretiyor, telefondaki sohbet asistanı onu okuyor.

Alan seti `seans_brief.sembol_olgusu()`'ndan geliyor — ikinci bir olgu üreticisi
YAZILMADI, feed enjekte ediliyor. Testler yorum sıfatı ve emir kalıbı taramasıyla
kilitli (mutasyonla doğrulandı).

**Bu sırada iki sessiz yalan buldum ve düzelttim:**

- **Kısmi gün**: bugünün kapanmamış günlük barı ATR/hacim/EMA'ya giriyordu.
  NASDAQ "ATR 100 günün %0. yüzdeliği" basıyordu — yarım günün aralığı elbette
  en dar. Göstergeler artık kapalı günlerden; bugünün ham aralığı ayrı alan.
- **Bulutta EMA200 60 barla hesaplanıyordu**: yfinance 15m'i ~60 gün veriyor ve
  günlük seri ondan resample ediliyordu. Gerçek günlük seri eklendi (`1d`
  desteği), 412 bar.

Ayrıca ilk canlı seansta çıktı: FX'te hacim yok, brief "hacim 0, %0. yüzdelik"
basıyordu. "Ölçülmemiş" ile "düşük" farklı iddialar; katman kapısında hacim
katmanını yanlışlıkla dolu saydırabilirdi. Artık "BU FEED HACIM VERMIYOR".

### 2. Trend katmanı (`trend_katmani.py`) — EN ÇOK BUNU DENETLE

Kullanıcı telefondan "trend haline gelmiş pariteleri bul" diye sormak istedi.
Bunu modele sordurmayı reddettim: model kendi tanımını uydurur, kendi listesini
seçer, filtrelenmiş bir evren gösterir — 2026-08-01'de kapatılan AI scout'un
aynısı. Onun yerine kodlanmış sabit tanım:

- 200EMA konumu + % uzaklık, ADX(14) günlük, 20/50 günlük % değişim
- sıralama 20 günlük değişime göre, **eleme yok** — 21 sembolün tamamı listede
- tanım sonuca bakılmadan sabitlendi, sabitler testle kilitli

**Sana sorularım:**

1. **Sıralama bir seçim mi?** Ben "evrenin tamamı listeleniyor, yalnız sırası
   belirleniyor, eleme yok" diye savundum. Eşik koysaydım (ADX>25) o bir
   hipotez olurdu. Sıralamanın kendisi de dikkati yönlendiriyor mu — yani
   listenin başındakine bakma eğilimi ölçülmemiş bir seçim üretir mi?

2. **Evren genişlemesi.** Kullanıcı 21 sembol istedi (portföyün ötesinde:
   GER40, XAGUSD, WTI, JPY çaprazları, kripto). Uyardım — `sweep_cok_endeks`
   katalogda `rejected` ve slot kısıtı ölçülmüştü; kullanıcı yine geniş evreni
   seçti, uyguladım ve brifingin kendi metnine **"bu liste işlem evreni
   değil"** satırını koydum. Bu yeterli bir sınır mı, yoksa geniş evren
   diskresyoner rayı ölçülemez hale getirir mi? (Aday sayısı artarsa
   seçicilik metriği ne anlama gelir?)

3. **ADX taşındı.** `edge_lab._adx` → `indicators.adx`; edge_lab geri import
   ediyor. Gerekçe: brifing bunu bulutta hesaplıyor, edge_lab modül seviyesinde
   `data` + `honest_engine` çekiyor. Davranış değişmedi (adx_lab/sweep aynası
   testleri geçiyor) ama gerçekten birebir mi, doğrulamanı isterim.

4. **Yeni semboller `cloud_feed._EXTRA`'ya eklendi.** O tablo "forward EA
   adaylarının kullandığı semboller" diye yazılmıştı. Yorumla ayırdım ("yalnız
   trend katmanı için, üzerlerinde çalışan modül yok") ama tablo artık iki işi
   birden taşıyor. Ayrı tablo mu olmalı, yoksa iki tablo tutmak zaten bu
   projenin tekrar eden hatası mı?

### 3. Defter yayınlama (`defter_yayinla.py`)

Bulut defteri saat başı kendini işliyordu, MT5 defteri elle commit ediliyordu ve
29 Ağustos'tan beri push edilmemişti. Ölçtüm: bulut başladığından beri 30
forward işleminin **6'sı yalnız MT5'te** (bedava feed ^FTSE/^FCHI/RTY'yi kötü
kapsıyor) — yani tek diskte duruyordu. Canlı modüllerde fark yoktu, aday
katmanında ~%20 eksikti.

`Forward-EA-Guncelle.cmd` sonunda çalışıyor. State dosyası bilerek dışarıda
(makineye özel). Başarısız push commit'i geri almıyor.

## Ölçüm notu — senin toleans ölçümünü tekrarladım

İlk canlı seansta iki şüpheli çift gördüm ve iki kez sayma olabilir diye
korktum. Ölçtüm, değilmiş: eşleşen 18 gerçek çiftin farkı **medyan 0, maks 5
dakika** (senin ölçümünle aynı). Şüpheli çiftin risk mesafeleri 3.4 kat farklı
(SL 1.67 vs 5.74 puan) — ayrı sinyal olduğunun kanıtı. 15 dakikalık tolerans
geniş marjla doğru.

Yan gözlem: `CAND_SWEEP_US2000` iki feed'de **farklı barlarda** tetikleniyor.
Aday katmanında, kararı etkilemiyor, ama kayda geçiyor.

## Emin olmadıklarım (senin bakmanı istediğim yerler)

- Trend katmanı **bulutta henüz koşmadı**; lokalde 15.5 sn. Bir sonraki cron'da
  görülecek, hata olursa Telegram uyarısı var.
- Brifing %30 büyüdü (5.5K → 7.2K karakter). Telefon tarafı bir kez test edildi
  ama trend katmanlı hali test edilmedi.
- `MIN_N` iki yerdeydi (`test_demotion_tripwire.py` ve `telefon_brief.py`).
  Bunu handoff'a "emin değilim" diye yazacaktım, yazmak yerine düzelttim:
  `risk.DEMOTION_MIN_N` tek kaynak, ikisi de oradan import ediyor, testi de var
  (`test_dusurme_esigi_TRIPWIRE_ile_AYNI_kaynaktan`). Ayrışsalardı brifing
  "eşiğe 3 işlem" derken tripwire başka eşikten karar verirdi.
