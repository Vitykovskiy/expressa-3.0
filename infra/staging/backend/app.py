import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


class Handler(BaseHTTPRequestHandler):
    server_version = "ExpressaStage0Backend/1.0"

    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/health", "/api/health"}:
            self._write_json(
                200,
                {
                    "status": "ok",
                    "service": "stage0-backend",
                    "environment": os.getenv("APP_ENV", "staging"),
                },
            )
            return

        if self.path == "/api/meta":
            self._write_json(
                200,
                {
                    "project": "expressa-stage0",
                    "environment": os.getenv("APP_ENV", "staging"),
                    "telegramAuthDisabled": bool_env("DISABLE_TG_AUTH", "true"),
                    "customerBotConfigured": bool(os.getenv("CUSTOMER_BOT_TOKEN")),
                    "backofficeBotConfigured": bool(os.getenv("BACKOFFICE_BOT_TOKEN")),
                    "adminTelegramConfigured": bool(os.getenv("ADMIN_TELEGRAM_ID")),
                    "databaseUrlPresent": bool(os.getenv("DATABASE_URL")),
                },
            )
            return

        self._write_json(404, {"status": "not_found", "path": self.path})

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8081"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
