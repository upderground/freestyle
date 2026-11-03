#!/usr/bin/env python3
"""Serve freestyle/local-edit and persist index.html (browser inline editing)."""
from __future__ import annotations

import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "local-edit"
INDEX = ROOT / "index.html"
SAVE_PATH = "/__save__"
PING_PATH = "/__ping__"


def looks_like_html(text: str) -> bool:
    s = text.lstrip().lower()
    return s.startswith("<!doctype html") or s.startswith("<html")


class LocalEditHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == PING_PATH:
            body = b'{"ok":true,"editor":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path != SAVE_PATH:
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            ctype = (self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
            if ctype == "application/json":
                payload = json.loads(raw.decode("utf-8"))
                html = payload.get("html", "")
            else:
                html = raw.decode("utf-8")
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            print(f"[save] bad request: {exc}", file=sys.stderr)
            self.send_error(400, "Bad body")
            return
        if not isinstance(html, str) or not looks_like_html(html):
            preview = html[:80].replace("\n", " ") if isinstance(html, str) else ""
            print(f"[save] rejected (not html): {preview!r}", file=sys.stderr)
            self.send_error(400, "Expected HTML document")
            return
        INDEX.write_text(html, encoding="utf-8")
        print(f"[save] wrote {len(html)} bytes -> {INDEX}", file=sys.stderr)
        body = json.dumps({"ok": True, "path": str(INDEX)}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        if self.path.split("?", 1)[0] in {SAVE_PATH, PING_PATH}:
            self._cors_headers()
        super().end_headers()

    def log_message(self, format: str, *args) -> None:
        first = str(args[0]) if args else ""
        if SAVE_PATH in first or PING_PATH in first:
            return
        super().log_message(format, *args)


def main() -> None:
    port = int(__import__("os").environ.get("PORT", "8770"))
    server = ThreadingHTTPServer(("127.0.0.1", port), LocalEditHandler)
    print(f"Freestyle local edit: http://127.0.0.1:{port}/", flush=True)
    print(f"Saving to: {INDEX}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
