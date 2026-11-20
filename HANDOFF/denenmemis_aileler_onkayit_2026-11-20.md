# Ön-kayıt: hiç test edilmemiş aileler H1–H4 (2026-11-20)

Bu dosya `untested_families.py` gerçek veride çalışmadan ÖNCE commit edilir. Kural, parametre, evren, eşik değişmez.
Kurallar kaynak makalenin manşet varyantı; hiçbir parametre bu veride seçilmez.

## Veri (multi_panel.py)
15 piyasa, Dukascopy (+ data_quality.clean), günlük kapanış = her hafta içi günü 21:00 UTC öncesi son bar (ortak saat):
FX AUDUSD EURUSD GBPUSD USDCAD USDCHF USDJPY · XAUUSD · endeks NASDAQ100 SP500 US30 US2000(2018+) UK100 FRA40 JAP225 · BTCUSD (Binance 2017+).
EURJPY, GBPJPY, XAGUSD: uzun geçmiş yok → dışarıda (sonuca bakılmadan, veri yokluğundan).
Dönem 2013-01-01 – 2026-08-28 (ortak son tarih). Maliyet: Maven reality_profile `real_cost_per_side_central` × |pozisyon değişimi|.
**Swap modellenmedi** (tarihsel swap yok; FN swap-free hesap varsayımı) → çok günlük H1–H3 için etiket "swap ölçülmedi".

## Hipotezler
- **H1 TSMOM** (Moskowitz–Ooi–Pedersen 2012): her varlık için son 252 gün getirisinin işareti; pozisyon = %40 / σ (EWMA, kütle merkezi 60 gün,
  yıllık 261); ay sonu karar, ertesi günden itibaren tutulur; mevcut varlık sayısına bölünür (eşit ağırlık).
- **H2 Kesitsel momentum** (Asness–Moskowitz–Pedersen 2013): 12–1 ay getirisinin sırası; ağırlık ∝ (sıra − ort. sıra), long $1 / short $1;
  sınıf içinde (FX 6, endeks 7); iki sınıf, her biri yıllık %10 ex-ante oynaklığa ölçeklenip eşit birleştirilir; aylık.
- **H3 Pairs** (Gatev–Goetzmann–Rouwenhorst 2006): 12 ay oluşum (normalize fiyat, en küçük SSD), sınıf içi en iyi 5 çift; 6 ay işlem;
  |spread| > 2 oluşum-σ açılış, sıfır geçişte kapanış, dönem sonunda kapanır; çift başı $1/$1, 5'e bölünür; 6 ayda bir yeni dönem.
- **H4 Endeksler arası gece MR** (Quant Returns, doğrulanamamış kaynak): ABD endeksleri (NQ, SP, US30, US2000) NY 16:00→09:30 gece getirisi
  kesitsel arındırılır; ağırlık = −(r_i − ort), brüt 2; NY 09:30 giriş, 16:00 çıkış; maliyet her gün tam aç/kapa.
- **Dışarıda:** FX carry (tarihsel faiz farkı yüklü değil + swap-free hesap carry gelirini sıfırlar), perakende sentiment (tarihsel veri yok).

## Ölçüm ve karar kuralı
- Birincil: 1x maliyette günlük net getiri ortalaması > 0, tek yönlü p (dairesel blok bootstrap, blok 20, 10.000, seed 20261120).
- Çoklu test: dört hipotez Holm düzeltmesi, α = 0.05.
- **GEÇER** = Holm anlamlı (1x) **ve** 4 rejim bloğundan (2013–17, 2018–21, 2022–23, 2024–26) ≥ 3'ünde 1x ortalama > 0 **ve** 2x maliyette yıllık > 0.
- Rapor: maliyetsiz / 1x ölçülmüş / 2x üç satır, Sharpe, blok ortalamaları, ortalama brüt kaldıraç.
- Geçen olursa bile LIVE'a girmez: sıradaki adım Maven forward PAPER + prop uygulanabilirlik (lot inceliği, %3 açık risk).

## İstişare sonrası kesinleşme (Gemini 4 Argon, sonuç görülmeden)
- **Birincil test yalnız H1 ve H2 (Holm M=2).** H3 ve H4 KEŞİF olarak raporlanır, tek başına "geçti" sayılamaz (Argon: doğal çift 3–4,
  CFD temettü kayması; 4 ABD endeksinde günlük tam aç/kapa maliyeti ~yıllık %6). Kod Holm'u yalnız H1/H2'ye uygular.
- **Güç beyanı:** literatür önceli net Sharpe A 0.25–0.50, B 0.10–0.35 (Argon; Hurst-Ooi-Pedersen 2017 2010'lar, AMP 2013 — rakamlar doğrulanmadı).
  14 yılda Sharpe standart hatası ≈ 0.27 → gerçek Sharpe 0.4 bile çoğu zaman anlamlı çıkmaz. "Geçmedi" ≠ "edge yok".
- Ölçek (MOP %40/σ vs Argon %10/N) Sharpe'ı ve geçme kararını değiştirmez; MOP manşeti kalır.
- XSMOM: AMP Denk. 1 (sıra ağırlığı, varlık başı 1/σ YOK); Argon'un 1/σ'lı varyantı test edilmez.
- Dolum: karar kapanışında, kapanıştan kapanışa getiri (MOP aylık standardı); hafif iyimser, etiketlenir. Endeks CFD finansmanı (rf − temettü) swap-free varsayımıyla 0.
