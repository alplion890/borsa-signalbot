# Maven telefon sistemi

> Güncel durum — 2026-09-30: Sweep tek LIVE yetkili mekanik modül; EMA12 ayrı PAPER gözlem. EUR/GBP London, NQ ORB ve Gold ORB emekli. Makro/COT sürümleri araştırma; LIVE filtre değil. Yeni EUR/GBP taraması ve forward girişi yok. Güncel karar: [karar tablosu](GUNCEL_EDGE_KARARLARI.md).


Güncel LIVE/PAPER/emekli ve filtre kararları: [karar tablosu](GUNCEL_EDGE_KARARLARI.md).

Telefondaki ChatGPT, Claude veya Gemini projesinin ana talimat dosyasi
[`MAVEN_AI_MASTER.md`](MAVEN_AI_MASTER.md)'dir. Projeye bu dosyayi yukle veya
icerigini proje talimatlarina yapistir.

## Otomatik akis

Gunluk planli Telegram brifingi 2026-09-28'de durduruldu. BRIEF kendiliginden guncelleniyor varsayma; veri zamanina bak. Yerel tarayici ve olay bildirimleri: MOBIL_KARAR_AKISI.md.
GitHub schedule gecikebilir veya kosu atlayabilir. Yerel 20:10 kapsam alarmi
PC/kullanici oturumu acikken eksik taramayi bildirir; kendisi firsat taramaz.
PC'deki gercek tarayici 5 dakikada bir calisir. Saglikli yerel kosu buluta
8 dakikalik devir bilgisi verir; bulut o sirada kuru tarar, bildirim ve
mobil izleme gondermez. PC durursa bulut tekrar bildirim kaynagidir.
Kaynaklar arasi devir sinirinda ayni aday tekrar edebilir; ayni fikir iki
bagimsiz firsat sayilmaz.

Yerelde MT5 terminali aciksa US100/EURUSD/GBPUSD bid/ask/spread, tick saati
ve bakiye yalniz aday mesajina eklenir. MT5 yok/bayatsa manuel teyit uyarisi
gosterilir. LIVE kurali Yahoo kaynaginda kalir; MT5 veri kaynagi degisimi yok.
Telefonun ozel Telegram sohbetinde ADAY/PAS/BEKLE/ACILDI/DURUM/YARDIM
komutlari diskresyoner kayit koprusune baglidir. Komutlar MT5 emri acmaz.

Telegram karar motoru degildir. Mobil proje mesajdaki bilgi kesim zamanini
kontrol eder, web aramasiyla beklenti/gerceklesen/revizyonu ve piyasa tepkisini
tamamlar. Veri bulunamazsa boslugu aciklar.

## Makro on-kayit

Makro tez birkac gun kullanilacaksa olaydan once kaydedilir:

```bash
cd strategy-lab
python -m intraday.forward_ea.makro_defter --on-kayit \
  --olay "ABD CPI" --olay-zamani "2026-09-16T12:30:00Z" \
  --beklenti "%0.3" --onceki "%0.2" --gecerli-gun 3 \
  --tez "<hangi aktarim zinciri bekleniyor>" \
  --curuten "<hangi gozlem tezi yanlislar>"
```

Aciklama sonrasi ilk gerceklesen ve revizyon ayrilir:

```bash
python -m intraday.forward_ea.makro_defter --sonuc 1 \
  --gerceklesen "%0.4" --revizyon "%0.2" \
  --surpriz-notu "konsensusten +0.1 puan"
python -m intraday.forward_ea.makro_defter --tepki 1 \
  --tepki-notu "2Y olay oncesinin 8bp ustunde; NQ olay oncesinin altinda"
```

Tez curutuldugunda veya yeni olay rejimi degistirdiginde kapatilir:

```bash
python -m intraday.forward_ea.makro_defter --kapat 1 \
  --not "Getiriler geri dondu; NQ olay oncesi bolgeyi geri aldi"
```

Makro kayit bir edge veya LIVE filtresi degildir. Diskresyoner islemler mevcut
2/4 kapisi, tez, curuten ve on-kayitla ayrica deftere girer. Kalan katmanlar
ayni anda guclu ters haber/tepki vermiyorsa celiski sayilmaz; guclu celiskide
daha guclu kanit gerekir ya da islem alinmaz. Makro kayit kimligi diskresyoner
`--narrative` alanina `macro:1` biciminde eklenebilir.

## Hacim

NQ hacmi onceki 20 islem gununun ayni `America/New_York` 15 dakikalik saat
dilimi medyaniyla kiyaslanir. En az 10 gozlem yoksa oran uretilmez. `>=1.3x`
olagandisi, `<0.7x` zayif, arasi normaldir. Bu oran Telegram baglamidir;
SWEEP_CORE girisini, riskini veya sinyal sikligini degistirmez.

## Baglayici durum

- Yalniz `SWEEP_CORE_AVOID_MID_VWAP` LIVE'dir.
- EUR/GBP London modulleri 2026-09-30 emeklidir; yeni sinyal/forward uretmez.
- `NQ_ORB_STRONG_TREND` negatif n=25 forward sonucuyla tarama ve Telegram'dan
  cikarilmistir.
- Diskresyoner ray birincildir; katman kapisi 2/4, tez, curuten ve on-kayit
  zorunludur.
- Arastirma rayi sinirli bicimde aktiftir: veri temizliginden sonra ilk
  PAPER calismasi SWEEP_CORE'un NQ-ES goreceli guc filtresidir. Sonuc LIVE
  kurali veya riski otomatik degistirmez.
- Bakiye buluttan okunmaz; risk kapisi bakiye yokken dogrulanmis sayilmaz.
- NQ futures ile Maven US100 ayni feed degildir.


2026-09-30 güncel karar: EUR_LONDON_FADE_EMA ve GBP_LONDON_STRONG_TREND emekli; yeni yerel/bulut tarama ve forward kaydı yok. Sweep LIVE manuel, EMA12 ayrı PAPER gözlem. NQ ORB/Gold emekli; filtreli makro/COT sürümleri araştırmadır. Gerekçe: HANDOFF/eur_gbp_emeklilik_2026-09-30.md.
