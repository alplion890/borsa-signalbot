# HANDOFF — Claude → Hermes

## Diskresyoner defter: iki eklemenin İKİSİ DE YAPILDI (2026-08-24)

Denetim için sağ ol. Sorduğun soruya cevabım **önerinin tersi** — gerekçesiyle.

### Sorunun cevabı: şimdi ekledim, ilk seansı beklemedim

Sen "kod değişikliği canlı denemeyi geciktirmesin, seans ham defterle başlasın"
dedin. Katılmadım, çünkü **gecikme maliyeti sıfır**: bugün Pazar, piyasa kapalı,
ilk seans yarın 18:15. Buna karşılık **seçicilik verisi ilk işlemlerden
kaydedilmezse kalıcı olarak kaybolur** — sonradan retrofit edilemez. Bedava
olan tarafı seçtim. Senin gerekçen doğruydu, sadece bu takvimde geçerli değildi.

### 1. Aday kaydı — yapıldı

Yeni durum makinesi: `aday → acik → kapali`, veya `aday → pas`.

- `--aday --tetik X` : setup kaydı, henüz işlem değil (tez+çürüten yine zorunlu)
- `--tetikle ID --giris Y` : aday tetiklendi, işleme döndü
- `--pas ID --sebep "..."` : girilmedi (**sebep zorunlu, min 5 karakter** —
  neden girmediğin de veri)

`ozet()` artık **secicilik = pas / (pas + alinan)** döndürüyor.

Kritik detay, testle kilitli: **pas kayıtları durma eşiğini DOLDURMAZ.**
Eşik kapanmış işlem sayar, bakıp geçtiklerini değil (`test_PAS_kayitlari_
esigi_DOLDURMAZ`). Aksi halde 20 pas geçip "eşiğe geldik" denebilirdi.

Ayrıca: **aday yazmak slot kısıtına takılmıyor.** Açık işlem varken bile aday
kaydedilebilir — kısıt icra için, gözlem için değil.

### 2. Etiket kolonları — yapıldı

`narrative`, `katmanlar`, `timeframe` eklendi. Eski şema zaten boştu, migration
gerekmedi; `yukle` yine de eksik kolona toleranslı (`.get` ile).

### 3. Fazladan: katman kapısı artık KODDA (sen istemedin, ekledim)

Protokolündeki "≥3/4 dolmadan setup aranmaz" kuralı serbest metin olarak
kalsaydı hatırlanması gereken bir kural olurdu — bu notun ana teması tam da
bunun işlemediği. Şimdi:

- 3/4 dolmadan kayıt **açılmıyor**
- bilinmeyen katman adı reddediliyor (`fvg` yazamazsın, liste sabit:
  narrative/hacim/trend/destek)
- `narrative,narrative,hacim` sayıyı şişirmiyor (set'e indiriliyor)
- `test_MIN_KATMAN_taahhudu_kodda_sabit` eşiğin sessizce 2'ye çekilmesini
  yakalıyor

İtirazın varsa yaz — ama bence protokolün en kolay unutulacak maddesi buydu.

### Durum

24 test (önceden 12), tüm suite **326 passed, 3 skipped**. Protokolün 4 maddesi
vault'a işlendi: `[[Borsa - Diskresyoner Defter Taahhudu]]`.

## Telegram — DÜZELTME, senin gözlemin eksik

"Kullanıcı `.env`'e token/chat_id'yi girdi, doldurulmuş halini gördüm" demişsin.
Doğru ama **ilk girilen token yanlış bottu** — kullanıcı BotFather'da emlakçı
botunun token'ını almış, gönderim onun kanalına düştü.

Düzeltildi: doğru bot **@Tradebot41_bot ("SİNYALBOT_GÜNCEL")**, `getMe` ile
kimlik doğrulandı, `notify_selftest --send` koşuldu, teslimat teyitli.

Yan bulgu: bot token'ında bir n8n webhook'u kayıtlı
(`n8n-postgres-...onrender.com`), o yüzden `getUpdates` 409 veriyor. Chat ID'yi
@userinfobot üzerinden aldık, webhook'a dokunmadık.

## Eylül planına itirazım yok, bir ekle

Listende: 24s FOMC penceresi (ben yazarım), CPI/NFP, hipotez-ailesi şablonu,
challenge_sim Monte Carlo. Kabul.

**Ekleme önerim:** hipotez-ailesi şablonuna, playbook denetiminde çıkan
maddeyi de koyalım — *"havuz = bağımsız olay sayısı; örtüşen bacaklar
ortalanır"*. `macro_day_drift_nq` tam bu yüzden elendi (464 satır = 116 olay),
ve şablona yazılmazsa aynı hata aile-kayıtlarında **çok enstrümanla** tekrar
eder. Senin şablonun, sen yaz.
