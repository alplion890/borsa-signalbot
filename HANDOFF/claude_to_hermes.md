# HANDOFF — Claude → Hermes

## DÜZEN DEĞİŞTİ: üç raylı son düzen (2026-08-28, kullanıcı kararı)

İki raylı düzen bitti. Yeni düzen `[[Borsa - Uc Rayli Son Duzen]]` olarak
vault'a yazıldı. Commit `8d8e1d2`. **Senin rolün değişiyor, aşağıda.**

### Kararın dayandığı tablo (115 forward işlem)

```
Havuz        n=115  exp_R +0.085  t=+0.52   (+9.79R)
LIVE portföy n=30   exp_R +0.177  t=+0.52   (+5.31R)
```

Defter artıda ama **t=0.52**. Aylık savrulma sinyalden büyük (Tem −17.02R,
Ağu +26.09R). Dayanıklılık testi: her modülün en iyi işlemi çıkarılınca
SWEEP_CORE +0.804→+0.147, JAP225 +0.791→**−0.185**, SP500 +2.994→**−1.210**.
Tek ayakta kalan EUR_LONDON (+0.299→+0.148, n=8).

Kanıta kalan süre (t=2, mevcut hız): NQ_ORB ~56 ay, SWEEP ~14 ay, SP500_ORB
~267 ay. Bu sayı "bekle" demiyor, **"bu büyüklükteki edge kovalamaya değmez"**
diyor. Şimdiden bilinen: büyük bir edge yok — exp_R +0.5 olsaydı 30 işlemde
görünürdü.

### Üç ray

1. **Mekanik — DONDURULDU.** Çalışır, bedava (bulut + kullanıcının PC'si),
   tripwire'lar kararı otomatik verir. Yeni modül/parametre/araştırma yok.
2. **Diskresyoner — BİRİNCİL.** Aktif iş burada. Ben olgu getiriyorum
   (`seans_brief`), kullanıcı yorumluyor ve karar veriyor.
3. **Araştırma — UYKUDA.** Silinmedi, donduruldu. Gerekçe fikir değil ölçüm:
   14 yıllık veri istatistiksel olarak 1-3 hipotez finanse ediyor, darboğaz
   işlem gücü değil VERİ.

## Faz 1 — yapıldı, DENETİMİNİ İSTİYORUM

Bu iki değişikliği ben yazdım, o yüzden denetçi sensin.

### 1. Düşürme eşiği artık MT5 ∪ BULUT

**Bulduğum hata:** tripwire sadece MT5 defterini sayıyordu. MT5 terminali
çevrimlerin **~%16'sında kapalıydı** (1510 "terminal kapalı" hatası). O sırada
oluşan işlemler eşiğe girmiyordu — yani **bir modülün LIVE kalıp kalmayacağı
kullanıcının PC'sinin kaç saat açık olduğuna bağlanmıştı.** Modülün ürettiği
işlem sayısı ile PC uptime'ı ayrı şeyler; taahhüt birincisini ölçmeli.

`ledger.birlesik_forward()` MT5 ∪ bulut birleşimini 90dk toleransla
tekilleştirip döndürüyor (parite raporunun zaten kullandığı tolerans — tek
sayı, iki yer). MT5 satırları esas, buluttan yalnızca **karşılığı olmayanlar**
ekleniyor. 6 yeni test.

> **Etki: NQ_ORB n=21 → 22, exp_R −0.092 → −0.090. Eşiğe 3 işlem.**

Bakmanı istediğim yer: tekilleştirme doğru mu, 90dk toleransı iki defterin
bar farkı için yeterli/fazla mı, ve bulut backfill'inin sızmadığından emin ol.

### 2. GOLD_NY_ORB_TREND emekli edildi

Üç ölçüm: defterdeki **tek |t|>2 sonuç ve negatif** (−0.411, n=9, t=−2.05);
2026-07-09'dan beri **sıfır sinyal** (ATR filtresi ~%88 kesiyor → 50 gündür ne
doğrulanabilir ne çürütülebilir); PAPER olduğu için para riski yoktu ama
`default_modules`'te olduğu için ateşlediğinde telefona sinyal olarak
düşüyordu. 9 satırlık geçmiş defterde adıyla duruyor.

Geri dönüş koşulu teste yazıldı: ATR filtresi yeniden gerekçelendirilir ve
`CAND_` katmanında ölçülür.

`test_module_parity`'deki modül-kümesi kilidi kasıtlı güncellendi, gerekçesi
testin içine yazıldı. 333 test yeşil.

## Eylül ön-kayıtları: ERTELENDİ (iptal değil)

Araştırma rayı **uykuda**, silinmiş değil. Dolayısıyla 24s FOMC penceresi ve
CPI/NFP kayıtları iptal edilmiyor — dondurulmuş sırada. `hypotheses.json`,
bütçe defteri, `event_calendar` (477 olay) duruyor. Ray uyanırsa oradan devam.

Bu benim yorumum değil, planın lafzı: "altyapı silinmez, dondurulur."

## Rolün değişiyor

Hipotez denetçiliği (uyuyan ray) → **diskresyoner defter denetçisi**.

Somut olarak beklediğim:
- Faz 1'in iki değişikliğinin denetimi (yukarıda)
- Diskresyoner defter ilk işlemleri aldıkça: tez/çürüten alanlarının gerçekten
  ön-kayıt işlevi görüp görmediği, seçicilik metriğinin anlamlı olup olmadığı
- Durma kuralının (n≥20 & exp_R<0) işletilip işletilmediği — kullanıcı eşiğe
  yaklaşınca "bu sefer farklı" argümanı gelirse, kayıt sende olsun

## Bilgi: hesabın gerçek durumu (ilk kez bakıldı)

```
10325017 @ MavenTrade   bakiye 4,998.29   equity 5,008.50   (depozit 5,000)
```
Hesap açıldığından beri **3 işlem**: US30 (06-22, −1.70) ve EURUSD SELL 0.01
lot (08-20, hâlâ açık, +10.21, **stop yok** — kullanıcı kendisi koyacak).
Manuel açılmış, hiçbir deftere kayıtlı değil.

Ayrıca: bulut kadansı saatlikten **9-12 saatliğe** düştü (koşumlar başarılı,
cron tetiklenmiyor). Veri kaybı yok, telafi mekanizması çalışıyor.
