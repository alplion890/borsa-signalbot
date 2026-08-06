# Borsa Canlı Sinyal Botu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bedava-bulut Telegram sinyal botu — 7/24 cron ile yfinance/Binance verisini mevcut strateji dedektörlerine besler, LIVE/PAPER etiketli sade-Türkçe sinyalleri telefona yollar. Emir icrası YOK (Maven yasak).

**Architecture:** `free_data.py` mevcut `mt5_io.ohlcv` ile AYNI şekilli DataFrame (DatetimeIndex UTC + open/high/low/close/volume) döndürür; böylece `forward_ea/modules.py` içindeki kanıtlı dedektörler değişmeden kullanılır. `signal_scan.py` modülleri çalıştırır, tier etiketler, lot hesaplar, `telegram_notify.py` ile yollar. GitHub Actions cron seans-gated tetikler. Sırlar (token/chat_id) GitHub Secrets + lokal `.env`.

**Tech Stack:** Python 3.11, pandas, yfinance, requests (Binance + Telegram), python-dotenv, pytest, GitHub Actions.

---

## Faz Notu

- **Faz 1 (YARIN kritik):** Task 1-10. DataFrame-enjekte edilebilen 5 modül (Gold ORB, NQ ORB, Sweep core, EUR London, GBP London) + Telegram + scan + workflow. Yarın NY/London seansında sinyal verir.
- **Faz 2 (sonra):** Task 11. ES-Div feed wiring (SP500+NQ çift-feed), BTC Absorption dedektörü, parity skorkartı.

Yeni paket dizini: `strategy-lab/intraday/signalbot/`. Mevcut `forward_ea` ve `mt5_bridge` koduna dokunulmaz; sadece import edilir.

---

## Task 1: Proje iskeleti + bağımlılıklar + .env koruması

**Files:**
- Create: `strategy-lab/intraday/signalbot/__init__.py`
- Create: `strategy-lab/intraday/signalbot/requirements.txt`
- Create: `strategy-lab/intraday/signalbot/.env.example`
- Modify: `.gitignore`

- [ ] **Step 1: requirements.txt yaz**

```
pandas>=2.0
yfinance>=0.2.40
requests>=2.31
python-dotenv>=1.0
pytest>=8.0
```

- [ ] **Step 2: .env.example yaz (gerçek değer YOK)**

```
# GitHub Secrets ile birebir aynı isimler. Lokal test için bu dosyayı .env olarak kopyala.
TELEGRAM_BOT_TOKEN=koy-buraya
TELEGRAM_CHAT_ID=koy-buraya
PHASE=challenge
ACCOUNT_BALANCE=5000
```

- [ ] **Step 3: __init__.py boş oluştur** (tek satır boş dosya)

- [ ] **Step 4: .gitignore'a .env ekle**

`.gitignore` dosyasına şu satırları ekle (yoksa):

```
.env
strategy-lab/intraday/signalbot/.env
```

- [ ] **Step 5: Doğrula — .env ignore ediliyor mu**

Run: `cd strategy-lab/intraday/signalbot && printf 'TELEGRAM_BOT_TOKEN=x\n' > .env && cd ../../.. && git check-ignore strategy-lab/intraday/signalbot/.env`
Expected: yol basılır (ignore ediliyor). Test sonrası: `rm strategy-lab/intraday/signalbot/.env`

- [ ] **Step 6: Commit**

```bash
git add strategy-lab/intraday/signalbot/__init__.py strategy-lab/intraday/signalbot/requirements.txt strategy-lab/intraday/signalbot/.env.example .gitignore
git commit -m "chore: signalbot iskelet + .env koruması"
```

---

## Task 2: Sembol haritası + provider yönlendirme

**Files:**
- Create: `strategy-lab/intraday/signalbot/symbols.py`
- Test: `strategy-lab/intraday/signalbot/test_symbols.py`

Detektörlerin `symbol_key` değerleri (modules.py): `XAUUSD, NASDAQ100, EURUSD, GBPUSD, SP500`. Bunları yfinance/Binance kaynağına eşler.

- [ ] **Step 1: Failing test yaz**

```python
# test_symbols.py
from strategy_lab.intraday.signalbot.symbols import resolve, Source

def test_gold_maps_to_yfinance_gc():
    s = resolve("XAUUSD")
    assert s.source == Source.YFINANCE
    assert s.ticker == "GC=F"

def test_btc_maps_to_binance():
    s = resolve("BTC")
    assert s.source == Source.BINANCE
    assert s.ticker == "BTCUSDT"

def test_unknown_raises():
    import pytest
    with pytest.raises(KeyError):
        resolve("DOGECOIN")
```

