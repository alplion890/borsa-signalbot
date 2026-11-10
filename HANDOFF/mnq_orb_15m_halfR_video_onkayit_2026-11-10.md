# "15 saniyede $20K/ay" MNQ ORB (9:15–9:30 NY, 0.5R) — ön-kayıt (2026-11-10)

Bu belge koşumdan ÖNCE commit edilir. Kaynak: Instagram `Dfgh93qza61` (@theagent_trades, "Prop Firm Algo Trader").
Video TradingView raporu iddia ediyor: Nis 2023–Kas 2026, 714 işlem, WR %72, max DD $2,489, 2026'da WR %80, PF 2.06,
$8,849 / 100K hesap. Sonu "HTF yaz, ayarlı versiyonu göndereyim" (ayarlar gizli). `elenenler --kontrol`: "0.5r" yok;
ORB ailesinde `gold_ny_orb` elenmiş, bizim NQ_ORB ayrı kural (CAND_RT_NQ_ORB Maven forward PAPER).

## Kurallar (videodaki prompt metninden kelimesi kelimesine, 00:11–00:21)
- Enstrüman MNQ1! (biz: Dukascopy NASDAQ100 = E-mini NQ CFD), 15m grafik.
- Aralık: 9:15–9:30 New York (tek 15m mum) high/low. Saat dönüşümü America/New_York, DST dahil.
- Long: sonraki bir 15m mum **kapanışı** aralık high'ının üstünde → giriş o mumun kapanışı; stop = kırılım mumunun low'u; hedef 0.5R.
- Short ayna: kapanış aralık low'unun altında, stop kırılım mumunun high'ı, hedef 0.5R.
- Günde tek işlem (ilk kırılım).
- Prompt'taki "5 rejim filtresi oluştur, en iyisini seç" kısmı **uygulanmaz**: bu sonuca bakıp filtre seçmektir (post-hoc). Taban kural test edilir.

## Videonun belirtmedikleri → sabit seçim
- Giriş penceresi: 9:30 mumundan 15:45 mumuna kadar (kapanışı ≤ 16:00 ET).
- Çıkış: hedef/stop yoksa 16:00 ET'de piyasada kapanış (prop gün sonu düz). Duyarlılık: zaman sınırsız (max 480 bar) da raporlanır.

## Motor, maliyet, veri
- Simülatör: `sweep_prop_lab.simulate` (honest_engine ile parite kanıtlı) + force_exit maskesi. Bar/SL-önce.
- Maliyet: `INSTRUMENTS["NASDAQ100"]` (0.00009/yön) 1x ve 2x; ayrıca maliyetsiz (yalnız teşhis).
- `min_rr=0.01`, `max_rr=20` (hedef tam 0.5R).
- Birincil veri: NASDAQ100 15m 2021-06 → 2026-06 (önbellek 1825d). İkincil: uzun geçmiş 2012+ (`data_quality.clean`, donuk günler atılır).

## Karar kuralı (sabit)
Birincil veride: (a) n ≥ 30, (b) 1x maliyet exp_R > 0, (c) 2x maliyet exp_R > 0, (d) iki yarıda da exp_R > 0 →
"aday" (yalnız Maven forward PAPER ön-kaydına aday; LIVE'ı kendiliğinden değiştirmez). Aksi halde ELENİR ve kataloğa girer.
Not: 0.5R hedefte başabaş WR (maliyetsiz) %66.7'dir; %72 WR tek başına edge göstermez, maliyet sonrası R belirler.

## Yasak
Ara sonuca göre saat, pencere, hedef, filtre değiştirmek.

## Sonuç (koşum 2026-11-10, ön-kayıt e0382e8 sonrası)
Kod: `strategy-lab/intraday/mnq_orb_video_lab.py`; çıktı `outputs/intraday/mnq_orb_video/result_2026-11-10.json`.

| veri | n | exp_R 1x | WR % | PF | 2x | maliyetsiz | 1. yarı | 2. yarı | long / short |
|---|---|---|---|---|---|---|---|---|---|
| 2021-06 → 2026-06 (birincil) | 1288 | **-0.079** | 65.7 | 0.78 | -0.145 | -0.014 | -0.068 | -0.090 | -0.082 / -0.076 |
| 2012 → 2026-08 (temiz) | 3578 | -0.158 | 62.2 | 0.63 | -0.256 | -0.060 | -0.225 | -0.097 | -0.177 / -0.136 |

Birincil yıllık exp_R: 2021 -0.129, 2022 -0.029, 2023 -0.081, 2024 -0.089, 2025 -0.116, 2026 -0.019 (hiçbir yıl pozitif değil).
Gün sonu kapanışı kaldırılınca değişmiyor (-0.080). 2012 (-0.912, n=113) veri başlangıcı; kararı etkilemez.
Ort. kazanç 0.44R, ort. kayıp -1.07R; maliyetsiz WR %65.7 < başabaş %66.7.
**KARAR: ELENDİ.** Katalogda `mnq_orb_15m_half_r_video`.
Sınır: Dukascopy NQ CFD (MNQ vadeli değil); maliyet config 0.00009/yön, gerçek MNQ maliyetinden yüksek olabilir — maliyetsiz sonuç da negatif olduğu için karar değişmez.
