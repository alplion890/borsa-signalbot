"""Read-only local dashboard for FTMO demo state snapshots.

This module has no broker, FTMO, or order-execution integration. It reads a
JSON snapshot or a SQLite database supplied by the caller and serves HTML.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

_LOOPBACKS = {"127.0.0.1", "localhost", "::1"}


def _read_sqlite(path: Path) -> dict[str, Any]:
    """Read a serialized snapshot from common SQLite state table layouts."""
    with sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True) as db:
        tables = [
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        for table in tables:
            # Table names come from sqlite_master, but quote defensively.
            quoted = '"' + table.replace('"', '""') + '"'
            cols = [r[1] for r in db.execute(f"PRAGMA table_info({quoted})")]
            data_cols = [
                c for c in ("state_json", "payload", "data", "json") if c in cols
            ]
            if data_cols:
                order = next(
                    (c for c in ("updated_at", "created_at", "id") if c in cols), None
                )
                sql = f"SELECT {data_cols[0]} FROM {quoted}"
                if order:
                    sql += f' ORDER BY "{order}" DESC'
                sql += " LIMIT 1"
                row = db.execute(sql).fetchone()
                if row and row[0]:
                    parsed = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    if isinstance(parsed, dict):
                        return parsed
            # A key/value table can store a single row per state field.
            if {"key", "value"}.issubset(cols):
                values = dict(db.execute(f'SELECT "key", "value" FROM {quoted}'))
                if values:
                    if "state" in values and isinstance(values["state"], str):
                        parsed = json.loads(values["state"])
                        if isinstance(parsed, dict):
                            return parsed
                    return values
    raise ValueError(
        "SQLite içinde state_json/payload/data/json snapshot tablosu bulunamadı"
    )


def load_state(state_path: str | Path) -> dict[str, Any]:
    """Load a JSON object, or a serialized snapshot from SQLite, read-only."""
    path = Path(state_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError("Durum dosyası bulunamadı")
    if path.suffix.lower() in {".sqlite", ".sqlite3", ".db"}:
        state = _read_sqlite(path)
    else:
        state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ValueError("Durum kökünde JSON nesnesi bekleniyor")
    return state


def _fmt(value: Any, suffix: str = "") -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(float(value)):
            return "—"
        value = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
    return f"{html.escape(str(value))}{html.escape(suffix)}"


def _chart(history: Any) -> str:
    if not isinstance(history, list) or not history:
        return '<div class="empty">Özkaynak geçmişi yok</div>'
    points = []
    for item in history[-120:]:
        if isinstance(item, dict):
            try:
                points.append((str(item.get("time", "")), float(item["value"])))
            except (KeyError, TypeError, ValueError):
                continue
    if not points:
        return '<div class="empty">Özkaynak geçmişi yok</div>'
    vals = [v for _, v in points]
    lo, hi = min(vals), max(vals)
    span = hi - lo or 1
    coords = [
        f"{10 + i * 780 / max(1, len(vals)-1):.1f},{110 - (v-lo)*90/span:.1f}"
        for i, v in enumerate(vals)
    ]
    label = html.escape(f"{len(points)} kayıt · {points[0][0]} – {points[-1][0]}")
    return f'<svg viewBox="0 0 800 130" role="img" aria-label="Özkaynak geçmişi"><polyline points="{" ".join(coords)}" fill="none" stroke="#74e0b5" stroke-width="3"/><text x="10" y="126" fill="#9aabc1" font-size="11">{label}</text></svg>'


def render_dashboard(state: dict[str, Any], error: str | None = None) -> str:
    metrics = state.get("metrics") if isinstance(state.get("metrics"), dict) else {}
    account = state.get("account") if isinstance(state.get("account"), dict) else {}
    floors = state.get("floors") if isinstance(state.get("floors"), list) else []
    risks = state.get("open_risk") if isinstance(state.get("open_risk"), list) else []
    modules = state.get("modules") if isinstance(state.get("modules"), list) else []
    notes = state.get("notes") if isinstance(state.get("notes"), list) else []
    items = [
        ("Bakiye", metrics.get("balance"), account.get("currency", "")),
        ("Özkaynak", metrics.get("equity"), account.get("currency", "")),
        ("Kâr / zarar", metrics.get("profit"), account.get("currency", "")),
        ("Güncel düşüş", metrics.get("drawdown_pct"), "%"),
        ("Günlük zarar", metrics.get("daily_loss_pct"), "%"),
        ("Tutarlılık", metrics.get("consistency_pct"), "%"),
    ]
    cards = "".join(
        f'<article class="metric"><span>{html.escape(label)}</span><strong>{_fmt(value, suffix)}</strong></article>'
        for label, value, suffix in items
    )
    floor_rows = (
        "".join(
            f'<tr><td>{html.escape(str(x.get("name", "—")))}</td><td>{_fmt(x.get("value"), str(x.get("unit", "")))}</td><td><span class="pill">{html.escape(str(x.get("status", "—")))}</span></td><td>{html.escape(str(x.get("source", "—")))}</td></tr>'
            for x in floors
            if isinstance(x, dict)
        )
        or '<tr><td colspan="4" class="empty">Limit verisi yok</td></tr>'
    )
    risk_rows = (
        "".join(
            f'<tr><td>{html.escape(str(x.get("symbol", "—")))}</td><td>{html.escape(str(x.get("side", "—")))}</td><td>{_fmt(x.get("size"))}</td><td>{_fmt(x.get("risk"), str(x.get("currency", "")))}</td></tr>'
            for x in risks
            if isinstance(x, dict)
        )
        or '<tr><td colspan="4" class="empty">Açık risk kaydı yok</td></tr>'
    )
    module_rows = (
        "".join(
            f'<tr><td>{html.escape(str(x.get("name", "—")))}</td><td>{_fmt(x.get("trades"))}</td><td>{_fmt(x.get("net"))}</td><td>{_fmt(x.get("r"))}</td></tr>'
            for x in modules
            if isinstance(x, dict)
        )
        or '<tr><td colspan="4" class="empty">Modül sonucu yok</td></tr>'
    )
    accepted = metrics.get("accepted_trades", 0) or 0
    required = metrics.get("required_trades", 20) or 20
    days = metrics.get("eligible_days", 0) or 0
    required_days = metrics.get("required_days", 14) or 14
    payout = metrics.get("payout_ready")
    readiness = (
        "Hazır"
        if payout is True
        else "Hazır değil" if payout is False else "Bilinmiyor"
    )
    status = (
        "HATA · " + html.escape(error)
        if error
        else html.escape(str(state.get("status", "Durum bilinmiyor")))
    )
    source = html.escape(str(state.get("source", "Kaynak belirtilmedi")))
    updated = html.escape(str(state.get("updated_at", "Zaman belirtilmedi")))
    note_html = (
        "".join(f"<li>{html.escape(str(n))}</li>" for n in notes)
        or "<li>Ek not yok</li>"
    )
    title = html.escape(str(account.get("label", "Demo hesabı")))
    mode = html.escape(str(account.get("mode", "Durum dosyası")))
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="15"><title>FTMO demo · {title}</title>
<style> :root{{--bg:#0a1019;--panel:#121c29;--line:#253548;--text:#e8eef6;--muted:#9aabc1;--green:#74e0b5;--amber:#f5c56c}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:28px 20px}}header,.section-head{{display:flex;justify-content:space-between;gap:20px;align-items:center}}h1{{font-size:25px;margin:0}}h2{{font-size:17px;margin:0}}p,.muted{{color:var(--muted)}}.pill,.badge{{border:1px solid var(--line);border-radius:999px;padding:4px 10px;color:var(--green);font-size:12px}}.badge{{color:var(--amber)}}.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}}.metric,.panel{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}}.metric span{{display:block;color:var(--muted);font-size:13px}}.metric strong{{display:block;font-size:24px;margin-top:7px}}.grid{{display:grid;grid-template-columns:1.3fr 1fr;gap:14px;margin:14px 0}}.panel h2{{margin-bottom:12px}}svg{{width:100%;height:auto;display:block}}table{{width:100%;border-collapse:collapse;text-align:left}}th,td{{padding:10px 8px;border-bottom:1px solid var(--line);font-size:13px}}th{{color:var(--muted);font-weight:500}}.empty{{color:var(--muted);padding:14px 8px}}.progress{{height:8px;background:#253548;border-radius:8px;overflow:hidden;margin:10px 0}}.progress i{{display:block;height:100%;background:var(--green)}}.checkline{{display:flex;justify-content:space-between;margin:6px 0}}footer{{margin-top:20px;color:var(--muted);font-size:12px}}@media(max-width:760px){{.metrics{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}header{{align-items:flex-start;flex-direction:column}}}}</style></head><body><main>
<header><div><h1>FTMO demo · {title}</h1><p>{mode} · Bu panel salt okunur</p></div><div><span class="pill">{status}</span> <span class="badge">Panelde emir uç noktası yok</span></div></header>
<section class="metrics">{cards}</section>
<section class="grid"><article class="panel"><div class="section-head"><h2>Özkaynak geçmişi</h2><span class="muted">Kaynak: {source}</span></div>{_chart(state.get("equity_history"))}</article><article class="panel"><h2>Değerlendirme kapıları</h2><div class="checkline"><span>Kabul edilmiş işlem</span><strong>{_fmt(accepted)} / {_fmt(required)}</strong></div><div class="progress"><i style="width:{min(100, max(0, float(accepted or 0) / max(1, float(required or 20)) * 100)):.1f}%"></i></div><div class="checkline"><span>Uygun gün</span><strong>{_fmt(days)} / {_fmt(required_days)}</strong></div><div class="progress"><i style="width:{min(100, max(0, float(days or 0) / max(1, float(required_days or 14)) * 100)):.1f}%"></i></div><div class="checkline"><span>Payout uygunluğu</span><strong>{readiness}</strong></div><p class="muted">Sayaçlar durum dosyasından okunur; panel uygunluk kararı üretmez.</p></article></section>
<section class="grid"><article class="panel"><h2>Limitler ve eşikler</h2><table><thead><tr><th>Alan</th><th>Değer</th><th>Durum</th><th>Kaynak</th></tr></thead><tbody>{floor_rows}</tbody></table></article><article class="panel"><h2>Açık risk</h2><table><thead><tr><th>Sembol</th><th>Yön</th><th>Büyüklük</th><th>Risk</th></tr></thead><tbody>{risk_rows}</tbody></table></article></section>
<section class="panel"><h2>Modül sonuçları</h2><table><thead><tr><th>Modül</th><th>Tamamlanan işlem</th><th>Net sonuç</th><th>Toplam R</th></tr></thead><tbody>{module_rows}</tbody></table></section>
<section class="panel"><h2>Kaynak notları</h2><ul>{note_html}</ul></section><footer>Durum zamanı: {updated} · Dosya yolu servis çıktısında gösterilmez · Yenileme: 15 sn · Simüle hesap verisi</footer></main></body></html>"""