- [ ] **Step 2: Test fail doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_symbols.py -v`
Expected: FAIL (module yok)

- [ ] **Step 3: symbols.py yaz**

```python
"""symbol_key -> bedava veri kaynağı eşlemesi. Tek değişiklik noktası."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Source(str, Enum):
    YFINANCE = "yfinance"
    BINANCE = "binance"


@dataclass(frozen=True)
class SymbolSpec:
    source: Source
    ticker: str


_MAP: dict[str, SymbolSpec] = {
    "XAUUSD":    SymbolSpec(Source.YFINANCE, "GC=F"),
    "NASDAQ100": SymbolSpec(Source.YFINANCE, "NQ=F"),
    "SP500":     SymbolSpec(Source.YFINANCE, "ES=F"),
    "EURUSD":    SymbolSpec(Source.YFINANCE, "EURUSD=X"),
    "GBPUSD":    SymbolSpec(Source.YFINANCE, "GBPUSD=X"),
    "BTC":       SymbolSpec(Source.BINANCE, "BTCUSDT"),
}


def resolve(symbol_key: str) -> SymbolSpec:
    if symbol_key not in _MAP:
        raise KeyError(f"bilinmeyen symbol_key: {symbol_key}")
    return _MAP[symbol_key]
```

- [ ] **Step 4: Test pass doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_symbols.py -v`
Expected: PASS (3 test)

- [ ] **Step 5: Commit**

```bash
git add strategy-lab/intraday/signalbot/symbols.py strategy-lab/intraday/signalbot/test_symbols.py
git commit -m "feat: signalbot sembol-kaynak eşlemesi"
```

---

## Task 3: yfinance veri adaptörü (mt5_io şekliyle)

**Files:**
- Create: `strategy-lab/intraday/signalbot/free_data.py`
- Test: `strategy-lab/intraday/signalbot/test_free_data.py`

Dedektörler `df` bekliyor: DatetimeIndex (UTC), sütunlar `open, high, low, close, volume` (küçük harf). yfinance büyük harf + tz-aware verir → normalize et.

- [ ] **Step 1: Failing test yaz (offline, monkeypatch)**

```python
# test_free_data.py
import pandas as pd
import numpy as np
from strategy_lab.intraday.signalbot import free_data

def _fake_yf_df():
    idx = pd.date_range("2026-06-18 13:00", periods=5, freq="5min", tz="America/New_York")
    return pd.DataFrame({
        "Open": np.arange(5.0), "High": np.arange(5.0)+1,
        "Low": np.arange(5.0)-1, "Close": np.arange(5.0)+0.5,
        "Volume": np.arange(5.0)*10,
    }, index=idx)

def test_yfinance_normalized_shape(monkeypatch):
    monkeypatch.setattr(free_data, "_yf_download", lambda *a, **k: _fake_yf_df())
    df = free_data.ohlcv("XAUUSD", "5m", days=1)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert str(df.index.tz) == "UTC"
    assert len(df) == 5
```

- [ ] **Step 2: Test fail doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_free_data.py -v`
Expected: FAIL

- [ ] **Step 3: free_data.py yaz**

```python
"""Bedava veri adaptörü — mt5_io.ohlcv ile AYNI şekil döndürür.

