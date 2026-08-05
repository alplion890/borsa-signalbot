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

## Sembol durumu (MetaQuotes-Demo)
| Modül sembolü | MT5 adı | Durum |
|---|---|---|
| NASDAQ100 | `USTEC` | var (geçmiş 2022+) |
| SP500 | `US500` | var (2015+) |
| XAUUSD | `XAUUSD` | var (2015+) |
| EURUSD | `EURUSD` | var (2015+) |
| BTCUSDT | — | **YOK** (BTC = Grayscale ETF). Binance'ten ayrı kontrol. |

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
