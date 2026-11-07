# 14 günlük icra denemesi — ön-kayıt (2026-11-07)

Kullanıcı kararı: Maven hesabında 14 gün boyunca işlemleri KENDİ açacak (PC veya telefon).
Amaç **edge ölçmek değil, icrayı ölçmek**: sinyal gelince işlem doğru ve zamanında açılabiliyor mu.
14 günde ~3–8 işlem beklenir; R sonucu raporlanır ama karar ölçütü değildir (küçük örneklem).
Eski kural ile uyumlu: [[Borsa - Karar Kurali (baslama ve durma)]] — "ilk 10 işlemde sadece icra ölçülür".

## Dönem
2026-11-09 Pazartesi 00:00 TR → 2026-11-22 Pazar 23:59 TR.

## Enstrümanlar ve kurallar (tek kural / enstrüman, yorum yok)
1. **US100 (Nasdaq)** — SWEEP_CORE sinyali. Kaynak: bot Telegram alarmı; Maven grafiğinde doğrula.
   Giriş = sinyal fiyatı civarı, SL ve TP = alarmdaki değerler.
2. **XAUUSD (Altın)** — Donchian N20, 1 saatlik mum: kapanış önceki 20 mumun en yükseğini
   yukarı keserse long (en düşüğünü aşağı keserse short); SL = karşı kanal, TP = 2R; en fazla 200 mum.
   (Uzun geçmiş n848, +0.083R; 3× maliyette +0.039R. Mevcut forward'da ölçülmüyor.)

## Risk
Her işlemde sabit risk = hesap bakiyesinin %0.5'i (bakiye kullanıcıdan teyit edilecek). Aynı anda en fazla 1 pozisyon.
Lot hesabı: risk$ / (giriş−SL mesafesi × puan değeri). Kullanıcı isterse Claude hesaplar; emri kullanıcı basar.

## Ölçüm (14. gün, MT5 geçmişinden — kullanıcıdan ayrıca kayıt istenmez)
Kaynak: Maven MT5 işlem geçmişi (deals) + bot sinyal kaydı + forward defter.
1. **Alım oranı:** kullanıcının müsait olduğu saatlerdeki sinyallerin kaçı ≤10 dk içinde açıldı.
2. **Gecikme:** sinyal → giriş dakika; **kayma:** giriş fiyatı − sinyal fiyatı (puan ve R).
3. **Kural uyumu:** SL girildi mi (hedef %100), TP kurala uygun mu, lot planlanan riskin ±%20'si içinde mi.
4. **Kural dışı işlem sayısı:** sinyalsiz/içgüdüsel işlem (hedef 0).
5. **R sonucu:** yalnız raporlanır.

## "Başarılı icra" eşiği (önceden)
Alım oranı ≥ %80 **ve** SL %100 **ve** risk sapması ≤ ±%20 işlemlerin ≥ %80'inde **ve** kural dışı işlem = 0.
Eşik sağlanırsa instant/prop hesabı değerlendirilir (karar kullanıcıda). Sağlanmazsa sebep ölçülür
(kaçırılan saat, telefon/PC, dikkat) ve plan değiştirilir — R sonucuna bakılarak değil.

## Yasak
14 gün içinde kural, enstrüman veya risk değiştirmek; kaybeden işlemden sonra risk büyütmek.

## Ek (2026-11-07, deneme başlamadan önce — kural değişikliği değil, altyapı)
- Alarmların tek kaynağı Maven MT5 (yerel forward EA). Bulut Sweep alarmı 2026-11-09..22 arası kuru çalışır (`continuous_scan._trial_local_only`).
- XAU Donchian `CAND_DONCHIAN_XAU_1H` olarak Maven forward'da ölçülür ve yalnız deneme penceresinde Telegram'a "ICRA DENEMESI" kartıyla çıkar (`notify.TRIAL_ALERT_MODULES`). Gecikme: 1H mum kapanışı + en çok 5 dk.
- Alarm yalnız PC + MT5 (Maven hesabı) açıkken çalışır.
