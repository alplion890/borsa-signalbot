# Signalbot Current Status - 2026-06-24

Bu dosya botun Capital.com sonrasi son pratik durumunu ozetler. Amac: bir ay
sonra bile "biz nerede kalmistik?" sorusuna hizli ve net cevap vermek.

## 1m intrabar fill-modeli — UYGULANDI ve OLCULDU (2026-08-11)

**Sonuc: 1m cozumu bu stratejilerde HIC devreye girmiyor (540 gun, 0 vaka).**
Yeni mod `1m_then_sl_first` opt-in olarak eklendi, eski `bar_sl_first`
varsayilan ve degismemis kaldi (192/192 test yesil, 16 yeni test).

| Vaka | islem | eski toplam_R | yeni toplam_R | cakisan bar |
|---|---|---|---|---|
| NQ_ORB / NASDAQ100 5m | 133 | +2.66 | +4.13 | 0 |
| NQ_ORB / SP500 5m | 129 | +5.24 | +5.01 | 0 |
| SWEEP_CORE / NASDAQ100 15m | 35 | +20.60 | +20.75 | 0 |
| SWEEP_CORE / SP500 15m | 22 | −12.22 | −12.38 | 0 |
| **HAVUZ** | **319** | **exp_R +0.051** | **exp_R +0.055** | **0** |

**`cakisan bar = 0` BUG DEGIL, olculdu:** bir barin hem SL'e hem TP'ye degmesi
icin menzilinin ~(1+rr)R olmasi gerekir. SWEEP'te bu 3.0R = fiyatin ~%0.425'i;
15m bar menzili medyan %0.118, p99 %0.791. Ayrica 36 sweep isleminin 10'unda
ILERIDE boyle bir bar var ama islem oraya varmadan zaten kapanmis — belirsizlik
penceresine ulasilmiyor. Yani `honest_engine`'in SL-first varsayimi bu
konfigurasyonlarda pratikte hic kullanilmiyordu.

**Kalan fark tamamen giris fiyatindan geliyor** (sinyal kapanisi -> sonraki
open), 1m'den degil. Fark havuzda +0.004R — gurultu seviyesinde, yon bile
tutarsiz (NASDAQ100'de artiyor, SP500'de azaliyor).

**Gap kurali karari: SKIP.** Giris sonraki open'da stopun otesindeyse islem
alinmaz ve `gap_skipped` sayacinda ayri raporlanir. Gerekce proje mantigindan:
`signalbot/signal_scan.py` `MAX_ADVERSE_ENTRY_DRIFT_R = 0.5` — stopun otesine
gecmis bir acilis >=1.0R aleyhine kaymadir, o sinyal kullaniciya hic gitmezdi.
Olculen donemde 0 vaka.

**Kalan sinirlama:** yeni mod yalnizca saf Python referans yolunda calisir;
numba `fast_honest_core` sadece `bar_sl_first` icindir. Bu sinirlama
`test_new_mode_does_not_silently_use_numba_core` ile sabitlendi.

**Rapor:** `python -m intraday.fill_model_ab` (MT5 venv gerekmez, dukascopy
1m cache yeterli). Dosyalar: `intraday/honest_engine.py`,
`intraday/fill_model_ab.py`, `intraday/test_honest_engine_1m.py`,
`intraday/data.py` (1m interval).

### Orijinal plan (tarihsel kayit)

`honest_engine` sinyal 15m mumunun kapanisini giris kabul ediyordu ve sonraki
15m mumda hem SL hem TP gorulurse muhafazakâr olarak SL sonucunu yaziyordu. Bu
davranis kaldirilmadan, karsilastirmali bir ikinci fill modu planlanmisti.

### Hedef sozlesme
1. 15m sinyal ancak mum kapandiginda kesinlesir.
2. Varsayimsal giris, sinyal mumunun kapanisi degil **sonraki 15m mumun open**
   fiyatidir.
3. SL yapisal/sinyal aninda belirlenen seviyedir; yeni giris nedeniyle RR hedefi
   yeniden hesaplanir. Giris stopun diger tarafina gap ile acilirsa islem,
   onceden tanimlanacak bir **skip veya gap-loss** kuralina gore ele alinmalidir.
4. Bir sonraki 15m mumda yalniz SL veya yalniz TP gorulurse sonuc direkt yazilir.
5. Sadece ayni 15m mumda hem SL hem TP gorulurse, o pencereye ait **1m OHLC**
   mumlari kronolojik sirayla taranir.
6. 1m mumlar TP veya SL siralamasini ayristiriyorsa ilk dokunan seviye sonuc
   olur. Tek bir 1m mumda ikisi de gorulurse veya 1m veri eksikse fallback yine
   **SL-first** olur.

