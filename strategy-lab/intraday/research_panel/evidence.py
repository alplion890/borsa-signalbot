"""Descriptive source comparison; never grants trading authority."""
from __future__ import annotations

import pandas as pd

from .data import SWEEP


def metrics(rows):
    if not rows:
        return {"n": 0, "sum_r": None, "mean_r": None, "win_pct": None, "drawdown_r": None}
    values = pd.Series([row["r"] for row in rows], dtype=float)
    curve = pd.concat([pd.Series([0.0]), values.cumsum()], ignore_index=True)
    return {"n": len(rows), "sum_r": float(values.sum()), "mean_r": float(values.mean()),
            "win_pct": float((values > 0).mean() * 100),
            "drawdown_r": float((curve.cummax() - curve).max()),
            "start": min(row["entry_time"] for row in rows),
            "end": max(row["entry_time"] for row in rows)}


def compare_sources(left, right):
    if not left or not right:
        return {"status": "insufficient", "label": "İki kaynak için ortak kanıt yok", "matched": 0}
    from ..forward_ea.ledger import eslestir_bir_bir
    begin = max(min(pd.Timestamp(r["entry_time"]) for r in left), min(pd.Timestamp(r["entry_time"]) for r in right))
    finish = min(max(pd.Timestamp(r["entry_time"]) for r in left), max(pd.Timestamp(r["entry_time"]) for r in right))
    tolerance = pd.Timedelta(minutes=15)
    if begin > finish + tolerance:
        return {"status": "insufficient", "label": "Ortak kayıt dönemi yok", "matched": 0}
    start, end = begin - tolerance, finish + tolerance
    a = [r for r in left if start <= pd.Timestamp(r["entry_time"]) <= end]
    b = [r for r in right if start <= pd.Timestamp(r["entry_time"]) <= end]
    columns = ["module", "symbol", "dir", "entry_time", "r"]
    af, bf = pd.DataFrame(a, columns=columns), pd.DataFrame(b, columns=columns)
    for frame in (af, bf):
        frame["module"] = frame["module"].fillna("comparison")
        frame["entry_time"] = pd.to_datetime(frame["entry_time"], utc=True)
    matched, _, _ = eslestir_bir_bir(af, bf, tolerance)
    pairs = [(a[i], b[j]) for i,j in matched]
    start, end = start.isoformat(), end.isoformat()
    conflicts = sum((x["r"] > 0) != (y["r"] > 0) for x, y in pairs)
    opposite = bool(a and b and sum(r["r"] for r in a) * sum(r["r"] for r in b) < 0)
    # Strict descriptive agreement, not a statistical sufficiency threshold.
    status = "conflict" if conflicts or opposite else "insufficient"
    if pairs and len(pairs) == len(a) == len(b) and not conflicts:
        status = "aligned"
    return {"status": status, "label": {"conflict": "Kaynak uyuşmazlığı",
            "aligned": "Eşleşen kayıtların sonuç yönü tutarlı",
            "insufficient": "Kaynak tutarlılığı doğrulanamadı"}[status],
            "start": start, "end": end, "matched": len(pairs), "sign_conflicts": conflicts,
            "unmatched_mt5": len(a) - len(pairs), "unmatched_cloud": len(b) - len(pairs),
            "mt5": metrics(a), "cloud": metrics(b),
            "mean_absolute_delta_r": sum(abs(x["r"]-y["r"]) for x,y in pairs)/len(pairs) if pairs else None,
            "method": "Ortak giriş dönemi; aynı sembol/yön, giriş ±15 dk, kanonik maksimum eşleme / minimum zaman farkı; dönem sınırı ±15 dk paylı. Tam eşleme ve aynı kazanç/kayıp işareti yalnız betimsel tutarlılıktır; bağımsız kanıt değildir."}


def strategy_evidence(sources, modules):
    result = []
    for module in modules:
        name = module["name"]
        retired = name.startswith(("EUR_LONDON", "GBP_LONDON", "NQ_ORB", "GOLD_ORB", "GOLD_NY_ORB", "SWEEP_ES_DIV"))
        authority = "Manuel LIVE yetkili" if name == SWEEP else "Emekli" if retired else "PAPER / araştırma"
        views, normal = [], []
        for source in sources[:1]:
            valid = source["ledger_valid"] and name not in source["quarantined_modules"]
            rows = [r for r in source["rows"] if r["module"] == name]
            forward = [r for r in rows if r["backfill"] == 0]
            excluded = 0
            if name.startswith(("EUR_LONDON", "GBP_LONDON")):
                excluded = sum(r["entry_time"] < "2026-08-05" for r in forward)
                forward = [r for r in forward if r["entry_time"] >= "2026-08-05"]
            normal.append(forward if valid else [])
            views.append({"key": source["key"], "valid": valid, "forward": metrics(forward) if valid else None,
                          "backfill": metrics([r for r in rows if r["backfill"] == 1]) if valid else None,
                          "excluded_old_config": excluded})
        comparison = {"status": "primary", "label": "Maven MT5 · tek referans"}
        reasons = []
        if retired:
            reasons.append("Mevcut karar emekli. Pozitif kısa dönem sonuç bu kararı kendiliğinden kaldırmaz.")
        elif name != SWEEP:
            reasons.append("Bu stratejinin LIVE yetkisi yok; yalnız PAPER/araştırma kapsamında.")
        else:
            reasons.append("Mevcut manuel LIVE yetkisi sürüyor; bu ekran yeni kullanım veya risk kararı vermez.")
        if not all(v["valid"] for v in views):
            assessment = "Veri sorunu · karar üretilemez"
        else:
            assessment = "LIVE uygunluğu doğrulanmadı · kanıt incelemesi gerekli"
        reasons.append("Ölçüm kaynağı yalnız Maven MT5. Bulut/diğer feed sonuçları bu değerlendirmeye katılmaz; eksik kayıtlar başka feed ile tamamlanmaz.")
        reasons.append("Eski yerel defterde broker kimliği satır bazında tutulmamıştı. Tek referans seçimi geçmiş kayıtlardaki bu eksikliği veya stratejinin kârlılığını doğrulamaz.")
        reasons.append("Örneklem büyüklüğü tek başına yeterlilik vermez. Dönem dışı test, maliyet ve veri kalitesi birlikte incelenmeli.")
        for source in sources[:1]:
            if not source.get("state_valid", False) or source.get("freshness", {}).get("status") != "fresh":
                reasons.append(f"{source.get('label', source['key'])}: son ölçüm güncelliği doğrulanmalı; Veri ve güncellik ekranına bakın.")
        if name.startswith(("EUR_LONDON", "GBP_LONDON")):
            reasons.append("05.08.2026 öncesi eski konfigürasyon kayıtları ana forward metriklerinden çıkarıldı. Emeklilik: seyrek sinyal, dikkat maliyeti ve zayıf uzun tarih kanıtı.")
        result.append({"name": name, "authority": authority, "assessment": assessment,
                       "reasons": reasons, "sources": views, "comparison": comparison, "primary": views[0]})
    priority = {SWEEP: 0, "CAND_SWEEP_JAP225": 1, "EUR_LONDON_FADE_EMA": 2, "GBP_LONDON_STRONG_TREND": 3}
    return sorted(result, key=lambda item: (priority.get(item["name"], 9), item["name"]))
