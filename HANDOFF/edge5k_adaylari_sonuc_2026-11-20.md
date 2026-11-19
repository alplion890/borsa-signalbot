# Sonuç: derin tarama adayları C1–C8 (2026-11-20)

Ön-kayıt: `HANDOFF/edge5k_adaylari_onkayit_2026-11-20.md` (b3bf8ef). Kod: `strategy-lab/intraday/edge5k_adaylari.py`
(Antigravity yazdı, Claude denetledi: C6 limit dolumu, C8 aynı-gün şartı, veri sonu sınır hatası düzeltildi; 10 birim testi).
Maliyet: Maven reality_profile 2026-11-12 (merkez), swap 0.000118/gece. Bonferroni 0.05/16. Tüm paket 777 passed.

**16/16 GEÇMEDİ.** bp/işlem maliyetsiz / merkez / 2× [merkez CI], yıllık işlem:
- C1 ay sonu rebalans: SP +20/+17/+14 [-24,60], NQ +11/+9/+7 [-42,62]; 11.7/yıl; 4–6 gece (hafta sonu dahil).
- C2 tatil öncesi long: SP +12/+9/+6 [-10,27], NQ +14/+12/+10 [-12,37]; 9.3/yıl; 1 gece.
- C3 3. Cuma settlement (4 test): merkez -3..-5 bp; 11.4/yıl.
- C4 VIX contango günü long: SP +2.0/-1.2/-4.4, NQ +2.9/+0.7/-1.6; şart FAIL (sinyalsiz günler 12.8/18.1 bp daha iyi).
- C5 VIX backwardation filtresi NB: filtre değeri -10/-8/-6 → atlanacak NB işlemleri kârlı; filtre zarar.
- C6 küçük boşluk doldurma: NQ -0.6/-2.8/-5.0 [-4.0,-1.6], SP -0.2/-3.3/-6.5; 60/yıl. İşlemlerin %54'ü girişte hedef
  zaten geçilmiş (0 getiri); onlar hariç tutulsa da maliyetsiz ~-1.2 bp (tanı, karar değil).
- C7 boşluk fade her gün: NQ -0.4/-2.6/-4.8, SP +0.1/-3.1/-6.3; ~245/yıl.
- C8 altın Asya long: +1.2/-1.5/-4.2; 258/yıl; baz oran şartı geçti ama maliyet sonrası negatif.

**Prop aşaması:** ön-kayıt gereği yalnız geçenler portföye eklenip firmalarda simüle edilir → eklenen yok.
Firma kuralı açısından (bilgi için): C1 hafta sonu taşır (IF Evolve, FTM gibi hafta sonu yasaklı firmalarda elenir)
ve stopsuzdur (FN %3 anlık risk kuralı stop ister). C2/C3 tek gece. Sık ve gün içi olanlar (C4, C6, C7, C8)
prop şekline uyuyordu ama maliyet öncesi ~0.
Katalog: `edge5k_c1_c8` (rejected).
