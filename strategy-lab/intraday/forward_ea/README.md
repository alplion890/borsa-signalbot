# Forward EA — MT5 Demo Canlı Forward Test

**Çözdüğü sorun:** Final portföy 7 modüllü + çok varlıklı; gerçek kullanım fon
hesabı ister ve 7 indikatörü elle takip etmek pratik değil. Bu motor portföyü
MT5 canlı feed'inde **otomatik** yürütür — fon hesabı gerekmez, `trade_allowed`
iznine takılmaz (emir göndermez, paper-fill ile gerçek forward *sinyal* testi yapar).

## Çalıştırma
```bash
# Tek döngü (Task Scheduler için ideal)
python -m intraday.forward_ea.live_runner --once

# İlk kurulumda son 30 günü backfill et (hemen sonuç gör)
python -m intraday.forward_ea.live_runner --once --warmup 30

# Sürekli döngü (her 5 dk)
python -m intraday.forward_ea.live_runner --loop 300

# Sadece durum panosu
python -m intraday.forward_ea.live_runner --status
```

## Nasıl çalışır
Her döngüde her modül için:
1. MT5'ten güncel bar çekilir (son kapanmamış bar dışlanır).
2. Son işlenen bardan sonraki yeni barlar sırayla işlenir:
   - önce açık paper-pozisyonlar güncellenir (SL/TP/timeout, **honest = SL-önce**),
   - sonra o barda yeni sinyal varsa pozisyon açılır.
3. Durum `forward_state.json`'a yazılır → **restart'a dayanıklı**, kaldığı yerden devam.

Maliyet `config.cost_per_side`'dan R cinsinden düşülür (backtest ile aynı).

## Windows Task Scheduler ile otomatik
```
Program: wscript.exe
Argümanlar: "<repo>\strategy-lab\run_forward_ea_hidden.vbs"
Tetikleyici: her 5 dakikada bir + oturum açılışında
```
`run_forward_ea_hidden.vbs`, `run_forward_ea.cmd`'yi görünür pencere açmadan
çalıştırır (aksi halde 5 dakikada bir cmd penceresi yanıp söner).

Görev ayarlarında `DisallowStartIfOnBatteries` / `StopIfGoingOnBatteries`
varsayılan olarak açık gelir — dizüstünde fişte değilken bot hiç çalışmaz,
ikisini de kapat.

