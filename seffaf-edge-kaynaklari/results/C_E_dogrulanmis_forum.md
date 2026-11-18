# C/D6/E: Dogrulanmis track-record platformlari ve forumlar (2026-11-18)

Kural: yalniz acilan sayfalarda gorulenler. Sayfa acilmadan sadece arama snippet'i = "(snippet, acilmadi)".

## Ozet
Dogrulanmis canli kayit VE tam acik kural VE bagimsiz replikasyon uclusunu saglayan HICBIR strateji bulunamadi. Bulunanlar iki gruba ayrilir:
(a) Tam kural + maliyetli test var, canli kayit yok (blog/Substack/GitHub).
(b) Canli/verified kayit var, kural kapali (Darwinex, Myfxbook, MQL5 satis, Collective2).

## Bulgular

### 1. MQL5 blog: Zarattini-Aziz ORB 5 endekste replikasyon (E3, en degerli kayit)
URL: https://www.mql5.com/en/blogs/post/776235
- Kural: ilk 5dk mumun yonu; 2. mum acilisinda gir; stop ilk mumun karsi ucu; hedef 10x risk veya seans kapanisi.
- Veri: NQ, SPX, Dow, DAX, FTSE CFD dakika verisi, sadece cash seans, 2015-Haz 2026 (~2900 seans/piyasa).
- Maliyet: round-trip puan olarak NQ 2.5, SPX 0.8, Dow 4.0, DAX 2.5, FTSE 1.5; risk < 2x maliyet olan islemler dislanir.
- Sonuc (R/islem): NQ brut +0.131 (n=2934) -> net +0.002 (n=2638, t=0.0); SPX -0.081; Dow -0.081; DAX -0.038; FTSE -0.079. Rastgele yon benchmarkina gore NQ +0.124 (t=2.1).
- Donemler: 2015-2017 hepsi negatif; 2021-2026 NQ en iyi +0.06R.
- Sinirlar: CFD, parametre aramasi yok, vadeli + sadece komisyon test edilmedi. Yazar kimligi/ticari baglanti dogrulanmadi. Canli kayit yok.
- Anlam: NQ'da ilk-mum bilgisi ~maliyet buyuklugunde; net sifir.

### 2. MQL5 blog: Altinda 400+ varyant testi (E3)
URL: https://www.mql5.com/en/blogs/post/777404
- Gercek bid/ask, $0.07/oz komisyon, stop kaymasi; M5 2016-2026, H1 2016-2026, 12 piyasa gunluk 2000-2026; 2016-21 ve 2022-26 bolunmus; t>=3.3 esigi; rastgele giris kontrolu.
- Hepsi basarisiz: Unger saatlik breakout 0.000R (n=4340); Williams vol breakout 0 ile -0.03R; Raschke Holy Grail -0.20R; Qullamaggie -0.13R; SMB 9EMA -0.19R; SMC ilk mum -0.20R; acik kaynak FVG altin EA -0.13R (iddia: 6 ayda +%48.7); gunluk trend takibi 12 piyasa Sharpe 0.00 (swap sonrasi).
- Hayatta kalan: Asya kutusu breakout +0.035R (cok kucuk); ucretsiz altin breakout EA +0.21R ama rastgele cikis +0.14R (altinin yukselisi). Kural detayi verilmemis.
- Urun satmiyor (sayfa). Veto/negatif kanit olarak degerli.

### 3. Backtests, Not Signals Substack: MNQ ORB (E3)
URL: https://backtestsnotsignals.substack.com/p/opening-range-breakout-real-edge (Mart 2026, yazar "Ale")
- Kural: gunluk SMA(200) filtresi (150-300 optimize); ORB yukari/asagi kirilim, filtre yonunde; stop karsi uc; TP = RR 1.4-4.4 (optimize) x stop; statik stop siniri 150 tick; sonraki seans acilisinda zorunlu cikis; bir kayiptan sonra gun biter.
- Veri: Databento back-adjusted MNQ, 1 kontrat; IS 12.02.2020-30.12.2022 (n=451), OOS 03.01.2023-27.02.2026 (n=474).
- Maliyet: komisyon $0.68/taraf; SLIPAJ YOK.
- OOS: getiri %94.6, CAGR %15.7, Sharpe 1.10, MaxDD -%12.8, win %24.9, PF 1.32. Buy&hold OOS %127.6 (yani stratejiyi gecti).
- Sorunlar: parametreler IS'te optimize; slipaj yok; ORB suresi sayfada belirtilmedi; notebook/trade log paywall (ucretli abonelik satisi = cikar catismasi). Canli kayit yok.

