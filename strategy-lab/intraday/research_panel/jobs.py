"""Single-job, fixed-spec local backtests. No feed, broker or shell execution."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import threading
from uuid import uuid4

import numpy as np
import pandas as pd

from .data import LAB, utc_now, strict_json
from .evidence import metrics
from . import broker_history

POOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix="panel-backtest")
LOCK = threading.Lock()
ACTIVE = None
STRATEGIES = {"SWEEP_CORE": ("NASDAQ100", "15m", "Sweep · mevcut sabit tanım"),
              "CAND_SWEEP_JAP225": ("JAP225", "15m", "JAP225 Sweep · PAPER adayı"),
              "EUR_LONDON": ("EURUSD", "5m", "EUR London · arşiv araştırma tanımı"),
              "GBP_LONDON": ("GBPUSD", "5m", "GBP London · arşiv araştırma tanımı"),
              "NQ_ORB": ("NASDAQ100", "5m", "NQ ORB · arşiv araştırma tanımı")}


def code_digest(lab):
    digest = hashlib.sha256()
    for source in sorted((lab / "intraday").rglob("*.py")):
        digest.update(source.relative_to(lab).as_posix().encode())
        digest.update(source.read_bytes())
    return digest.hexdigest()


STARTUP_CODE = code_digest(LAB)


def datasets(lab=LAB):
    return broker_history.catalog(lab)


def catalog(lab=LAB):
    return {"strategies": [{"id": key, "symbol": v[0], "tf": v[1], "label": v[2]}
                           for key, v in STRATEGIES.items()], "datasets": datasets(lab)}


def directory(lab):
    return lab / "outputs/intraday/research_panel/jobs"


def write_job(lab, job):
    root = directory(lab)
    root.mkdir(parents=True, exist_ok=True)
    temp = root / (job["id"] + ".tmp")
    temp.write_text(json.dumps(job, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")
    temp.replace(root / (job["id"] + ".json"))


def list_jobs(lab=LAB):
    jobs = []
    for path in sorted(directory(lab).glob("*.json"), reverse=True):
        try:
            job = strict_json(path.read_text(encoding="utf-8"))
            if isinstance(job, dict) and isinstance(job.get("id"), str):
                jobs.append(job)
        except (OSError, ValueError):
            continue
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)[:50]


def recover_interrupted(lab=LAB):
    """Called once at server startup, before new jobs can be submitted."""
    for job in list_jobs(lab):
        if job.get("status") in ("queued", "running"):
            job.update(status="interrupted", finished_at=utc_now(),
                       error="Panel yeniden başladı; önceki çalışma tamamlanmadı. Yeniden başlatılabilir.")
            write_job(lab, job)


def validate(payload, lab=LAB):
    if (not isinstance(payload, dict) or not isinstance(payload.get("strategy"), str)
            or payload["strategy"] not in STRATEGIES):
        raise ValueError("Sabit listeden strateji seçin")
    symbol, tf, _ = STRATEGIES[payload["strategy"]]
    selected = payload.get("dataset")
    if not isinstance(selected, str) or not selected.startswith(f"{symbol}_{tf}_"):
        raise ValueError("Strateji ile uyumlu yerel veri seçin")
    broker_history.resolve_dataset(lab,selected)
    try:
        start, end = date.fromisoformat(payload["start"]), date.fromisoformat(payload["end"])
        factor = float(payload.get("cost_factor", 1))
    except (KeyError, TypeError, ValueError):
        raise ValueError("Geçerli tarih ve maliyet çarpanı gerekli") from None
    if start >= end or not math.isfinite(factor) or not 1 <= factor <= 5:
        raise ValueError("Başlangıç bitişten önce; maliyet çarpanı 1–5 olmalı")
    return {"strategy": payload["strategy"], "dataset": selected, "start": str(start),
            "end": str(end), "cost_factor": factor}


def submit(payload, lab=LAB):
    global ACTIVE
    config = validate(payload, lab)
    with LOCK:
        if ACTIVE is not None and not ACTIVE.done():
            raise ValueError("Bir backtest zaten çalışıyor; bitmesini bekleyin")
        job = {"id": str(uuid4()), "created_at": utc_now(), "status": "queued", "source": "maven_mt5", "config": config}
        write_job(lab, job)
        ACTIVE = POOL.submit(run_job, job, lab)
    return job


def run_job(job, lab=LAB):
    try:
        job = {**job, "status": "running", "started_at": utc_now()}
        write_job(lab, job)
        job.update(execute(job["config"], lab), status="completed", finished_at=utc_now())
    except Exception as exc:
        job.update(status="failed", error=f"{type(exc).__name__}: {exc}", finished_at=utc_now())
    write_job(lab, job)


def execute(config, lab=LAB):
    initial_code = code_digest(lab)
    if lab == LAB and initial_code != STARTUP_CODE:
        raise ValueError("Python kaynakları panel açıldıktan sonra değişti. Paneli yeniden başlatın.")
    from ..config import INSTRUMENTS
    from ..long_history_ab import spec_by_name, _sweep_build, _atr_rank
    from ..honest_engine import simulate_trades

    config = validate(config, lab)
    path = broker_history.root(lab) / config["dataset"]
    provenance = broker_history.resolve_dataset(lab,config["dataset"])["provenance"]
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != provenance["data_sha256"]:
        raise ValueError("Broker veri bütünlüğü bozuldu")
    if len(raw) > 100_000_000:
        raise ValueError("Veri 100 MB sınırını aşıyor")
    import io
    frame = pd.read_csv(io.BytesIO(raw))
    idx = pd.to_datetime(frame.pop("timestamp"), utc=True, errors="raise").dt.tz_localize(None)
    frame.index = pd.DatetimeIndex(idx)
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing or frame.index.hasnans:
        raise ValueError("Veri sıralı, benzersiz ve zaman damgalı olmalı")
    fields = ["open", "high", "low", "close", "volume"]
    frame = frame[fields].astype(float)
    if not np.isfinite(frame.to_numpy()).all() or (frame[["open","high","low","close"]] <= 0).any().any():
        raise ValueError("Geçersiz OHLCV değeri")
    if ((frame.high < frame[["open","close","low"]].max(axis=1)) |
            (frame.low > frame[["open","close","high"]].min(axis=1))).any():
        raise ValueError("OHLC sınırları tutarsız")
    start = pd.Timestamp(config["start"])
    stop = pd.Timestamp(config["end"]) + pd.Timedelta(days=1)
    # Warm-up is prior data only; never trade warm-up bars.
    window = frame.loc[(frame.index >= start) & (frame.index < stop)]
    if len(window) < 200:
        raise ValueError("Seçili dönemde en az 200 bar gerekli")
    frame = pd.concat([frame.loc[frame.index < start].tail(2000), window])
    if len(frame) > 150_000:
        raise ValueError("Tek iş en fazla 150.000 bar; dönemi daraltın")
    symbol, tf, _ = STRATEGIES[config["strategy"]]
    inst = replace(INSTRUMENTS[symbol], cost_per_side=INSTRUMENTS[symbol].cost_per_side * config["cost_factor"])
    sweep = config["strategy"] in ("SWEEP_CORE", "CAND_SWEEP_JAP225")
    spec = spec_by_name("SWEEP_CORE" if sweep else config["strategy"])
    le, se, lsl, ltp, ssl, stp = (_sweep_build(frame) if sweep else spec.build(frame))
    if sweep:
        rank = _atr_rank(frame)
        cap = pd.Series(np.select([rank < .33, rank < .67], [4., 6.], default=8.), index=frame.index)
        ltp = pd.Series(np.minimum(ltp, frame.close + (frame.close-lsl)*cap), index=frame.index)
        stp = pd.Series(np.maximum(stp, frame.close - (ssl-frame.close)*cap), index=frame.index)
        le, se = le & rank.notna(), se & rank.notna()
    eligible = (frame.index >= start) & (frame.index < stop)
    if sweep:
        eligible &= np.arange(len(frame)) >= 519  # live detector requires 520 bars
    r = simulate_trades(frame, le & eligible, se & eligible, lsl, ltp, ssl, stp,
                        inst, min_rr=spec.min_rr, max_rr=spec.max_rr, max_hold=spec.max_hold)
    rows = [{"entry_time": pd.Timestamp(t).isoformat(), "r": float(v)} for t,v in r.items()]
    # Never attribute cached imported code to a newer working-tree fingerprint.
    if code_digest(lab) != initial_code:
        raise ValueError("Çalışma sırasında Python kaynakları değişti; sonuç geçerli rapor olarak saklanmadı.")
    midpoint = window.index[len(window)//2]
    early = [row for row in rows if pd.Timestamp(row["entry_time"]) < midpoint]
    late = [row for row in rows if pd.Timestamp(row["entry_time"]) >= midpoint]
    return {"metrics": metrics(rows), "trades": rows, "first_half": metrics(early),
            "second_half": metrics(late), "split_at": midpoint.isoformat(),
            "metadata": {"source": "maven_mt5", "broker_provenance": provenance,
                         "data_sha256": hashlib.sha256(raw).hexdigest(), "code_sha256": initial_code,
                         "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
                         "symbol": symbol, "tf": tf, "bars": len(window),
                         "actual_start": window.index[0].isoformat(), "actual_end": window.index[-1].isoformat(),
                         "warmup_bars": len(frame)-len(window), "cost_per_side": inst.cost_per_side,
                         "requested_period_fully_covered": bool(pd.Timestamp(config["start"]) >= pd.to_datetime(idx).min().normalize()
                            and pd.Timestamp(config["end"]) <= pd.to_datetime(idx).max().normalize()),
                         "fill_model": "honest_engine / bar_sl_first / sinyal kapanışı / stop-market gap-open v2",
                         "strategy_version": "mevcut sabit Sweep tanımı" if sweep else "long_history_ab arşiv tanımı; güncel forward ile sürüm eşitliği varsayılmaz"},
            "limitations": ["Maven MT5 fiyat geçmişi; broker CFD verisidir. Forward ile aynı feed, ancak aynı icra modeli garantisi değildir.",
                            "Tarihsel yeniden ölçüm; görülmemiş OOS veya bağımsız yeni kanıt sayılmaz. İki yarı betimseldir.",
                            "OHLC bar simülasyonu: aynı barda SL önce. Tick/icra doğrulaması yok; son sınırdaki kapanışlar motor modeline tabidir.",
                            "LSE temizlik çalışmasının yerine geçmez. Sonuç LIVE yetkisini ve riski değiştirmez."]}
