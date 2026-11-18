# Ön-kayıt: şeffaf kaynak adayları B1–B6 (2026-11-18)

Test koşulmadan ÖNCE yazıldı. Kaynak raporları: `seffaf-edge-kaynaklari/results/{A_yarisma,B_acik_kod,D_akademik,C_E_dogrulanmis_forum}.md`.
Toplam bağımsız test sayısı **8** → Bonferroni α = 0.05/8. Parametre taraması YOK; kaynakta yazan değer kullanılır,
kaynakta olmayan değer aşağıda açıkça sabitlenir (sonuca bakmadan).

## Ortak
- Veri: Dukascopy önbellek 2012–2026 (BTC: mevcut BTCUSDT günlük/saatlik seri). Motor: honest_engine (bar içi
  stop önce), sinyal kapanışta, giriş sonraki bar açılışı.
- Maliyet: Maven `reality_profile.csv` merkez; rapor 3 satır (maliyetsiz / merkez / 2×). Gece taşıyanlar için
  Maven swap (2026-11-18 ölçümü) ayrıca, ve swap 0 (swap-free FundedNext varsayımı) ayrı satır.
- Geçme: merkez ortalama > 0, bootstrap alt sınır > 0 (α=0.05/8, gün bloğu), <2022 ve 2022+ ikisi > 0, 2× > 0.
- Geçenler: 6'lı portföye eklenir, `firms.py` FN 2-Step 25K mc=3 ile eklemeli/eklemesiz + sıfır-edge + gün içi
  1.5× stres; korelasyon raporlanır. Eklenme kararı kullanıcıda.

## Adaylar
**B1 — NB + 5 dk geri çekilme overlay'i (Pagani-Zarattini 2026, SSRN 6391638), NQ — 1 test.**
Mevcut Noise Band girişini aynen al; long sinyalinde girişi, önceki 5 dk getirisi negatif olan ilk 5 dk bar
kapanışına ertele (short: pozitif). Çıkışa aynı bekleme. Gün sonu kapanış korunur. Ölçüt: overlay'li NB −
NB farkı (eşleştirilmiş günlük), geçme kuralı farka uygulanır.

**B2 — BTC Donchian topluluğu, yalnız long (Zarattini, SSRN 5209907) — 1 test.**
n ∈ {5,10,20,30,60,90,150,250,360}; kapanış n-gün maksimumuna eşitse long; trailing stop = max(önceki stop,
Donchian orta noktası); her model eşit ağırlık; hedef vol %25 / 90 gün gerçekleşen vol. Swap 0 ve Maven −%30/yıl
iki satır; geçme swap 0 satırında, swap satırı firma kararı için.

**B3 — Gold Trend Breakout Lite (MQL5 CodeBase 79733), XAU H1 — 1 test.**
Long: H1 kapanış > önceki 120 bar en yükseği VE D1 EMA100 son 3 günde yükseliyor (EMA[t] > EMA[t−3]); short ayna.
SL 3×ATR14(H1), TP yok; fiyat +1R olunca stop giriş+0.1R. Yeni sinyal ters yönde gelirse çık. Donchian XAU ile
korelasyon raporlanır.

**B4 — EMA Trend Cross XAU M30 (MQL5 CodeBase 78968) — 1 test.**
Long: EMA20 EMA50'yi yukarı keser VE kapanış > EMA20 VE kapanış > EMA200; giriş 07:00–19:00 sunucu saati
(= UTC+2/+3, Maven sunucu saati UTC olduğundan 05:00–17:00 UTC sabitlendi); SL giriş fiyatının %1'i; TP yok;
20:00 sunucu (18:00 UTC) kapanış. Short ayna (kaynak long+short).

**B5 — Raschke Turtle Soup, günlük — 2 test (NQ, XAU).**
Bugünün high'ı önceki 20 günün en yükseğini aşar, o en yüksek ≥4 gün önce oluşmuş, kapanış o seviyenin altında
→ kapanışta short; stop günün high'ı; çıkış ertesi gün kapanışı; sinyal günü aralığı > 3×ATR14 ise atla. Long ayna.

