"""Intraday strateji laboratuvarı - merkezi konfigürasyon.

Hedef enstrümanlar: NASDAQ100 (E-mini NQ), EURUSD, GBPUSD.
Tüm maliyet/spread varsayımları gerçekçi tutuldu; backtest sonuçları
maliyet sonrasıdır (after-cost).
"""
from __future__ import annotations

from dataclasses import dataclass


# --- Enstrüman tanımları -------------------------------------------------
# Dukascopy sembol sabitleri data.py içinde isimle çözülür.
@dataclass(frozen=True)
class Instrument:
    key: str                 # iç anahtar
    duka: str                # dukascopy_python.instruments sabit adı
    # maliyet: fiyatın oranı olarak tek-yön (spread + komisyon + kayma)
    cost_per_side: float
    # tipik seans (UTC saat aralığı) - en likit pencere
    session_utc: tuple[int, int]
    pip: float               # 1 pip / 1 puan büyüklüğü (raporlama için)


INSTRUMENTS: dict[str, Instrument] = {
    # FX majors: ~0.6-1.0 pip spread + minik komisyon -> ~0.00007 oran
    "EURUSD": Instrument("EURUSD", "INSTRUMENT_FX_MAJORS_EUR_USD", 0.00007, (7, 20), 0.0001),
    "GBPUSD": Instrument("GBPUSD", "INSTRUMENT_FX_MAJORS_GBP_USD", 0.00009, (7, 20), 0.0001),
    # NASDAQ100 E-mini: ~1-2 puan spread, ~18000 fiyatta ~0.00009 oran
    "NASDAQ100": Instrument("NASDAQ100", "INSTRUMENT_IDX_AMERICA_E_NQ_100", 0.00009, (13, 21), 1.0),
    # S&P500 E-mini: ~0.5 puan spread, ~5500 fiyatta ~0.00009 oran
    "SP500": Instrument("SP500", "INSTRUMENT_IDX_AMERICA_E_SANDP_500", 0.00009, (13, 21), 0.25),
    # XAUUSD (altın): ~20-30 cent spread, ~2400 fiyatta ~0.00012 oran. Hem
    # Londra hem NY likit -> geniş seans (7-21 UTC).
    "XAUUSD": Instrument("XAUUSD", "INSTRUMENT_FX_METALS_XAU_USD", 0.00012, (7, 21), 0.1),
    # BTCUSDT (Binance): taker fee ~0.04-0.075% + kayma -> ~0.0006/yön. 7/24.
    "BTCUSDT": Instrument("BTCUSDT", "BINANCE_BTCUSDT", 0.0006, (0, 24), 1.0),
    # XAGUSD (gümüş): ~2-5 cent spread, ~30$ fiyatta ~0.0003-0.0006/yön. Londra+NY likit.
    "XAGUSD": Instrument("XAGUSD", "INSTRUMENT_FX_METALS_XAG_USD", 0.0004, (7, 21), 0.001),
}


# --- Zaman dilimleri -----------------------------------------------------
ENTRY_TF = "15m"          # giriş zaman dilimi
ENTRY_FREQ = "15min"      # pandas/vectorbt frekansı
HTF_RULE = "1H"           # trend filtresi (1H veya 4H denenir)

# --- Backtest sermaye/risk ----------------------------------------------
INIT_CASH = 10_000.0
RISK_PER_TRADE_PCT = 0.5      # işlem başına risk (%)
MAX_TRADES_PER_DAY = 3
COOLDOWN_BARS = 4             # ardışık sinyaller arası min bar

# --- Setup kalite filtresi ----------------------------------------------
# Esnek RR: yapı/likidite seviyesine TP. Bu değerin altındaki setup atlanır.
MIN_RR = 2.5
MAX_RR = 6.0                  # aşırı uzak TP'leri 6R'ye sınırla (gerçekçilik)
ATR_LEN = 14
SL_ATR_BUFFER = 0.25         # SL'ye eklenen ATR tamponu (fitil avı koruması)

# --- Veri penceresi ------------------------------------------------------
LOOKBACK_DAYS = 540          # ~18 ay 15m geçmiş

# --- Çıktı ---------------------------------------------------------------
STRATEGIES = ["smc_sweep", "vwap_pullback", "orb"]
