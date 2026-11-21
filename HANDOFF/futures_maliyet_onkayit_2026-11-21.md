# Ön-kayıt: CFD maliyetine yenilen iki kural vadeli (CME) maliyetiyle (2026-11-21)

Bu dosya `futures_cost_retest.py` gerçek veride çalışmadan ÖNCE commit edilir. Kural, eşik, maliyet yöntemi değişmez.

## Neden ve DÜRÜST ETİKET
Futures prop firmaları CME mikro vadelileri (MNQ/MES) verir; maliyet CFD'den çok küçük.
İki kural Dukascopy CFD verisinde **brüt pozitif** çıkıp yalnız Maven CFD maliyetine yenilmişti:
- Noise Band SP500 (2026-11-17, 6537c91): maliyetsiz +2.37 bp/gün CI>0, ölçülmüş −0.63 → elendi.
- EMA12 ilk 5 dk NQ (2026-11-17, 5400829): maliyetsiz +0.138R CI>0, ölçülmüş +0.036R CI 0'ı kapsıyor → elendi.

**Bu test bağımsız edge kanıtı DEĞİL.** Brüt sonuçlar aynı dönemde (2012–2026) zaten görüldü ve bu iki kural brüt pozitif
oldukları için seçildi (seçim yanlılığı). Test yalnız şunu sorar: aynı kural **gerçek borsa verisinde** ve **vadeli
maliyetiyle** ayakta kalıyor mu? Gerçekten görülmemiş veri: CME 2010-06-06 – 2011-12-31 (Dukascopy'de yok) → ayrıca raporlanır.
Referans (hipotez değil): Noise Band NQ (CFD'de zaten geçti) aynı motorla raporlanır.

## Veri
Databento GLBX.MDP3 ohlcv-1m, ES.c.0 ve NQ.c.0 (sürekli, ayarsız), 2010-06-06 – 2026-11-19, UTC → 5m'ye toplanır
(label=left). Mikro (MES/MNQ) fiyatı mini ile aynı, yalnız çarpan farklı → sinyal mini barlarından.
**Roll günü:** önceki seansla `instrument_id` değişen gün işlem almaz (önceki kapanış/EMA farklı kontrattan gelir).
Bayram günleri: tam 78 barlı olmayan seanslar zaten atılıyor (motor kuralı).

## Kurallar (değişmeden, mevcut motor)
- **H1 Noise Band ES:** `intraday.noise_band_research.simulate` (Zarattini 2024 uyarlaması), aynen.
- **H2 EMA12 ilk 5 dk NQ:** `intraday.ema12_first5m_14y.trades` (09:30 5m mumu EMA12 üstü/altı → yön; stop mum aralığı;
  72 bar zaman aşımı), aynen.

## Maliyet (ölçülür, tahmin edilmez)
Yön başına maliyet puanı = **yarım spread** + **komisyon puanı**.
- Yarım spread: Databento bbo-1m MES.c.0 / MNQ.c.0, 2025-01 – 2026-11, NY 09:30–16:00 dakika barlarının (ask−bid)/2 **medyanı**.
  Ölçüm dosyası + tarih rapora yazılır. Bu bugünkü spread; tick büyüklüğü sabit olduğundan geçmişe **puan** olarak taşınır
  (oransal maliyet = puan / o günkü fiyat).
- Komisyon: Topstep yardım merkezi örneği MES tam maliyet **$1.22 gidiş-dönüş** (komisyon $0.50 + borsa $0.70 + NFA $0.02),
  yön başına $0.61. MNQ için aynı tutar kullanılır (**MNQ için ayrıca doğrulanmadı**). Puan = $0.61 / çarpan (MES $5, MNQ $2).
- Raporlanan üç satır: maliyetsiz / ölçülmüş merkez / **kötümser = 2× merkez** (stop kayması ve fix dışı spread açılması ölçülmedi).
- Maven CFD maliyeti satırı kıyas için yan yana verilir.

## Karar kuralı (her hipotez ayrı; Bonferroni 2 test)
- H1 GEÇER = merkez maliyette günlük ortalama net için dairesel blok bootstrap (blok 5, 10.000, seed 20261121) iki yönlü
  Bonferroni %95 (0.0125 kuantil) alt sınırı > 0 **ve** 2012–21 ve 2022+ ortalamaları > 0 **ve** kötümser ortalama > 0.
- H2 GEÇER = merkez maliyette işlem başı R için aynı bootstrap alt sınırı > 0 **ve** 2012–21 ve 2022+ > 0 **ve** kötümser > 0.
- Değerlendirme dönemi 2012-01-01 – 2026-11-19 (Dukascopy testleriyle aynı). 2010-06 – 2011 görülmemiş dilim ayrıca
  raporlanır; karar şartı değil (n ~370 gün, güç düşük), işareti yazılır.
- Geçen olursa bile LIVE'a girmez: sonraki adım futures prop uygunluğu (bot izni, Türkiye kabulü) + forward PAPER.
