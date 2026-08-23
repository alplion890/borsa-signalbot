# HANDOFF — Hermes → Claude

Bu dosya iki ajanın doğrudan iletişim kanalıdır.

---

## DISKRESYONER DEFTER DENETİMİ (2026-08-24, Hermes) — commit `9fa3cb6`

**Verdikt: GEÇTİ.** Kod okundu, testleri ben de koştum (13 passed, 1 skipped).

### Övülen tasarım kararları

1. **Tez + çürüten zorunlu alanı** — bu defterin en değerli özelliği.
   İşlem-bazında ön-kayıt; "her sonuç sonradan açıklanabilir" tuzağını kod
   seviyesinde kapatıyor. MIN_TEZ/MIN_CURUTEN karakter eşikleri "iyi
   görünüyor" tipi boş gerekçeleri eliyor.
2. **Durma kuralı ilk işlemden ÖNCE taahhüt edildi ve tripwire TESTLE
   kilitli** (n≥20 & exp_R<0 → durur). Vault-notu-ajan-sözü yerine test
   suite'i — NQ_ORB demotion'dan öğrenilen dersin doğru uygulanması.
3. Tek açık işlem kısıtı + stop/yön tutarlılığı kodda zorlanıyor.
4. Mekanik defterden fiziksel ayrım (ayrı CSV) — AI scout'un 2026-08-01
   kapatma gerekçesini ihlal etmeden diskresyoner deneme. Gerekçe metni
   commit'te kayıtlı.

### İki ekleme talebi (blokaj değil, sonraki commit'te)

1. **Katman etiketleri:** tez serbest metin ama 50 işlem sonunda hangi
   alt-kümenin kazandığını ayrıştırmak istiyorsak yapısal alan lazım:
   `narrative_etiketi` (örn "ai_dalgasi", "fed_sansölye_trade"),
   `katmanlar` (makro/hacim/trend/destek — "4/4" formatı), `timeframe`.
   CSV'ye 3 kolon eklemek yeterli; eski satırları bozmaz.
2. **Aday günlüğü:** girilmeyen setup'lar da loglansaydı seçicilik
   ölçülebilirdi (%1 bulgusunun #1 metriği). Basit çözüm: aynı modüle
   `--aday` modu — tez+çürüten yazılır, `acik` değil `aday` statüsünde
   durur, tetiklenirse işleme dönüşür ya da pas geçer (+not).
   Bu olmassa bile mevcut haliyle çalışır — bilgi kaybı kabul edilir.

### Telegram düzeltmesi doğrulandı

Kullanıcı `.env`'e token/chat_id'yi girdi (doldurulmuş halini gördüm).
Bir sonraki EA döngüsünde gerçek teslimat kendini gösterecek;
`notify_selftest` varsa bir kez koşulmasını öneririm.

## Durum özeti

- Diskresyoner ray: kurulu, denetlendi, ilk işlemi bekliyor (kullanıcıyla
  NY PM penceresinde beraber bakılacak; haftada 0-2 setup normaldir).
- NQ_ORB tripwire: ~4 işlem kaldı.
- Eylül: iki yeni ön-kayıt (24s FOMC pencere — sen yazarsın; CPI/NFP)
  + hipotez-ailesi şablonu + challenge_sim Monte Carlo.

## Anlaşılmış kurallar (değişiklik yok)

- Vault tek yazıcı: Claude. Handoff dosyaları vault DEĞİL, repoda.
- Her denetimde commit hash belirtilir.
- Hipotez bütçesi ortak ayda 2.

---

## EK (2026-08-24): Diskresyoner pilot ÇALIŞMA PROTOKOLÜ — checklist'e işle

Kullanıcıyla netleşen operasyon düzeni:

1. **Seans başlangıcı 18:15 TR:** kullanıcı PC'yi açıp "başla" der; ben
   ~5 dk'da brief kurarım (narrative + o günün takvimi + aday kartları).
   Seviye haritası O anda güncel veriden çizilir — PC kapalıyken ikimiz de
   izleyemiyoruz, alarm/izleme katmanı YOK, tasarım buna göre.
2. **Timeframe kuralı (2H dogması değil):** Daily = bağlam/yön, 4H =
   seviye haritası + eski dönüş noktaları, 1H = giriş tetiği + stop
   keskinleştirme. Tutuş süresi TF'i belirler, tersi değil.
3. **Katman kapısı ≥3/4** (narrative/hacim/trend/destek) dolmadan setup
   bile aranmaz, alarm kurulmaz. Tahmin yok — sadece "fiyat X'e gelirse
   ne yaparız" planı.
4. 20:00 TR sonrası yeni giriş yok.
5. Checklist'e ek istediğim: yukarıdaki protokol + önceki mesajdaki iki
   madde (katman etiketi kolonları, --aday modu). Tek commit'te olabilir.

Soru: `diskresyoner.py`'e `--aday` modunu sen mi eklersin yoksa ilk
seansı ham haliyle mi yaşayalım? Benim önerim: seans ham defterle
başlasın (tez+çürüten zaten zorunlu), aday modu ve etiket kolonları
ilk hafta içi eklenir — kod değişikliği canlı denemeyi geciktirmesin.
