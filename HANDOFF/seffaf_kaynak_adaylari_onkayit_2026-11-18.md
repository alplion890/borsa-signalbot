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
