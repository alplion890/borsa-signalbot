# Edge yeniden yargılama — ön-kayıt (2026-11-05)

Bu belge yeni veri görülmeden, aday modül koda eklenmeden ÖNCE commit edilir.
Karar dayanağı: [[Borsa - Strateji Eleme Adaleti ve Motor Denetimi 2026-10-29]]
ve [[Borsa - Tek Kaynak ve Bulut Rolu Karari 2026-11-05]].

## Neden forward, neden yeniden backtest değil

2012–2026 Dukascopy uzun geçmişi ve 2026-04-16→10-14 Maven verisi 2026-10-29
denetiminde zaten görüldü. Aynı veriyi yeniden koşmak yeni kanıt üretmez;
sonucu gördükten sonra o veride kriter seçmek post-hoc olur. Yeni kanıt yalnız
görülmemiş veriden gelir: bu commit'ten sonraki Maven MT5 forward barları.

## Aday seçim kuralı (önceden bilinen sayılara uygulanır)

Uzun geçmiş net beklentisi (gap-v2 motoru, 1× maliyet) **> 0** olmayan aday
forward'a alınmaz. 2026-10-29 tablosuna göre:

| Strateji | Uzun geçmiş n / ort. R | Karar |
|---|---|---|
| NQ ORB (`NQ_ORB_STRONG_TREND` arşiv tanımı) | 1907 / +0,0276 | **Forward adayı** |
| Donchian XAU 1H N20 | 848 / +0,0834 (3× maliyette +0,0392) | Aday; **motor kayan çıkış desteklemiyor** → ayrı iş (aşağıda) |
| EUR London | 1105 / −0,0968 | Aday değil |
| Gold NY ORB | 235 / −0,0687 | Aday değil |
| GBP London | geçersiz (geleceğe bakış) | Bu ön-kayıt dışı; kendi düzeltme ön-kaydı: `strategy-lab/outputs/intraday/fairness_audit/20261027/GBP_DUZELTME_ONKAYIT.md` |
| BTC absorption | uzun geçmiş yok; forward negatif | Aday değil |

## Ölçülecek modül (birebir arşiv tanımı, parametre değişikliği yok)

`CAND_RT_NQ_ORB` — `9acf55b` ile kaldırılan tanımın aynısı:
`ORBCase("NASDAQ100", 14.5, 15, 20.5, "retest", "none", 1.5, "other_side", 1.0, 48)`,
`_orb_detector(..., adx_min=28.0)`, 5m, max 48 bar, ağırlık 0.0 (PAPER, Telegram yok).

## Karar kuralı

- Ölçüm: Maven MT5 forward, `backfill=0` satırlar, bu commit'ten sonra açılan işlemler.
  Eski NQ ORB forward (n=25, −0,106R) ayrı tutulur, bu sayıma girmez.
- Değerlendirme: n=30'da. n=30'a 2027-05-05'e kadar ulaşılmazsa o tarihte mevcut n ile raporlanır, karar n=30'a kadar ertelenir.
- **Geçer** (yalnızca "LIVE adayı" — LIVE'a geçiş yine kullanıcı kararıdır, otomatik değil):
  n≥30 **ve** Maven maliyetiyle exp_R > 0 **ve** 2× maliyetle exp_R > 0.
- **Kalır/emekli:** n≥30 ve exp_R ≤ 0 → kalıcı emekli; katalogda `retired`, gerekçe bu belge.
- Arada (exp_R > 0 ama 2× maliyette ≤ 0) → "maliyete duyarlı", LIVE adayı değil; ölçüm n=60'a uzar.
- Ara bakış serbesttir ama ara sonuca göre kural, parametre veya n değiştirilmez.

## Bilinen bağımlılıklar

- NQ ORB ve Sweep aynı sembolde (NQ). Aynı anda pozisyon çakışması olabilir
  (slot kısıtı, [[Borsa - Portfoy Kompozisyonu ve Slot Kisiti]]). Bu ölçüm
  modülü tek başına değerlendirir; portföy etkisi geçerse ayrıca ölçülür.
- Donchian XAU 1H: kanal tabanlı kayan çıkış gerekir; forward motoru yalnız
  sabit SL/TP/zaman aşımı destekler. Motor desteği eklendiğinde aynı karar
  kuralıyla (n=30, 1× ve 2× maliyet > 0) ayrı ön-kayıt satırı açılır. Yaklaşık
  sabit hedefli bir sürüm ÖLÇÜLMEZ (hipotezi değiştirir).
