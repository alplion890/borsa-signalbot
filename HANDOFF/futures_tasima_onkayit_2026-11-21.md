# Ön-kayıt: CFD'den futures'a taşıma, ikinci tur (2026-11-21)

Bu dosya `futures_transfer_retest.py` gerçek veride çalışmadan ÖNCE commit edilir.

## Soru
CFD (Dukascopy + Maven maliyeti) testlerinde **brüt pozitif ama maliyet yüzünden elenen** ve elimizdeki CME ES/NQ
verisiyle test edilebilen kurallar, futures maliyetiyle ayakta kalıyor mu? Ayrıca CFD'de geçen kurallar futures'ta
nasıl görünüyor (yalnız referans, karar değil)?

**Dürüst etiket:** bağımsız edge kanıtı DEĞİL. Brüt sonuçlar 2012–2026'da görüldü ve kurallar brüt pozitif oldukları için
seçildi (seçim yanlılığı). Gerçekten görülmemiş dilim: CME 2010-06-06 – 2011-12-31, ayrıca raporlanır.

## Hipotezler (Bonferroni 4 test)
- **F1 Baltussen son 30 dk NQ** (`intraday.last30_momentum.trades_for`, 15:30→15:55): CFD maliyetsiz +0.75 bp, ölçülmüş −1.46.
- **F2 Baltussen son 30 dk ES** (aynı kural, ES): CFD'de test edilmedi; orijinal makale SPY.
- **F3 Williams Oops NQ** (`seffaf_adaylari.simulate_b6`, RTH günlük): CFD 2× negatif.
- **F4 Williams Oops ES** (aynı kural).

## Referans (hipotez değil, yalnız tablo)
B7 IBS NQ (CFD'de geçti), B7 IBS ES, B5 Turtle Soup NQ. Önceki turdaki NB NQ / NB ES / EMA12 sonuçları tabloya aynen taşınır.

## Veri ve maliyet (önceki ön-kayıtla aynı, 57bf0ba)
Databento GLBX ohlcv-1m ES.c.0 / NQ.c.0 → 5m (label=left). Roll günü işlem almaz; çok günlük işlem (B5/B7) giriş ile çıkış
arasında roll varsa atılır (ayarsız sürekli seri sahte getiri verir). Maliyet yön başına puan: MES 0.247, MNQ 0.555
(bbo-1m ölçümü + $0.61 komisyon); oransal = puan / giriş fiyatı. Üç satır: maliyetsiz / merkez / 2×. Futures'ta swap yok.

## Karar kuralı (her hipotez ayrı)
GEÇER = merkez maliyette işlem başı net için blok bootstrap (blok 1, 10.000, seed 20261121) iki yönlü Bonferroni
(0.05/4/2 kuantil) alt sınırı > 0 **ve** 2012–21 ve 2022+ ortalamaları > 0 **ve** 2× maliyet ortalaması > 0.
Değerlendirme 2012-01-01 – 2026-11-19. Geçen olursa bile LIVE'a girmez: sonraki adım forward PAPER.
