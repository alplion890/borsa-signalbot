# Discretionary Trade Checklist — ICT/SMC/Orderflow

> Seans sırasında aç, gir. 6 mekanik modül TUTMADIĞINDA bakılır.
> Mekanik tetikliyorsa bu dosyayı açma — direkt mekanik trade.
> **Funded fazda bu tamamen KAPALI (gerçek para, tutarlılık kuralı riski).
> Sadece challenge'da serbest — hesap canlı değil, patlarsa $5'e yenisi.**

---

## Saatler — senin için (işten 18:00'de çıkıyorsun, TR saati)

| Seans | TR saati | Durum | Ne yapılır |
|---|---|---|---|
| Londra killzone | 10:00-13:00 | İşte, kaçar | — |
| NY açılış / ORB | 16:30 | İşte, kaçar | mekanik giriş canlı yakalanmaz |
| NY AM killzone | 15:30-18:00 | İşte, kaçar | — |
| **NY PM seansı** | **18:00-22:00** | **Müsait ✅** | **senin ana pencere** |

**Pratik plan:**
- Ana pencere: akşam **18:00-22:00** NY PM. Sembol: NQ/US100, XAUUSD.
- Bu saatte confluence ararız; kapı geçerse discretionary trade.
- 22:00'den sonra likidite düşer, momentum biter → yeni giriş yok.
- Sabah işe gitmeden 5 dk: morning_brief + günlük bias oku, aklında tut.
- Mekanik ORB modülleri (Gold/NQ) gündüz tetikliyor — onlar bot/forward
  EA işi, canlı elle yakalamana gerek yok. Sen akşam discretionary'ye bak.

---

## 0. Ön koşul (bunlar YOKSA dur)

- [ ] 6 mekanik modülden hiçbiri tetiklemedi
- [ ] Challenge fazdayım (funded'da DEĞİLİM — funded'da sadece mekanik)
- [ ] Ana pencere içindeyim: NY PM 18:00-22:00 TR (senin müsait saatin)
- [ ] Bugün discretionary günlük kayıp limitine ULAŞMADIM

Biri bile ✗ → **TRADE YOK.** Dosyayı kapat.

---

## 1. HTF Bias (yön) — 1 katman

- [ ] Günlük / 4H yön belli mi? (HH-HL = long bias, LH-LL = short bias)
- [ ] morning_brief / günlük bias notu ile aynı yönde miyim?
- [ ] Karşı yönde büyük HTF likidite havuzu (PDH/PDL) önümde DEĞİL

Yön net değilse → dur. Range ortasında trade yok.

---

## 2. Session / Killzone — 1 katman

- [ ] Killzone içindeyim (yukarıdaki saatler)
- [ ] Asya range'i / önceki seans likiditesi süpürüldü mü?
- [ ] Haber saatine 15 dk'dan yakın DEĞİLİM (yüksek etkili)

---

## 3. ICT / SMC yapısı — 1 katman (en az 2 madde ✓)

**ÖNCE REJİM SORUSU (2026-07-07 dersi, playbook kural #1):**
- [ ] Bugün range mi trend mi belirledim? (ADX / VWAP eğimi / gap / displacement)
- Range günü → sweep-REVERSAL: reclaim + absorption sonrası limit retest
- Trend günü → sweep-CONTINUATION: retest BEKLEME, FVG'de market / kırılımda stop-entry
- Trend gününde reversal-retest kurmak YASAK (XAUUSD 07-07: fiyat dönmedi, 0R)

- [ ] Likidite süpürme (sweep) oldu — eski dip/tepe alındı
- [ ] CHoCH / BOS — yapı bias yönüne kırıldı
- [ ] FVG / order block var ve fiyat oraya dönüyor (giriş bölgesi)
- [ ] Premium/discount doğru: long'da discount, short'ta premium

---

## 4. Orderflow teyidi — 1 katman

- [ ] CVD / delta yön ile UYUMLU (long'da alıcı baskısı, short'ta satıcı)
- [ ] Absorption / imbalance giriş bölgesini destekliyor
- [ ] Momentum karşı tarafta tükenmiş (divergence)

---

## CONFLUENCE KAPISI

**Bölüm 1-2-3-4'ten en az 3 tanesi tam ✓ olmalı.**

- 3+ bölüm ✓ → geçebilir
- 2 veya az → **TRADE YOK**

---

## 5. Risk & emir (girmeden önce son kontrol)

- [ ] Risk ≤ %0.25 (mekanikten küçük, ayrı kova)
- [ ] SL yapısal yerde (sweep dibi / OB arkası) — keyfi değil
- [ ] TP en yakın karşı likiditede, RR ≥ 2
- [ ] Pozisyon boyutu SL mesafesine göre hesaplandı
- [ ] Martingale yok (kaybedene ekleme yok)

---

## 6. Trade sonrası — LOG (zorunlu)

Her discretionary trade'i kaydet. 30-50 trade sonra expectancy çıkar.
Edge yoksa katmanı kes.

| Tarih | Sembol | Yön | Bias | Session | SMC yapı | OF | RR | Sonuç (R) | Not |
|---|---|---|---|---|---|---|---|---|---|

---

**Hatırlatma:** "structure gördüm" = istatistiksel edge DEĞİL. Mekanik 6
modül her zaman önce. Bu katman kanıtlanana kadar ikinci sınıf.
