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
