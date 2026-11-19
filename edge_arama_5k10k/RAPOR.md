# Edge arama 5K/10K — derin tarama özeti (2026-11-20)

18 kalem, 6 Haiku ajanı, `results/*.json` (her biri 30/30 alan doğrulandı; belirsiz alan sayısı 11–26).
Hiçbir kalem test değil; aday özeti. Maliyet ölçülmedi.

## Veto (elenenler kataloğu, `python -m intraday.elenenler --kontrol`)
Zaten ölçülüp elenmiş (rejected): ITSM (`gao_itsm_first30_last30`), FX fix dönüşü (`fx_fix_reversal_london_tokyo`),
opex haftası long (`opex_week_long`), son 30 dk momentumu / GEX-LETF mekanizması (`baltussen_last30_momentum`),
ay dönümü +1 (`turn_of_month_plus1`), altın EA'ları (`seffaf_kaynak_b1_b6`), ORB ailesi (NQ/Gold ORB emekli).
Gap fill: FVG doldurma `standalone_rejected` (bağlam olabilir, tek başına giriş değil).

## Ölçülmemiş kalanlar (öncelik 2/5 en yüksek, hiçbiri 3+ değil)
- Ay sonu son 4 işlem günü rebalansı (Harvey-Mazzoleni-Melone NBER 33554; in-sample Sharpe 1.11, OOS yok, 2023+ yok). Yakın akraba `turn_of_month_plus1` elendi.
- Tatil öncesi (büyük endekste 1980'lerden beri azalma; 2023+ test yok; yılda ~9 olay).
- Üçüncü Cuma a.m. settlement sıçraması (Terstegge-Whelan AEA 2025; yön/büyüklük okunamadı; yılda 12 olay).
- VIX vade yapısı rejimi (Quantpedia replikasyonu OOS hafif negatif; günlük, az işlem; rejim etiketi olarak).
- GEX rejimi (veri ücretli: SqueezeMetrics ~$720/ay; vendor çalışması VIX kontrolü sonrası p=0.18).
- Kripto çeyrek saat dönüşü (0.58 bp/dk brüt, spread altı olası; 2023+ yok).
- NQ CISD London 2R (TradingView açık kod; yalnız in-sample, önceki 6 ay zarar; Sweep ile örtüşür).

## Kaynak havuzları
Yarışma kazananları: test edilebilir kural yok. GitHub/freqtrade: OOS'lu güçlü örnek yok. QuantConnect: intraday girdilerde OOS yok.
SSRN 2023-26 en iyi aday "Beat the Market" = mevcut NB modülünün kaynağı.

## Sonuç
Yeni, güçlü, sık işlemli gün içi edge bulunmadı. Ölçülmemiş adayların hepsi seyrek (yılda 9–12 olay) ya da veri/maliyet sorunlu.
5K/10K hedefi için not: mevcut portföy 5K/10K'ya zaten sığıyor (FN 5K instant x1: ~21 gün, 12 ay medyan $273, %9 zarar);
orada engel edge değil fiyat ($104.99 / $209.99).
