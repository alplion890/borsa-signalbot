# Kaynak taraması: Concretum + Quantpedia/akademik + kripto (2026-11-17)

Yöntem: 3 paralel araştırma ajanı (web), sonra ana oturum kaynak doğrulaması (WebSearch).
Ajan rakamları DOĞRULANMADI; yalnız aşağıda "doğrulandı" yazan kaynak/iddia kontrol edildi.
Hiçbir aday teste girmedi. Sıradaki adım: aday başına ön-kayıt.

## Güvenilirlik notu
- Quantpedia/akademik ajanı: SSRN/Quantpedia Premium'a erişemedi; atıfların bir kısmı uydurma
  görünüyor (opex için "Bender-Sun-Zadeh 2018", "Chaudhary-Scheid 2016"), win rate'ler kaynaksız,
  Gao-Han-Li-Zhou'yu "dönüş" diye yanlış anlattı. Rakamları atıldı; yalnız fikirler tutuldu.
- Concretum ve kripto ajanları: URL veriyor, daha somut; yine de rakamlar ikincil kaynak.

## Aday listesi (ön-kayıt sırası önerisi değil, olgu listesi)

| # | Aday | Doğrulanan kaynak | Enstrüman | Maven uyumu | Not |
|---|---|---|---|---|---|
| A1 | Gün içi zaman serisi momentumu (ilk 30 dk → son 30 dk), ABD dışı endeksler | Li-Sakkas-Urquhart, J. Financial Markets 2022 (16 gelişmiş piyasa); Gao-Han-Li-Zhou JFE 2018 — doğrulandı | UK100, FRA40, JAP225, GER40 | Uyar: günde 1 karar, kapanışta çıkış | Baltussen (NQ/XAU, rROD) veto etmez — farklı kural ve piyasa. Brüt etki < 2× maliyet riski (Baltussen'de 0.5–0.75 bp çıktı). GER40 maliyeti ölçülmedi. |
| A2 | Opsiyon vadesi haftası long | Stivers-Sun, J. Banking & Finance 2013 — doğrulandı. S&P500 1983–2008 OE haftası yüksek; S&P100 hisseleri haftalık %0.45 vs %0.12 | SP500, NASDAQ100 | Uyar: ayda 1 işlem; gece taşıma (swap ölçülmedi) | Son yıllarda zayıfladığı iddiası (blog). Yılda 12 işlem → 14 yılda ~170, düşük n. |
| A3 | Ay dönümü (TOM) long | Maberly-Waggoner 2000: S&P futures'ta 1990 sonrası kayboldu. Carchano-Pardo 2011: "+1" günü (son gün kapanış → ertesi kapanış) 1991–2008 maliyetten sonra tek kalıcı etki — doğrulandı | SP500, NASDAQ100 | Uyar: ayda 1 işlem, 1 gece swap | Kanıt 2008'de bitiyor; çelişkili. Yayın sonrası bozulma riski yüksek. |
| A4 | BTC gece seansı (NYSE kapalıyken long) | Quantpedia (Dujava) 2024-11-12 — doğrulandı: 2021 sonrası getiri gece seanslarında, özellikle Cuma kapanış→Pzt açılış, Pzt→Salı, Salı→Çarş. Detay kural Premium arkasında | BTCUSD | Uyar (elle saat bazlı); gece swap ölçülmedi | BTC 21–23 UTC ile AYNI etkinin genişi olabilir → bağımsız sayma. Test sorusu: "21–23 mi, tüm gece mi" (ikame, ekleme değil). |
| A5 | BTC haftalık mevsimsellik (Pazar ~19:00 ET sonrası) | Concretum blog notu "Seasonality in Bitcoin Intraday Trend Trading" — var, doğrulandı; kural yok ("ileride ayrı çalışma") | BTCUSD | Belirsiz | Kural yayımlanmamış → ön-kayıt için kural uydurmak gerekir = post-hoc riski. Beklemede. |
| A6 | Concretum kripto trend (Donchian topluluğu) | Zarattini-Pagani-Barbon, SFI 25-80 (2025) — var | BTCUSD | Uyar (günlük/saatlik) | Tam kural makale PDF'inde; okunmadı. Bağımsız tekrar yok. |

## Elenenler (bu tarama)
- Concretum ORB 5 dk QQQ: bağımsız MQL5 tekrarı (ajan raporu, URL mql5.com/en/blogs/post/776235) NQ net ≈ +0.002R; bizim MNQ ORB testi de elendi.
- Concretum "Stocks in Play" ORB, VIX ETN, hisse trend: Maven'de hisse/ETN yok.
- Concretum VWAP QQQ: çıkış kuralı yayımlanmamış → test için kural uydurmak gerekir.
- Noise Band'i diğer endekslerde "parametre ayarıyla" yeniden denemek (Concretum ajanı önerdi): REDDEDİLDİ — sabit parametreyle geçmedi; ayarlamak post-hoc filtre.
- Altın Londra fix dönüşü: FX fix testine yakın + gece swap bilinmiyor.
- EUR/USD Tokyo açılışı söndürme: kaynak belirsiz, yılda 200+ elle işlem.
- Çeyrek sonu dengeleme: brüt etki maliyetten küçük (ajan iddiası).
- Kripto: funding rate (R²≈0), CME gap (metodoloji yok), ETF akış (günlük veri), ABD son saati (maliyetle negatif), likidasyon, stablecoin basımı, Shen-Urquhart-Wang (2022 sonrası test yok).
- Deribit Cuma 08:00 UTC vade (Weiss vd. FRL 2026): Deribit OI tarihsel verisi yok, etki büyüklüğü bilinmiyor → beklemede.

## Maven'de tutmayan kural → firma eşlemesi
- Bu turdaki adayların hiçbiri Maven'in EA yasağı veya haber yasağına takılmıyor (hepsi saat bazlı, az karar).
- Açık risk: gece taşıyan adaylarda (A2, A3, A4) **swap** — Maven sembol özelliklerinden ölçülmeli (MT5 açık iken).
- %20 tutarlılık: ayda 1 işlemli adaylar (A2, A3) az sayıda büyük gün üretir → tutarlılık kuralı kısıtlayıcı olabilir; `prop_fit` ile simüle edilmeli. Tutmazsa tutarlılıksız firma (FTMO 2-Step / FundedNext Stellar 2-Step) adayı.

## Sıradaki adım
1. MT5 açılınca: UK100/FRA40/JAP225/GER40 + BTC için `reality_profiler` (GER40 yok) ve swap değerleri.
2. A1 için ön-kayıt (en güçlü akademik destek: 16 piyasa, hakemli). Bonferroni = test edilen endeks sayısı.
3. A4 için ön-kayıt: BTC 21–23 vs NYSE-kapalı gece, ikame testi.
4. A2/A3 tek ön-kayıtta (takvim etkileri), düşük n uyarısıyla.

Kaynaklar:
- https://centaur.reading.ac.uk/95566 (Li-Sakkas-Urquhart 2022)
- https://ideas.repec.org/a/eee/jbfina/v37y2013i11p4226-4240.html (Stivers-Sun 2013)
- https://www.atlantafed.org/research/publications/wp/2000/11.aspx (Maberly-Waggoner 2000)
- https://cxoadvisory.com/calendar-effects/stock-index-futures-calendar-effects (Carchano-Pardo özeti)
- https://quantpedia.com/how-to-profitably-trade-bitcoins-overnight-sessions/ (Dujava 2024)
- https://concretumgroup.com/seasonality-in-bitcoin-intraday-trend-trading/
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5209907 (Concretum kripto trend)
- https://www.mql5.com/en/blogs/post/776235 (ORB tekrarı, ajan kaynağı, açılıp okunmadı)