### Gereklilikler ve guvenlik kapilari
- `data.py`/veri katmaninda 1m Dukascopy cache; tum indeksler UTC ve ayni
  [15m_baslangic, 15m_bitis) penceresinde hizalanmis olmali.
- Mevcut `bar_sl_first` modu varsayilan olarak korunmali; yeni mod
  `1m_then_sl_first` gibi acik isimle opt-in olmali.
- Once testler: sonraki-open girisi, long/short 1m TP-once ve SL-once,
  1m-ici belirsizlik, eksik 1m veri, gap davranisi ve eski mod regresyonu.
- Numba `fast_honest_core` ile saf Python referans yolunun ayni sonucu verdigi
  yeniden dogrulanmali; ilk guvenli surumde yeni mod referans yolda calisabilir.
- Eski ve yeni fill modeli ayni sembol/donem/fee/slippage ile karsilastirilmali:
  islem sayisi, exp_R, PF, max drawdown, TP/SL-cakisma sayisi ve 1m ile
  cozulen sonuc sayisi raporlanmali.
- Bu, mevcut modulleri canliya alma gerekcesi degil; backtest varsayimini
  olcmek icin bir arastirma katmanidir. Once paper/forward kanit korunur.

## Ana karar

Capital.com Turkiye'de kullanilamadigi icin Capital demo/API yolu tamamen terk
edildi. Capital primary feed, Capital secret'lari, `test_capital` workflow
secenegi ve ilgili kod/test yolu kaldirildi.

Bu karar sonrasi bot cop olmadi; rolu degisti:

```text
Bot = setup radari
Kullanici = execution pilotu
```

Sifir maliyet + PC kapali + TradingView/VPS yok + Capital yok kosulunda,
5m/15m futures icin kusursuz real-time otomatik sinyal mumkun degil. En guvenli
ucretsiz kurulum GitHub radar + manuel Maven teyididir.

## Aktif mimari

```text
Normal strateji botu:
  - GitHub Actions uzerinden calisir.
  - Telegram'a sinyal yollar.
  - Emir acmaz.
  - Gold/NQ ana penceresinde 5 dakikada bir tarama yapar.
  - Londra penceresinde 15 dakikada bir, NY ikinci yarida 30 dakikada bir calisir.

Veri kaynaklari:
  - XAUUSD / NASDAQ100 / SP500 / EURUSD / GBPUSD: Yahoo Finance mum verisi.
  - BTCUSDT: Binance public API.
  - Finnhub: sadece uyumlu sembollerde ikincil anlik fiyat.

Futures karari:
  - Gold, NQ ve ES futures seviyeleri spot/CFD proxy ile karistirilmiyor.
  - Bu yuzden Gold/NQ/ES icin Finnhub anlik fiyat karsilastirmasi kapali.
  - Bu sinyallerde Maven/prop grafiginden guncel fiyat manuel kontrol edilmeli.
```

## Normal bot korumalari

```text
Tekrar-spam korumasi:
  - Ayni bardaki ayni sinyal ikinci kez gonderilmez.
  - Ayni modul/yon/giris/stop/hedef yapisindaki kucuk revizyonlar 24 saat icinde
    ayni fikir kabul edilir.
  - Eski NQ ORB gibi 18:01 ve 18:11'de ayni setup'in tekrar gelmesi engellenir.

Gecikme filtresi:
  - Fiyat setup yonunde +1.0R'den fazla ilerlemisse aday gonderilmez.
  - Fiyat setup tersine -0.5R gitmisse aday gonderilmez.
  - Bu filtre en son kapanmis mum fiyatina gore calisir.
  - Futures'ta sahte CFD/spot proxy fiyati kullanmaz.

Bayat mum filtresi:
  - 5m setup maksimum 45 dakika eski olabilir.
  - 15m setup maksimum 90 dakika eski olabilir.
  - 1H/BTC setup maksimum 360 dakika eski olabilir.
  - Daha eski mumlardan gelen adaylar Telegram'a cikmaz.
```

## DeepSeek AI scout

AI scout ana bottan bagimsizdir. Ana bot setup mesajini once yollar; DeepSeek
ana botu bekletmez.

```text
Kurallar:
  - Ayni Telegram sohbetine "AI FIRSAT" mesaji yollar.
  - Minimum 2R altindaki firsatlar Telegram'a cikmaz.
  - Minimum guven: 80.
  - VWAP reclaim/rejection tek basina setup sayilmaz.
  - Flash model once tum aktif piyasalari tarar.
  - Sadece kaliteli adaylar Pro modelden ikinci teyit alir.
  - Watch/risk/ham model cevaplari Telegram'a cikmaz, audit dosyasina yazilir.
  - Gercek AI FIRSAT adaylari ledger'a yazilir; TP/SL/MFE/MAE sonradan izlenir.
```

