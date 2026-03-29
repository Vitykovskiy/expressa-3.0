from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any


class ApiError(Exception):
    def __init__(self, status: int, reason: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.reason = reason
        self.message = message


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def parse_database_path(database_url: str | None) -> Path:
    if not database_url:
        return Path("/data/expressa.sqlite3")
    if database_url.startswith("sqlite:///"):
        return Path(database_url.replace("sqlite:///", "", 1))
    return Path("/data/expressa.sqlite3")


@dataclass(frozen=True)
class RequestContext:
    headers: dict[str, str]


class ExpressaBackend:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_path = parse_database_path(database_url or os.getenv("DATABASE_URL"))
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.disable_tg_auth = bool_env("DISABLE_TG_AUTH", "true")
        self._ensure_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_database(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    telegram_id TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    is_blocked INTEGER NOT NULL DEFAULT 0,
                    role TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    sort_order INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    category_id TEXT NOT NULL REFERENCES categories(id),
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    sort_order INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS product_sizes (
                    id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL REFERENCES products(id),
                    code TEXT NOT NULL,
                    label TEXT NOT NULL,
                    price_rub INTEGER NOT NULL,
                    is_default INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS modifier_groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    min_select INTEGER NOT NULL,
                    max_select INTEGER NOT NULL,
                    sort_order INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS modifier_options (
                    id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL REFERENCES modifier_groups(id),
                    label TEXT NOT NULL,
                    price_delta_rub INTEGER NOT NULL,
                    sort_order INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS product_modifier_bindings (
                    product_id TEXT NOT NULL REFERENCES products(id),
                    group_id TEXT NOT NULL REFERENCES modifier_groups(id),
                    sort_order INTEGER NOT NULL,
                    PRIMARY KEY (product_id, group_id)
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS carts (
                    user_id TEXT PRIMARY KEY REFERENCES users(id),
                    version INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS cart_items (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id),
                    product_id TEXT NOT NULL REFERENCES products(id),
                    size_code TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    modifier_option_ids TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id),
                    slot_start TEXT NOT NULL,
                    slot_end TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_rub INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    reject_reason TEXT
                );

                CREATE TABLE IF NOT EXISTS order_items (
                    id TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL REFERENCES orders(id),
                    product_id TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    size_code TEXT NOT NULL,
                    size_label TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    modifier_option_ids TEXT NOT NULL,
                    modifier_labels TEXT NOT NULL,
                    unit_price_rub INTEGER NOT NULL,
                    total_price_rub INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS order_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL REFERENCES orders(id),
                    status TEXT NOT NULL,
                    changed_at TEXT NOT NULL,
                    changed_by TEXT NOT NULL,
                    reason TEXT
                );

                CREATE TABLE IF NOT EXISTS notification_outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

            count = connection.execute("SELECT COUNT(*) AS count FROM categories").fetchone()["count"]
            if count:
                return

            self._seed(connection)

    def _seed(self, connection: sqlite3.Connection) -> None:
        connection.executemany(
            "INSERT INTO users(id, telegram_id, display_name, is_blocked, role) VALUES(?, ?, ?, ?, ?)",
            [
                ("customer-1", "987654321", "Maria", 0, "customer"),
                ("barista-1", "100200300", "Alex Barista", 0, "barista"),
                ("admin-1", "200300400", "Sam Admin", 0, "administrator"),
            ],
        )
        connection.executemany(
            "INSERT INTO categories(id, name, description, sort_order, is_active) VALUES(?, ?, ?, ?, ?)",
            [
                ("coffee", "Coffee", "Espresso drinks and filter", 1, 1),
                ("tea", "Tea", "Green, black, and signature tea", 2, 1),
                ("pastry", "Pastry", "Fresh bakery and desserts", 3, 1),
            ],
        )
        connection.executemany(
            "INSERT INTO products(id, category_id, name, description, sort_order, is_active) VALUES(?, ?, ?, ?, ?, ?)",
            [
                ("flat-white", "coffee", "Flat White", "Double espresso with silky milk", 1, 1),
                ("filter-citrus", "coffee", "Filter Citrus", "Clean filter coffee with citrus notes", 2, 1),
                ("matcha-latte", "tea", "Matcha Latte", "Ceremonial matcha with milk", 3, 1),
                ("almond-croissant", "pastry", "Almond Croissant", "Flaky croissant with almond cream", 4, 0),
            ],
        )
        connection.executemany(
            "INSERT INTO product_sizes(id, product_id, code, label, price_rub, is_default) VALUES(?, ?, ?, ?, ?, ?)",
            [
                ("flat-white-small", "flat-white", "small", "S / 250 ml", 260, 1),
                ("flat-white-medium", "flat-white", "medium", "M / 350 ml", 290, 0),
                ("flat-white-large", "flat-white", "large", "L / 450 ml", 330, 0),
                ("filter-citrus-small", "filter-citrus", "small", "S / 250 ml", 220, 1),
                ("filter-citrus-medium", "filter-citrus", "medium", "M / 350 ml", 250, 0),
                ("filter-citrus-large", "filter-citrus", "large", "L / 450 ml", 290, 0),
                ("matcha-latte-small", "matcha-latte", "small", "S / 250 ml", 280, 1),
                ("matcha-latte-medium", "matcha-latte", "medium", "M / 350 ml", 310, 0),
                ("matcha-latte-large", "matcha-latte", "large", "L / 450 ml", 350, 0),
                ("almond-croissant-piece", "almond-croissant", "piece", "1 piece", 190, 1),
            ],
        )
        connection.executemany(
            "INSERT INTO modifier_groups(id, name, min_select, max_select, sort_order, is_active) VALUES(?, ?, ?, ?, ?, ?)",
            [
                ("milk", "Milk", 0, 1, 1, 1),
                ("extras", "Extras", 0, 2, 2, 1),
            ],
        )
        connection.executemany(
            "INSERT INTO modifier_options(id, group_id, label, price_delta_rub, sort_order, is_active) VALUES(?, ?, ?, ?, ?, ?)",
            [
                ("whole", "milk", "Whole milk", 0, 1, 1),
                ("oat", "milk", "Oat milk", 40, 2, 1),
                ("lactose-free", "milk", "Lactose-free milk", 30, 3, 1),
                ("vanilla", "extras", "Vanilla syrup", 20, 1, 1),
                ("shot", "extras", "Extra espresso shot", 50, 2, 1),
                ("cinnamon", "extras", "Cinnamon", 0, 3, 1),
            ],
        )
        connection.executemany(
            "INSERT INTO product_modifier_bindings(product_id, group_id, sort_order) VALUES(?, ?, ?)",
            [
                ("flat-white", "milk", 1),
                ("flat-white", "extras", 2),
                ("filter-citrus", "extras", 1),
                ("matcha-latte", "milk", 1),
                ("matcha-latte", "extras", 2),
            ],
        )
        connection.executemany(
            "INSERT INTO settings(key, value) VALUES(?, ?)",
            [
                ("open_time", "09:00"),
                ("close_time", "20:00"),
                ("slot_step_minutes", "10"),
                ("slot_capacity", "5"),
            ],
        )
        connection.execute("INSERT INTO carts(user_id, version) VALUES(?, ?)", ("customer-1", 1))
        connection.commit()

    def handle(self, method: str, path: str, query: dict[str, list[str]], body: bytes, headers: dict[str, str]) -> tuple[int, Any]:
        try:
            if path in {"/health", "/api/health"} and method == "GET":
                return 200, {
                    "status": "ok",
                    "service": "expressa-backend",
                    "environment": os.getenv("APP_ENV", "staging"),
                }
            if path == "/api/meta" and method == "GET":
                return 200, self._meta_payload()
            if path == "/api/customer/session" and method == "GET":
                return 200, self.get_customer_session(RequestContext(headers))
            if path == "/api/customer/menu" and method == "GET":
                category_id = query.get("categoryId", [None])[0]
                return 200, self.get_customer_menu(category_id)
            if path.startswith("/api/customer/products/") and method == "GET":
                product_id = path.rsplit("/", 1)[-1]
                return 200, self.get_product_detail(product_id)
            if path == "/api/customer/cart" and method == "GET":
                return 200, self.get_cart(RequestContext(headers))
            if path == "/api/customer/cart/items" and method == "POST":
                payload = self._load_json(body)
                return 201, self.add_cart_item(RequestContext(headers), payload)
            if path.startswith("/api/customer/cart/items/") and method == "PATCH":
                item_id = path.rsplit("/", 1)[-1]
                payload = self._load_json(body)
                return 200, self.update_cart_item(RequestContext(headers), item_id, payload)
            if path.startswith("/api/customer/cart/items/") and method == "DELETE":
                item_id = path.rsplit("/", 1)[-1]
                self.delete_cart_item(RequestContext(headers), item_id)
                return 204, None
            if path == "/api/customer/slots" and method == "GET":
                selected_date = query.get("date", ["today"])[0]
                return 200, self.list_slots(selected_date)
            if path == "/api/customer/orders" and method == "POST":
                payload = self._load_json(body)
                return 201, self.create_order(RequestContext(headers), payload)
            if path == "/api/customer/orders" and method == "GET":
                return 200, self.list_orders(RequestContext(headers))
            if path.startswith("/api/customer/orders/") and method == "GET":
                order_id = path.rsplit("/", 1)[-1]
                return 200, self.get_order_detail(RequestContext(headers), order_id)
            raise ApiError(404, "NOT_FOUND", f"Path {path} is not available")
        except ApiError as error:
            return error.status, {"status": "error", "reason": error.reason, "message": error.message}

    def _meta_payload(self) -> dict[str, Any]:
        return {
            "project": "expressa-stage0",
            "environment": os.getenv("APP_ENV", "staging"),
            "telegramAuthDisabled": self.disable_tg_auth,
            "customerBotConfigured": bool(os.getenv("CUSTOMER_BOT_TOKEN")),
            "backofficeBotConfigured": bool(os.getenv("BACKOFFICE_BOT_TOKEN")),
            "adminTelegramConfigured": bool(os.getenv("ADMIN_TELEGRAM_ID")),
            "databaseUrlPresent": bool(os.getenv("DATABASE_URL")),
            "backendMode": "customer-core-live",
        }

    def _load_json(self, body: bytes) -> dict[str, Any]:
        if not body:
            return {}
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ApiError(400, "INVALID_JSON", "Body must be valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ApiError(400, "INVALID_JSON", "Body must be a JSON object.")
        return payload

    def _resolve_customer(self, context: RequestContext) -> sqlite3.Row:
        telegram_id = context.headers.get("x-telegram-user-id")
        with self._connect() as connection:
            if self.disable_tg_auth or not telegram_id:
                user = connection.execute("SELECT * FROM users WHERE id = 'customer-1'").fetchone()
            else:
                user = connection.execute(
                    "SELECT * FROM users WHERE telegram_id = ? LIMIT 1",
                    (telegram_id,),
                ).fetchone()
            if not user:
                raise ApiError(401, "AUTH_CONTEXT_MISSING", "Customer session is unavailable.")
            return user

    def get_customer_session(self, context: RequestContext) -> dict[str, Any]:
        user = self._resolve_customer(context)
        return {
            "userId": user["id"],
            "displayName": user["display_name"],
            "isBlocked": bool(user["is_blocked"]),
            "telegramId": user["telegram_id"],
            "isTelegramContext": not self.disable_tg_auth and bool(context.headers.get("x-telegram-user-id")),
        }

    def get_customer_menu(self, category_id: str | None) -> dict[str, Any]:
        with self._connect() as connection:
            categories = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                }
                for row in connection.execute(
                    "SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order"
                ).fetchall()
            ]
            query = """
                SELECT p.*, MIN(ps.price_rub) AS price_from_rub
                FROM products p
                JOIN product_sizes ps ON ps.product_id = p.id
                JOIN categories c ON c.id = p.category_id
                WHERE p.is_active = 1 AND c.is_active = 1
            """
            params: list[Any] = []
            if category_id:
                query += " AND p.category_id = ?"
                params.append(category_id)
            query += " GROUP BY p.id ORDER BY p.sort_order"
            products = [
                {
                    "id": row["id"],
                    "categoryId": row["category_id"],
                    "name": row["name"],
                    "description": row["description"],
                    "priceFromRub": row["price_from_rub"],
                    "badge": "Hit" if row["id"] == "flat-white" else ("New" if row["id"] == "matcha-latte" else None),
                    "isAvailable": bool(row["is_active"]),
                }
                for row in connection.execute(query, params).fetchall()
            ]
        return {"categories": categories, "products": products}

    def get_product_detail(self, product_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            product = connection.execute(
                """
                SELECT p.*, MIN(ps.price_rub) AS price_from_rub
                FROM products p
                JOIN product_sizes ps ON ps.product_id = p.id
                WHERE p.id = ? AND p.is_active = 1
                GROUP BY p.id
                """,
                (product_id,),
            ).fetchone()
            if not product:
                raise ApiError(404, "PRODUCT_NOT_FOUND", "Requested product was not found.")
            sizes = [
                {"code": row["code"], "label": row["label"], "priceRub": row["price_rub"]}
                for row in connection.execute(
                    "SELECT code, label, price_rub FROM product_sizes WHERE product_id = ? ORDER BY is_default DESC, price_rub",
                    (product_id,),
                ).fetchall()
            ]
            groups = []
            bindings = connection.execute(
                """
                SELECT mg.*
                FROM product_modifier_bindings b
                JOIN modifier_groups mg ON mg.id = b.group_id
                WHERE b.product_id = ? AND mg.is_active = 1
                ORDER BY b.sort_order
                """,
                (product_id,),
            ).fetchall()
            for group in bindings:
                options = [
                    {
                        "id": option["id"],
                        "label": option["label"],
                        "priceDeltaRub": option["price_delta_rub"],
                        "isAvailable": bool(option["is_active"]),
                    }
                    for option in connection.execute(
                        "SELECT * FROM modifier_options WHERE group_id = ? ORDER BY sort_order",
                        (group["id"],),
                    ).fetchall()
                ]
                groups.append(
                    {
                        "id": group["id"],
                        "name": group["name"],
                        "minSelect": group["min_select"],
                        "maxSelect": group["max_select"],
                        "options": options,
                    }
                )
        return {
            "product": {
                "id": product["id"],
                "categoryId": product["category_id"],
                "name": product["name"],
                "description": product["description"],
                "priceFromRub": product["price_from_rub"],
                "badge": "Hit" if product["id"] == "flat-white" else ("New" if product["id"] == "matcha-latte" else None),
                "isAvailable": bool(product["is_active"]),
            },
            "sizes": sizes,
            "modifierGroups": groups,
        }

    def _ensure_cart(self, connection: sqlite3.Connection, user_id: str) -> sqlite3.Row:
        cart = connection.execute("SELECT * FROM carts WHERE user_id = ?", (user_id,)).fetchone()
        if cart:
            return cart
        connection.execute("INSERT INTO carts(user_id, version) VALUES(?, 1)", (user_id,))
        return connection.execute("SELECT * FROM carts WHERE user_id = ?", (user_id,)).fetchone()

    def _load_product_detail_db(self, connection: sqlite3.Connection, product_id: str) -> tuple[sqlite3.Row, list[sqlite3.Row], list[sqlite3.Row], dict[str, list[sqlite3.Row]]]:
        product = connection.execute(
            "SELECT * FROM products WHERE id = ? AND is_active = 1",
            (product_id,),
        ).fetchone()
        if not product:
            raise ApiError(404, "PRODUCT_NOT_FOUND", "Requested product was not found.")
        sizes = connection.execute(
            "SELECT * FROM product_sizes WHERE product_id = ? ORDER BY is_default DESC, price_rub",
            (product_id,),
        ).fetchall()
        groups = connection.execute(
            """
            SELECT mg.*
            FROM product_modifier_bindings b
            JOIN modifier_groups mg ON mg.id = b.group_id
            WHERE b.product_id = ? AND mg.is_active = 1
            ORDER BY b.sort_order
            """,
            (product_id,),
        ).fetchall()
        options_by_group: dict[str, list[sqlite3.Row]] = {}
        for group in groups:
            options_by_group[group["id"]] = connection.execute(
                "SELECT * FROM modifier_options WHERE group_id = ? AND is_active = 1 ORDER BY sort_order",
                (group["id"],),
            ).fetchall()
        return product, sizes, groups, options_by_group

    def _validate_line(self, connection: sqlite3.Connection, product_id: str, size_code: str | None, qty: Any, modifier_option_ids: list[str]) -> tuple[sqlite3.Row, sqlite3.Row, list[str], int]:
        product, sizes, groups, options_by_group = self._load_product_detail_db(connection, product_id)
        if not size_code:
            raise ApiError(422, "SIZE_REQUIRED", "Product size is required.")
        size = next((row for row in sizes if row["code"] == size_code), None)
        if not size:
            raise ApiError(422, "SIZE_REQUIRED", "Product size is required.")
        if not isinstance(qty, int) or qty < 1:
            raise ApiError(422, "INVALID_QTY", "Quantity must be at least 1.")

        modifier_labels: list[str] = []
        total_delta = 0
        remaining = set(modifier_option_ids)
        for group in groups:
            options = options_by_group[group["id"]]
            selected = [option for option in options if option["id"] in modifier_option_ids]
            if len(selected) < group["min_select"] or len(selected) > group["max_select"]:
                raise ApiError(422, "MODIFIER_SELECTION_INVALID", f"Modifier selection is invalid for group {group['name']}.")
            for option in selected:
                remaining.discard(option["id"])
                modifier_labels.append(option["label"])
                total_delta += option["price_delta_rub"]
        if remaining:
            raise ApiError(422, "MODIFIER_SELECTION_INVALID", "Unknown modifier option was provided.")
        return product, size, modifier_labels, total_delta

    def _cart_items(self, connection: sqlite3.Connection, user_id: str) -> list[dict[str, Any]]:
        rows = connection.execute(
            "SELECT * FROM cart_items WHERE user_id = ? ORDER BY rowid",
            (user_id,),
        ).fetchall()
        items = []
        for row in rows:
            modifier_option_ids = json.loads(row["modifier_option_ids"])
            product, size, modifier_labels, total_delta = self._validate_line(
                connection,
                row["product_id"],
                row["size_code"],
                row["qty"],
                modifier_option_ids,
            )
            unit_price = size["price_rub"] + total_delta
            items.append(
                {
                    "cartItemId": row["id"],
                    "productId": product["id"],
                    "productName": product["name"],
                    "sizeCode": size["code"],
                    "sizeLabel": size["label"],
                    "qty": row["qty"],
                    "modifierOptionIds": modifier_option_ids,
                    "modifierLabels": modifier_labels,
                    "unitPriceRub": unit_price,
                    "totalPriceRub": unit_price * row["qty"],
                }
            )
        return items

    def get_cart(self, context: RequestContext) -> dict[str, Any]:
        user = self._resolve_customer(context)
        with self._connect() as connection:
            cart = self._ensure_cart(connection, user["id"])
            items = self._cart_items(connection, user["id"])
            subtotal = sum(item["totalPriceRub"] for item in items)
            return {
                "items": items,
                "subtotalRub": subtotal,
                "totalRub": subtotal,
                "version": cart["version"],
            }

    def add_cart_item(self, context: RequestContext, payload: dict[str, Any]) -> dict[str, Any]:
        user = self._resolve_customer(context)
        product_id = str(payload.get("productId", "")).strip()
        size_code = str(payload.get("sizeCode", "")).strip() or None
        qty = payload.get("qty")
        modifier_option_ids = payload.get("modifierOptionIds") or []
        if not isinstance(modifier_option_ids, list) or any(not isinstance(value, str) for value in modifier_option_ids):
            raise ApiError(422, "MODIFIER_SELECTION_INVALID", "Modifier option IDs must be a list of strings.")
        with self._connect() as connection:
            self._ensure_cart(connection, user["id"])
            self._validate_line(connection, product_id, size_code, qty, modifier_option_ids)
            cart_item_id = f"cart-{datetime.now(timezone.utc).timestamp():.6f}".replace(".", "")
            connection.execute(
                "INSERT INTO cart_items(id, user_id, product_id, size_code, qty, modifier_option_ids) VALUES(?, ?, ?, ?, ?, ?)",
                (cart_item_id, user["id"], product_id, size_code, qty, json.dumps(modifier_option_ids)),
            )
            connection.execute("UPDATE carts SET version = version + 1 WHERE user_id = ?", (user["id"],))
            connection.commit()
        return self.get_cart(context)

    def update_cart_item(self, context: RequestContext, cart_item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        user = self._resolve_customer(context)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM cart_items WHERE id = ? AND user_id = ?",
                (cart_item_id, user["id"]),
            ).fetchone()
            if not existing:
                raise ApiError(404, "CART_ITEM_NOT_FOUND", "Cart item was not found.")
            size_code = str(payload.get("sizeCode", existing["size_code"])).strip() or None
            qty = payload.get("qty", existing["qty"])
            modifier_option_ids = payload.get("modifierOptionIds")
            if modifier_option_ids is None:
                modifier_option_ids = json.loads(existing["modifier_option_ids"])
            if not isinstance(modifier_option_ids, list) or any(not isinstance(value, str) for value in modifier_option_ids):
                raise ApiError(422, "MODIFIER_SELECTION_INVALID", "Modifier option IDs must be a list of strings.")
            self._validate_line(connection, existing["product_id"], size_code, qty, modifier_option_ids)
            connection.execute(
                "UPDATE cart_items SET size_code = ?, qty = ?, modifier_option_ids = ? WHERE id = ?",
                (size_code, qty, json.dumps(modifier_option_ids), cart_item_id),
            )
            connection.execute("UPDATE carts SET version = version + 1 WHERE user_id = ?", (user["id"],))
            connection.commit()
        return self.get_cart(context)

    def delete_cart_item(self, context: RequestContext, cart_item_id: str) -> None:
        user = self._resolve_customer(context)
        with self._connect() as connection:
            connection.execute("DELETE FROM cart_items WHERE id = ? AND user_id = ?", (cart_item_id, user["id"]))
            connection.execute("UPDATE carts SET version = version + 1 WHERE user_id = ?", (user["id"],))
            connection.commit()

    def _settings(self, connection: sqlite3.Connection) -> dict[str, str]:
        return {
            row["key"]: row["value"]
            for row in connection.execute("SELECT key, value FROM settings").fetchall()
        }

    def list_slots(self, requested_date: str) -> dict[str, Any]:
        if requested_date != "today":
            raise ApiError(422, "DATE_NOT_SUPPORTED", "Only current-day slots are available in v1.")
        with self._connect() as connection:
            settings = self._settings(connection)
            slot_capacity = int(settings["slot_capacity"])
            slot_step = int(settings["slot_step_minutes"])
            open_hour, open_minute = map(int, settings["open_time"].split(":"))
            close_hour, close_minute = map(int, settings["close_time"].split(":"))
            current_day = date.today()
            start_dt = datetime.combine(current_day, time(open_hour, open_minute), tzinfo=timezone.utc)
            end_dt = datetime.combine(current_day, time(close_hour, close_minute), tzinfo=timezone.utc)
            counts = {
                row["slot_start"]: row["used_count"]
                for row in connection.execute(
                    """
                    SELECT slot_start, COUNT(*) AS used_count
                    FROM orders
                    WHERE status IN ('Created', 'Confirmed', 'Ready for pickup')
                      AND substr(slot_start, 1, 10) = ?
                    GROUP BY slot_start
                    """,
                    (current_day.isoformat(),),
                ).fetchall()
            }
            slots = []
            pointer = start_dt
            while pointer < end_dt:
                next_pointer = pointer + timedelta(minutes=slot_step)
                key = pointer.isoformat().replace("+00:00", "Z")
                used = counts.get(key, 0)
                capacity_left = max(slot_capacity - used, 0)
                slots.append(
                    {
                        "start": key,
                        "end": next_pointer.isoformat().replace("+00:00", "Z"),
                        "capacityLeft": capacity_left,
                        "isAvailable": capacity_left > 0,
                    }
                )
                pointer = next_pointer
        return {"slots": slots}

    def create_order(self, context: RequestContext, payload: dict[str, Any]) -> dict[str, Any]:
        user = self._resolve_customer(context)
        slot_start = str(payload.get("slotStart", "")).strip()
        cart_version = payload.get("cartVersion")
        if not slot_start:
            raise ApiError(422, "SLOT_REQUIRED", "Pickup slot is required.")
        with self._connect() as connection:
            cart = self._ensure_cart(connection, user["id"])
            if cart["version"] != cart_version:
                raise ApiError(409, "CART_VERSION_CONFLICT", "Cart version no longer matches the server state.")
            items = self._cart_items(connection, user["id"])
            if not items:
                raise ApiError(422, "CART_EMPTY", "Cart is empty.")

            slot_payload = self.list_slots("today")
            slot = next((entry for entry in slot_payload["slots"] if entry["start"] == slot_start), None)
            if not slot or not slot["isAvailable"]:
                raise ApiError(409, "SLOT_UNAVAILABLE", "Selected pickup slot is no longer available.")

            order_id = f"ord-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            created_at = utc_now()
            total_rub = sum(item["totalPriceRub"] for item in items)
            connection.execute(
                """
                INSERT INTO orders(id, user_id, slot_start, slot_end, status, total_rub, created_at, reject_reason)
                VALUES(?, ?, ?, ?, 'Created', ?, ?, NULL)
                """,
                (order_id, user["id"], slot["start"], slot["end"], total_rub, created_at),
            )
            for index, item in enumerate(items, start=1):
                connection.execute(
                    """
                    INSERT INTO order_items(
                        id, order_id, product_id, product_name, size_code, size_label, qty,
                        modifier_option_ids, modifier_labels, unit_price_rub, total_price_rub
                    ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"{order_id}-item-{index}",
                        order_id,
                        item["productId"],
                        item["productName"],
                        item["sizeCode"],
                        item["sizeLabel"],
                        item["qty"],
                        json.dumps(item["modifierOptionIds"]),
                        json.dumps(item["modifierLabels"]),
                        item["unitPriceRub"],
                        item["totalPriceRub"],
                    ),
                )
            connection.execute(
                "INSERT INTO order_status_history(order_id, status, changed_at, changed_by, reason) VALUES(?, 'Created', ?, 'system', NULL)",
                (order_id, created_at),
            )
            notification_payload = {
                "orderId": order_id,
                "customerTelegramId": user["telegram_id"],
                "status": "Created",
                "changedByUserId": "system",
            }
            connection.execute(
                "INSERT INTO notification_outbox(kind, payload_json, created_at) VALUES(?, ?, ?)",
                ("order.status.changed", json.dumps(notification_payload), created_at),
            )
            connection.execute("DELETE FROM cart_items WHERE user_id = ?", (user["id"],))
            connection.execute("UPDATE carts SET version = version + 1 WHERE user_id = ?", (user["id"],))
            connection.commit()
        return {"orderId": order_id, "status": "Created", "slotStart": slot_start, "totalRub": total_rub}

    def list_orders(self, context: RequestContext) -> dict[str, Any]:
        user = self._resolve_customer(context)
        with self._connect() as connection:
            orders = [
                {
                    "orderId": row["id"],
                    "status": row["status"],
                    "slotStart": row["slot_start"],
                    "totalRub": row["total_rub"],
                    "createdAt": row["created_at"],
                    "itemCount": connection.execute(
                        "SELECT COUNT(*) AS count FROM order_items WHERE order_id = ?",
                        (row["id"],),
                    ).fetchone()["count"],
                    "rejectReason": row["reject_reason"],
                }
                for row in connection.execute(
                    "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
                    (user["id"],),
                ).fetchall()
            ]
        return {"orders": orders}

    def get_order_detail(self, context: RequestContext, order_id: str) -> dict[str, Any]:
        user = self._resolve_customer(context)
        with self._connect() as connection:
            order = connection.execute(
                "SELECT * FROM orders WHERE id = ? AND user_id = ?",
                (order_id, user["id"]),
            ).fetchone()
            if not order:
                raise ApiError(404, "ORDER_NOT_FOUND", "Order was not found.")
            items = [
                {
                    "cartItemId": row["id"],
                    "productId": row["product_id"],
                    "productName": row["product_name"],
                    "sizeCode": row["size_code"],
                    "sizeLabel": row["size_label"],
                    "qty": row["qty"],
                    "modifierOptionIds": json.loads(row["modifier_option_ids"]),
                    "modifierLabels": json.loads(row["modifier_labels"]),
                    "unitPriceRub": row["unit_price_rub"],
                    "totalPriceRub": row["total_price_rub"],
                }
                for row in connection.execute(
                    "SELECT * FROM order_items WHERE order_id = ? ORDER BY rowid",
                    (order_id,),
                ).fetchall()
            ]
            history = [
                {
                    "status": row["status"],
                    "changedAt": row["changed_at"],
                    "changedBy": row["changed_by"],
                }
                for row in connection.execute(
                    "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY id",
                    (order_id,),
                ).fetchall()
            ]
            summary = {
                "orderId": order["id"],
                "status": order["status"],
                "slotStart": order["slot_start"],
                "totalRub": order["total_rub"],
                "createdAt": order["created_at"],
                "itemCount": len(items),
                "rejectReason": order["reject_reason"],
            }
        return {"order": summary, "items": items, "statusHistory": history}