### 4. Project Kintoun (GitHub Pages): NQ rejim-filtreli ORB (E3)
URL: https://mrjerm.github.io/project_kintoun.html (13.12.2025)
- Kural: 9:30-9:45 ET ORB; 9:45-14:00 giris, gunde 1 islem; kirilim sonrasi seviyeye donus + tutunma; VWAP egimi yonle ayni, fiyat NY VWAP'in dogru tarafinda ve bantlar icinde; stop ORB karsi ucu, hedef ORB ucu + range; cikislar VWAP/5dk/EOD 14:59.
- Veri: DataBento 1dk NQ, 2022-06-01 ile 2025-10-31. Sonuc: n=1062, win %33.9, PF 1.47, yillik %57, MaxDD -%8.5, Sharpe 2.28.
- Zayifliklar: slipaj yok, bar-kapanis dolumu, komisyon $2.74/islem, OOS/holdout yok, bilesik pozisyon boyutu sonucu sisiriyor, kod "sanitized" ve metinle celisiyor (SD bandi, hacim carpani 0, DST sabit EST). Canli kayit yok. Guvenilmez; ilgi cekici ama replike edilmemis.

### 5. Darwinex LBXP roportaji (C1)
URL: https://blog.darwinex.com/lbxp-interview
- Kural: arz/talep bolgeleri, onceki gun high/low ve haftalik acilis araligi onay; 4H ve 1H; haftada 1-3 islem; dinamik boyutlama (volatilite + drawdown).
- Kayit: PF 1.22, payoff 1.61; 2024 cogunda negatif. Enstruman adlandirilmamis. Seed rakamlari sayfada tutarsiz (EUR 560k / EUR 500k / "$700K AuM").
- Kural SUBJEKTIF (bolge cizimi); uygulanabilir deney degil. Darwinex'in kendi pazarlama icerigi (cikar catismasi, sponsorluk aciklamasi yok).
- Genel: Darwinex yardim sayfasi islem detaylarinin yatirimcilara aciklanmadigini soyluyor (https://help.darwinex.com/what-is-a-darwin, snippet). DARWIN kurallari yapisal olarak kapali.

### 6. MQL5 satis blogu: MNQ EA (C3 benzeri)
URL: https://www.mql5.com/en/blogs/post/778179
- Maliyetli test (real tick, 11 kontrat 04.2024-10.2026, $2/round-turn + 1 tick slipaj): net $30.199 -> $25.744, PF 1.34 -> 1.28, n=1485, MaxDD $2627. Canli hesap 19.10.2026'da basladi (3 haftadan az).
- KURALLAR ACIKLANMADI; EA satiliyor. Kullanilamaz.

### 7. Elite Trader "Systematic FX Trading Journal" (E1)
URL: https://www.elitetrader.com/et/threads/systematic-fx-trading-journal.54002/post-861317
- 2005, ~2 hafta, kendi beyan, kural kapali, dogrulama yok. Degersiz.

## Bakilan ama kullanilabilir kanit cikmayanlar
- Collective2 (C4): ornek sayfalar arama sonucunda goruldu, ama hicbiri acilmadi. Sonuclar "hypothetical" etiketli, cogu strateji 2023-2025 baslangicli (snippet). Kural aciklamasi/audit kaniti bulunamadi. (acilmadi)
- Myfxbook/FXBlue/Kinfo (C2): Kinfo icin sonuc yok. Myfxbook strateji sayfasi (vcap2) acilamadi (ECONNRESET). Myfxbook kendi uyarisi: performans spread/komisyonu hesaba katmayabilir (snippet). Aramadaki "verified" hesaplar satici blogu (ATM GBPUSD 14 gun, GOLD KING demo) = pazarlama, kural kapali.
- MQL5 Signals (C3): arama 2+ yillik, kaynak kodu acik, gercek hesapli sinyal vermedi. "Bohemia Gold MT5" ucretsiz kaynak ama sadece demo testi (snippet, acilmadi). Nova GOLD Breakout: FTMO challenge sinyali, ucretli (snippet).
- NexusFi/Elite Trader (E1): bagimsiz uye backtestli, tam kurallı NQ thread bulunamadi. NexusFi "someone backtest this" thread'i yalnizca basligi goruldu (acilmadi).
- r/algotrading (E2): reddit.com acilamadi (mirror ENOTFOUND). Mart 2025 ORB postu (S&P CFD, 15dk aralik, 4. mumda giris, stop aralik tabani, 1.5:1, GitHub kodu var) yalniz snippet, maliyet/replikasyon dogrulanmadi.
- Forex Factory (E1): jurnaller sistemi aciklamayi reddediyor (snippet).
- D6 JKP: https://research.cbs.dk/en/publications/is-there-a-replication-crisis-in-finance/ — 153 faktor, 93 ulke, hisse agirlikli (snippet); vadeli/FX kapsami dogrulanmadi. Alaka dusuk. 

## Dogrulanmis-VE-acik materyal ne kadar var
Pratikte sifir. Verified canli kayit sunan platformlar (Darwinex, Collective2, MQL5 Signals, Myfxbook) kurali kapali tutuyor; kurali aciklayan kaynaklar (blog/Substack/GitHub) canli kayit sunmuyor ve cogu slipaj/OOS eksigi tasiyor. En guvenilir bulgular NEGATIF (maliyet sonrasi ORB ~0, altinda 400 varyant coguhepsi basarisiz) ve projenin mevcut elenme bulgulariyla uyumlu.
