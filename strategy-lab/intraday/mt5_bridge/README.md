# MT5 Reality Bridge (a)

Python honest-engine backtest sonuçlarının **gerçek emir mikro-yapısına**
(spread + slippage) ne kadar dayandığını ölçer. Pine/TradingView görselleştirme
gerçeklik kontrolü vermez; bu köprü verir.

## Gereksinim
- MetaTrader 5 terminali kurulu + **açık** + bir hesap girili (demo yeterli).
- `pip install MetaTrader5` (yalnızca Windows).

## Akış
```bash
# 1) Gerçek spread + slippage profilini ölç (config.cost_per_side ile kıyas)
python -m intraday.mt5_bridge.reality_profiler

# 2) Profili final ledger'a uygula -> reality-adjusted pass
python -m intraday.mt5_bridge.apply_reality_discount
```

## Modüller
| Dosya | Sorumluluk |
|---|---|
| `mt5_io.py` | MT5 bağlantı, sembol haritası, OHLCV/tick çekme. Strateji yok. |
| `reality_profiler.py` | Sembol başına gerçek tek-yön maliyet (spread + slippage + fiyat-seviye düzeltmesi). |
| `apply_reality_discount.py` | Maliyet farkını R cezasına çevirip challenge sim'i yeniden koşar. |

## ⚠️ Terminal koruması (2026-08-06)

`mt5.initialize()` argümansız çağrılınca terminal kapalıysa **onu kendisi
başlatır**. Forward EA 5 dakikada bir koştuğu için MT5 sürekli geri açılıyordu;
bu yüzden Task Scheduler görevi kapatılmış ve veri toplama durmuştu.

`initialize()` artık önce `_terminal_running()` (tasklist ile) kontrol eder;
terminal kapalıysa `mt5.initialize()` **hiç çağrılmaz**, anlaşılır bir
`MT5Error` fırlatır ve döngü sessizce atlar. Tespit edilemezse `True` döner —
yanlış negatif botu sessizce öldürürdü.

**Sonuç:** MT5'i sen açarsın, bot asla açmaz. Kapalıyken zarar yok, açınca
kaldığı yerden devam eder.

## Binance feed (BTC)

BTC bu broker'da spot olarak yok. `live_runner._fetch_ohlcv` `BTCUSDT`/`BTC`
anahtarlarını Binance public API'ye yönlendirir (key gerekmez).

**Kritik:** Binance tz-**aware** index döner, bu modül tz-**naive** döner
("UTC index, tz-naive" sözleşmesi). `_binance_ohlcv` normalize eder. Karışık
kalırsa defter yazımı patlar ve hata `_save_state` içinde olduğu için o
döngüdeki **tüm modüllerin** kaydı kaybolur.

## Sembol durumu (MavenTrade-Server — güncellendi 2026-08-05)
| Modül sembolü | MT5 adı | Durum |
|---|---|---|
| NASDAQ100 | `US100` | var. **`USTEC` DEĞİL** — bu broker'da o isim yok. |
| SP500 | `US500` | var |
| US30 / US2000 | `US30` / `US2000` | var (maliyet 2026-08-02'de ölçüldü) |
| UK100 / FRA40 / JAP225 | aynı | var (düşük spread, <2.5 bps) |
| XAUUSD | `XAUUSD` | var |
| EURUSD / GBPUSD | aynı | var |
| BTCUSDT | `BTCUSD` (CFD) | CFD var, ama OF_ABSORPTION Binance-spot ister → bağlı değil |

> ⚠️ `USTEC` yanlış eşleme 2026-07-04'te düzeltildi (NQ/SWEEP modülleri o zamana
> kadar sessizce atlanıyordu). Eski `USTEC` referansı gören yer kalırsa bayattır.
> Bu isim 2026-08-05'te `test_order_executor.py` fixture'ında da bulundu ve
> düzeltildi — test 1 aydır kırıktı, "bize ait değil" diye yanlış etiketlenmişti.

## Maliyet → R dönüşümü
```
delta_R = -2 * max(real_cost - assumed_cost, 0) / stop_ratio
real_cost   = period_adj_spread + slippage_p90 * slip_mult
stop_ratio  = median(ATR_14 / close) * 1.5   (MT5'ten ölçülür)
```
Muhafazakâr: sadece config'in **iyimser** olduğu sembollerde ceza uygulanır;
muhafazakâr sembollere kredi verilmez. Slippage çarpanı ile duyarlılık bandı
(0.5x / 1.0x / 2.0x) üretilir.

## İlk bulgular (2026-06-16)
- Ham spread tüm sembollerde config'ten düşük; ama slippage + fiyat-seviye
  düzeltmesi eklenince **NASDAQ100 (0.56x) ve SP500 (0.80x) config İYİMSER** çıktı.
- Reality-adjusted pass: kâğıt %51.0 → orta tahmin **%50.8** (−0.3 puan),
  kötümser slip×2 %47.7 (totalDD %10.95). Hedef gerçekçi maliyetlere dayanıyor.

Çıktılar: `outputs/intraday/mt5_bridge/`
