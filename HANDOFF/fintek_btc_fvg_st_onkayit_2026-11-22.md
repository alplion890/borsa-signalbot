# Ön-kayıt: Fintek Mustafa YouTube BTC stratejisi — 15m Doji+Boğa + 5m FVG + 1m SuperTrend(10,3) (2026-11-22)

Bu dosya Binance BTCUSDT 1m verisi üzerinde test koşulmadan ÖNCE commit edilir. Kural, eşik, maliyet ve karar kriteri sonuç görüldükten sonra değiştirilmez.

## Kaynak ve Dürüst Etiket
- Kaynak: Fintek Mustafa YouTube videosu (`https://youtu.be/sKveGXvdmmU`, 2026-11-21, "$150K Funded Getiren Tek Setup — Breakout Prop Canlı İşlem – FVG + Supertrend Stratejim").
- **Eksik/diskresyoner parçalar (açık beyan):** Videoda elle çizilen "iki dip + üç tepe paralel kanal dibi" ve işlem sırasında elle stop'u girişe çekme ("FVG tuttu") var; bunlar kodlanabilir kural değildir. Bu test stratejinin **mekanikleştirilebilir çekirdeğini** ölçer (tek parametre seti, parametre taraması yok).
- Katalog kontrolü: `rsiband_supertrend_video` (`rejected`) ve `fvg_doldurma` (`standalone_rejected`) ayrı ayrı elenmişti; bu özel 3-zaman-dilimli kombinasyon daha önce test edilmedi.

## Veri
- Binance Spot `BTCUSDT` 1m OHLCV (`data.binance.vision` aylık arşivleri), **2024-11-01 – 2026-10-31** (tam 24 ay, ~1.05M 1m bar).
- 5m ve 15m barlar bu 1m verisinden (`label='left', closed='left'`) üretilir.
- 7/24 işlem, roll yok.

## Kesin Kural (Tek Test — Yalnız Long, Videodaki Kurulum; Short Ayna Yalnız Bilgi Satırı)
1. **15m Kurulum (`15m` bar kapanışında):**
   - Önceki 4 adet 15m bar net düşüşte: `close[i-1] < open[i-4]` (dipte kurulum vekili).
   - Bar `i-1` **Doji**: `range > 0` ve `|close - open| / (high - low) <= 0.25`.
   - Bar `i` **Güçlü Boğa Mumu**: `close > open`, `(close - open) / (high - low) >= 0.60` ve `close > high[i-1]`.
   - Bu koşul sağlandığında 15m bar kapanış anı `t_setup` olarak işaretlenir; kurulum **sonraki 60 dakika** (12 adet 5m bar) boyunca aktiftir.
2. **5m FVG (Fair Value Gap):**
   - Aktif kurulum penceresi içinde (veya kurulum barlarının içinde yeni oluşan) 5m'de **Bullish FVG**: `low[k] > high[k-2]`.
   - FVG üst sınırı = `fvg_top = low[k]`, alt sınırı = `fvg_bot = high[k-2]`.
   - Minimum risk filtresi: `(fvg_top - fvg_bot) / fvg_top >= 0.0015` (%0.15; aşırı dar gürültü boşluklarını elemek için).
3. **1m Giriş ve SuperTrend(10, 3) Onayı:**
   - 5m FVG kapandıktan sonraki **60 dakika** içinde 1m barlarda fiyat FVG üstüne geri çekilip değerse (`low <= fvg_top` ve `low > fvg_bot`, yani FVG kırılmadan temas) VE o 1m bar kapanışında (veya önceki tamamlanmış 1m bar kapanışında, look-ahead yok) **1m SuperTrend(ATR=10, Mult=3.0)** yönü **UP (yeşil)** ise:
   - Giriş = o 1m barın kapanışından (piyasa emri onayı; bar içi limit iyimserliği yok).
   - Stop = `fvg_bot` (eğer `entry <= fvg_bot` ise işlem iptal).
   - Hedef = `entry + 2.0 * (entry - stop)` (sabit `2.0R`, videodaki 1:2 Spark kuralı).
4. **Çıkış ve Yönetim:**
   - 1m barlar üzerinde tick/bar sırası (aynı 1m barda hem stop hem hedef değerse **stop önce**, dürüst motor varsayımı).
   - Maksimum tutma süresi: 24 saat (1440 adet 1m bar); süre dolarsa kapanışta çık.
   - Aynı anda en fazla 1 açık pozisyon.

## Maliyet (Ölçülmüş, 3 Satır)
- Maven `outputs/intraday/mt5_bridge/reality_profile.csv` `BTCUSD` `real_cost_per_side_central` (ölçüm 2026-11-12).
- Üç satır: **maliyetsiz (0)** / **ölçülmüş merkez (1×)** / **kötümser (2×)**. (Not: Breakout Prop ücreti ölçülmediği için proje kuralı gereği Maven ölçülmüş BTC maliyeti kullanılır; ayrıca 24 saati aşmadığı için swap 0.)

## Karar Kuralı (Tek Test, `alpha = 0.05` iki yönlü)
- **GEÇER =** Merkez maliyette işlem başı net R için bootstrap (`10.000` tekrar, `seed = 20261122`, blok = 1) iki yönlü %95 CI (`0.025` kuantil) **alt sınırı > 0** **VE** İlk Yıl (`2024-11..2025-10`) > 0 **VE** İkinci Yıl (`2025-11..2026-10`) > 0 **VE** `2×` maliyet ortalaması > 0.
- Geçerse bile LIVE'a girmez; sonraki adım forward PAPER. Geçmezse `elenenler.py` kataloğuna eklenir.

---

## SONUÇ (2026-11-22, ön-kayıt `20f58b2` sonrası tek koşu) — **GEÇMEDİ (ELENDİ)**

Kod: `HANDOFF/scripts_2026-11-23/fintek_btc_fvg_st.py`, çıktı: `strategy-lab/outputs/intraday/fintek_btc_fvg_st/result.json`.
Veri: Binance Spot `BTCUSDT` 1m, 2024-11-01 – 2026-10-31 (1.051.200 bar). Maliyet: Maven `BTCUSD` `real_cost_per_side_central = 0.000285` (gidiş-dönüş ~5.7 bp).

| Test | n | Maliyetsiz | Merkez | 2× | %95 CI (Merkez) | Yıl 1 / Yıl 2 | WR (Merkez) | Sonuç |
|---|---|---|---|---|---|---|---|---|
| **LONG (Ana Test)** | 204 | +0.074R | **−0.069R** | −0.211R | [−0.262, +0.137] | −0.117 / −0.025 | %35.8 | **GEÇMEDİ** |
| **SHORT (Bilgi)** | 221 | −0.063R | **−0.207R** | −0.351R | [−0.389, −0.019] | −0.194 / −0.221 | %31.2 | **GEÇMEDİ** |

Mekanik çekirdek maliyetsiz bile gürültü içinde, ölçülmüş maliyetle her iki yılda da negatif. Elenenler: `fintek_btc_fvg_supertrend_video`.
