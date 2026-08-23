# HANDOFF — Hermes → Claude

Bu dosya iki ajanın doğrudan iletişim kanalıdır. Kullanıcı sadece
"oku/koş/devam" der, içerik aktarmaz.

---

## ARAŞTIRMA RAPORU: Profesyoneller bu işi nasıl yapıyor? (2026-08-24, Hermes)

Kullanıcının sorusu: "gerçek quantitative sistem yapan retail/professional
traderların yöntemi bizimkiyle aynı mı, bekleme süresini kısaltan ne var?"
Kaynaklar: Rob Carver (AHL 7 yıl, systematicmoney.org/qoppac), Kevin Davey
(World Cup Champion, Wiley kitabı), Harvey-Liu-Zhu (t>=3 kuralı),
Lopez de Prado (DSR/PBO — zaten kullanıyoruz), Grinold-Kahn (temel yasa),
paperswithbacktest/awesome-systematic-trading, r/algotrading konsensüsü,
Better System Trader #026 (Carver walk-forward eleştirisi).

### SONUÇ 1: Mevcut yolumuz kurumsal playbook ile büyük ölçüde AYNI

| Profesyonel standart | Bizde |
|---|---|
| Maliyet-dahil muhafazakâr backtest | ✅ honest engine |
| Çoklu-test düzeltmesi (Harvey-Liu t>=3, DSR/PBO) | ✅ overfit_stats.py |
| Gerçek-veri inkübasyonu canlıdan önce (fund'larda 6+ ay) | ✅ forward EA + bulut defteri |
| Az sayıda, yapısal gerekçeli hipotez | ✅ ön-kayıt + aylık bütçe |
| Rejim-stabilite kontrolü | ✅ yıl-yıl kırılımı |

r/algotrading'in tekrarlayan dersi de bu: başarısızların %90'ı overfitting +
maliyeti görmezden gelme; hayatta kalanların tavsiyesi bizim zaten kurduğumuz
altyapının aynısı. Yani boşluğa düşmedik — kurumsal disiplini retail'e
uygulayan azınlıkta olduğumuzu gösterdik.

### SONUÇ 2 (ASIL BULGU): Bizde eksik olan ve bekleme süresini KISALTAN teknik

Profesyoneller işlem-bazlı PnL yerine **sinyal-bazlı IC** (Information
Coefficient) ölçer: her barda "sinyalin yön tahmini vs sonraki getirinin
gerçek yönü" korelasyonu. Fark istatistikte:

- İşlem-bazlı test: gözlem = işlem. NQ_ORB kanıtı için 1000+ işlem = 8 yıl.
- IC-bazlı test: gözlem = BAR. 14 yıl 15m = ~350.000 gözlem. Aynı sinyalin
  kalitesi aylar içinde anlamlı ölçülür.

Yani "NQ_ORB pratikte kanıtlanamaz" ([[Borsa - Sans mi Edge mi]]) sorununu
işlem bekleyerek değil, aynı sinyali bar bazında ölçerek aşabiliriz.
Sınırlar: IC yön/zamanlama kalitesini ölçer, fill/maliyet yaşatmayı ölçmez —
son kapı yine honest engine + forward. IC bir ÖN-ELEME katmanı (kaba eleme
yerine güçlü eleme), bütçeden bağımsız çünkü yeni hipotez kaydı değil,
mevcut sinyallerin daha hassas ölçümü.

Kaynak: MQL5 low-frequency quant yazısı (IC/RankIC/ICIR/t-stat), quantinsti,
Carver'ın standardized forecast yaklaşımı.

### SONUÇ 3: İkinci eksik = Breadth (genişlik)

Grinold: IR ≈ IC × √breadth. Kurumsallar daha iyi edge bulmaz; binlerce
enstrümanda minik edge'leri toplar. Bizde canlıda slot=1 kısıtı var (Maven)
AMA araştırma tarafında breadth bedava: aynı yapısal hipotezi (örn. ORB)
çok enstrümanda koşmak hem IR hem KANIT üretir — NQ pozitif + SP500 pozitif
+ FX negatif bulgusu zaten tek-enstrüman testinden güçlü kanıt. Bu,
[[Borsa - Sans mi Edge mi]]'nin "ölçemediği kanıt #1" (önceden tahmin edilen
yön) sistematik hale getirilebilir: hipotez ailesi ön-kaydı (1 hipotez =
çok enstrüman replikasyonu, sonuçlardan ÖNCE tanımlı).

### SONUÇ 4: Küçük eklemeler (Davey/Carver standardı)

1. **Monte Carlo işlem-yeniden-örnekleme:** mevcut defterlerden drawdown
   dağılımı → challenge risk boyutlandırması duyarlılık testi
   (challenge_sim'e eklenebilir; Davey'in standart adımı).
2. **Carver walk-forward uyarısı:** klasik walk-forward tek geçişte zayıftır;
   purged/embargoed CV tercih edilir (bizde overfit katmanı var, yeterli).

### DEV BÜTÇE GEREKTİRENLER (yapmıyoruz, bilinçli)

Tick-level mikroyapı, colokasyon, alternatif veri (uydu/kredi kartı),
HFT frekansı, binlerce enstrümanlı cross-section. Bunlar kurumsal avantaj;
retail karşılığı yok ve gerekmez — bizim frekans bandında (15m-intraday,
5-10 enstrüman) yukarıdaki yöntemler tam kapasite çalışır.

### ÖNERİLEN AKSİYONLAR (öncelik sırasıyla, hepsi bütçesiz)

1. `ic_eval.py`: mevcut modüllerin sinyallerini bar-bazında Rank-IC ile ölç
   (NQ_ORB ilk hedef — 8 yıl bekleme sorununun cevabı).
2. Hipotez-ailesi şablonu: 1 kayıt = çok enstrüman replikasyonu (eylül
   kayıtlarında uygula: 24s pencere zaten 2 enstrümanlı).
3. challenge_sim'e Monte Carlo DD bootstrap'u.
4. Bu raporu vault'a [[Borsa - Profesyonel Quant Playbook Karsilastirmasi]]
   olarak kaydet (sen tek yazıcısın).

## Anlaşılmış kurallar (değişiklik yok)

- Vault tek yazıcı: Claude. Handoff dosyaları vault DEĞİL, repoda.
- Her denetimde commit hash belirtilir.
- Hipotez bütçesi ortak ayda 2.
