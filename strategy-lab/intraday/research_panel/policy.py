"""One authoritative broker feed; alternate sources stay in diagnostics."""
from __future__ import annotations

from .data import snapshot
from .data import strict_json


def primary_snapshot(lab):
    value = snapshot(lab)
    primary = next(s for s in value["sources"] if s["key"] == "mt5")
    external = {r["module"] for r in primary["rows"] if r["symbol"] in ("BTC", "BTCUSDT")}
    external |= {p["module"] for p in primary["state"].get("open_positions", [])
                 if p["symbol"] in ("BTC", "BTCUSDT")}
    # Local runner explicitly routes BTC to Binance, despite the CSV filename.
    external.add("CAND_BTC_ABSORPTION")
    primary = {**primary, "rows": [r for r in primary["rows"] if r["module"] not in external],
               "state": {**primary["state"], "open_positions": [p for p in primary["state"].get("open_positions", [])
                          if p["module"] not in external]}}
    provenance = primary["state"].get("broker_source")
    primary["provenance_note"] = "Eski MT5 kayıtlarında broker kimliği satır bazında saklanmamıştı; geçmişin tamamı doğrulanmış sayılmaz."
    if provenance and (provenance["provider"] != "maven_mt5" or "maven" not in
                       (provenance["broker"] + " " + provenance["server"]).lower()):
        primary["ledger_valid"] = False
        primary["errors"] = [*primary["errors"], "Kaynak Maven olarak doğrulanamadı; panel değerlendirmesi bloke."]
    names = {r["module"] for r in primary["rows"]} | set(primary["quarantined_modules"])
    names |= {p["module"] for p in primary["state"].get("open_positions", [])}
    value["audit_sources"] = [s for s in value["sources"] if s["key"] != "mt5"]
    value["sources"] = [primary]
    value["modules"] = [m for m in value["modules"] if m["name"] in names and m["name"] not in external]
    value["source_policy"] = {"id": "maven_mt5_only_v1", "label": "Maven MT5 · tek karar kaynağı",
                              "fallback": False, "excluded_external_modules": sorted(external),
                              "scope": "Panel forward değerlendirmesi ve yeni backtestler. Eski bulut/diğer-feed çalışmaları arşiv; yürürlükteki durma taahhütleri ve LIVE yetkileri bu görünümle değiştirilmez."}
    try:
        value["broker_history_status"] = strict_json((lab / "outputs/intraday/research_panel/broker_history/export_status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        value["broker_history_status"] = {"errors": [{"error": "Henüz broker geçmişi alınmadı"}]}
    return value
