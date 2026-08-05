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
    # US30 / US2000: dukascopy karsiligi yok (duka=""), sadece MT5 CFD'si olarak
    # kullanilir. Maliyetler 2026-08-02'de MT5'ten OLCULDU (tahmin degil):
    #   US30   spread 27.0 puan @ ~52600 -> 5.13 bps -> tek yon 2.56e-04
    #   US2000 spread  0.80 puan @ ~2950 -> 2.71 bps -> tek yon 1.36e-04
    # US30 spread'i NASDAQ'in ~3.7 katidir; strateji karliligini ciddi etkiler.
    "US30": Instrument("US30", "", 0.000256, (13, 21), 1.0),
    "US2000": Instrument("US2000", "", 0.000136, (13, 21), 0.1),
    # Dusuk-maliyetli endeksler (spread<2.5 bps, MT5'ten 2026-08-03'te olculdu).
    # Sweep'in maliyet duyarliligi kanitlandi: korelasyon(spread, exp_R) = -0.731.
    # Seans (13,21) ABD saatine gore; sweep seanstan bagimsiz calisir (VWAP+ADX).
    "UK100": Instrument("UK100", "", 0.0000595, (7, 21), 0.1),
    "FRA40": Instrument("FRA40", "", 0.0000935, (7, 21), 0.1),
    "JAP225": Instrument("JAP225", "", 0.000110, (0, 21), 1.0),
    # XAUUSD (altın): ~20-30 cent spread, ~2400 fiyatta ~0.00012 oran. Hem
    # Londra hem NY likit -> geniş seans (7-21 UTC).
    "XAUUSD": Instrument("XAUUSD", "INSTRUMENT_FX_METALS_XAU_USD", 0.00012, (7, 21), 0.1),
    # BTCUSDT (Binance): taker fee ~0.04-0.075% + kayma -> ~0.0006/yön. 7/24.
    "BTCUSDT": Instrument("BTCUSDT", "BINANCE_BTCUSDT", 0.0006, (0, 24), 1.0),
    # XAGUSD (gümüş): ~2-5 cent spread, ~30$ fiyatta ~0.0003-0.0006/yön. Londra+NY likit.
    "XAGUSD": Instrument("XAGUSD", "INSTRUMENT_FX_METALS_XAG_USD", 0.0004, (7, 21), 0.001),
    # --- Karakter röntgeni için taranmamış pariteler (2026-07-10) --------
    # JPY çiftleri: Tokyo (0-7) + Londra (7-13) likit. pip=0.01.
    "USDJPY": Instrument("USDJPY", "INSTRUMENT_FX_MAJORS_USD_JPY", 0.00007, (0, 13), 0.01),
    "EURJPY": Instrument("EURJPY", "INSTRUMENT_FX_CROSSES_EUR_JPY", 0.00009, (0, 13), 0.01),
    # GBPJPY: geniş spread (~2-3 pip), yüksek volatilite "canavar".
    "GBPJPY": Instrument("GBPJPY", "INSTRUMENT_FX_CROSSES_GBP_JPY", 0.00016, (0, 13), 0.01),
    # Majors: Londra+NY likit (7-20). pip=0.0001.
    "AUDUSD": Instrument("AUDUSD", "INSTRUMENT_FX_MAJORS_AUD_USD", 0.00009, (7, 20), 0.0001),
    "USDCAD": Instrument("USDCAD", "INSTRUMENT_FX_MAJORS_USD_CAD", 0.00007, (7, 20), 0.0001),
    "USDCHF": Instrument("USDCHF", "INSTRUMENT_FX_MAJORS_USD_CHF", 0.00011, (7, 20), 0.0001),
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
