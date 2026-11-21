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

## SONUÇ (2026-11-21, ön-kayıt 4f78b05 sonrası) — F1–F4 GEÇMEDİ; referans IBS NQ ve ES geçer kriterini sağlıyor
Kod `scripts_2026-11-21/futures_transfer_retest.py`, çıktı `strategy-lab/outputs/intraday/futures_transfer_retest/result.json`.
Not: ilk koşuda CI birim hatası (bp iki kez ölçeklendi) vardı, yalnız CI satırı düzeltilip yeniden koşuldu; ortalamalar değişmedi.
bp/işlem, Bonferroni CI merkez maliyette:

| | maliyetsiz | futures merkez | 2× | Maven CFD | CI | 2012–21 / 2022+ | 2010–11 görülmemiş | n |
|---|---|---|---|---|---|---|---|---|
| F1 Baltussen NQ | +0.46 | −1.26 | −2.98 | −1.75 | [−2.57, +0.07] | −1.33 / −1.13 | −2.77 | 3642 |
| F2 Baltussen ES | +0.65 | −1.15 | −2.95 | −2.54 | [−2.29, +0.04] | −1.10 / −1.24 | −3.24 | 3620 |
| F3 Oops NQ | +4.52 | +2.84 | +1.16 | +2.31 | [−4.15, +9.72] | +2.45 / +3.61 | −14.64 | 978 |
| F4 Oops ES | +1.42 | −0.38 | −2.17 | −1.78 | [−5.65, +4.88] | −0.19 / −0.75 | −1.96 | 999 |
| REF IBS NQ | +62.5 | +60.9 | +59.2 | +60.3 | [+36.2, +86.1] | +64.5 / +54.2 | +68.1 | 382 |
| REF IBS ES | +51.7 | +49.9 | +48.1 | +48.5 | [+28.9, +70.4] | +50.7 / +48.3 | +46.3 | 362 |
| REF Turtle NQ | +19.9 | +18.2 | +16.6 | +17.7 | [−2.8, +40.1] | +1.1 / +42.4 | −12.2 | 111 |

- F1/F2: maliyetsiz bile ~0; günde tek 25 dk işlemde futures maliyeti de etkiyi aşıyor → GEÇMEDİ.
- F3/F4: CI 0'ı kapsıyor; F3 görülmemiş dilimde −14.6 → GEÇMEDİ.
- IBS (referans): CME verisinde NQ ve ES, görülmemiş 2010–11 dahil pozitif; maliyet etkisi küçük (işlem başı ~60 bp brüt, ~1.7 bp maliyet).
  Çok günlük; roll'u kapsayan işlemler atıldı (NQ 26, ES 24). Futures'ta swap yok (CFD'de B7 swap ile değerlendirilmişti).
  ES ve NQ günlük getiri korelasyonu yüksek; iki ayrı edge sayılmaz.
