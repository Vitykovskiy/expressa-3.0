from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


def fetch_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"{url} -> HTTP {exc.code}: {body}") from exc


def main() -> int:
    base_url = (sys.argv[1] if len(sys.argv) > 1 else "http://216.57.105.133:8080").rstrip("/")

    meta = fetch_json(f"{base_url}/api/meta")
    if meta.get("backendMode") != "customer-core-live":
        raise SystemExit(f"/api/meta returned unexpected backendMode: {meta!r}")

    session = fetch_json(f"{base_url}/api/customer/session")
    if session.get("userId") != "customer-1":
        raise SystemExit(f"/api/customer/session returned unexpected payload: {session!r}")

    menu = fetch_json(f"{base_url}/api/customer/menu")
    if not menu.get("products"):
        raise SystemExit(f"/api/customer/menu returned no products: {menu!r}")

    orders = fetch_json(f"{base_url}/api/customer/orders")
    if "orders" not in orders or not isinstance(orders["orders"], list):
        raise SystemExit(f"/api/customer/orders returned unexpected payload: {orders!r}")

    print("live_customer_contract_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