Dönüş: DatetimeIndex(UTC), sütunlar open/high/low/close/volume (float).
Böylece forward_ea/modules.py dedektörleri değişmeden çalışır.
"""
from __future__ import annotations
import pandas as pd
from .symbols import resolve, Source

_TF_YF = {"5m": "5m", "15m": "15m", "1H": "60m"}


def _yf_download(ticker: str, interval: str, period: str) -> pd.DataFrame:
    import yfinance as yf
    return yf.download(ticker, interval=interval, period=period,
                       progress=False, auto_adjust=False)


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    idx = pd.DatetimeIndex(df.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    df = df.set_axis(idx).astype(float)
    return df[~df.index.duplicated(keep="last")].sort_index()


def _period_for(days: int) -> str:
    return f"{max(1, min(days, 59))}d"


def ohlcv(symbol_key: str, tf: str, days: int = 60) -> pd.DataFrame:
    spec = resolve(symbol_key)
    if spec.source is Source.YFINANCE:
        raw = _yf_download(spec.ticker, _TF_YF[tf], _period_for(days))
        return _normalize(raw)
    if spec.source is Source.BINANCE:
        from .binance_data import klines
        return klines(spec.ticker, tf, days)
    raise ValueError(f"desteklenmeyen kaynak: {spec.source}")
```

- [ ] **Step 4: Test pass doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_free_data.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add strategy-lab/intraday/signalbot/free_data.py strategy-lab/intraday/signalbot/test_free_data.py
git commit -m "feat: yfinance adaptörü (mt5_io şekli)"
```

---

## Task 4: Binance veri adaptörü (BTC)

**Files:**
- Create: `strategy-lab/intraday/signalbot/binance_data.py`
- Test: `strategy-lab/intraday/signalbot/test_binance_data.py`

- [ ] **Step 1: Failing test yaz (offline)**

```python
# test_binance_data.py
from strategy_lab.intraday.signalbot import binance_data

_SAMPLE = [
    [1781800000000, "100", "110", "90", "105", "12.5", 0, 0, 0, 0, 0, 0],
    [1781803600000, "105", "115", "95", "108", "9.0", 0, 0, 0, 0, 0, 0],
]

def test_klines_normalized(monkeypatch):
    monkeypatch.setattr(binance_data, "_get", lambda *a, **k: _SAMPLE)
    df = binance_data.klines("BTCUSDT", "1H", days=1)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert str(df.index.tz) == "UTC"
    assert float(df["close"].iloc[-1]) == 108.0
```

- [ ] **Step 2: Test fail doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_binance_data.py -v`
Expected: FAIL

- [ ] **Step 3: binance_data.py yaz**

```python
"""Binance public klines -> mt5_io şekli. Key gerekmez."""
from __future__ import annotations
import pandas as pd
import requests

_TF_BINANCE = {"5m": "5m", "15m": "15m", "1H": "1h"}
_BASE = "https://api.binance.com/api/v3/klines"


def _get(symbol: str, interval: str, limit: int) -> list:
    r = requests.get(_BASE, params={"symbol": symbol, "interval": interval,
                                    "limit": limit}, timeout=15)
    r.raise_for_status()
    return r.json()


def klines(symbol: str, tf: str, days: int = 60) -> pd.DataFrame:
    per_day = {"5m": 288, "15m": 96, "1H": 24}[tf]
    limit = min(1000, max(200, per_day * days))
    rows = _get(symbol, _TF_BINANCE[tf], limit)
    df = pd.DataFrame(rows, columns=[
        "ot", "open", "high", "low", "close", "volume",
        "ct", "qv", "n", "tb", "tq", "ig"])
    idx = pd.to_datetime(df["ot"], unit="ms", utc=True)
    out = df[["open", "high", "low", "close", "volume"]].astype(float)
    return out.set_axis(pd.DatetimeIndex(idx)).sort_index()
```

- [ ] **Step 4: Test pass doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_binance_data.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add strategy-lab/intraday/signalbot/binance_data.py strategy-lab/intraday/signalbot/test_binance_data.py
git commit -m "feat: Binance BTC adaptörü"
```

---

## Task 5: Lot/risk hesabı + tier eşlemesi

**Files:**
- Create: `strategy-lab/intraday/signalbot/risk.py`
- Test: `strategy-lab/intraday/signalbot/test_risk.py`

Lot = risk_$ / (stop_mesafesi * birim_değeri). LIVE modüller (Gold/NQ) için birim değer doğru; FX paper tier (implementer config'ten düzeltir).

- [ ] **Step 1: Failing test yaz**

```python
# test_risk.py
from strategy_lab.intraday.signalbot.risk import lot_for, risk_dollars, Tier, tier_of

def test_risk_dollars_challenge():
    assert risk_dollars("challenge", 5000) == 75.0

def test_risk_dollars_funded():
    assert risk_dollars("funded", 5000) == 25.0

def test_lot_positive():
    assert lot_for("XAUUSD", entry=4225.0, sl=4214.0, risk_usd=75.0) > 0

def test_tier_live_for_orb():
    assert tier_of("GOLD_NY_ORB_TREND") is Tier.LIVE
    assert tier_of("NQ_ORB_STRONG_TREND") is Tier.LIVE

def test_tier_paper_for_rest():
    assert tier_of("SWEEP_CORE_AVOID_MID_VWAP") is Tier.PAPER
    assert tier_of("EUR_LONDON_FADE_EMA") is Tier.PAPER
```

- [ ] **Step 2: Test fail doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_risk.py -v`
Expected: FAIL

- [ ] **Step 3: risk.py yaz**

```python
"""Risk/lot hesabı + LIVE/PAPER tier eşlemesi."""
from __future__ import annotations
from enum import Enum

_RISK_PCT = {"challenge": 0.015, "funded": 0.005}

# Enstrüman başına 1 lot için 1 puan hareketin $ değeri.
# LIVE modüller (Gold/NQ) doğru; FX paper -> implementer config.py'den düzeltir (~10$/pip/lot).
_VALUE_PER_POINT = {
    "XAUUSD": 100.0,    # 1 lot = 100 oz
    "NASDAQ100": 20.0,  # NQ 1 puan = 20$
    "SP500": 50.0,      # ES 1 puan = 50$
    "EURUSD": 100000.0, # FX: lot*price-move; implementer pip-değeriyle düzeltir
    "GBPUSD": 100000.0,
    "BTC": 1.0,
}

_LIVE_MODULES = {"GOLD_NY_ORB_TREND", "NQ_ORB_STRONG_TREND"}


class Tier(str, Enum):
    LIVE = "LIVE"
    PAPER = "PAPER"


def tier_of(module_name: str) -> Tier:
    return Tier.LIVE if module_name in _LIVE_MODULES else Tier.PAPER


def risk_dollars(phase: str, balance: float) -> float:
    return round(balance * _RISK_PCT[phase], 2)


def lot_for(symbol_key: str, entry: float, sl: float, risk_usd: float) -> float:
    dist = abs(entry - sl)
    if dist <= 0:
        return 0.0
    vpp = _VALUE_PER_POINT[symbol_key]
    return max(0.01, round(risk_usd / (dist * vpp), 2))
```

> Implementer notu: `strategy-lab/intraday/config.py` `INSTRUMENTS[symbol_key]` gerçek contract/cost bilgisini taşır. FX (EURUSD/GBPUSD) için `_VALUE_PER_POINT`'i oradan doğrula (standart lot ~10$/pip). LIVE modüller doğru olduğundan yarın için kritik değil.

- [ ] **Step 4: Test pass doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_risk.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add strategy-lab/intraday/signalbot/risk.py strategy-lab/intraday/signalbot/test_risk.py
git commit -m "feat: risk/lot hesabı + tier eşlemesi"
```

---

## Task 6: Sade-Türkçe mesaj biçimlendirme

**Files:**
- Create: `strategy-lab/intraday/signalbot/message.py`
- Test: `strategy-lab/intraday/signalbot/test_message.py`

KULLANICI GEREKSİNİMİ: insan gibi düz yazı, sade, minimum noktalama, emoji yok.

- [ ] **Step 1: Failing test yaz**

```python
# test_message.py
from strategy_lab.intraday.signalbot.message import format_signal
from strategy_lab.intraday.signalbot.risk import Tier

def test_live_message_plain_prose():
    msg = format_signal(
        tier=Tier.LIVE, module="GOLD_NY_ORB_TREND", symbol_key="XAUUSD",
        direction=1, entry=4225.0, sl=4214.0, tp=4247.0, lot=0.68,
        risk_usd=75.0, trt_time="16 42")
    assert "long" in msg.lower()
    assert "4225" in msg and "4214" in msg and "4247" in msg
    assert msg.count("|") == 0
    assert "retest" in msg.lower()

def test_paper_message_has_warning():
    msg = format_signal(
        tier=Tier.PAPER, module="EUR_LONDON_FADE_EMA", symbol_key="EURUSD",
        direction=-1, entry=1.08, sl=1.084, tp=1.072, lot=0.5,
        risk_usd=75.0, trt_time="11 05")
    assert "paper" in msg.lower()
    assert "teyit" in msg.lower() or "kontrol" in msg.lower()
```

- [ ] **Step 2: Test fail doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_message.py -v`
Expected: FAIL

- [ ] **Step 3: message.py yaz**

```python
"""Telegram mesajı — sade Türkçe düz yazı, emoji/sembol yığını yok."""
from __future__ import annotations
from .risk import Tier

_HUMAN = {
    "GOLD_NY_ORB_TREND": "Gold ORB",
    "NQ_ORB_STRONG_TREND": "NQ ORB",
    "SWEEP_CORE_AVOID_MID_VWAP": "NQ sweep",
    "EUR_LONDON_FADE_EMA": "EUR London fade",
    "GBP_LONDON_STRONG_TREND": "GBP London trend",
    "SWEEP_ES_DIV": "NQ ES uyumsuzluk",
    "BTC_ABSORPTION": "BTC absorption",
}


def format_signal(*, tier: Tier, module: str, symbol_key: str, direction: int,
                  entry: float, sl: float, tp: float, lot: float,
                  risk_usd: float, trt_time: str) -> str:
    yon = "long" if direction == 1 else "short"
    ad = _HUMAN.get(module, module)
    if tier is Tier.LIVE:
        return (
            f"{ad} {yon} sinyali geldi. Yaklasik {entry:g} ten gir, "
            f"stop {sl:g}, hedef {tp:g}. Risk {risk_usd:g} dolar yani lot {lot:g}. "
            f"Saat {trt_time}. Retest girisi bekle, kirilimi kovalama."
        )
    return (
        f"Paper sinyali {ad} {yon}. Once chart ac ve teyit et, kalite iyiyse "
        f"funded hesabinda degerlendir. Yaklasik {entry:g} ten, stop {sl:g}, "
        f"hedef {tp:g}, lot {lot:g}. Saat {trt_time}."
    )
```

- [ ] **Step 4: Test pass doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_message.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add strategy-lab/intraday/signalbot/message.py strategy-lab/intraday/signalbot/test_message.py
git commit -m "feat: sade Türkçe sinyal mesajı"
```

---

## Task 7: Telegram gönderici (env'den sır)

**Files:**
- Create: `strategy-lab/intraday/signalbot/telegram_notify.py`
- Test: `strategy-lab/intraday/signalbot/test_telegram_notify.py`

- [ ] **Step 1: Failing test yaz (offline, requests monkeypatch)**

```python
# test_telegram_notify.py
from strategy_lab.intraday.signalbot import telegram_notify as tn

class _Resp:
    def raise_for_status(self): pass
    def json(self): return {"ok": True}

def test_send_uses_env_and_posts(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TESTTOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")
    captured = {}
    def fake_post(url, data, timeout):
        captured["url"] = url; captured["data"] = data
        return _Resp()
    monkeypatch.setattr(tn.requests, "post", fake_post)
    tn.send("merhaba")
    assert "TESTTOKEN" in captured["url"]
    assert captured["data"]["chat_id"] == "999"
    assert captured["data"]["text"] == "merhaba"

def test_send_raises_without_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    import pytest
    with pytest.raises(RuntimeError):
        tn.send("x")
```

- [ ] **Step 2: Test fail doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_telegram_notify.py -v`
Expected: FAIL

- [ ] **Step 3: telegram_notify.py yaz**

```python
"""Telegram gönderici. Token/chat_id YALNIZCA env'den. Asla hardcode/log."""
from __future__ import annotations
import os
import requests

