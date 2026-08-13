# Portföy Kompozisyonu — Hangi Modüller Gerçek Parayla İşlem Yapar

**Tarih:** 2026-08-14
**Durum:** Tasarım onaylandı, ölçüm HENÜZ KOŞULMADI
**Kapsam dışı:** Funded faz savunması (ayrı spec), `LIVE_MODULES` bug'ı (ayrı düzeltme)

---

## 1. Problem

Gerçek parayla işlem yapabilen portföy fiilen tek modül:

| Modül | n | exp_R | işlem/hafta |
|---|---|---|---|
| SWEEP_CORE (NASDAQ100) | 9 | +1.206 | 0.74 |
| NQ_ORB (NASDAQ100) | 26 | +0.067 | 2.14 |

İkilinin +0.388'i neredeyse tamamen SWEEP'ten geliyor. NQ_ORB sıfıra çok yakın ve
forward testle kanıtlanamaz (gerekli n≈1030, ~9 yıl).

Aynı anda tek işlem kuralı altında slot zamanın yalnızca **%6.8'inde** dolu —
yani kapasite kısıtı yok, %93 boş duruyor.

Bu arada SWEEP'in aynı config'i 6 sembolde daha aday olarak kurulu ve MT5
backtest'inde 7 sembol havuzunda **exp_R +0.194, n=118, PSR 0.837** vermiş.

**Soru:** Gerçek parayla hangi modüller işlem yapmalı?

## 2. Karar metriği (ölçümden ÖNCE taahhüt edildi)

