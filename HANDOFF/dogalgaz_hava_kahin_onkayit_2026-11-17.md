# Doğalgaz–hava "kâhin" testi ön-kaydı — 2026-11-17

Amaç: uydu/hava veri hattı kurmadan önce, doğalgaz için bilginin fiyata çevrilebilir
olup olmadığını üst sınırda sınamak (gerçek veri önceden biliniyormuş gibi).
Yöntem önceki uydu-petrol testiyle aynı (1d19123).

## Veri (hepsi ücretsiz, resmi)
- EIA haftalık çalışan gaz depolaması, Lower 48 (NW2_EPG0_SWO_R48_BCF), hafta Cuma biter,
  Perşembe 10:30 ET açıklanır.
- NOAA CPC günlük nüfus ağırlıklı derece-gün, CONUS satırı, HDD + CDD (2001–2026).
- Fiyat: Yahoo **UNG** günlük (birincil; vade geçişinde fiyat sıçraması yok),
  **NG=F** günlük (ikincil rapor; vade geçiş sıçramaları içerir).
Dönem: 2011-01-01 → son veri. Bölme: <2022 / 2022+.

## Hipotezler
- **H1 depolama kâhini:** sürpriz = haftalık değişim − aynı ISO haftasının önceki 5 yıl
  ortalama değişimi. Sürpriz > 0 (normalden fazla stok) → short, < 0 → long.
  Giriş: haftayı izleyen Pazartesi açılış; çıkış: Perşembe kapanış (tatil: 2 gün içindeki
  ilk işlem günü).
- **H2 hava kâhini:** işlem haftası Pzt–Paz toplam CONUS (HDD+CDD); normal = her takvim
  gününün önceki 10 yıl ortalaması. Sapma > 0 (normalden fazla ısıtma/soğutma ihtiyacı) →
  long, < 0 → short. Giriş Pazartesi açılış, çıkış Cuma kapanış.

## Baz oranlar (rapor, kriter değil)
- Depolama sürprizi işaretinin bir önceki haftayla aynı olma oranı.
- Hava sapması işaretinin bir önceki haftayla aynı olma oranı (naif hava tahmini).

## Maliyet
Prop/Maven doğalgaz maliyeti ÖLÇÜLMEDİ. Maliyetsiz ve yön başı 5 bp duyarlılık satırı;
sonuç "maliyet ölçülmedi" etiketlidir.

## Geçme (UNG, maliyetsiz, her hipotez ayrı)
Ortalama > 0, isabet > %50, <2022 ve 2022+ ayrı ayrı > 0, t > 2.
Kâhin geçmezse gerçek tahmin de geçemez → veri hattı kurulmaz.
Geçerse: isabeti naif baz oran düzeyine indirip (rastgele işaret çevirme, 1000 tekrar)
ortalama getiri raporlanır; asıl soru tahminin naif tahminden iyi olup olamayacağıdır.
