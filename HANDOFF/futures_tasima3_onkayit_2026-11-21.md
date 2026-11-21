# Ön-kayıt: CFD'den futures'a taşıma, üçüncü tur — Sweep NQ, Donchian GC, Sweep RTY (2026-11-21)

Bu dosya `futures_transfer3.py` gerçek veride çalışmadan ÖNCE commit edilir. Kural, eşik, maliyet yöntemi değişmez.

## Soru ve dürüst etiket
CFD'de maliyetsiz pozitif, Maven maliyetiyle sıfıra/negatife inen üç kural vadeli maliyetiyle ayakta kalıyor mu?
- Sweep NQ (14y, slot kısıtsız, cd76805): maliyetsiz +0.228R, ölçülmüş −0.005R, 2022+ +0.718R.
- Donchian XAU N=20 1H (2026-08-23): +0.085R (Maven config maliyeti).
- Sweep US2000 (cd76805): maliyetsiz +0.128R, ölçülmüş −0.076R.
**Bağımsız edge kanıtı DEĞİL** (aynı 2012–2026 döneminde görüldü, maliyetsiz pozitif oldukları için seçildi).
Gerçekten görülmemiş dilim: CME 2010-06-06 – 2011-12-31, ayrıca raporlanır, karar şartı değil.

## Kurallar (değişmez motorlar)
- **T1 Sweep NQ:** `long_history_ab._sweep_build` + `run_spec` mantığı (ADX>25, Çarşamba hariç, ATR rejimine göre
  max RR 4/6/8, min RR 2.0, max 480 bar), NQ.c.0 15m.
- **T2 Donchian GC:** `donchian_xau_lab.build_signals` N=20, RR 2, max 200 bar, `honest_engine.simulate_trades`, GC.c.0 1h.
- **T3 Sweep RTY:** T1 ile aynı, RTY.c.0 15m.
Parametre taraması yok. N=55 koşulmaz.

## Veri
Databento GLBX ohlcv-1m, UTC naive, 15m/1h'e toplanır (label=left, closed=left). **Roll:** çok günlük işlemler
nedeniyle seri **oranla geriye ayarlanır** (ardışık 1m barlarda `instrument_id` değişince, öncesi yeni ilk kapanış /
eski son kapanış oranıyla çarpılır; aradaki 1 dk gerçek hareket hataya dahil). Sinyal ayarlı seride üretilir.
Maliyet oranı **ayarsız** giriş fiyatıyla hesaplanır.

## Maliyet (ölçülür)
Yön başı puan = yarım spread medyanı + komisyon / çarpan.
- MNQ: 0.555 puan (önceki ölçüm, bbo-1m 2025–26, NY 09:30–16:00).
- MGC (çarpan 10), M2K (çarpan 5): bbo-1m MGC.c.0 / M2K.c.0 2025-01 – 2026-11, aynı NY 09:30–16:00 penceresi,
  (ask−bid)/2 medyanı; tüm saatlerin medyanı da raporlanır (bilgi). Komisyon $0.61/yön (Topstep MES örneği;
  **MGC/M2K için doğrulanmadı**).
- Motor maliyeti oran olarak alır; puan maliyeti işlem bazında uygulanır: motor iki kez koşulur (maliyet 0 ve 1e-4),
  aynı işlem kümesi olduğu doğrulanır, R_net = R0 − (R0 − R1)/1e-4 × (puan / ayarsız giriş).
- Üç satır: maliyetsiz / merkez / 2× merkez. Ayrıca Maven CFD satırı (`reality_profile.csv` NASDAQ100, XAUUSD, US2000).

## Karar kuralı (her hipotez ayrı, Bonferroni 3 test)
GEÇER = merkez maliyette işlem başı R için bootstrap (blok 1, 10.000, seed 20261121) iki yönlü Bonferroni (0.05/3/2)
alt sınırı > 0 **ve** 2012–21 ve 2022+ ortalamaları > 0 **ve** 2× ortalaması > 0. Değerlendirme 2012-01-01 – 2026-11-19.
Geçen olursa bile LIVE'a girmez; sonraki adım forward PAPER.

## Bilinen tuzak
Sweep NQ'nun 2012–21 yarısı CFD Maven maliyetiyle negatifti (−0.417R); kural iki yarıyı da şart koşuyor, 2022+ tek başına
"geçti" sayılmaz (post-hoc filtre).

## EK (2026-11-22, sonuç görülmeden, kod çalışmadan önce) — veri düzeltmesi
- **GC.c.0 takvim önayı ince**: 2024'te yalnız 9.721 dakikalık bar (günlük medyan hacim 53 kontrat). Donchian bu
  seride anlamsız. **T2 GC.v.0 (hacim sıralı önay) ohlcv-1h** ile koşulur; roll = ardışık saat barlarında
  `instrument_id` değişimi, aynı oranla geriye ayarlama. Kural ve maliyet değişmez.
- **RTY CME'de 2017-07'den beri var**: T3'ün 2012–21 yarısı fiilen 2017-07 – 2021; 2010–11 görülmemiş dilimi yok.
  Karar kuralı aynı (iki yarı > 0).