def create_server(
    state_path: str | Path, host: str = "127.0.0.1", port: int = 8767
) -> ThreadingHTTPServer:
    """Create the read-only HTTP server, useful for embedding and tests."""
    if host not in _LOOPBACKS:
        raise ValueError(
            "Güvenlik için dashboard yalnızca localhost arayüzünde çalışır"
        )
    source_path = Path(state_path).expanduser()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            route = urlsplit(self.path).path
            if route not in {"/", "/api/state"}:
                self.send_error(404)
                return
            try:
                state = load_state(source_path)
                error = None
            except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
                state, error = {}, str(exc)
            if route == "/api/state":
                body = json.dumps(
                    {"state": state, "error": error}, ensure_ascii=False, default=str
                ).encode("utf-8")
                content_type = "application/json; charset=utf-8"
            else:
                body = render_dashboard(state, error).encode("utf-8")
                content_type = "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: Any) -> None:
            # Avoid writing request-controlled strings into the console.
            return

    return ThreadingHTTPServer((host, port), Handler)


def serve(state_path: str | Path, host: str = "127.0.0.1", port: int = 8767) -> None:
    """Serve a read-only state dashboard on a loopback interface."""
    server = create_server(state_path, host, port)
    print(f"Salt okunur panel: http://{host}:{server.server_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Yerel, salt okunur FTMO demo paneli")
    parser.add_argument("state_path", help="Durum JSON'u veya SQLite dosyası")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    serve(args.state_path, args.host, args.port)


if __name__ == "__main__":
    main()
