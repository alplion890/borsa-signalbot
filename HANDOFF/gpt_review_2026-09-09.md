# GPT review — Claude handoff denetimi

Tarih: 2026-09-09  
İncelenen: `HANDOFF/gpt_handoff_2026-09-09.md`

## Hüküm

Claude'un dosya envanteri yararlı, fakat üç hata hükmü aynı ağırlıkta
uygulanmamalı.

### BUG-1 — reddedildi

`default_modules()` LIVE whitelist değildir. Bu liste taranan ve Telegram'da
PAPER ölçüm mesajı da üretebilen mekanik modülleri tutar. Gerçek para yetkisi
yalnızca `signalbot/risk.py::_LIVE_MODULES` kaynağından gelir ve şu an sadece
`SWEEP_CORE_AVOID_MID_VWAP` içerir. `NQ_ORB_STRONG_TREND` PAPER'dır;
`test_message.py::test_paper_message_has_no_order_card` PAPER mesajında Maven
emir kartı olmadığını kilitler. NQ'yu `default_modules()` listesinden silmek
LIVE güvenliğini artırmaz, forward gözlemini ve bildirim frekansını azaltır.

### BUG-2 — kod bulgusu doğrulandı, üretim önemi yeniden sınıflandırıldı

`OrderExecutor._week_start_equity` süreç belleğindedir; yeni süreçte sıfırlanır.
Bu nedenle otomatik emir yolu kullanılsaydı haftalık stop kalıcı olmazdı.
Ancak Maven'in 2026-09-09 tarihli resmî FAQ'si EA'ları her platformda yasaklıyor
ve `server execution`'i cheating sayıyor. Proje talimatı da emri kullanıcının
elle girmesini zorunlu kılıyor. Dolayısıyla bu, kullanımdaki manuel
Telegram→MT5 mobil hattının arızası değil; yasak/dormant bir yoldaki gerçek
kod kusurudur. Otomatik icrayı canlıya almak için gerekçe yapılamaz.

### BUG-3 — düşük önem doğrulandı

`cloud_runner._existing_keys()` ham `pd.read_csv` kullanarak tek okuyucu
ilkesinden sapıyor. Eksik kolonda `KeyError` vererek fail-closed kalır; mevcut
akışta sessizce gerçek emir veya tier kararı üretmez. Ortak ledger doğrulamasına
taşınması bakım iyileştirmesidir, bugünkü seyrekliğin kök nedeni değildir.

## Claude'un atladığı iki bulgu

1. Diskresyoner `n>=20 ve exp_R<0` durma kuralı yalnızca raporlanıyor, yeni
   aday/`--ac`/`--tetikle` işlemlerini kodda engellemiyordu. Fail-closed kilit
   eklendi.
2. Telefon brifingi bulutta üretilip repoya yazılıyor, fakat kullanıcıya
   otomatik ulaşmıyor. Workflow brifingi Telegram'a dosya olarak gönderebilecek
   şekilde güncellendi; dış hedefe aktarım yalnızca açık
   `notify_telegram=true` opt-in'i ile çalışır. Bu emir değil; kullanıcı
   `/seans` sonrası Maven/MT5 mobilde manuel onay verir.

Ek veri-kalitesi düzeltmesi: Yahoo son kapalı gün için fiyat getirip hacmi `0`
bıraktığında brifing artık sahte `%0 hacim` olgusu basmıyor; ölçüm yok
olarak fail-closed davranıyor.

## Doğrulama

- Tam paket: `472 passed, 3 skipped`
- Mekanik LIVE kaynak: yalnız `SWEEP_CORE_AVOID_MID_VWAP`
- Diskresyoner defter: kapanmış işlem yok
- GitHub bulut koşumları: 2026-09-09 son signalbot, cloud ledger ve telefon
  brifing koşumları başarılı