**P(challenge geç **VE** 12 ay funded'da hayatta kal)**

Tek sayı. Sebep: challenge'ı en hızlı geçen portföy, funded'da en çok patlayan
olabilir — yüksek oynaklık yakın hedefe (+%4) yardım eder, uzun vadede öldürür.
İki fazı ayrı optimize etmek çelişkili portföyler seçtirir.

Simülasyon zinciri tek yolda koşar:

**Challenge fazı**
- Başlangıç bakiyesi 4998.30 (gerçek MT5 bakiyesi)
- Risk %1.5; önceki kapanan işlem kazandıysa %3
- Geçiş: +%4
- Durma: −%8 (Karar Kuralı'nın kendi limiti; Maven'ın statik −%10'undan sıkı)

**Funded fazı** (yalnızca challenge geçilirse)
- Risk %0.5 (kodda hazır funded profili)
- Maven kuralları: %4 günlük DD, %8 **trailing** DD, %20 tutarlılık, min 5 ödeme günü
- Hayatta kalma: 12 ay boyunca trailing DD'ye çarpmamak

## 3. Karşılaştırılacak portföyler (ölçümden ÖNCE sabitlendi)

| # | Portföy | İçerik |
|---|---|---|
| 1 | SWEEP tek sembol | SWEEP_CORE (NASDAQ100) |
| 2 | **Mevcut (kıyas)** | SWEEP_CORE + NQ_ORB |
| 3 | SWEEP 7 sembol | NASDAQ100, SP500, US30, US2000, UK100, FRA40, JAP225 |
| 4 | SWEEP 7 sembol + NQ_ORB | 3 + NQ_ORB |

**Dört tane. Sonradan ekleme yok.** "Şunu da deneyelim" yasak — bu projede sahte
edge'in üçü de (inside-day, gold `atr_max_rank`, EUR/GBP Perşembe) sonuca bakıp
aday eklemekten çıktı.

**7 sembolün hepsi dahil, kaybedenler dahil.** Backtest'te US2000 (−0.562) ve
UK100 (−0.760) negatifti. En iyi 5'i seçmek sonuca göre seçmek olurdu. Yedisinin
de modülü kurulu, yedisi de Maven'da mevcut (2026-08-14'te MT5'ten doğrulandı:
US100/US500/US30/JAP225/FRA40/UK100/US2000 — hepsi VAR, 15m verisi geliyor).

## 4. Karar kuralı (ölçümden ÖNCE taahhüt edildi)

1. Her portföy için metrik, **eşleştirilmiş bootstrap** ile hesaplanır (aynı
   rastgele çekimler tüm portföylere uygulanır).
2. Bir portföy #2'yi (mevcut) yenmiş sayılmak için:
   **P(metrik_aday − metrik_mevcut > 0) ≥ 0.95**
3. Birden fazla portföy bu eşiği geçerse, aralarında en yüksek metriğe sahip olan
   seçilir.
4. **Hiçbiri geçemezse: DEĞİŞİKLİK YOK.** Mevcut portföy (#2) kalır.

Beraberlik mevcut duruma yazılır. "Biraz daha iyi göründü" yetersizdir.

## 5. Veri sağlamlığı (ölçümden ÖNCE taahhüt edildi)

Simülasyon **iki bağımsız veri kaynağıyla** koşulur:

**Veri A — forward defteri** (dürüst, küçük)
SWEEP ailesi toplam 15 işlem (NASDAQ100 9, US30 3, JAP225 2, SP500 1;
US2000/UK100/FRA40 0), NQ_ORB 26.

**Veri B — MT5 backtest, 6 ay, 7 sembol** (büyük, iyimser)
Havuz n=118, exp_R +0.194, PSR 0.837.
`multi_index_lab.fetch` + `run_sweep` ile üretilir.

**Kazanan her iki kaynakta da 4. maddedeki eşiği geçmelidir.** Cevap veri
kaynağına göre değişiyorsa cevap yok demektir → değişiklik yok.

Beklenti: Veri A'nın 15 işlemi güven aralıklarını çok geniş yapacak ve muhtemelen
hiçbir portföy eşiği geçemeyecek. **Bu bir kusur değil, tasarımın çalıştığının
işaretidir** — 15 işlemle portföy değiştirilmemeli.

## 6. Simülasyon kısıtları

**Aynı anda tek işlem ZORUNLU.** 7 sembol eklemek işlem sayısını 7'ye katlamaz;
zaman çakışan sinyaller elenir. Ölçüldü: tüm modüller açıkken **%28 eleniyor**.
Bu kısıt uygulanmazsa çok sembollü portföyler sistematik olarak şişer — bu,
ölçümün en kolay yanlış yapılacak yeri.

Uygulama: R havuzu ve işlem hızı hesaplanmadan **önce**, işlemler kronolojik
sıralanıp önceki pozisyon kapanmadan başlayanlar elenir.

**İşlem hızı** her portföy için kendi veri kaynağından ölçülür (forward: defter
tarihlerinden; backtest: 6 aylık pencereden), tek-slot filtresi uygulandıktan
sonra.

## 7. Kazanan portföy koda nasıl bağlanır

Terfi beş yeri etkiler:

| Yer | Değişiklik |
|---|---|
| `forward_ea/modules.py` | `candidate_modules()` → `default_modules()`, weight 0.0 → 1.0 |
| `forward_ea/order_executor.py` | `LIVE_MODULES`'e ekle |
| `signalbot/risk.py` | tier ataması (risk yüzdesi) |
| `forward_ea/notify.py` | Telegram'a çıkabilir hale gelir |
| test | `LIVE_MODULES` = Karar Kuralı seti, testle sabitlenir |

### İsimlendirme çakışması ve çözümü

`test_candidate_isolation.py:67` her aday modül adının `CAND_` ile başlamasını
zorunlu kılıyor. `notify.py._is_candidate` adayı **iki bağımsız işaretle** tanıyor
(`CAND_` öneki VEYA weight=0.0) — bu ikilik bilerek konmuş, biri bozulursa diğeri
tutsun diye.

Terfi eden modülün adı değişmeli, ama değişirse defterdeki eski satırlar kopar.
Proje bu sorunu daha önce yaşadı (`SWEEP_CORE_AVOID_MID_VWAP` adı yanlış olduğu
halde veri sürekliliği için değiştirilmedi).

**Karar: yeniden adlandır + rapor katmanına takma-ad haritası.**
`CAND_SWEEP_US30` → `SWEEP_US30`; rapor/analiz katmanında
`{"SWEEP_US30": ["CAND_SWEEP_US30"]}` haritasıyla geçmiş satırlar yeni ada
bağlanır. Böylece izolasyon invaryantı (iki bağımsız işaret) bozulmaz ve defter
sürekliliği korunur.

Reddedilen alternatif: adı koruyup yalnızca weight'i değiştirmek. `_is_candidate`
in `CAND_` kolunu gevşetmeyi gerektirirdi — iki katmanlı güvenliğin biri giderdi.
Bu proje sessiz sızıntılardan üç kez yara aldı; katman feda edilmez.

## 8. Bu tasarımın bilerek kabul ettiği sınırlar

- Metrik, gözlemlenen R dağılımının gelecekte de geçerli olduğunu varsayar.
  SWEEP'in n=9'u ve exp_R +1.206'sı büyük ihtimalle küçük-örnek şişkinliğidir.
- Backtest verisi (B) gerçek spread/kayma altında yaşamayabilir. 2026-08-11'de
  fill-model araştırması bar-çözünürlüğü şüphesini eledi, ama dar stopta gerçek
  spread sorusu açık kaldı.
- Sembol korelasyonu modellenmiyor. US100/US500/US30 yüksek korele; 3 işlem
  3 bağımsız kanıt değil. Tek-slot kuralı bunu kısmen maskeliyor ama tamamen
  değil.
- Bu çalışma bir edge iddiası değildir. Kazanan portföy çıksa bile bu, edge'in
  kanıtlandığı anlamına gelmez — yalnızca eldeki kanıtla en savunulabilir
  kompozisyon seçilmiş olur.

## 9. Yapılmayacaklar

- Yeni strateji/gösterge/veri kaynağı aranmayacak (Karar Kuralı madde 7).
  Sembol genişlemesi yeni arayış değildir: aynı config, aynı dedektör.
- Risk yüzdeleri, durma limitleri, sinyal filtreleri değiştirilmeyecek.
- Ölçüm sonucuna bakılıp 3. maddedeki portföy listesi genişletilmeyecek.

---

# SONUÇ (ölçüm 2026-08-14'te koşuldu)

Yukarıdaki bölümler ölçümden önce commit edildi (`5756c2b`) ve değiştirilmedi.
Aşağısı çıktıdır.

## Veri A — forward defteri

| Portföy | n | exp_R | işlem/hf | metrik | P(>mevcut) |
|---|---|---|---|---|---|
| 1 SWEEP tek sembol | 9 | +1.206 | 0.74 | 81.3% | 71.7% |
| 2 **MEVCUT** | 36 | +0.388 | 2.96 | 67.7% | (kıyas) |
| 3 SWEEP 7 sembol | 16 | +1.381 | 1.32 | 75.9% | 61.3% |
| 4 SWEEP 7 sembol + NQ_ORB | 43 | +0.587 | 3.54 | 64.9% | 46.3% |

## Veri B — MT5 backtest 6 ay, 7 sembol

| Portföy | n | exp_R | işlem/hf | metrik | P(>mevcut) |
|---|---|---|---|---|---|
| 1 SWEEP tek sembol | 18 | +1.343 | 0.70 | 89.5% | 68.3% |
| 2 **MEVCUT** | 59 | +0.586 | 2.29 | 84.2% | (kıyas) |
| 3 SWEEP 7 sembol | 80 | **−0.062** | 3.11 | 5.5% | 0.3% |
| 4 SWEEP 7 sembol + NQ_ORB | 111 | +0.050 | 4.32 | 9.6% | 0.3% |

## Karar: DEĞİŞİKLİK YOK

Hiçbir portföy %95 eşiğini geçmedi. Mevcut portföy (SWEEP_CORE + NQ_ORB) kalır.

## Ana bulgu: sembol genişlemesi tek-slot altında edge'i YOK EDİYOR

Vault'taki "7 sembol havuzu +0.194, n=118, PSR 0.837" rakamı **aynı anda tek
işlem kısıtını hesaba katmıyor.** Kısıt uygulanınca:

- 118 işlem → 80 işlem (38 elendi)
- exp_R +0.194 → **−0.062**

Yani elenenler iyi olanlardı. Sebep yapısal: slot ilk gelene veriliyor, en iyi
sembole değil. US100'ün +1.343'lük sinyalleri, önce tetiklenen zayıf sembol
sinyalleri yüzünden kaçırılıyor. Tek başına US100 (portföy 1) exp_R +1.343
verirken, 7 sembol birlikte −0.062 veriyor.

**Bu, sembol genişlemesi fikrini çürütür** — mevcut "ilk gelen kazanır" slot
kuralı altında. Öncelik sıralamalı bir slot tahsisi farklı sonuç verebilir ama
o ayrı bir tasarımdır ve bu spec'in kapsamı dışındadır.

## İkincil gözlem (karara etki etmedi)

SWEEP tek başına (portföy 1) her iki kaynakta da mevcut portföyden yüksek metrik
verdi (81.3 vs 67.7 ve 89.5 vs 84.2) — yani NQ_ORB seyreltiyor olabilir. Ama
P(>mevcut) yalnızca %71.7 ve %68.3, eşiğin çok altında. **Taahhüt edilen kural
bizi %70'lik bir sinyale göre hareket etmekten korudu.** NQ_ORB kalır.

## Ölçüm sırasında düzeltilen kusur

İlk koşumda backtest çıkış zamanları sabit varsayılmıştı (sweep +8sa, ORB +4sa).
Tek-slot filtresi çıkış zamanına bağlı olduğu için bu sonucu kaydırabilirdi.
Forward defterindeki gerçek tutma dağılımından örneklemeye çevrildi (SWEEP
medyan 2.2sa/ort 6.2sa; NQ_ORB medyan 1.5sa/ort 3.9sa). Veri B portföy 3:
−0.086 → −0.062. Karar değişmedi — sonuç bu varsayıma dayanıklı.

## Kalan sınırlar

- Veri A'da SWEEP ailesi yalnızca 16 işlem; güven aralıkları çok geniş.
- Sembol korelasyonu modellenmedi (US100/US500/US30 yüksek korele).
- Tek-slot kuralı "ilk gelen kazanır" olarak uygulandı; canlı sistemde de öyle.
