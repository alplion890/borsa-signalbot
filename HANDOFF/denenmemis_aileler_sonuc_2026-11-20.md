# Sonuç: hiç test edilmemiş aileler H1–H4 (2026-11-20)

Ön-kayıt `1efb78c` (Argon istişaresiyle kesinleşti). Kod: `scripts_2026-11-20/{multi_panel,untested_families}.py`, ham: `untested_families.txt`,
`outputs/intraday/untested_families/result.json`. 15 piyasa, 2013-01-01..2026-08-28, Maven ölçülmüş maliyet, **swap ölçülmedi** (swap-free varsayımı).
Kod düzeltmesi (sonuç sonrası, kural değil): H2'de erken dönemde 0 oynaklık → sonsuz ölçek; NaN'a çevrildi.

**Sonuç: 4/4 GEÇMEDİ.**

| Test | Rol | Maliyetsiz SR | 1x SR · yıl % | p (1x) | Pozitif blok (1x) | 2x yıl % |
|---|---|---|---|---|---|---|
| H1 TSMOM (MOP 2012) | birincil | +0.37 | +0.37 · +7.6 | 0.058 (Holm eşik 0.025) | 2/4 | +7.5 |
| H2 Kesitsel momentum (AMP 2013) | birincil | +0.27 | +0.26 · +2.1 | 0.153 (eşik 0.05) | 3/4 | +2.0 |
| H3 Pairs (GGR 2006) | keşif | −0.33 | −0.34 · −1.1 | 0.905 | 1/4 | −1.1 |
| H4 ABD endeks gece MR | keşif | +0.68 | −0.48 · −4.5 | 0.941 | 2/4 | −15.3 |

Blok ortalamaları (bp/gün, 1x): H1 2013–17 +5.2 · 2018–21 −2.0 · 2022–23 −0.8 · 2024–26 +8.9; H2 +0.5 · +2.0 · −0.4 · +0.4.
H1 yıllık: 2013 +32.7, 2016 −17.3, 2017 +29.0, 2018 −18.3, 2019 −14.5, 2022 +5.2, 2023 −9.3, 2024 +28.8, 2025 +19.6 (ort. kaldıraç 3.8x).
2022'de FX + (USDJPY +5.7, GBPUSD +4.6), endeksler −; evrende tahvil/enerji yok.

Olgular:
- H1 ve H2 literatür önceli aralığında (Argon: A 0.25–0.50, B 0.10–0.35). Güç beyanı gereği "geçmedi" ≠ "edge yok"; 14 yılda SR 0.37 anlamlılık sınırının altında.
- H1/H2 maliyete duyarsız (aylık); kırılgan olan rejim: 2018–21 ve 2022–23 negatif.
- H4 maliyetsiz +0.68 SR, ölçülmüş maliyet tamamen yiyor (Argon'un ~%6/yıl tahminiyle uyumlu).
- Sonuç LIVE kuralını değiştirmez. H1 için 30 günlük payout ile uyum yok: yıllık oynaklık yüksek (yıllar ±%30).
