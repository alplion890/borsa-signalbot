# Maven telefon sistemi

Bu belge insan/operator icindir. ChatGPT ve Claude icin calisma anindaki tek metin [KISA_TALIMAT.md](KISA_TALIMAT.md) icindeki **Kopyalanacak metin** bolumudur.

## Telegram brifingi

- Hafta ici hedef saatler 16:20 ve 18:15 TR'dir. GitHub Actions, platform gecikmesine karsi her hedef saat icin kisa bir yeniden-deneme penceresi kullanir; ayni pencere icinde tek mesaj gonderir.
- Mesaj yalniz Maven sistem durumu ile NQ'nun hesaplanan fiyat/trend/hacim baglamini tasir. Turkiye masasi Telegram'a eklenmez.
- NQ hacmi, onceki 20 islem gununun ayni New York 15 dakikalik saat dilimi medyaniyla karsilastirilir. America/New_York saat dilimi ve DST kullanilir. En az 10 gecmis gozlem yoksa oran yazilmaz; 1.3x ve uzeri olagandisi, 0.7x alti zayiftir.
- Hacim metni yalniz baglamdir; SWEEP giris filtresini, riski veya sinyal sikligini degistirmez.

## Baglayici sistem durumu

- Tek LIVE modul: NASDAQ100/US100, 15 dakikalik `SWEEP_CORE_AVOID_MID_VWAP`.
- EUR/GBP London modulleri PAPER'dir; gercek-risk firsati olarak sunulmaz.
- `NQ_ORB_STRONG_TREND`, negatif forward sonucu nedeniyle 2026-09-11'de tarama ve Telegram listesinden cikarildi.
- Diskresyoner ray birincildir. Katman kapisi 2/4; tez, curuten ve on-kayit zorunludur.
- Arastirma rayi uykudadir.

## AI ve arsiv siniri

`TELEFON/BRIEF.md` arsiv/denetim ciktisidir. AI projeleri onu veya GitHub uzerindeki herhangi bir kopyasini calisma aninda kaynak olarak kullanmaz. Guncel kamusal piyasa bilgisi `seans` aninda web aramasi ve kaynak linkleriyle kurulur. Son Telegram mesaji gorunuyorsa, yalnizca oradaki ozel sistem olcumu kullanilir; gorunmuyorsa dinamik forward sayilari tahmin edilmez.

AI'nin kosullu temel analiz kurallari ve NQ/Turkiye iki-masa cikti formati KISA_TALIMAT'tadir. Bu analiz yalniz narrative katmanidir; otomatik emir, SWEEP sinyali veya risk degisikligi degildir.