**B6 — Williams Oops, günlük — 2 test (NQ, XAU).**
Açılış < dünkü low ise dünkü low'da buy stop (gün içi dolarsa); stop gün içi en düşük; çıkış aynı gün kapanış
(kaynakta n=1 seçeneği; sabitlendi). Short ayna (açılış > dünkü high, dünkü high'da sell stop).

## Elenen / alınmayan (neden, sonuca bakmadan)
- VWAP trend (Zarattini-Aziz): 1 dk veri + ~15 işlem/gün, CFD spread'i baştan yer; 5 dk'ya uyarlamak kural değiştirir.
- Overnight drift (NY Fed SR917): kaynak bid-ask sonrası negatif rapor ediyor.
- Turtle S1/S2: B2 ve Donchian XAU ile aynı aile.
- NY Open Candle: EMA12 ilk mum ailesi, n küçük. Asya kutusu: kural tanımı elde yok.
- London drift GMM: 53+ kombinasyon itiraflı, 1 bar gecikmede işaret değişiyor.
- Unger DAX/altın: parametre eksik. StrategyQuant XAU: veri madenciliği izi.
- MQL5 blog 777404 (altın 400+ varyant, gerçek maliyet): Unger/Williams/Raschke/FVG altında negatif → B5/B6'nın
  XAU testleri için önsel uyarı; sonuç ne çıkarsa çıksın raporlanır.

## Tuzaklar
Post-hoc filtre yasak; parametre "biraz değiştir" yok; geçmeyen aday yeniden tanımlanmaz.

## EK (2026-11-18, test koşulmadan önce): ikinci tarama turu → B7
Kaynak: `seffaf-edge-kaynaklari/results/F_connors_151_qs.md`, `G_kitap_dergi.md`. Test sayısı 8 → **9**,
Bonferroni α = 0.05/9 (B1–B6 dahil hepsine uygulanır).

**B7 — IBS ortalamaya dönüş, NQ günlük, yalnız long (QuantifiedStrategies; Kinlay replikasyonu) — 1 test.**
IBS = (C−L)/(H−L) günlük NY seansı barı (09:30–16:00 ET). IBS < 0.2 → kapanışta long; IBS > 0.8 olan ilk
günün kapanışında çık. Stop yok (kaynakta yok). Gece taşıma: Maven US100 long swap (−1.18 bp/gece) ayrı satır.
Önsel uyarı: kaynaklarda maliyet yok; Kinlay 2013 sonrası zayıflama, backtrex NAS100 CFD RSI(2) zayıf.

Alınmayanlar: RSI(2)/Double 7s/TPS/%b (NQ CFD bağımsız maliyetli test zayıf, satıcı kaynaklı, OOS yok — IBS aynı
ailenin en sade temsilcisi olarak tek test); BTC MAX/MIN (B2 ailesi); BTC 21–23 vol filtresi (canlı modüle
post-hoc filtre); altın gece/gündüz seansı (kaynak bid/ask sonrası negatif); overnight drift (2021+ kayboldu);
151 Strategies (backtest yok, geniş sepet ister).

## SONUÇ (2026-11-18, ön-kayıt 8db3103 + 560aaa7 sonrası tek koşu)
Kod: `strategy-lab/intraday/seffaf_adaylari.py` (Antigravity yazdı, Claude denetledi: short getiri formülü
düzeltildi — hata Claude'un görev metnindeydi; B1 overlay koşul=True iken nb_simulate ile 802/802 birebir).
bp/işlem (B2 bp/gün): maliyetsiz / merkez / 2× · Bonferroni CI (merkez) · <2022 / 2022+ · n
- B1 NB overlay farkı: +0.5 / +0.5 / +0.5 · [−0.2, 1.2] · +0.8 / −0.1 · 3473 gün → GEÇMEDİ
- **B2 BTC Donchian topluluk (swap 0): +4.27 / +4.24 / +4.21 · [0.73, 7.99] · +6.39 / +2.42 · 3289 gün → GEÇTİ**
  - swap −%30/yıl satırı: +2.70 · [−0.78, 6.42] · +5.24 / +0.55 → swaplı firmada GEÇMEZ. Ortalama toplam ağırlık 0.19.
- B3 XAU H1: +52.6 / +49.9 / +47.2 · [−26, 235] · +7.3 / +161 · 228 → GEÇMEDİ
- B4 XAU M30: +4.0 / +1.3 / −1.4 · [−3.3, 6.0] · −0.9 / +6.4 · 1128 → GEÇMEDİ
- B5 NQ: +6.4 / +4.2 / +1.9 · [−16, 25] · 120 → GEÇMEDİ; B5 XAU: +8.6 / +5.9 / +3.2 · [−14, 28] · 115 → GEÇMEDİ
- B6 NQ: +3.8 / +1.6 / −0.6 · [−5.9, 9.2] · 1028 → GEÇMEDİ; B6 XAU: −14.4 / −17.1 / −19.8 · [−44, 5.7] · 64 → GEÇMEDİ
- **B7 IBS NQ: +54.3 / +52.1 / +49.8 · [23.1, 79.3] · +58.9 / +39.2 · 415 → GEÇTİ**
  - swap −1.18 bp/gece (ort. 4.6 gece): +46.6 · [17.5, 74.1] · 2022+ +33.5 → swaplı da geçer.
  - İcra duyarlılığı (kural değil, bilgi): IBS ve giriş/çıkış 15:55 bar kapanışı → +41.6 · [15.9, 66.4] · 2022+ +26.4, n=436.

### Portföy adımı (FN 2-Step 25K, 2022+, 20 gün blok bootstrap 800 yol, seed 20261118)
Boyut ön-kayıtta yoktu; varsayım (sonuca bakmadan, TOM ile eş): B7 0.5× nominal, B2 0.5× (hedef vol %12.5).
Günlük korelasyon 2022+: B7 ile mevcut 6 modül −0.02..0.09; B2 ile BTC_21_23 0.20, BTC_GECE 0.12, diğerleri ≤0.04.
Yıllık % / Sharpe / maxDD%; mc=3: ilk payout medyan gün, 12 ay net $, zarar olasılığı (gün içi 1.5× stres):
- 6'lı: 18.1 / 1.48 / 11.1 · 99g $2968 %3 (%7)
- +B7: 23.9 / 1.70 / 14.5 · 79g $4239 %2 (%6)
- +B2: 22.5 / 1.54 / 12.0 · 91g $3821 %4 (%9)
- +B7+B2: 28.3 / 1.74 / 14.5 · 75g $5151 %2 (%8)
- +B7+B2 swaplı: 24.1 / 1.48 / 14.7 · 80g $4389 %4 (%12)
- mc=1 aynı sıra: 214g $1092 / 178g $2381 / 185g $1984 / 160g $3172 / 171g $2417.
Sıfır-edge kontrol (ortalama çıkarılmış) her sette negatif/≈0 medyan → değer edge'den geliyor.
Açık noktalar: B7'de stop yok → FN "en fazla %3 açık risk" kuralı stop'suz pozisyonda nasıl ölçülür, doğrulanmadı.
B2/B7 P&L simülasyonda giriş gününe yazıldı (mevcut TOM ile aynı) → çok günlük taşımada gün içi dip eksik ölçülür.
FundedNext'in BTC/NDX swap'ı doğrulanmadı. Eklenme kararı kullanıcıda.
