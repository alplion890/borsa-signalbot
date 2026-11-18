# Stop'lu portföy firma simülasyonu (2026-11-18)

Stop mesafeleri stop testinden (ön-kayıt 440d204, sonuç 3a1a707), simülasyon öncesi sabit: NB 1 ATR, BTC 21–23 1.5,
BTC gece 1.5, Ay dönümü 4, B7 4. Sweep/Donchian zaten stop'lu (%0.5 risk).
Üç boyutlama: (a) stop'suz mevcut nominal ölçekler, (b) aynı nominal + stop, (c) RİSK-BOYUTLU: her stop'lu işlem
stop mesafesine göre %0.5 risk (lot = %0.5 / (k·ATR/giriş)).
2022+ günlük, 20 gün blok bootstrap 500 yol × 365 gün, seed 20261118. B7 günlük piyasa değeri + swap; diğerleri gün içi dip = kayıp × 1.5.
Açık risk "üst sınır" = aynı gün açılan işlemlerin stop risk toplamı (gün içi işlemler çakışmayabilir → abartır).
FXIFY Instant varsayımları (resmi sayfada yok): fiyat bilinmiyor → ÜCRET HARİÇ; kâr payı %80; 14 günde bir ödeme,
%4 tampon bırakılarak (ödeme sonrası limit başlangıç bakiyesinde kilitlenir). FXIFY swap-free hesap sunmuyor.

```
RISK-BOYUTLU acik risk ust sinir: 6li max %3.50 >%3 gun %1.5 | +B7 max %4.00 >%3 gun %4.0
ACIK RISK ust sinir (gun ici ayni gun toplami), risk x1: 6li max %14.07 >%3 gun %46.4 | +B7k4 max %18.35 >%3 gun %55.6
6li stop'suz: yil% 18.1 sharpe 1.48 en kotu gun(stres) %-4.99
6li stop'lu: yil% 17.7 sharpe 1.45 en kotu gun(stres) %-4.03
6li+B7 0.35x stop'suz: yil% 21.8 sharpe 1.53 en kotu gun(stres) %-6.17
6li+B7 0.35x stop'lu(k4): yil% 20.6 sharpe 1.46 en kotu gun(stres) %-4.78
6li RISK-BOYUTLU stop'lu: yil% 12.6 sharpe 1.47 en kotu gun(stres) %-2.23
6li+B7 RISK-BOYUTLU stop'lu: yil% 13.1 sharpe 1.50 en kotu gun(stres) %-2.29

=== FN_INSTANT 5K $149.99
 x1.0 6li stop'suz: ilk payout med 16g (yok %0) | 12ay net med $202 zarar %27 | hesap ort 4.4
 x1.0 6li stop'lu: ilk payout med 17g (yok %0) | 12ay net med $203 zarar %27 | hesap ort 4.3
 x1.0 6li+B7 0.35x stop'suz: ilk payout med 14g (yok %0) | 12ay net med $236 zarar %26 | hesap ort 5.5
 x1.0 6li+B7 0.35x stop'lu(k4): ilk payout med 15g (yok %0) | 12ay net med $208 zarar %28 | hesap ort 5.4
 x1.0 6li RISK-BOYUTLU stop'lu: ilk payout med 22g (yok %0) | 12ay net med $172 zarar %22 | hesap ort 2.4
 x1.0 6li+B7 RISK-BOYUTLU stop'lu: ilk payout med 21g (yok %0) | 12ay net med $188 zarar %21 | hesap ort 2.4
 x1.0 SIFIR-EDGE (6li+B7 risk-boyutlu): ilk payout med 33g (yok %1) | 12ay net med $-184 zarar %75 | hesap ort 3.1
 x0.5 6li stop'suz: ilk payout med 24g (yok %0) | 12ay net med $131 zarar %20 | hesap ort 1.5
 x0.5 6li stop'lu: ilk payout med 25g (yok %0) | 12ay net med $131 zarar %20 | hesap ort 1.4
 x0.5 6li+B7 0.35x stop'suz: ilk payout med 21g (yok %0) | 12ay net med $182 zarar %17 | hesap ort 1.9
 x0.5 6li+B7 0.35x stop'lu(k4): ilk payout med 22g (yok %0) | 12ay net med $169 zarar %19 | hesap ort 1.8
 x0.5 6li RISK-BOYUTLU stop'lu: ilk payout med 41g (yok %2) | 12ay net med $55 zarar %31 | hesap ort 1.1
 x0.5 6li+B7 RISK-BOYUTLU stop'lu: ilk payout med 38g (yok %1) | 12ay net med $69 zarar %29 | hesap ort 1.1
 x0.5 SIFIR-EDGE (6li+B7 risk-boyutlu): ilk payout med 48g (yok %18) | 12ay net med $-113 zarar %79 | hesap ort 1.3

=== FXIFY Instant 5K (ucret HARIC, split %80 varsayim)
 x1.0 6li stop'suz: ilk payout med 68g (yok %0) | 12ay net med $692 zarar %0 | hesap ort 2.6
 x1.0 6li stop'lu: ilk payout med 70g (yok %0) | 12ay net med $672 zarar %0 | hesap ort 2.5
 x1.0 6li+B7 0.35x stop'suz: ilk payout med 56g (yok %0) | 12ay net med $886 zarar %0 | hesap ort 3.4
 x1.0 6li+B7 0.35x stop'lu(k4): ilk payout med 56g (yok %0) | 12ay net med $807 zarar %0 | hesap ort 3.3
 x1.0 6li RISK-BOYUTLU stop'lu: ilk payout med 98g (yok %4) | 12ay net med $384 zarar %0 | hesap ort 1.6
 x1.0 6li+B7 RISK-BOYUTLU stop'lu: ilk payout med 98g (yok %4) | 12ay net med $398 zarar %0 | hesap ort 1.6
 x1.0 SIFIR-EDGE (6li+B7 risk-boyutlu): ilk payout med 126g (yok %30) | 12ay net med $81 zarar %0 | hesap ort 2.2
 x0.5 6li stop'suz: ilk payout med 126g (yok %8) | 12ay net med $248 zarar %0 | hesap ort 1.3
 x0.5 6li stop'lu: ilk payout med 126g (yok %8) | 12ay net med $230 zarar %0 | hesap ort 1.3
 x0.5 6li+B7 0.35x stop'suz: ilk payout med 98g (yok %3) | 12ay net med $330 zarar %0 | hesap ort 1.5
 x0.5 6li+B7 0.35x stop'lu(k4): ilk payout med 112g (yok %4) | 12ay net med $309 zarar %0 | hesap ort 1.5
 x0.5 6li RISK-BOYUTLU stop'lu: ilk payout med 168g (yok %21) | 12ay net med $111 zarar %0 | hesap ort 1.0
 x0.5 6li+B7 RISK-BOYUTLU stop'lu: ilk payout med 168g (yok %19) | 12ay net med $119 zarar %0 | hesap ort 1.0
 x0.5 SIFIR-EDGE (6li+B7 risk-boyutlu): ilk payout med 210g (yok %70) | 12ay net med $0 zarar %0 | hesap ort 1.1

[exited with code 0]
```
