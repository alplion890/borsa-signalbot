# Ön-kayıt: SWEEP_CORE diğer endekslerde, slot kısıtsız (2026-11-18)

Yazıldı: test koşulmadan ÖNCE. Commit hash'i sonuç raporunda anılır.

## Neden yeniden
`elenenler.sweep_cok_endeks` (2026-08-14) vetosu "aynı anda tek işlem" (slot) kısıtı altındaydı ve kısa
pencerede (n=118) ölçüldü. Kapsamı: yalnız "7 endekse yay" genişlemesi slot kuralı altında. FundedNext
yapısında slot kuralı yok; soru farklı: her endeks **kendi başına** 14 yılda ölçülmüş maliyetle geçiyor mu,
geçenler portföye eklenince FundedNext simülasyonu iyileşiyor mu.

## Kural (değişmez)
- Dedektör: `long_history_ab._sweep_build` + `run_spec` (SWEEP_CORE canlı aynası, ADX>25, Çarşamba hariç,
  adaptif RR 4/6/8, min_rr 2.0, max_hold 480 bar). Parametre taraması YOK.
- Veri: Dukascopy 5m önbellek → 15m OHLC resample, 2012–2026.
- Semboller (önceden sabit, 6): SP500, US30, US2000, UK100, FRA40, JAP225. GER40 hariç (maliyet ölçülmedi,
  INSTRUMENTS'ta yok). NASDAQ100 yalnız kontrol (bilinen 14y sonucu yeniden üretmeli).
- Maliyet: `reality_profile.csv` `real_cost_per_side_central` (Maven, 2026-11-12 ölçümü); 2× kötümser.
  honest_engine üç kez koşulur: Instrument.cost_per_side = 0 / ölçülmüş merkez / 2× merkez.

## Geçme kuralı (her sembol ayrı)
1. Ölçülmüş merkez maliyetle ortalama R > 0.
2. Bootstrap (seed 20261118, 10.000) alt sınır > 0, Bonferroni α = 0.05/6.
3. 2012–2021 ve 2022+ alt dönemlerin ikisi de > 0.
4. 2× maliyetle ortalama > 0.
Hepsi sağlanmazsa sembol eklenmez. "En iyi 3'ü seç" yok.

## Portföy adımı (yalnız geçen semboller)
Geçenler aynı risk (%0.5) ile 6'lı portföye eklenir; `firms.py` FN 2-Step 25K mc=3 ve mc=1 simülasyonu
eklemeli/eklemesiz karşılaştırılır (sıfır-edge ve gün içi 1.5× stres dahil). Korelasyon (NQ/SP/US30)
raporlanır; günlük toplam açık risk FN %3 kuralına göre ölçülür.

## Bilinen tuzaklar
- Aynı anda tetiklenen korele endeksler bağımsız gözlem değildir (örtüşen bacak) → portföy günlük bazda ölçülür.
- Sonuca bakıp sembol çıkarmak/eklemek yasak.

## SONUÇ (2026-11-18, ön-kayıt cd76805 sonrası tek koşu)
R/işlem: maliyetsiz / ölçülmüş merkez / 2× · Bonferroni alt sınır · <2022 / 2022+ · n
- NASDAQ100 (kontrol): +0.228 / −0.005 / −0.238 · −0.44 · −0.417 / **+0.718** · 237 → bilinen sonuç yeniden üretildi
- SP500: −0.446 / −0.865 / −1.284 · −2.18 · −1.027 / −0.402 · 228 → GEÇMEDİ
- US30: −0.020 / −0.148 / −0.276 · −0.48 · −0.142 / −0.164 · 198 → GEÇMEDİ
- US2000: +0.128 / −0.076 / −0.281 · −0.48 · −0.151 / −0.015 · 149 → GEÇMEDİ
- UK100: +0.059 / −0.113 / −0.286 · −0.39 · −0.077 / −0.195 · 274 → GEÇMEDİ
- FRA40: −0.030 / −0.205 / −0.381 · −0.53 · −0.237 / −0.131 · 276 → GEÇMEDİ
- JAP225: +0.124 / −0.162 / −0.448 · −0.38 · −0.122 / −0.212 · 545 → GEÇMEDİ
Portföy adımı koşulmadı (geçen yok). Kısa pencere PAPER artıları (JAP225 n13, SP500 n7, UK100 n7) 14 yılda
tutmadı — küçük örneklem. `elenenler.sweep_cok_endeks` ölçüm satırı güncellendi.
Çıktı: `strategy-lab/outputs/intraday/kaynak_adaylari/sweep_multi.json`, `sweep_multi_trades.csv`.
