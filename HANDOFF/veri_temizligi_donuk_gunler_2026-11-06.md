# Veri temizliği: Dukascopy donuk günleri — 2026-11-06

Kural (`strategy-lab/intraday/data_quality.py`, sonuçtan önce sabitlendi): bir gün donuk
sayılır eğer barlarının ≥%80'i O=H=L=C ise **veya** gün aralığı önceki 60 günün medyan
aralığının %25'inden küçükse. Donuk günlerin barları TEMİZ kopyadan çıkarılır; ham önbellek
değişmedi. Koşucu: `intraday/long_history_clean_rerun.py` (10-29 mantığının aynısı + clean()).

Hafta içi donuk NQ günleri: 54; büyük kısmı ABD tatilleri (Noel, yılbaşı, 4 Temmuz, Şükran,
MLK, Presidents, Good Friday, Memorial, Juneteenth) ve 2012–2014 bozuk bölümleri
(ör. 2013-02-25: gerçekte sert düşüş günü, veride ~2 puan sabit aralık).

| Strateji | donuk gün (hafta içi) | n eski→temiz | ort R eski→temiz | en kötü | <2022 | ≥2022 |
|---|---|---|---|---|---|---|
| SWEEP_CORE | 532 (54) | 235→241 | **+0.0485→+0.1028** | −3.04 | −0.248 | +0.723 |
| NQ_ORB | 532 (54) | 1907→1897 | +0.0276→+0.0269 | −2.03 | +0.009 | +0.069 |
| GOLD_ORB | 373 (16) | 235→235 | −0.0687→−0.0475 | −2.34 | −0.113 | +0.096 |
| EUR_LONDON | 622 (5) | 1105→1104 | −0.0968→−0.0982 | −1.39 | −0.109 | −0.077 |
| GBP_LONDON | 546 (7) | 1395→1296 | −0.0694→−0.0595 | −1.19 | (geleceğe bakış, geçersiz) | |

Sonuç: Sweep'in uzun geçmiş beklentisi ikiye katlandı (bozuk veri tek işlemi −22.46R yapıyordu;
hafta sonu dolgusu ayrıca 20 barlık pencereleri bozuyordu). Rejim bulgusu değişmedi: 2022 öncesi
negatif, sonrası güçlü pozitif. NQ ORB ve EUR London etkilenmedi; Gold hâlâ negatif.
Temiz veri, hafta sonu barı olmayan Maven canlı feed'ine daha yakındır.
Önceki payout simülasyonları ham veriyle yapıldı (Sweep için biraz kötümser).