_API = "https://api.telegram.org/bot{token}/sendMessage"


def send(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env eksik")
    resp = requests.post(_API.format(token=token),
                         data={"chat_id": chat_id, "text": text}, timeout=15)
    resp.raise_for_status()
```

- [ ] **Step 4: Test pass doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_telegram_notify.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add strategy-lab/intraday/signalbot/telegram_notify.py strategy-lab/intraday/signalbot/test_telegram_notify.py
git commit -m "feat: Telegram gönderici (env sır)"
```

---

## Task 8: Seans penceresi + TRT (sessions.py)

**Files:**
- Create: `strategy-lab/intraday/signalbot/sessions.py`
- Test: `strategy-lab/intraday/signalbot/test_sessions.py`

- [ ] **Step 1: Failing test yaz**

```python
# test_sessions.py
import datetime as dt
from strategy_lab.intraday.signalbot.sessions import to_trt, is_active

def test_to_trt_is_utc_plus_3():
    utc = dt.datetime(2026, 6, 18, 13, 42, tzinfo=dt.timezone.utc)
    assert to_trt(utc) == "16 42"

def test_btc_always_active():
    utc = dt.datetime(2026, 6, 18, 3, 0, tzinfo=dt.timezone.utc)
    assert is_active("BTC_ABSORPTION", utc) is True

def test_gold_orb_inactive_at_night():
    utc = dt.datetime(2026, 6, 18, 3, 0, tzinfo=dt.timezone.utc)
    assert is_active("GOLD_NY_ORB_TREND", utc) is False
```

- [ ] **Step 2: Test fail doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_sessions.py -v`
Expected: FAIL

- [ ] **Step 3: sessions.py yaz**

```python
"""Seans pencereleri UTC tabanlı. TRT gösterim = UTC+3 (sabit, DST yok)."""
from __future__ import annotations
import datetime as dt

# (utc_start_hour, utc_end_hour) — yaz referansı; DST toleransı için geniş.
_WINDOWS = {
    "GOLD_NY_ORB_TREND": (13, 16),
    "NQ_ORB_STRONG_TREND": (13, 17),
    "SWEEP_CORE_AVOID_MID_VWAP": (13, 21),
    "SWEEP_ES_DIV": (13, 21),
    "EUR_LONDON_FADE_EMA": (7, 11),
    "GBP_LONDON_STRONG_TREND": (7, 11),
    "BTC_ABSORPTION": None,  # 7/24
}


def to_trt(utc: dt.datetime) -> str:
    trt = utc.astimezone(dt.timezone(dt.timedelta(hours=3)))
    return f"{trt.hour:02d} {trt.minute:02d}"


def is_active(module_name: str, utc: dt.datetime) -> bool:
    win = _WINDOWS.get(module_name, None)
    if win is None:
        return True
    start, end = win
    return start <= utc.hour < end
```

- [ ] **Step 4: Test pass doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_sessions.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add strategy-lab/intraday/signalbot/sessions.py strategy-lab/intraday/signalbot/test_sessions.py
git commit -m "feat: seans penceresi + TRT"
```

---

## Task 9: Tarama orkestratörü + giriş scripti (MVP uç-uca)

**Files:**
- Create: `strategy-lab/intraday/signalbot/signal_scan.py`
- Create: `run_bot.py` (repo kökü giriş scripti, import yolunu ayarlar)
- Test: `strategy-lab/intraday/signalbot/test_signal_scan.py`

ES-Div (SP500 çift-feed, mt5_io çağırır) Faz 2'ye kadar `_SKIP_UNTIL_PHASE2` ile atlanır. Geri kalan 5 modül free_data ile beslenir.

- [ ] **Step 1: Failing test yaz**

```python
# test_signal_scan.py
import pandas as pd, numpy as np, datetime as dt
from strategy_lab.intraday.signalbot import signal_scan
from strategy_lab.intraday.forward_ea.modules import LiveModule, Signal

def _df():
    idx = pd.date_range("2026-06-18 09:00", periods=300, freq="5min", tz="UTC")
    p = np.linspace(4200, 4225, 300)
    return pd.DataFrame({"open": p, "high": p+1, "low": p-1,
                         "close": p, "volume": np.ones(300)*10}, index=idx)

def test_scan_emits_message_for_signal(monkeypatch):
    mod = LiveModule("GOLD_NY_ORB_TREND", "XAUUSD", "5m", 1.0, 48,
                     lambda df: Signal(1, 4225.0, 4214.0, 4247.0))
    monkeypatch.setattr(signal_scan, "_load_modules", lambda: [mod])
    monkeypatch.setattr(signal_scan.free_data, "ohlcv", lambda *a, **k: _df())
    monkeypatch.setattr(signal_scan.sessions, "is_active", lambda *a, **k: True)
    sent = []
    monkeypatch.setattr(signal_scan.telegram_notify, "send", lambda t: sent.append(t))
    now = dt.datetime(2026, 6, 18, 13, 42, tzinfo=dt.timezone.utc)
    signal_scan.run(now=now, phase="challenge", balance=5000.0)
    assert len(sent) == 1
    assert "long" in sent[0].lower()

def test_scan_skips_when_no_signal(monkeypatch):
    mod = LiveModule("GOLD_NY_ORB_TREND", "XAUUSD", "5m", 1.0, 48, lambda df: None)
    monkeypatch.setattr(signal_scan, "_load_modules", lambda: [mod])
    monkeypatch.setattr(signal_scan.free_data, "ohlcv", lambda *a, **k: _df())
    monkeypatch.setattr(signal_scan.sessions, "is_active", lambda *a, **k: True)
    sent = []
    monkeypatch.setattr(signal_scan.telegram_notify, "send", lambda t: sent.append(t))
    signal_scan.run(now=dt.datetime(2026,6,18,13,42,tzinfo=dt.timezone.utc),
                    phase="challenge", balance=5000.0)
    assert sent == []
```

- [ ] **Step 2: Test fail doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_signal_scan.py -v`
Expected: FAIL

- [ ] **Step 3: signal_scan.py yaz**

```python
"""Tarama orkestratörü. Mevcut dedektörleri bedava veriyle besler, yollar."""
from __future__ import annotations
import datetime as dt
import os

from . import free_data, sessions, telegram_notify
from .risk import lot_for, risk_dollars, tier_of
from .message import format_signal

# ES-Div mt5_io çağırır -> Faz 2'ye kadar atla (Task 11 shim ekleyince kaldır).
_SKIP_UNTIL_PHASE2 = {"SWEEP_ES_DIV"}


def _load_modules() -> list:
    from ..forward_ea.modules import default_modules
    return [m for m in default_modules() if m.name not in _SKIP_UNTIL_PHASE2]


def run(*, now: dt.datetime | None = None, phase: str | None = None,
        balance: float | None = None) -> None:
    now = now or dt.datetime.now(dt.timezone.utc)
    phase = phase or os.environ.get("PHASE", "challenge")
    balance = balance if balance is not None else float(os.environ.get("ACCOUNT_BALANCE", "5000"))
    risk_usd = risk_dollars(phase, balance)

    for mod in _load_modules():
        if not sessions.is_active(mod.name, now):
            continue
        try:
            df = free_data.ohlcv(mod.symbol_key, mod.tf, days=60)
        except Exception:
            continue  # veri kaynağı geçici hata -> sessizce atla, sonraki cron dener
        if df is None or len(df) < 200:
            continue
        sig = mod.detect(df)
        if sig is None:
            continue
        lot = lot_for(mod.symbol_key, sig.entry, sig.sl, risk_usd)
        msg = format_signal(
            tier=tier_of(mod.name), module=mod.name, symbol_key=mod.symbol_key,
            direction=sig.direction, entry=sig.entry, sl=sig.sl, tp=sig.tp,
            lot=lot, risk_usd=risk_usd, trt_time=sessions.to_trt(now))
        telegram_notify.send(msg)


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: Test pass doğrula**

Run: `cd strategy-lab/intraday/signalbot && python -m pytest test_signal_scan.py -v`
Expected: PASS (2 test)

- [ ] **Step 5: run_bot.py giriş scripti yaz (repo kökü)**

`strategy-lab` tire içerdiğinden `python -m strategy_lab...` çalışmaz. Kökten import yolunu ayarlayan giriş scripti:

```python
"""Repo kökü giriş scripti. GitHub Actions bunu çağırır."""
import sys, pathlib
root = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(root / "strategy-lab"))
from intraday.signalbot.signal_scan import run

if __name__ == "__main__":
    run()
```

> Not: signalbot içi importlar `strategy_lab.intraday...` yerine paket-içi göreli (`from . import`, `from ..forward_ea`) olduğu için `strategy-lab` `sys.path`'e eklenince `intraday` paketi import edilir. Testlerdeki `strategy_lab.intraday...` mutlak yolu için repo kökünde `conftest.py` veya `PYTHONPATH` ayarı Step 6'da.

- [ ] **Step 6: conftest.py ile test import yolu (repo kökü)**

Create: `conftest.py` (repo kökü) — testlerin `strategy_lab.intraday...` ve `intraday...` ikisini de çözebilmesi için:

```python
import sys, pathlib
root = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(root / "strategy-lab"))
```

Testlerde import `from intraday.signalbot...` olacak şekilde Step 1-8 importlarını `strategy_lab.intraday` -> `intraday` olarak güncelle (tek seferlik, tutarlı). Tüm testleri çalıştır:

Run: `cd "C:/Users/quantum/OneDrive/Masaüstü/borsa" && python -m pytest strategy-lab/intraday/signalbot -v`
Expected: tüm testler PASS

- [ ] **Step 7: Dry-run (token olmadan, import + akış)**

Run: `cd "C:/Users/quantum/OneDrive/Masaüstü/borsa" && python -c "import sys; sys.path.insert(0,'strategy-lab'); from intraday.signalbot import signal_scan; print('import OK')"`
Expected: `import OK`

- [ ] **Step 8: Commit**

```bash
git add strategy-lab/intraday/signalbot/signal_scan.py strategy-lab/intraday/signalbot/test_signal_scan.py run_bot.py conftest.py
git commit -m "feat: tarama orkestratörü + giriş scripti (MVP uç-uca)"
```

---

## Task 10: GitHub Actions workflow + README

**Files:**
- Create: `.github/workflows/signalbot.yml`
- Create: `strategy-lab/intraday/signalbot/README.md`

- [ ] **Step 1: workflow yaz**

```yaml
name: borsa-signalbot
on:
  schedule:
    - cron: "*/5 7-21 * * 1-5"   # hafta içi 07-21 UTC her 5 dk
    - cron: "0 * * * *"          # BTC saatlik (7/24)
  workflow_dispatch: {}

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r strategy-lab/intraday/signalbot/requirements.txt
      - name: Tara ve yolla
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          PHASE: challenge
          ACCOUNT_BALANCE: "5000"
        run: python run_bot.py
```

- [ ] **Step 2: README yaz**

```markdown
# Borsa Sinyal Botu

Maven challenge için 7/24 bedava-bulut sinyal botu. EMİR ICRASI YOK — sadece sinyal.

## Kurulum (kullanıcı, tek seferlik)
1. Telegram @BotFather ile bot oluştur, token al.
2. Bota mesaj at; https://api.telegram.org/bot<TOKEN>/getUpdates ile chat_id öğren.
3. Repo'yu GitHub'a push et.
4. Settings -> Secrets and variables -> Actions -> New secret:
   - TELEGRAM_BOT_TOKEN
   - TELEGRAM_CHAT_ID
5. Actions sekmesinden workflow_dispatch ile test tetikle.

## Tier
- LIVE (Gold ORB, NQ ORB): tam emir hazır, kör girilebilir.
- PAPER (diğerleri): teyit et, kalite iyiyse funded'da değerlendir.

## Güvenlik
Token/chat_id ASLA repoda değil; sadece Secrets/.env. .env gitignore'da.
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/signalbot.yml strategy-lab/intraday/signalbot/README.md
git commit -m "ci: signalbot workflow + kurulum README"
```

---

## Task 11 (Faz 2): ES-Div shim + BTC dedektörü + parity skorkartı

> Yarın için kritik değil. MVP yayına girdikten sonra.

**Files:**
- Create: `strategy-lab/intraday/signalbot/mt5_shim.py`
- Create: `strategy-lab/intraday/signalbot/btc_absorption.py`
- Create: `strategy-lab/intraday/signalbot/scorecard.py`
- Test: her biri için `test_*.py`

- [ ] **Step 1:** ES-Div `_feeds` çağrısını free_data'ya yönlendiren shim (monkeypatch/dependency-inject); `_SKIP_UNTIL_PHASE2`'den `SWEEP_ES_DIV` çıkar. TDD.
- [ ] **Step 2:** BTC Absorption dedektörünü pine `07_btc_absorption` mantığıyla (OBV + hacim spike + sweep + VWAP) `detect(df)->Signal|None` olarak yaz, `LiveModule("BTC_ABSORPTION","BTC","1H",...)` ekle. TDD.
- [ ] **Step 3:** scorecard: gönderilen her sinyali `signals.jsonl`'e yaz (alanlar: ts_utc ISO8601, module, tier, direction, entry, sl, tp). Haftalık parity özeti mesajı. TDD.

---

## Self-Review

- **Spec coverage:** A Mimari→Task 1-10; B Tier→Task 5 (tier_of); C Takvim→Task 8 (sessions); D Mesaj→Task 6; E Terfi/skorkart→Task 11; F Faz→Task 5 (risk_dollars phase). BTC→Task 4 (veri) + Task 11 (dedektör). ES-Div→Task 11. Tümü kapsandı.
- **Placeholder:** `risk.py` FX value_per_point açık implementer notuyla işaretli (LIVE doğru, FX paper). Import-yolu (tire sorunu) Task 9'da run_bot.py + conftest.py ile somut çözüldü.
- **Type tutarlılık:** `Signal(direction, entry, sl, tp)` ve `LiveModule(name, symbol_key, tf, weight, max_hold_bars, detect)` modules.py ile birebir. `ohlcv(symbol_key, tf, days)` her yerde aynı. `tier_of`/`Tier`, `risk_dollars(phase, balance)`, `lot_for(symbol_key, entry, sl, risk_usd)`, `format_signal(...)`, `to_trt`/`is_active`, `run(now, phase, balance)` çağrılarla tutarlı.
```