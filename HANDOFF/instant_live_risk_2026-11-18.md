# Instant funding risk simülasyonu: 6'lı + B7 (+B2), 2026-11-18

Kullanıcı kararı: LIVE + doğrudan instant hesap. Bu dosya yalnız risk sayılarıdır, öneri değildir.
Yöntem: 2022+ günlük portföy, 20 gün blok bootstrap 500 yol × 365 gün, seed 20261118, patlayınca yeniden alım.
B7 günlük piyasa değeriyle (close-to-close + gün içi low dibi, swap −1.18bp/gece, maliyet giriş/çıkış günü);
diğer modüllerde gün içi dip = günlük kayıp × 1.5 (stres). B2 swaplı (−%30/yıl) ve 0.5×.
B7 (1× nominal): en kötü gün −%6.3 (2026-11-05, gerçek NQ düşüşü), equity maxDD −%17.4, günlerin %38'inde pozisyonda.
Firma kuralları firms.py (2026-11-18 resmi sayfalar); FN Instant payout kuralı yaklaşık modellendi (doğrulanmadı).
"risk x" = 6'lı portföyün funded risk çarpanı. Ham çıktı aşağıda.

```

=== FN_INSTANT 5K $149.99 ===
 risk x1.0 6li: ilkpayout-oncesi-patlama %9 | payout med 17g (1 yilda hic payout yok %0) | 12ay net med $203 zarar %26 | alinan hesap ort 4.4
 risk x1.0 6li+B7 0.2x: ilkpayout-oncesi-patlama %12 | payout med 15g (1 yilda hic payout yok %0) | 12ay net med $230 zarar %25 | alinan hesap ort 4.9
 risk x1.0 6li+B7 0.35x: ilkpayout-oncesi-patlama %13 | payout med 14g (1 yilda hic payout yok %0) | 12ay net med $229 zarar %27 | alinan hesap ort 5.6
 risk x1.0 6li+B7 0.5x: ilkpayout-oncesi-patlama %13 | payout med 14g (1 yilda hic payout yok %0) | 12ay net med $196 zarar %31 | alinan hesap ort 6.5
 risk x1.0 6li+B7 0.35x+B2(swapli): ilkpayout-oncesi-patlama %21 | payout med 15g (1 yilda hic payout yok %0) | 12ay net med $69 zarar %42 | alinan hesap ort 7.6
 risk x1.0 SIFIR-EDGE kontrol (6li+B7+B2): ilkpayout-oncesi-patlama %32 | payout med 20g (1 yilda hic payout yok %0) | 12ay net med $-515 zarar %85 | alinan hesap ort 8.7
 risk x0.5 6li: ilkpayout-oncesi-patlama %3 | payout med 24g (1 yilda hic payout yok %0) | 12ay net med $135 zarar %20 | alinan hesap ort 1.5
 risk x0.5 6li+B7 0.2x: ilkpayout-oncesi-patlama %3 | payout med 23g (1 yilda hic payout yok %0) | 12ay net med $164 zarar %18 | alinan hesap ort 1.6
 risk x0.5 6li+B7 0.35x: ilkpayout-oncesi-patlama %4 | payout med 22g (1 yilda hic payout yok %0) | 12ay net med $179 zarar %18 | alinan hesap ort 1.9
 risk x0.5 6li+B7 0.5x: ilkpayout-oncesi-patlama %5 | payout med 20g (1 yilda hic payout yok %0) | 12ay net med $190 zarar %18 | alinan hesap ort 2.1
 risk x0.5 6li+B7 0.35x+B2(swapli): ilkpayout-oncesi-patlama %7 | payout med 20g (1 yilda hic payout yok %0) | 12ay net med $122 zarar %30 | alinan hesap ort 2.6
 risk x0.5 SIFIR-EDGE kontrol (6li+B7+B2): ilkpayout-oncesi-patlama %23 | payout med 30g (1 yilda hic payout yok %1) | 12ay net med $-188 zarar %78 | alinan hesap ort 3.2

=== FYFX_INST 5K $39.6 ===
 risk x1.0 6li: ilkpayout-oncesi-patlama %14 | payout med 34g (1 yilda hic payout yok %0) | 12ay net med $502 zarar %1 | alinan hesap ort 2.2
 risk x1.0 6li+B7 0.2x: ilkpayout-oncesi-patlama %15 | payout med 31g (1 yilda hic payout yok %0) | 12ay net med $584 zarar %0 | alinan hesap ort 2.4
 risk x1.0 6li+B7 0.35x: ilkpayout-oncesi-patlama %15 | payout med 28g (1 yilda hic payout yok %0) | 12ay net med $669 zarar %0 | alinan hesap ort 2.7
 risk x1.0 6li+B7 0.5x: ilkpayout-oncesi-patlama %17 | payout med 25g (1 yilda hic payout yok %0) | 12ay net med $746 zarar %0 | alinan hesap ort 3.2
 risk x1.0 6li+B7 0.35x+B2(swapli): ilkpayout-oncesi-patlama %25 | payout med 24g (1 yilda hic payout yok %0) | 12ay net med $785 zarar %0 | alinan hesap ort 4.5
 risk x1.0 SIFIR-EDGE kontrol (6li+B7+B2): ilkpayout-oncesi-patlama %40 | payout med 34g (1 yilda hic payout yok %0) | 12ay net med $419 zarar %5 | alinan hesap ort 5.9
 risk x0.5 6li: ilkpayout-oncesi-patlama %3 | payout med 75g (1 yilda hic payout yok %2) | 12ay net med $196 zarar %3 | alinan hesap ort 1.1
 risk x0.5 6li+B7 0.2x: ilkpayout-oncesi-patlama %4 | payout med 70g (1 yilda hic payout yok %1) | 12ay net med $210 zarar %2 | alinan hesap ort 1.1
 risk x0.5 6li+B7 0.35x: ilkpayout-oncesi-patlama %5 | payout med 65g (1 yilda hic payout yok %1) | 12ay net med $261 zarar %2 | alinan hesap ort 1.2
 risk x0.5 6li+B7 0.5x: ilkpayout-oncesi-patlama %7 | payout med 58g (1 yilda hic payout yok %1) | 12ay net med $285 zarar %2 | alinan hesap ort 1.3
 risk x0.5 6li+B7 0.35x+B2(swapli): ilkpayout-oncesi-patlama %10 | payout med 57g (1 yilda hic payout yok %1) | 12ay net med $282 zarar %2 | alinan hesap ort 1.4
 risk x0.5 SIFIR-EDGE kontrol (6li+B7+B2): ilkpayout-oncesi-patlama %36 | payout med 90g (1 yilda hic payout yok %13) | 12ay net med $83 zarar %27 | alinan hesap ort 2.0

=== MAVEN_INST 5K $18.05 ===
 risk x1.0 6li: ilkpayout-oncesi-patlama %86 | payout med 150g (1 yilda hic payout yok %31) | 12ay net med $234 zarar %31 | alinan hesap ort 8.4
 risk x1.0 6li+B7 0.2x: ilkpayout-oncesi-patlama %85 | payout med 140g (1 yilda hic payout yok %28) | 12ay net med $241 zarar %29 | alinan hesap ort 9.6
 risk x1.0 6li+B7 0.35x: ilkpayout-oncesi-patlama %86 | payout med 142g (1 yilda hic payout yok %29) | 12ay net med $220 zarar %31 | alinan hesap ort 11.8
 risk x1.0 6li+B7 0.5x: ilkpayout-oncesi-patlama %90 | payout med 142g (1 yilda hic payout yok %34) | 12ay net med $133 zarar %38 | alinan hesap ort 14.8
 risk x1.0 6li+B7 0.35x+B2(swapli): ilkpayout-oncesi-patlama %94 | payout med 151g (1 yilda hic payout yok %44) | 12ay net med $-70 zarar %56 | alinan hesap ort 18.9
 risk x1.0 SIFIR-EDGE kontrol (6li+B7+B2): ilkpayout-oncesi-patlama %99 | payout med 189g (1 yilda hic payout yok %81) | 12ay net med $-379 zarar %87 | alinan hesap ort 21.3
 risk x0.5 6li: ilkpayout-oncesi-patlama %43 | payout med 160g (1 yilda hic payout yok %23) | 12ay net med $257 zarar %23 | alinan hesap ort 2.3
 risk x0.5 6li+B7 0.2x: ilkpayout-oncesi-patlama %42 | payout med 148g (1 yilda hic payout yok %18) | 12ay net med $290 zarar %18 | alinan hesap ort 2.4
 risk x0.5 6li+B7 0.35x: ilkpayout-oncesi-patlama %45 | payout med 143g (1 yilda hic payout yok %17) | 12ay net med $313 zarar %17 | alinan hesap ort 2.7
 risk x0.5 6li+B7 0.5x: ilkpayout-oncesi-patlama %49 | payout med 149g (1 yilda hic payout yok %18) | 12ay net med $327 zarar %18 | alinan hesap ort 3.1
 risk x0.5 6li+B7 0.35x+B2(swapli): ilkpayout-oncesi-patlama %67 | payout med 147g (1 yilda hic payout yok %20) | 12ay net med $263 zarar %21 | alinan hesap ort 4.4
 risk x0.5 SIFIR-EDGE kontrol (6li+B7+B2): ilkpayout-oncesi-patlama %88 | payout med 196g (1 yilda hic payout yok %64) | 12ay net med $-72 zarar %66 | alinan hesap ort 6.0

[exited with code 0]
```

Not: FYFX sıfır-edge kontrolü pozitif çıkıyor (ucuz yeniden alım + düşük eşik) → model bu firmayı güvenilir ölçmüyor.
