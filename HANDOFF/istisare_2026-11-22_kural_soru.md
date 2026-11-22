# Görev: ön-kayıt için kesin, kodlanabilir kural tanımları (veriye bakılmadan)

Bir perakende futures araştırma projesi, sonuç görülmeden önce kuralları sabitleyip (ön-kayıt) tek seferde test edecek.
Senden istenen: aşağıdaki her aile için **literatürde veya yaygın pratisyen kaynaklarında (ATAS, Sierra Chart,
Jigsaw, Axia Futures, Trader Dale, akademik makaleler) en yaygın tanıma en yakın**, tek parametre setli, kodlanabilir kural.
Parametre taraması yapılmayacak; her kural için TEK eşik seti ver ve kaynağını yaz. Kaynak yoksa "kaynak yok, makul varsayılan" yaz.

## Veri (ne var)
- CME NQ (E-mini Nasdaq) `trades` şeması: her işlem için ts_event (ns), price, size, side (A = satıcı agresör,
  B = alıcı agresör). 2026-03-01 – 2026-11-19 (~8.5 ay). Tick 0.25 puan.
- CME NQ `mbo` (emir bazlı, order_id, add/cancel/modify/fill) yalnız 10 işlem günü (2026-10-05 – 10-16).
- CME 1m OHLCV NQ/ES 2010–2026; günlük OHLCV v.0 (hacim sıralı önay) CL, ZN, 6E 2010–2026; 1h OHLCV CL/ZN/6E.
- Ölçülmüş maliyet/yön (yarım spread + $0.61 komisyon): MNQ 0.555 puan, MES 0.247 puan.
- İcra gecikmesi: Türkiye ev interneti, ~150 ms varsay. İşlemler 1 kontrat; RTH 09:30–16:00 NY.

## Aileler
1. **Footprint emilim (absorption)** — agresif hacim yüksek ama fiyat ilerlemiyor → ters yöne işlem. Bar boyu,
   hacim eşiği (ne ile normalize), "ilerlemiyor" tanımı, yön, giriş zamanı/fiyatı, stop, hedef/çıkış süresi.
2. **Stacked imbalance (üst üste dengesizlik)** — diyagonal karşılaştırma (ask hacmi fiyat p vs bid hacmi p−1 tick),
   oran eşiği, kaç ardışık seviye, minimum hacim, yön (devam mı destek/direnç mi), giriş/çıkış/stop.
3. **Delta sapması (delta divergence)** — fiyat yeni N dakikalık tepe/dip yaparken bar delta'sı ters işaretli
   veya önceki tepeden küçük. N, bar boyu, giriş/çıkış/stop.
4. **Iceberg / tekrar dolan limit (refill)** — MBO'dan tespit: aynı fiyatta görünür miktardan fazla dolum veya
   iptal/ekleme ile yenilenme. Sadece 10 gün var; bunu **test mi yoksa sadece betimleme mi** yapmak gerektiğini söyle.
5. **Opex** — aylık opsiyon vadesi (her ayın 3. Cuma'sı) etrafında ES/NQ getirisi. Literatürdeki tanım
   (ör. Stivers & Sun opex haftası, opex günü/pinning). Kesin giriş/çıkış günü ve saati.
6. **IBS ve Donchian'ın başka varlıklara taşınması** — CL, ZN, 6E. IBS = (C−L)/(H−L) günlük. Literatürde IBS'in
   emtia/tahvil/döviz vadelilerinde çalışıp çalışmadığı (kaynak). Donchian 20 kırılımı 1h.

## Her kural için istenen format
- Ad, kaynak (yazar/yıl veya site), tanım (formül), eşik(ler), yön, giriş (zaman + fiyat), çıkış, stop, günde en fazla işlem.
- Beklenen işlem sıklığı (kabaca, gün/ay başına), örneklem yeterli mi?
- Bilinen tuzaklar (look-ahead, bar içi sıra, kuyruk iyimserliği, roll).

Sonuç görmeden yazıyoruz; "veriye bakıp ayarla" önerme. Sayı uydurma; bilmiyorsan söyle.
