from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from apps.api.backend import ExpressaBackend


BACKEND = ExpressaBackend()


class Handler(BaseHTTPRequestHandler):
    server_version = "ExpressaBackend/1.0"

    def _write_json(self, status: int, payload: object | None) -> None:
        body = b""
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _dispatch(self, method: str) -> None:
        parsed = urlparse(self.path)
        status, payload = BACKEND.handle(
            method=method,
            path=parsed.path,
            query=parse_qs(parsed.query),
            body=self.rfile.read(int(self.headers.get("Content-Length", "0") or "0")),
            headers={key.lower(): value for key, value in self.headers.items()},
        )
        self._write_json(status, payload)

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def do_PATCH(self) -> None:  # noqa: N802
        self._dispatch("PATCH")

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch("DELETE")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def serve() -> None:
    port = int(os.getenv("PORT", "8081"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    serve()
