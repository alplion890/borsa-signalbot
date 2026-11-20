# Sonuç: ucuz hesapta boyutlama/kapı yöntemleri (2026-11-20)

Ön-kayıt: `ucuz_hesap_boyutlama_onkayit_2026-11-20.md` (d01912b). Kod: `scripts_2026-11-20/cheap_sizing.py`
(yalnız commit'li strategy-lab modüllerine bağlı; eski `firms.py` scratchpad'de silinmişti → 11-18/11-19 scriptlerinin
16'sı yeniden üretilemiyor). Ham çıktı: `cheap_sizing.txt`, `cheap_sizing_results.csv`. 300 yol × 260 iş günü, 20 gün blok.
Maliyet: Maven ölçülmüş merkez (FN maliyeti ÖLÇÜLMEDİ). Tek hesap, yeniden alım yok.

## Ön-kayıttan sapma (açıkça)
- Sıfır-edge kontrolü ilk koşuda tüm 2013–2026 ortalamasıyla arındırıldı → Sweep 2022 öncesi negatif olduğu için 2022+ "sıfır-edge"
  serisine pozitif kayma ekledi (sıfır-edge gerçekten iyi çıktı). Düzeltme: arındırma test edilen rejimin kendi içinde. Eşik/yöntem değişmedi.
- Kural 2'nin "2x maliyette en kötü blok ≥ −ücret" şartı tek hesap/yeniden alımsız tasarımda her zaman sağlanır (kayıp ücretle sınırlı) → bilgi taşımıyor.

## Bağımsız kontrolde çıkan olgular
1. Bugünkü NQ fiyatıyla (27.757) 0.01 lot NB riski: 2K'da medyan %2.19 (p90 %3.87) → %0.5–1 riskte NB **hiç açılmaz**, %1.5'te %7.
   5K'da medyan %0.87 (≤%1: %60), 6K'da %0.73 (≤%1: %74). Önceki "%1.49" eski fiyat seviyesinden.
2. Modül ortalama R (Maven ölçülmüş maliyet, NB k1 / BTC k1.5 stop'lu):

| Modül | 2013–17 | 2018–21 | 2022–23 | 2024–26 |
|---|---|---|---|---|
| SWEEP | −0.81 (n52) | −0.81 (n91) | +0.37 (n35) | +0.89 (n52) |
| NB | +0.001 | +0.016 | +0.037 | +0.002 |
| BTC 21–23 | +0.039 | +0.008 | −0.004 | +0.004 |

   Prop hesabında getiri neredeyse tamamen Sweep 2022+ (87 işlem) üzerinden geliyor. NB ve BTC stop'lu + ölçülmüş maliyetle ~0.

## Sonuç (1x maliyet; 12 ay net ortalama $, tek hesap)
- Ön-kayıt kural 1 (sıfır-edge 2022+ > 0 → piyango): I2K F1.0, F1.5, B1.0, B1.5 elendi. Challenge'ların hiçbiri piyango değil.
- Kural 2 (en kötü rejim bloğu maximin): **hiçbir yöntem/firma en kötü blokta pozitif değil**. 2013–2021 bloklarında hepsi ücretin
  çoğunu kaybediyor (−$21..−$44). Sıralama pratikte ücret sıralaması: L5K BT1.5 −26, S2_6K BT1.5 −30, I2K F0.5 −34.
- Sağlam (rejimden bağımsız) çıkan TEK etki: **tampon orantılı risk (B)** patlamayı düşürüyor, kârı değil:
  I2K F0.5 patlama 2013–17 %38 / 2018–21 %67 → B0.5 %0 / %0; S2_6K B1.0 3/4 blokta %0. Sıfır-edge bundan kazanmıyor.
- ≤30 gün payout: yalnız I2K (2022+ %25–26, B0.5/F0.5); sıfır-edge de 14 günlük ≥%1 eşiğinden payout alabiliyor.
  Challenge'larda 90 günde payout olasılığı %0–12.

| Firma · yöntem | 2013–17 | 2018–21 | 2022–23 | 2024–26 | patlama 2022+ | p30 | p90 |
|---|---|---|---|---|---|---|---|
| I2K F0.5 | −26 | −34 | +25 | +81 | %2 | .26 | .57 |
| I2K B0.5 | −28 | −36 | +13 | +65 | %0 | .25 | .54 |
| L5K BT1.5 | −21 | −26 | +64 | +326 | %30 | 0 | .03 |
| S2_6K B1.0 | −25 | −35 | +77 | +193 | %0 | 0 | .01 |
| S1_6K BT1.0 | −39 | −44 | +103 | +243 | %31 | 0 | .05 |

Yorum yok; karar kullanıcıda. Bu sonuç LIVE kuralını veya riski değiştirmez.

## Ek: Argon fikri #4 "kâr merdiveni" (R) — ek ön-kayıt addd658
2022+ (1x): S2_6K R1.0 net +$111 patlama %16 (B1.0: +$106, %0); L5K R1.0 +$73 %44 (B1.0 +$69 %22); S1_6K R1.0 +$55 %74 (B1.0 +$125 %34);
I2K R1.0 piyango (sıfır-edge +$13). En kötü blokta hiçbiri pozitif değil. Merdiven aynı nete daha yüksek patlamayla ulaşıyor.

## İstişare (Gemini 4 Argon, high) — kıyas
| Konu | Claude | Argon | Sonuç |
|---|---|---|---|
| ≤30 gün + piyangosuzluk | Challenge'larda p30 ≈ 0 (ölçüldü) | Sharpe 1.5 × √(1/12) ≈ 0.43σ; kaldıraçtan bağımsız → uyumsuz | Aynı. 30 gün şartı esneyen kısıt |
| 6K'da NB lot riski | %0.73 medyan (bugünkü fiyat 27.757) | %0.49 (eski fiyat) | Argon'un sayısı eski fiyattan |
| 2K granülerlik kapısı | NB 2K'da ≤%1'de %0 açılır → I2K ≈ Sweep+BTC | Kapıyla NB/XAU'nun "dar stoplu" kısmı geçer | Bugünkü fiyatta geçen NB işlemi yok |
| Rejim testi | 2013–2021 dahil: Sweep −0.81R, her yöntem eksi | Yalnız 2022–2026 yılları | Argon'un eşikleri 2022+ verisinde geçer, 2022 öncesinde kalır |
| Felaket stopu + yeniden giriş (#3) | Önceki stop testi: B7'ye her mesafede zarar | Önerdi | Daha önce yanlışlandı, tekrar test edilmedi |
| İki hesaba modül bölme (#5) | Test edilmedi (gece modülleri bu motorda yok; FN "farklı strateji/EA" şartı yazılı teyit ister) | Önerdi | Açık |
| Tampon orantılı risk (B) | Patlamayı 2022 öncesi bloklarda %38–67 → %0'a indiriyor | — (ters yönlü merdiven önerdi) | Rejimden bağımsız çıkan tek etki; kârı artırmıyor |
