"""Run with python -m intraday.research_panel --port 8765."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
from urllib.parse import parse_qs, urlsplit

from .data import LAB, read_report, save_experiment, snapshot
from .evidence import strategy_evidence
from .jobs import catalog, list_jobs, submit, recover_interrupted
from .policy import primary_snapshot

ASSETS = Path(__file__).with_name("static")


def make_handler(lab: Path = LAB):
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def send(self, status: int, body: bytes, content_type: str):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(body)

        def json_response(self, status, data):
            self.send(status, json.dumps(data, ensure_ascii=False, allow_nan=False).encode(),
                      "application/json; charset=utf-8")

        def valid_host(self):
            return self.headers.get("Host") in {
                f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

        def do_GET(self):
            if not self.valid_host():
                return self.json_response(403, {"error": "Yalnız yerel erişim"})
            url = urlsplit(self.path)
            try:
                if url.path == "/api/snapshot":
                    value = primary_snapshot(lab)
                    value["strategies"] = strategy_evidence(value["sources"], value["modules"])
                    return self.json_response(200, {**value, "csrf_token": token})
                if url.path == "/api/backtests":
                    return self.json_response(200, {**catalog(lab), "jobs": list_jobs(lab)})
                if url.path == "/api/report":
                    report_id = parse_qs(url.query).get("id", [""])[0]
                    return self.json_response(200, {"text": read_report(lab, report_id)})
                assets = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}
                if url.path not in assets:
                    return self.json_response(404, {"error": "Bulunamadı"})
                name = assets[url.path]
                content_type = {"index.html": "text/html", "app.js": "text/javascript",
                                "style.css": "text/css"}[name]
                return self.send(200, (ASSETS / name).read_bytes(), content_type + "; charset=utf-8")
            except ValueError as exc:
                self.json_response(400, {"error": str(exc)})
            except Exception:
                self.json_response(500, {"error": "Okuma hatası; kaynak dosyaları kontrol edin"})

        def do_POST(self):
            origin = self.headers.get("Origin")
            if (not self.valid_host() or self.headers.get("X-Panel-Token") != token
                    or (origin is not None and origin != f"http://{self.headers.get('Host')}")):
                return self.json_response(403, {"error": "Yerel oturum doğrulanamadı"})
            if self.path not in ("/api/experiments", "/api/backtests"):
                return self.json_response(404, {"error": "Bulunamadı"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 50000:
                    raise ValueError("İstek boyutu 1–50000 bayt olmalı")
                if self.headers.get("Content-Type") != "application/json":
                    raise ValueError("application/json gerekli")
                data = json.loads(self.rfile.read(size))
                result = submit(data, lab) if self.path == "/api/backtests" else save_experiment(lab, data)
                self.json_response(202 if self.path == "/api/backtests" else 201, result)
            except (ValueError, UnicodeError) as exc:
                self.json_response(400, {"error": str(exc)})
            except OSError:
                self.json_response(500, {"error": "Deney kaydedilemedi"})

        def log_message(self, fmt, *args):
            # Avoid query strings or user content in access logs.
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Borsa yerel araştırma paneli")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler())
    recover_interrupted()
    print(f"Borsa Lab: http://127.0.0.1:{server.server_port} (durdur: Ctrl+C)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
