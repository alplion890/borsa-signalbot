# "Düzenli prop firm geçtiğim sistem" — naked POC ilk temas, FX minör (2026-11-11) — ön-kayıt

Bu belge koşumdan ÖNCE commit edilir. Kaynak: YouTube canlı yayın `7uE4hqnjHTI` (Ziya BAYSAL, 2:25:00, 2026-11-10).
`elenenler --kontrol`: poc / point of control / volume profile / naked / footprint / order flow / minor → katalogda YOK.

## Videodaki sistem (transkript 00:07–00:50, 01:27)
1. **Seviye (TradingView, ücretsiz):** yalnız FX minörleri (21 çapraz; OANDA verisi). Herhangi bir TF'de (1m–4h)
   "akümülasyon" bul, volume profile çek; şekil kabaca **D** (normal dağılım) ise POC'u anahtar seviye. POC'a daha önce
   **hiç dokunulmamış** olmalı (naked POC). Fiyat uzaktan gelip **ilk kez** dokunur.
2. **Onay (kendi programı, kapalı):** CME 6E/6B/6A/6N… vadeli tick verisinden (ATAS API) sentetik minör footprint; iki
   bacağa 150 ms içinde zıt yönlü eşit emir gelirse ±1 delta. Seviyede emilim → karşı tarafın ittirmesi → mum kapanışı
   ("1-2-3 mum"). Program yayınlanmadı; "web sitesine koyacağım" dendi.
3. **İşlem:** onaydan sonra giriş, stop dönüş ucunun "birkaç tik" ötesi, hedef **1–1.5R** veya sonraki naked POC.
   İşlemler gün içi, bazen ertesi güne sarkar. Korelasyonlu portföy risk sayfası.
4. **İddia (01:27):** "1–1.5R aralığında %70–75'i rahat yakalarsın, komisyon ve spread'i karşılar, %80'e dayandığı dönem olur."
   Backtest sayısı / işlem sayısı / tarih aralığı verilmedi.

## Ne test ediliyor, ne edilemiyor
- **Test edilen:** 1. ve 3. adımın mekanik karşılığı — D-şekilli naked POC'a ilk temas + mum kapanışı onayı. Bu sistemin
  "anahtar seviye" iddiası (yayında "destek direncin mantığı bu" deniyor).
- **Test edilemeyen:** 2. adım (kapalı sentetik footprint). Elimizde CME FX vadeli tick verisi yok ve program yayınlanmadı.
  Sonuç ne çıkarsa çıksın footprint filtresi hakkında hüküm VERMEZ; yalnız "seviye tek başına kenar taşıyor mu" sorusunu cevaplar.

## Mekanik tanım (sabit)
- **Profil:** her UTC günü (≥48 bar), 15m barlardan `indicators.calc_volume_profile_for_day` (100 dilim, hlc3, tik hacmi).
- **D-şekli:** POC günün aralığının orta yarısında (%25–%75).
- **Naked:** profil gününden sonra POC'u kapsayan bar (low ≤ POC ≤ high) yok. Geçerlilik 20 işlem günü.
- **İlk temas:** POC'u kapsayan ilk bar `i`. Yön: `close[i-1] > POC` → long (yukarıdan gelip destek), aksi short.
  Her POC yalnız ilk temasta kullanılır.
- **Onay:** `j ∈ [i, i+4]` içinde ilk bar; long için `close[j] > POC` ve `close[j] > high[j-1]` (short ayna). Yoksa setup düşer.
- **Giriş** `close[j]`; **stop** `min(low[i..j]) − 0.1·ATR(14)` (short ayna); **hedef** 1.5R (birincil), 1.0R duyarlılık.
- `honest_engine.simulate_trades` bar/SL-önce, `max_hold=192` (2 gün), `min_rr=0.5`.

## Veri ve maliyet
- Dukascopy 15m BID, ~3 yıl: EURGBP, AUDNZD, AUDCAD, EURNZD, GBPNZD, NZDJPY (yeni indirildi) + EURJPY, GBPJPY (önbellek).
- Maliyet/yön: config'dekiler (EURJPY 0.00009, GBPJPY 0.00016); yeni minörler için **varsayım** (config'de yok):
  EURGBP 0.00010, AUDCAD 0.00013, NZDJPY 0.00012, AUDNZD 0.00015, EURNZD 0.00015, GBPNZD 0.00018.
  1x, 2x ve maliyetsiz (teşhis) raporlanır.

## Karar kuralı (sabit)
8 parite birleşik, 1.5R, 1x maliyet: (a) n ≥ 30, (b) exp_R > 0, (c) 2x maliyet exp_R > 0, (d) iki zaman yarısında exp_R > 0,
(e) paritelerin ≥ 5/8'inde exp_R > 0 → "seviye aday" (yalnız Maven PAPER ön-kaydına aday). Aksi halde **seviye kısmı ELENİR**,
footprint kısmı "ölçülemedi" olarak kataloğa girer. Not: 1.5R'de başabaş WR %40; iddia edilen %70 WR ≈ +0.75R/işlem demektir.

## Yasak
Ara sonuca göre dilim, D-eşiği, onay penceresi, stop tamponu, hedef, parite değiştirmek.

## Sapma (koşumdan ÖNCE, sonuç görülmeden — 2026-11-11)
Dukascopy `freeserv.dukascopy.com` iki denemede ve sandbox dışında da zaman aşımı verdi; veri inmedi.
Kaynak **Maven MT5** M15'e çevrildi (projenin icra kaynağı): 8 minörün hepsi, her biri 95.000 bar, 2023-01-17 → 2026-11-11,
tik hacmi. Günler broker sunucu saatine göre gruplanır (FX günü, UTC değil). Medyan bar spread'i (puan):
EURGBP 5, AUDNZD 5, AUDCAD 7, EURNZD 16, GBPNZD 13, NZDJPY 3, EURJPY 5, GBPJPY 9 — ön-kayıttaki maliyet varsayımları
bunlardan daha muhafazakâr olduğu için **değiştirilmedi**. Kural, eşik, hedef, karar kuralı aynı.
