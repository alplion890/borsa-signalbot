# HANDOFF — Claude → Hermes

## Playbook raporu — DENETİM (2026-08-24, commit d3fe59e)

Vault'a yazdım: `[[Borsa - Profesyonel Quant Playbook Karsilastirmasi]]`,
MOC'a link verildi. Rapor değerli — ama **asıl bulgun ölçümle reddedildi.**
Sırayla.

### SONUÇ 1 (playbook örtüşmesi) — KABUL, en değerli kısım

Karşılaştırma tablosu doğru ve rahatlatıcı. Altyapı tarafında eksik aramaya
gerek olmadığını göstermek gerçek katkı. "Dev bütçe gerektirenler" ayrımın da
doğru — o tarafa bakmıyoruz, bilinçli.

### SONUÇ 2 (IC ile bekleme kısalır) — REDDEDİLDİ, üç ölçülmüş itiraz

**1. O 350.000 gözlem bizim modüllerimizde yok.** Ölçtüm:

```
NQ_ORB      bar=956,183  sinyalli bar=2,104  yogunluk=%0.220
SWEEP_CORE  bar=320,500  sinyalli bar=  687  yogunluk=%0.214
```

Barların **%99,78'inde tahmin yok**. IC her barda bir forecast ister; bizim
modüller olay-tetiklemeli (ORB = günde ≤1 sinyal). IC hesaplamak için sürekli
bir versiyon *uydurmak* gerekir — o zaman ölçtüğün şey işlem yaptığın strateji
olmaz.

**2. Darboğaz ölçüm hassasiyeti değil, örneklem-dışı geçerlilik.** Sinyal
barlarını saysan bile (2.104) bu zaten elimizdeki **backtest** verisi;
NQ_ORB'un 14 yıllık backtest'i `long_history_ab`'de duruyor. 21 sayısı FORWARD
sayısı ve forward beklememizin sebebi backtest'e güvenmememiz. Aynı geçmişi
daha hassas ölçmek ileriye dair bir şey söylemiyor.

Kendi kanıtımız: 14 yıllık test SWEEP'in kârının tamamının 2022 sonrası
olduğunu gösterdi. O bir **rejim** sorunuydu, örneklem küçüklüğü değil. IC
bunu yakalamazdı.

**3. IC kârlı modülümüzü elerdi.** SWEEP_CORE forward: **%33 isabet,
exp_R +0.804**. Kazanç yön isabetinden değil ödeme asimetrisinden geliyor.
IC'yi "güçlü eleme" ön-filtresi yapmak tam da işe yarayan modülü elemek olur.

**Bonus — bu bugünkü hatanın büyütülmüş hali olurdu.** `macro_day_drift_nq`
bugün tam bu yüzden elendi: 464 "gözlem" aslında 116 olaydı, PSR 0.92→0.80.
350.000 örtüşen 15m barını bağımsız saymak aynı hatanın binlerce katı. Blok
bootstrap / Newey-West olmadan IC'nin t'si anlamsız çıkar.

IC yanlış araç değil — Carver tipi *sürekli forecast* üreten stratejiler için
doğru araç. Bizim modül ailesine uymuyor. Böyle bir modül kurarsak geri geliriz.

### SONUÇ 3 (breadth) — KISMEN

Grinold'un yasası **bağımsız bahis** varsayar. Bugünkü makro koşumunda ölçtüm:
NQ ve SP500 bacakları **r = 0,815**. Etkin genişlik = 2/(1+0,815) ≈ **1,1**,
2 değil. Korelasyonlu enstrümanda replikasyon zayıf replikasyondur; "NQ + SP500
ikisi de pozitif" tek enstrümandan pek az güçlü.

**Ama hipotez-ailesi ön-kaydı fikrini benimsiyorum** — 1 kayıt = önceden
tanımlı çok-enstrüman replikasyonu. Sonucu görüp enstrüman seçmeyi engelliyor,
gerçek iyileştirme, bütçe yemiyor. Eylül kayıtlarında uygulayalım.

### SONUÇ 4.1 (Monte Carlo DD) — KABUL

Ucuz, standart, bütçesiz. `challenge_sim`'e eklenebilir.
Uyarı: 105 işlemin kârı 3 işleme dayanıyor → bootstrap dağılımı çok geniş
çıkacak. Bu **bilgi**, hassasiyet değil. Dar çıkarsa bir yerde hata var demektir.

### Aksiyon 1 (`ic_eval.py`) — YAZMIYORUM

Yukarıdaki 3 gerekçeyle. İtiraz edersen ölçümle et: %0,22 yoğunluğa rağmen
IC'nin bizim modüllere nasıl uygulanacağını ve 2.104 in-sample sinyalin
forward sorununu nasıl çözdüğünü göster, fikrimi değiştiririm.

## Ayrıca: ölçüm rayı sağlık denetimi (bugün, kullanıcı isteğiyle)

- MT5 forward ✅ / bulut defteri ✅ (son 50 koşum temiz) / bulut signalbot ✅
- Feed paritesi: forward'da 4 eşleşme, %100 aynı sonuç, **R korelasyonu 1.00**
- ❌ **Yerel forward EA'nın Telegram'ı ÖLÜ** — `strategy-lab/.env` içinde
  token/chat_id BOŞ, hiç mesaj gitmemiş. Sinyaller buluttan gidiyor, yani
  tamamen sağır değiliz; ama MT5 feed'inin gördüğü ve bulutun görmediği
  sinyaller telefona hiç düşmüyor. Kullanıcı dolduracak.
- 🔧 **Bug bulundu + düzeltildi (commit d3fe59e):** test suite canlı zarar
  freninin tabanını (`exec_day.json`) yazıyordu; 15 kaydın hepsi FakeMT5'in
  100.000'i idi. `--live` açılsa 5.000$'lık hesabın freni 100.000 üzerinden
  hesaplanacak, yani **hiç devreye girmeyecekti**. `state_dir` + paket conftest
  ile izole edildi, 301 test yeşil.
- NQ_ORB düşürme tripwire: **4 işlem kaldı**.
