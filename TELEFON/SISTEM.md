# Maven telefon sistemi

> Güncel durum — 2026-11-05: Tek ölçüm kaynağı Maven MT5. Sweep tek LIVE (manuel emir); EMA12 Maven'de PAPER. Bulut defteri dondu; bulut botu yalnız haber/makro ölçer. Diskresyoner ray kaldırıldı. Güncel karar: [karar tablosu](GUNCEL_EDGE_KARARLARI.md).


Güncel LIVE/PAPER/emekli ve filtre kararları: [karar tablosu](GUNCEL_EDGE_KARARLARI.md).

Telefondaki ChatGPT, Claude veya Gemini projesinin ana talimat dosyasi
[`MAVEN_AI_MASTER.md`](MAVEN_AI_MASTER.md)'dir. Projeye bu dosyayi yukle veya
icerigini proje talimatlarina yapistir.

## Otomatik akis

Gunluk planli Telegram brifingi 2026-09-28'de durduruldu. BRIEF kendiliginden guncelleniyor varsayma; veri zamanina bak.
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
Olcum kaynagi Maven MT5'tir: yerel forward EA defteri her dongude GitHub'a
yayinlar (`forward_ea/published/forward_ledger.csv`); brifing bu kopyayi okur.
Bulut (Yahoo) defteri 2026-11-05'te dondu.

## Makro olcum (bulut, 2026-11-05)

Her ABD yuksek etkili verisi icin: 60 dk once beklenti/onceki; +15 ve +60 dk
sonra gerceklesen, surpriz, NQ/XAU yuzde degisimi, 2Y vadeli (ZT=F) yuzde ve
5Y getiri baz puan. Kaynak Forex Factory haftalik takvimi. Deger yoksa "kaynakta
yok"/"veri yok" yazar. Sayi aktarilir; sifat eklenmez.

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

Makro kayit bir edge veya LIVE filtresi degildir.

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
- Sweep dusurme taahhudu: n>=25 ve exp_R<0 -> PAPER; birlesik sayim
  (MT5 + 2026-11-05'te donmus bulut).
- Diskresyoner ray 2026-11-05'te kaldirildi (0 kayit). Arsiv:
  docs/archive/diskresyoner-2026-11-05/.
- Arastirma rayi: elenen edge'lerin on-kayitli yeniden yargilanmasi. Sonuc
  LIVE kurali veya riski otomatik degistirmez.
- Bakiye buluttan okunmaz; risk kapisi bakiye yokken dogrulanmis sayilmaz.
- NQ futures ile Maven US100 ayni feed degildir.
