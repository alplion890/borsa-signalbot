# Genetic Optimization — Gate Arkasında (b)

GA tek başına tehlikelidir (overfit makinesi). Bu paket GA'yı **yalnızca
aday-üretici** olarak kullanır; her aday mevcut **purged-WF + DD-fail + 4/4-yıl
overfit gate**'inden geçer. Karar gate'in, arama GA'nın.

## Neden bu mimari
PROJECT_STATUS'ta kanıtlandı: gün filtreleri purged-WF'de DD'yi %7→%19.5
çatlattı = gerçek overfit. GA bu tür köşe çözümlerini bolca üretir. Gate'i
fitness'a gömerek GA'yı sadece **gate-geçen bölgeye** evrimleştiriyoruz.

## Çalıştırma
```bash
python -m intraday.ga.optimize_gold_orb --pop 24 --generations 18
```

## Modüller
| Dosya | Sorumluluk |
|---|---|
| `ga_core.py` | Generic GA motoru (GeneFloat/Int/Choice, tournament, elitizm, mutasyon, cache). Strateji bilgisi yok. |
| `gate.py` | Overfit gate'i hem hard-filter hem fitness olarak sarmalar. |
| `optimize_gold_orb.py` | Gold ORB parametrelerini gerçek portföy bağlamında arar. |

## Fitness mantığı (gate.py)
```
gate GEÇEN  -> 1000 + pass_pct + dd_margin*0.5   (her zaman kalandan yüksek)
gate KALAN  -> pass_pct - 50 * ihlal_sayısı
```
Böylece GA önce gate-geçen bölgeyi bulur, sonra orada pass_pct'yi maksimize eder.
Gate-geçen tüm adaylar `outputs/intraday/ga/ga_gold_survivors.csv`'ye yazılır.

## Aranan param uzayı (Gold ORB)
| Gen | Aralık |
|---|---|
| open_hour | 13.0–15.0 |
| range_minutes | 30–90 |
| rr | 0.8–2.5 |
| max_hold | 24–72 |
| adx_thresh | 25–40 |
| entry_mode | close / retest |
| trend_filter | ema / vwap |
| sl_mode | other_side / half_range / atr |

## Diğer modüllere genişletme
`optimize_gold_orb.py`'yi şablon al: `_gold_ledger`'i ilgili modülün
parametrik ledger kurucusuyla değiştir, `_space()`'i o modülün param yüzeyine
göre tanımla. `gate.py` ve `ga_core.py` değişmeden çalışır.
