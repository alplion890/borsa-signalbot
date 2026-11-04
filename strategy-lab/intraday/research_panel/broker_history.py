"""Read-only closed-bar export from the running Maven MT5 terminal."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path

import pandas as pd
import numpy as np

from .data import LAB, strict_json, utc_now

PAIRS = (("NASDAQ100", "15m"), ("JAP225", "15m"), ("EURUSD", "5m"),
         ("GBPUSD", "5m"), ("NASDAQ100", "5m"))


def root(lab):
    return lab / "outputs/intraday/research_panel/broker_history"


def publish(lab, symbol, tf, frame, broker, server):
    if "maven" not in (broker + " " + server).lower():
        raise ValueError("Bağlı hesap Maven değil; ana kaynak değiştirilemez")
    if frame.empty or not frame.index.is_monotonic_increasing or frame.index.has_duplicates or frame.index.hasnans:
        raise ValueError("Broker verisi boş, sırasız veya tekrarlı")
    frame = frame[["open", "high", "low", "close", "volume"]].copy()
    if (not np.isfinite(frame.to_numpy(dtype=float)).all() or (frame["volume"] < 0).any()
            or (frame[["open", "high", "low", "close"]] <= 0).any().any()
            or (frame.high < frame[["open","close","low"]].max(axis=1)).any()
            or (frame.low > frame[["open","close","high"]].min(axis=1)).any()):
        raise ValueError("Broker OHLCV değerleri geçersiz")
    frame.index.name = "timestamp"
    encoded = frame.to_csv().encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    name = f"{symbol}_{tf}_{digest[:16]}.csv"
    directory = root(lab)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        raise ValueError("Broker arşivi bütünlük hatası")
    if not target.exists():
        temp = target.with_suffix(".tmp")
        temp.write_bytes(encoded)
        temp.replace(target)
    manifest = {"source": "maven_mt5", "symbol": symbol, "tf": tf, "broker": broker, "server": server,
                "data_sha256": digest, "exported_at": utc_now(), "bars": len(frame),
                "start": frame.index[0].isoformat(), "end": frame.index[-1].isoformat(),
                "closed_bars_only": True}
    metadata = directory / (name + ".json")
    if not metadata.exists():
        temp = metadata.with_suffix(".tmp")
        temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(metadata)
    return {"id": name, **manifest}


def resolve_dataset(lab, identifier):
    if not isinstance(identifier,str) or not re.fullmatch(r"[A-Z0-9]+_(5m|15m)_[A-Za-z0-9_-]+[.]csv",identifier):
        raise ValueError("Geçersiz broker snapshot kimliği")
    path=root(lab)/identifier
    if not path.resolve().is_relative_to(root(lab).resolve()):
        raise ValueError("Broker snapshot yolu geçersiz")
    try:
        meta=strict_json(path.with_name(path.name+".json").read_text(encoding="utf-8"))
        if (meta["source"]!="maven_mt5" or meta["closed_bars_only"] is not True
                or "maven" not in (meta["broker"]+" "+meta["server"]).lower()
                or (meta["symbol"],meta["tf"]) not in PAIRS
                or not path.name.startswith(f"{meta['symbol']}_{meta['tf']}_")
                or hashlib.sha256(path.read_bytes()).hexdigest()!=meta["data_sha256"]):
            raise ValueError("Broker snapshot kimliği/bütünlüğü doğrulanamadı")
        return {"id":path.name,"label":f"Maven MT5 / {meta['symbol']} {meta['tf']} / {meta['start'][:10]}–{meta['end'][:10]}",
                "bytes":path.stat().st_size,"provenance":meta}
    except (OSError, KeyError, TypeError) as exc:
        raise ValueError("Broker snapshot okunamadı") from exc


def catalog(lab=LAB):
    candidates=[]
    for path in root(lab).glob("*.csv.json"):
        try:
            meta=strict_json(path.read_text(encoding="utf-8"))
            candidates.append((meta["end"],meta["symbol"],meta["tf"],path.name[:-5]))
        except (OSError,ValueError,KeyError,TypeError):
            continue
    latest={}
    for _,symbol,tf,identifier in sorted(candidates,reverse=True):
        if (symbol,tf) in latest:
            continue
        try:
            latest[(symbol,tf)]=resolve_dataset(lab,identifier)
        except ValueError:
            continue
    return list(latest.values())


def export(lab=LAB, count=40000):
    from ..mt5_bridge import mt5_io
    import MetaTrader5 as mt5
    exported, errors = [], []
    existing={(item["provenance"]["symbol"],item["provenance"]["tf"]):item for item in catalog(lab)}
    with mt5_io.session():
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        if account is None or terminal is None or not terminal.connected:
            raise ValueError("MT5 bağlantısı doğrulanamadı")
        if "maven" not in (account.company + " " + account.server).lower():
            raise ValueError("Bağlı hesap Maven değil")
        forward_state = lab / "outputs/intraday/forward_ea/forward_state.json"
        if forward_state.exists():
            recorded = strict_json(forward_state.read_text(encoding="utf-8"))
            pinned = recorded.get("broker_source") or {}
            if pinned.get("server") and pinned["server"] != account.server:
                raise ValueError("Forward defterinin broker sunucusu ile geçmiş kaynağı farklı; aktarım durduruldu")
        now = pd.Timestamp.now(tz="UTC").tz_localize(None)
        for symbol, tf in PAIRS:
            try:
                previous=existing.get((symbol,tf))
                if previous and previous["provenance"]["exported_at"][:10]==utc_now()[:10]:
                    exported.append({"id":previous["id"],**previous["provenance"]})
                    continue
                name = mt5_io.resolve(symbol)
                rates = mt5.copy_rates_from_pos(name, getattr(mt5,mt5_io._TF[tf]), 1, count)
                if rates is None or len(rates) == 0:
                    raise ValueError("Broker geçmişi yok")
                frame = pd.DataFrame(rates)
                frame.index = pd.to_datetime(frame.pop("time"),unit="s",utc=True).dt.tz_localize(None)
                frame = frame.rename(columns={"tick_volume":"volume"}).sort_index()
                frame = frame.loc[frame.index + pd.Timedelta(minutes=int(tf[:-1])) <= now]
                exported.append(publish(lab,symbol,tf,frame,account.company,account.server))
            except (ValueError, RuntimeError) as exc:
                errors.append({"symbol":symbol,"tf":tf,"error":str(exc)})
    return {"exported":exported,"errors":errors,"updated_at":utc_now()}


def main():
    parser=argparse.ArgumentParser(description="Read-only Maven history snapshots")
    parser.add_argument("--count",type=int,default=40000)
    parser.add_argument("--daily-if-needed",action="store_true")
    args=parser.parse_args()
    if args.daily_if_needed:
        try:
            previous=strict_json((root(LAB)/"export_status.json").read_text(encoding="utf-8"))
            if not previous["errors"] and len(previous["exported"])==len(PAIRS) and previous["updated_at"][:10]==utc_now()[:10]:
                return
        except (OSError,ValueError,KeyError,TypeError):
            pass
    if not 520 <= args.count <= 100000:
        parser.error("count 520–100000 olmalı")
    try:
        result=export(count=args.count)
    except Exception as exc:
        result={"exported":[],"errors":[{"error":str(exc)}],"updated_at":utc_now()}
    path=root(LAB)/"export_status.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    temp.replace(path)
    print(json.dumps(result,ensure_ascii=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__=="__main__":
    main()