## Risk yonetimi

```text
Challenge fazi:
  - Gold ve NQ normal risk: %1.5.
  - Onceki kapanan islem kazandiysa maksimum %3.
  - Ayni anda tek islem.
  - Toplam acik risk maksimum %3.
  - Gunluk zarar %4.5'e gelirse dur.

Funded fazi:
  - ACCOUNT_PHASE = bnpl_funded yapilinca devreye girer.
  - Gold/NQ risk yaklasik %0.35.
  - Toplam acik risk maksimum %0.50.
  - Gunluk zarar stopu %1.
  - Haftalik zarar stopu %2.
  - Gunluk kar tavani %0.50.
  - Paper moduller gercek para icin sifir risk gosterir.
```

## Aktif kullanim kurali

Telegram sinyali gelirse:

1. Acik islem var mi kontrol et.
2. Maven grafiginde guncel fiyati kontrol et.
3. Fiyat giris bolgesine yakin degilse alma.
4. +0.5R'den fazla kacmis hareketi kovalamama.
5. Sadece Gold/NQ ana saatlerinde ve ekrana bakabiliyorsan gercek hesaba dokun.

## Test ve deploy notu

```text
Local test:
  python -m pytest strategy-lab/intraday/signalbot -q --basetemp .pytest_tmp

Sonuc:
  72 passed

Dry-run:
  python run_bot.py --dry-run

Sonuc:
  Kod calisti. Bayat BTC mumlari artik tek satir ozetle atlandi ve Telegram'a
  cikacak yeni setup uretmedi.

Hazir commitler:
  GitHub main: 2a9c4d3 fix: remove unavailable capital feed path
  Bayat mum filtresi: sonraki commit ile eklenecek/guncellenecek.
```

## Son acik risk

GitHub baglantisi bu oturumda ara ara `github.com port 443` hatasi verdi. Baglanti
geldigi anda `face0778` commit'i `origin/main` uzerine fast-forward pushlanacak.
Push tamamlandiktan sonra GitHub Actions uzerinden dry-run/test calistirilip bot
aktif halde birakilacak.

## Guncelleme 2026-07-04: SWEEP_ES_DIV portfoyden kaldirildi

MT5 forward test (Maven hesabi [MT5-HESAP], MavenTrade-Server) 45 gunluk canli
backfill ile 7 modulden 6'sini kosturdu (BTC hala ayri Binance-spot altyapisi
istedigi icin MT5'e hic baglanmadi). Yol acan altyapi hatasi da bulundu:
`mt5_io.py` SYMBOL_MAP'te NASDAQ100 -> "USTEC" yanlisti, gercek broker sembolu
**US100**; bu yuzden NQ_ORB/SWEEP_CORE/SWEEP_ES_DIV daha once sessizce
atlaniyordu. Duzeltildi.

**SWEEP_ES_DIV (agirlik 2.0, portfoyun en agirlikli modulu) sahte edge
cikardi ve kaldirildi:**
- Backtest iddiasi: 19 islem, %47.4 win, exp_R +0.210, avg_loss -0.09R
- Gercek forward (45 gun, 10 islem): %20 win, exp_R -0.330R, avg_loss -1.14R
- Kanit: -0.09R'lik ortalama kayip fiziksel olarak imkansiz (gercek bir SL
  kaybi ~-1.0R olmali). Modulun igne-ince stop'u (sweep dibi - 0.25xATR,
  ~7-13 puan risk) temiz dukascopy backtest verisinde hic tetiklenmemis,
  timeout'ta basabasa yakin kapanmis. Canli US100 CFD gurultusunde ayni
  stop'lar aninda vuruluyor.
- Kod: `intraday/forward_ea/modules.py` `default_modules()` icinden silindi.
  Bu fonksiyonu signalbot `signal_scan.py` da kullaniyor -> Telegram'a artik
  SWEEP_ES_DIV sinyali cikmayacak, otomatik.

**Guncel gercek portfoy: 7 modulden 5'i dogrulanmis/aktif** (Gold NY ORB,
NQ ORB, Sweep Core VWAP, EUR London Fade, GBP London). BTC hic baglanmadi,
ES_DIV bugun elendi. Gold+NQ ORB backtest'le en tutarli olanlar; EUR
London 45 gunde hic sinyal uretmedi (asiri seyrek filtre); GBP London
zayif (3 islem, %33 win) ama ornekleme cok kucuk.

Detay: `strategy-lab/intraday/forward_ea/README.md`,
memory `project-state-signalbot.md`, Obsidian `traiding stratejim1.md`.
