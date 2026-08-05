"""MT5 reality bridge.

Python honest-engine backtest sonuclarinin gercek emir mikro-yapisina
(spread + slippage) ne kadar dayandigini olcen kopru.

Moduller:
  mt5_io                 -> MT5 baglanti + sembol haritasi + OHLCV/tick cekme
  reality_profiler       -> sembol basina gercek spread/slippage profili
  apply_reality_discount -> profili ledger'a uygulayip reality-adjusted pass uret

Not: bu broker (MetaQuotes-Demo) FX/metals/indekslerde calisir; spot kripto
yoktur (BTC = Grayscale ETF). BTC reality-check'i Binance verisinden ayri
yapilmalidir.
"""
