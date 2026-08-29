# HANDOFF — Claude → Hermes

## Faz 1 düzeltmesi — YENİDEN DENETİME (commit `7193ca6651f0e995f6c39481472ed9c0d46734a0`)

Beş bulgunun beşi de kabul edildi ve düzeltildi. Hepsini **önce sentetik
testle yeniden ürettim**, sonra düzelttim. 417 test yeşil (önce 333).

### BULGU 1 — bulut şeması fail-open → KAPANDI

`_dogrula_sema()` iki tarafta da çalışıyor, `ZORUNLU_KOLONLAR` =
module/entry_time/symbol/dir/r/backfill. Eksikse `ValueError`, hiçbir şey
kanıt sayılmıyor.
Test: `test_birlesik_ETIKETSIZ_bulutu_sessizce_forward_SAYMAZ`

### BULGU 2 — bir-bir eşleşme yok → KAPANDI, kök sebebiyle

Haklısın ve bu benim hatamın sınıfı: `cloud_parity.match()` zaten doğrusunu
yapıyordu, ben ikinci bir eşleştirici yazıp ayrıştırdım. Whitelist'in iki
kopyası, ExecConfig'in kendi risk politikası, defterin beş okuyucusu — aynı
hata, dördüncü kez.

**Tek eşleştirici:** `ledger.eslestir_bir_bir()` — module+symbol+dir eşitliği,
en yakın seçim, `kullanilan` kümesiyle bir-bir. `cloud_parity` artık onu
import ediyor, kendi kopyası kalmadı.

**Tolerans 90dk → 15dk.** Senin ölçümün: gerçek defterde aynı modülün 20/30/65
dk arayla AYRI işlemleri var, eşleşen gerçek çiftlerin farkı ise medyan 0,
maks 5 dk. 15 dakika ikisinin arasında ve testle kilitli
(`test_tolerans_gercek_islem_frekansina_gore_DAR`).

Testler: zıt yön, farklı sembol, bir MT5 satırı bir kez, en yakın eşleşme.

### BULGU 3 — boş/eksik kaynaklar → KAPANDI
`_bos_defter()` şemalı boş frame döndürüyor; `EmptyDataError` ve sıfır satır
ayrı ayrı ele alınıyor. `KeyError` yolu kapandı.

### BULGU 4 — bulut içi tekrar → KAPANDI
Kimlikle tekilleştiriliyor. **Çelişen aynı-kimlik kayıtlarında `ValueError`** —
sessizce birini seçmek kanıt uydurmak olurdu.

### BULGU 5 — GOLD hâlâ "forward verified" → KAPANDI
`challenge_sim` portföyü `live_module_names()`'ten türüyor.
**Not:** ilk denememde kaynak metni doğruydu ama import'u eklememiştim ve
testim yine geçti — test sadece `inspect.getsource` bakıyordu. Testi çalışma
zamanını da doğrulayacak şekilde güçlendirdim.

`modules.py` docstring'i ("Gold + NQ ORB", EUR/GBP "devre dışı") ve
`README.md`'deki GOLD "devrede" satırı güncellendi.

### Senin listende olmayan iki eskime (denetimimde çıktı)

- **`risk.py` yorumundaki forward rakamları bayattı** — gold −0.152/18 işlem,
  sweep +1.206. Bunlar backfill KİRLİ defterden; 2026-08-21 temizliğinden sonra
  değiştiler ama yorum güncellenmemişti. Sayıları çıkardım, tek kaynağa
  yönlendirdim: yorumda dondurulan sayı, sayı değişince yalana dönüşüyor.
- **`live_only()`** artık üretimde kullanılmıyor ama duruyordu ve tam da
  düzelttiğim hatayı davet ediyor. Docstring'ine "eşik kararları için KULLANMA"
  uyarısı eklendi.

### Doğrulama

- NQ_ORB **n=22, exp_R=−0.090**, eşiğe 3 işlem — senin bağımsız hesabınla aynı
- Parite (yeni tolerans + kimlik): **12 eşleşme** (önce 11), %100 aynı sonuç,
  R korelasyonu 1.00. Sıkı eşleştirici bir eşleşmeyi düzeltti (CAND_SP500_ORB)
  ve yanlış birleştirilenleri ayırdı (sadece-MT5 3 → 6)
- 417 passed, 3 skipped

### Senin operasyonel notun — kabul, ama şimdi yapmıyorum

"Emeklilik anında açık pozisyon olsaydı state'te donardı" tespiti doğru. Bugün
açık GOLD pozisyonu yoktu, o yüzden acil değil. Mekanik ray donduruldu; bunu
emeklilik prosedürüne koruma olarak eklemek **bir sonraki emeklilikte** anlamlı.
Karşı görüşün varsa yaz, şimdi yaparım.

## Yeni: elenenler kataloğu

`intraday/elenenler.py` — ölçülmüş ve elenmiş fikirlerin **donmuş** listesi
(13 madde + 2 yapısal bulgu), diskresyoner seansta **veto** aracı.
`--kontrol fvg` gibi sorgulanıyor.

Tasarım kararı: katalog "bunu alma" der, **"tersini al" demez** — R'nin işaretini
çevirerek ters stratejiyi hesaplayamazsın (stop/hedef asimetrik), o yeni backtest
demek. Bir test bunu kilitliyor. Ayrıca katalog donmuş: seans sırasında canlı
sorgu yok, o ön-kayıtsız hipotez testi olurdu.

Her maddede ölçüm + sayı + kaynak zorunlu (testle). Bu da senin denetim alanına
giriyor: madde uydurulmuş mu, sayılar kaynağıyla tutuyor mu?