MT5 terminali açık ve hesaba giriş yapılmış olmalı; kapalıysa döngü sessizce
atlar (log'a yazar).

## Güncelleme 2026-07-16 — bot dirildi + Telegram köprüsü

**İki gizli bug bulundu ve düzeltildi** (botun 2026-07-02'den beri durmasının
gerçek sebebi — artımlı bar işleme yolu HİÇ çalışmamıştı, sadece warmup
backfill çalışıyordu):
1. `live_runner.py`: `df.index > last` numpy ndarray döner, `.to_numpy()`
   çağrısı AttributeError atıyordu → `np.asarray` ile düzeltildi.
2. `positions.py ledger()`: state JSON'dan str, yeni kapanan işlemden
   Timestamp gelen karışık `entry_time` tipleri sort'u çökertiyordu →
   `pd.to_datetime` normalizasyonu eklendi.

**Yeni: Telegram köprüsü (`notify.py`).** Yeni pozisyon açıldığında signalbot
formatında mesaj + MAVEN EMİR KARTI (broker sembol adı, yön, giriş/SL/TP, lot,
risk) Telegram'a gider. Emri Maven kuralına uygun olarak KULLANICI elle girer
(EA/bot emri yasak). Korumalar: >30dk eski (backfill) sinyal gönderilmez; env
eksikse döngü kırılmaz. Kurulum: `strategy-lab/.env` içine TELEGRAM_BOT_TOKEN
ve TELEGRAM_CHAT_ID; `run_forward_ea.cmd` Task Scheduler'a 5dk'lık görev.

---

# ⚠️ GÜNCEL DURUM (2026-08-06) — aşağıdaki eski bölümler tarihsel kayıt

## Forward skor tablosu (97 işlem)

| Modül | n | WR | exp_R | PSR | Verdikt |
|---|---|---|---|---|---|
| SWEEP_CORE_AVOID_MID_VWAP | 9 | %44 | **+1.206** | **0.907** | en güçlü kanıt |
| NQ_ORB_STRONG_TREND | 26 | %46 | +0.067 | 0.619 | zayıf ama tutarlı pozitif |
| EUR_LONDON_FADE_EMA | 2 | %50 | +0.105 | — | **kayıt GEÇERSİZ**, konfig değişti |
| GBP_LONDON_STRONG_TREND | 4 | %50 | +0.093 | — | **kayıt GEÇERSİZ**, konfig değişti |
| GOLD_NY_ORB_TREND | 18 | %44 | −0.152 | 0.203 | negatif, challenge'da KULLANILMIYOR |
| CAND_BTC_ABSORPTION | 12 | %17 | **−0.691** | 0.113 | backtest çürüdü, sinyaline GİRME |

**KANITLI İKİLİ (SWEEP+NQ): n=35, exp_R +0.360, toplam +12.59R, PSR 0.911.**

## BTC ölçüme bağlandı (2026-08-06) — backtest'in TERSİ çıktı

signalbot BTCUSDT_OF_ABSORPTION'ı Telegram'a gönderiyordu ama forward
defterinde **sıfır** kaydı vardı — aylardır ölçülmeyen bir sinyal kaynağı
telefona düşüyordu (DeepSeek AI scout'un kapatılma gerekçesiyle aynı durum).

Bağlanırken üç sessiz hata çıktı:

| Hata | Etki |
|---|---|
| live_runner her modülü mt5_io'dan çekiyordu | Maven'da spot BTC yok → veri gelmiyor |
| `symbol_key="BTC"`, INSTRUMENTS anahtarı `"BTCUSDT"` | `cost_per_side` KeyError → dedektör 4.6 sinyal/hafta üretirken defter boş |
| Binance tz-aware, mt5_io tz-naive | Defter yazımı patlıyor; hata `_save_state` içinde olduğu için **o döngüdeki tüm modüllerin** kaydı kayboluyor |

Sonuç: backtest 138 işlem +0.073 exp_R · **forward 12 işlem −0.691 exp_R**.
SWEEP_ES_DIV kalıbının aynısı. Aday olarak (weight=0.0) ölçümde kalır ama
Telegram'dan gelen BTC sinyallerine işlem açılmamalı.

Dedektör **kopyalanmadı**, signalbot'un `detect`'i import edildi — kopya
olsaydı ikisi zamanla ayrışır, ölçüm gönderilen sinyali temsil etmezdi.

## MT5 artık kendiliğinden açılmıyor (2026-08-06)

`mt5.initialize()` argümansız çağrılınca terminal kapalıysa **onu kendisi
başlatır**. Forward EA 5 dakikada bir koştuğu için kullanıcı MT5'i kapatsa
bile geri açılıyordu → Task Scheduler görevi devre dışı bırakılmıştı → **veri
toplama tamamen durmuştu** (son koşum 2026-08-02, 4 gün kayıp).

`mt5_io._terminal_running()` eklendi (tasklist, ek bağımlılık yok): terminal
kapalıysa `initialize` hiç çağrılmaz, sessizce atlanır. Tespit edilemezse
`True` döner — yanlış negatif botu sessizce öldürürdü.

Görev tekrar aktif: 5 dk + oturum açılışı, pil koruması kapalı.

NQ_ORB üç kaynakta da pozitif (Dukascopy +0.082 · MT5 6ay +0.226 · canlı
+0.067). Önceki "NQ_ORB çöktü" teşhisi fazla sertti; doğrusu "küçük ama
tutarlı".

## Post-hoc gün filtreleri iki modülü sessizce kapatmıştı (düzeltildi)

`dow=3` (sadece Perşembe) filtresi EUR/GBP London'dan **kaldırıldı**
(commit 287ca55). Filtre bu dosyanın kendi yorumunda "final ledger'dan
birebir geri çıkarıldı" diye yazıyordu — sonuca bakılıp seçilmiş.

| Konfig | sinyal/hafta |
|---|---|
| EUR canlı (adx<18 + Perşembe) | **0.00** |
| EUR Perşembe filtresi yok | 1.75 |
| GBP canlı (Perşembe + rejim) | **0.00** |
| GBP Perşembe yok (rejim var) | 1.75 |

İki modül de "az sinyal veriyor" değil **hiç vermiyordu**. adx/rejim
filtreleri korundu (rejim gerekçesi var). Portföy hacmi ~3.5 → ~7.0/hafta.

**Eski EUR n=2 / GBP n=3 kayıtları artık geçersiz** — farklı konfigle
toplandılar. Bu iki modül şu an KANITSIZ, sıfırdan veri biriktiriyor.

## Sweep Çarşamba yasağı: ölçüldü, bırakıldı

16 hafta gün dağılımı: Pzt 5 | Sal 2 | **Çar 1** | Per 2 | Cum 2 | Paz 1.
Filtre 13 sinyalin 1'ini kesiyor (%8) — zararsız, ama aynı sebeple A/B ile
test edilemez (yıllar sürer). `CAND_SWEEP_ALLDAYS` bilerek kurulmadı: ölçüm
tiyatrosu olurdu. Detay: `_sweep_core_detector` docstring.

## Gold `atr_max_rank=0.67` modülü fiilen kapatmış

Filtreli **0** sinyal/hafta, filtresiz 2.33. Uzun pencerede 25 → 3 sinyal
(%88 kesme). Defterdeki "4 hafta sessiz" gizemi buydu. Bu hızda 30 işlem
~2 yıl sürer → **modül artık ölçülemez**. Challenge dışı olduğu için acil
değil, ama "kanıt topluyor" sanmak yanlış. Geri dönüş: `atr_max_rank=1.0`.

## SWEEP_CORE seyrek ama bozuk değil

Taze MT5 (US100 15m, 18.3 hafta): 0.77 sinyal/hafta. Forward defteri
1.54/hafta — backtest'ten daha **sık** tetikliyor. Seyreklik tasarım:
ADX>25 + VWAP trend + sweep + minRR 2.0 dördü birden nadir hizalanır.
Verimlilik: SWEEP ~1/hafta × +1.206 ≈ **+63R/yıl** vs NQ_ORB ~2.5/hafta ×
+0.067 ≈ +8.7R/yıl.

---

# Tarihsel kayıt (2026-07-16 ve öncesi)

**Gold ORB'a rangeci-rejim filtresi** (`modules.py`, `atr_max_rank=0.67`):
54 günlük forward'da gold 18 işlem exp −0.152R verdi (backtest +0.063
beklerken), tüm kayıplar yüksek-vol whipsaw timeout'u. `gold_orb_regime`
taraması `adx>=trend & atr<high` kovasını 4/4 yıl pozitif buldu (exp +0.072,
minYr +0.015) → yüksek-vol (rolling-500 pctile > 0.67) günler artık atlanıyor.
Geri dönüş: `atr_max_rank=1.0`.
⚠️ 2026-08-05'te ölçüldü: bu filtre modülü fiilen kapattı (yukarı bkz).

**Forward skor tablosu (54g, 2026-07-16 itibarıyla) — ESKİ:**

| Modül | İşlem | exp_R | Verdikt |
|---|---|---|---|
| NQ_ORB_STRONG_TREND | 16 | +0.366 | ⚠️ küçük-örneklem şişkinliği; 26 işlemde +0.067'ye indi |
| GOLD_NY_ORB_TREND | 18 | −0.152 | tökezledi → atr filtresi eklendi (modülü kapattı) |
| SWEEP_CORE_AVOID_MID_VWAP | 4 | +1.13 | 9 işlemde +1.206'ya çıktı, dayandı |
| GBP_LONDON_STRONG_TREND | 3 | +0.10 | kayıt geçersiz (dow=3 kaldırıldı) |
| EUR_LONDON_FADE_EMA | 0 | — | filtre fazla dar DEĞİL, **fiilen kapalıydı** |

## Modül durumu (güncellendi 2026-07-04)

**Kritik düzeltme:** `mt5_bridge/mt5_io.py` SYMBOL_MAP'te NASDAQ100 → "USTEC"
olarak eşliydi; MavenTrade-Server broker'ında bu isim yok, gerçek isim
**US100**. Bu yüzden NQ_ORB/SWEEP_CORE/SWEEP_ES_DIV önceden sessizce
atlanıyordu. Ayrıca "BTC bu broker'da yok" notu yanlıştı — **BTCUSD** CFD
olarak mevcut (Cryptocurrencies\BTCUSD), sadece OF_ABSORPTION modülü ayrı
Binance-spot altyapısı istediği için hâlâ bağlanmadı.

| Modül | Ağırlık | Durum |
|---|---|---|
| GOLD_NY_ORB_TREND | 1.0 | ✅ devrede (45g: 14 trade, win %57.1, +0.026R — backtest uyumlu) |
| NQ_ORB_STRONG_TREND | 1.0 | ✅ devrede (45g: 14 trade, win %57.1, +0.389R — yönü doğru, örneklem küçük) |
| SWEEP_CORE_AVOID_MID_VWAP | 1.0 | ✅ devrede (45g: 3 trade, win %66.7, +1.883R — yönü doğru, örneklem çok küçük) |
| EUR_LONDON_FADE_EMA | 1.0 | ✅ devrede (45g: 0 trade — sinyal hiç tetiklenmedi, filtre aşırı seyrek) |
| GBP_LONDON_STRONG_TREND | 0.25 | ✅ devrede (45g: 3 trade, win %33.3, +0.097R — zayıf, örneklem yetersiz) |
| SWEEP_ES_DIV | 2.0 | ❌ **KALDIRILDI 2026-07-04** — sahte edge (bkz. aşağı) |
| BTCUSDT_OF_ABSORPTION | 0.11 | ✖ Binance spot feed ister, MT5'e hiç wire edilmedi |

**SWEEP_ES_DIV neden kaldırıldı:** Backtest'te avg_loss **−0.09R** çıkıyordu
(19 işlem, %47.4 win, exp_R +0.210 iddiası) — bu fiziksel olarak imkânsız,
gerçek bir SL kaybı ~−1.0R olmalı. Kanıtladı ki modülün iğne-ince stop'u
(sweep dibi − 0.25×ATR, ~7-13 puan risk) temiz dukascopy verisinde hiç
tetiklenmemiş, timeout'ta başabaşa yakın kapanmış. Canlı US100 CFD
gürültüsünde aynı stop'lar anında vuruluyor (bars_held 1-4): forward'da
10 trade, **%20 win, −0.330R net, avg_loss −1.14R**. En yüksek ağırlığa
(w=2.0) sahip olması riski büyütüyordu — `default_modules()`'tan silindi.

**Doğrulanmış canlı portföy (45g backfill, 5 modül, sembol düzeltmesi sonrası):**
44 trade, win %47.7, toplam +8.45R, weighted +4.93R.

> Forward testin değeri: hem eski EUR/GBP wiring sorununu hem de bugün
> SWEEP_ES_DIV'in sahte backtest edge'ini **yakaladı**. Backtest'in görünürde
> kazandırdığı bir modül canlı feed'de kayıp çıkardı — forward test olmasa
> bu portföyde kalıp riski büyütecekti.

## Yeni modül ekleme
`modules.py` içinde `LiveModule(name, symbol_key, tf, weight, max_hold_bars, detect)`
tanımla. `detect(df) -> Signal|None` son kapanmış bara bakar. `default_modules()`
listesine ekle. `live_runner` ve `positions` değişmeden çalışır.

## Kapalı döngü (asıl değer)
```
GA gold adayı -> modules.py'de gold detektör paramlarını güncelle ->
forward EA ile demo'da canlı izle -> backtest ile tutuyorsa benimse
```
Çıktılar: `outputs/intraday/forward_ea/forward_ledger.csv`, `forward_state.json`

---

## Bulut defteri (`cloud_runner.py`) — 2026-08-20

**Çözdüğü sorun:** yukarıdaki motor MT5 terminaline bağlı. Terminal kapalıyken
döngü hiç koşmaz; 2026-08 başında bu yüzden günlerce delik oluştu
(`runner.log`'da 1000+ "terminal kapalı" kaydı). Ölçüm durunca kanıt birikmiyor.

Bulut koşucusu **aynı modülleri aynı döngüyle** (`engine.cycle`) bedava
feed'lerden besler ve GitHub Actions'ta saatlik koşar
(`.github/workflows/cloud_ledger.yml`). PC kapalıyken de defter ilerler.

```bash
python -m intraday.forward_ea.cloud_runner --once
python -m intraday.forward_ea.cloud_runner --once --warmup 14   # sadece ilk kurulum
```

### İki defter AYRI tutulur — birleştirme
| dosya | feed | ne işe yarar |
|---|---|---|
| `forward_ledger.csv` | MT5 (broker CFD'si) | **referans**; modül tier/risk kararları buna dayanır |
| `cloud_ledger.csv` | yfinance vadeli + Binance | deliksiz paralel ölçüm, `source` kolonu ile |

İlk 14 günlük backfill'de ölçüldü: **aynı feed'i paylaşan BTC satırları birebir
aynı** (Binance her iki tarafta da aynı), ama endeks/FX modüllerinde işlem
sayısı ve R farklı çıkıyor (MT5 55 işlem +21.58R, bulut 35 işlem +0.60R aynı
pencerede). Sebep: vadeli/CFD baz farkı + seans saati ve bar hizalaması.

**Bunun anlamı:** bulut defteri MT5 defterinin YERİNE geçmez. Modül terfisi
hâlâ MT5 defterine bakar. Bulut defteri (a) terminal kapalıyken bile sinyal
üretiminin sürdüğünü kaydeder, (b) "aynı strateji başka bir feed'de de para
kazanıyor mu" sorusunu bağımsız olarak ölçer.

### Kurallar
- `backfill=1` satırlar geçmiş veriden üretildi = **backtest**, forward kanıtı değil.
- Bulut koşucusu Telegram'a çıkmaz, emir atmaz, broker'a bağlanmaz — bildirim
  işini bulut signalbot yapıyor; iki taraf da gönderse sinyal iki kere düşerdi.
- Kalıcılık repo'da, Actions cache'inde değil: cache 7 gün dokunulmazsa silinir,
  bu işin varlık sebebi tam olarak delikti.
- Defter satırı `(modül, sembol, giriş zamanı)` ile tekilleştirilir; state
  kaybolsa bile aynı işlem ikinci kez yazılmaz.
