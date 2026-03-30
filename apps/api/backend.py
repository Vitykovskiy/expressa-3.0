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
            if path == "/api/backoffice/session" and method == "GET":
                return 200, self.get_backoffice_session(RequestContext(headers))
            if path == "/api/backoffice/orders" and method == "GET":
                return 200, self.list_backoffice_orders(
                    RequestContext(headers),
                    status_filter=query.get("status", [None])[0],
                    slot_start_from=query.get("slotStartFrom", [None])[0],
                    page=query.get("page", [None])[0],
                )
            if path.startswith("/api/backoffice/orders/") and method == "GET" and path.count("/") == 4:
                order_id = path.rsplit("/", 1)[-1]
                return 200, self.get_backoffice_order_detail(RequestContext(headers), order_id)
            if path.startswith("/api/backoffice/orders/") and method == "POST":
                order_id, action = path.rsplit("/", 2)[-2:]
                payload = self._load_json(body)
                return 200, self.apply_backoffice_order_action(RequestContext(headers), order_id, action, payload)
            if path == "/api/backoffice/availability" and method == "GET":
                return 200, self.list_availability(
                    RequestContext(headers),
                    entity_type=query.get("type", [None])[0],
                    search=query.get("search", [None])[0],
                )
            if path.startswith("/api/backoffice/availability/") and method == "PATCH":
                entity_type, entity_id = path.removeprefix("/api/backoffice/availability/").split("/", 1)
                payload = self._load_json(body)
                return 200, self.update_availability(RequestContext(headers), entity_type, entity_id, payload)
            if path == "/api/backoffice/menu" and method == "GET":
                return 200, self.get_backoffice_menu(RequestContext(headers))
            if path == "/api/backoffice/menu/categories" and method == "POST":
                payload = self._load_json(body)
                return 201, self.create_menu_category(RequestContext(headers), payload)
            if path.startswith("/api/backoffice/menu/categories/") and method == "PATCH":
                category_id = path.rsplit("/", 1)[-1]
                payload = self._load_json(body)
                return 200, self.update_menu_category(RequestContext(headers), category_id, payload)
            if path == "/api/backoffice/menu/products" and method == "POST":
                payload = self._load_json(body)
                return 201, self.create_menu_product(RequestContext(headers), payload)
            if path.startswith("/api/backoffice/menu/products/") and method == "PATCH":
                product_id = path.rsplit("/", 1)[-1]
                payload = self._load_json(body)
                return 200, self.update_menu_product(RequestContext(headers), product_id, payload)
            if path == "/api/backoffice/users" and method == "GET":
                return 200, self.list_backoffice_users(RequestContext(headers), query.get("search", [None])[0])
            if path.startswith("/api/backoffice/users/") and method == "PATCH":
                user_id, action = path.rsplit("/", 2)[-2:]
                payload = self._load_json(body)
                if action == "role":
                    return 200, self.update_user_role(RequestContext(headers), user_id, payload)
                if action == "block":
                    return 200, self.update_user_block(RequestContext(headers), user_id, payload)
            if path == "/api/backoffice/settings" and method == "GET":
                return 200, self.get_backoffice_settings(RequestContext(headers))
            if path == "/api/backoffice/settings" and method == "PATCH":
                payload = self._load_json(body)
                return 200, self.update_backoffice_settings(RequestContext(headers), payload)
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

    def _resolve_user_by_telegram(self, connection: sqlite3.Connection, telegram_id: str | None) -> sqlite3.Row | None:
        if not telegram_id:
            return None
        return connection.execute(
            "SELECT * FROM users WHERE telegram_id = ? LIMIT 1",
            (telegram_id,),
        ).fetchone()

    def _resolve_customer(self, context: RequestContext) -> sqlite3.Row:
        telegram_id = context.headers.get("x-telegram-user-id")
        with self._connect() as connection:
            if self.disable_tg_auth or not telegram_id:
                user = connection.execute("SELECT * FROM users WHERE id = 'customer-1'").fetchone()
            else:
                user = self._resolve_user_by_telegram(connection, telegram_id)
            if not user:
                raise ApiError(401, "AUTH_CONTEXT_MISSING", "Customer session is unavailable.")
            return user

    def _resolve_backoffice(self, context: RequestContext, allowed_roles: set[str] | None = None) -> sqlite3.Row:
        telegram_id = context.headers.get("x-telegram-user-id")
        requested_role = context.headers.get("x-backoffice-role")
        with self._connect() as connection:
            user = None
            if not self.disable_tg_auth and telegram_id:
                user = self._resolve_user_by_telegram(connection, telegram_id)
            if user is None and self.disable_tg_auth:
                if requested_role == "barista":
                    user = connection.execute("SELECT * FROM users WHERE id = 'barista-1'").fetchone()
                elif requested_role == "administrator":
                    user = connection.execute("SELECT * FROM users WHERE id = 'admin-1'").fetchone()
                elif requested_role:
                    user = connection.execute(
                        "SELECT * FROM users WHERE role = ? ORDER BY id LIMIT 1",
                        (requested_role,),
                    ).fetchone()
                else:
                    user = connection.execute("SELECT * FROM users WHERE id = 'admin-1'").fetchone()
            if not user:
                raise ApiError(401, "AUTH_CONTEXT_MISSING", "Backoffice session is unavailable.")
            if bool(user["is_blocked"]):
                raise ApiError(403, "BLOCKED_USER", "Blocked users cannot access backoffice.")
            if user["role"] not in {"barista", "administrator"}:
                raise ApiError(403, "INSUFFICIENT_ROLE", "Backoffice access requires barista or administrator role.")
            if allowed_roles and user["role"] not in allowed_roles:
                raise ApiError(403, "INSUFFICIENT_ROLE", "This action is not available for the current role.")
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
            reminder_payload = {
                "orderId": order_id,
                "status": "Created",
                "slotStart": slot["start"],
                "assigneeRole": "barista",
            }
            connection.execute(
                "INSERT INTO notification_outbox(kind, payload_json, created_at) VALUES(?, ?, ?)",
                ("order.requires.barista-action", json.dumps(reminder_payload), created_at),
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
                    "reason": row["reason"],
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

    def _allowed_tabs(self, role: str) -> list[str]:
        if role == "administrator":
            return ["orders", "availability", "menu", "users", "settings"]
        return ["orders", "availability"]

    def get_backoffice_session(self, context: RequestContext) -> dict[str, Any]:
        user = self._resolve_backoffice(context)
        return {
            "userId": user["id"],
            "displayName": user["display_name"],
            "role": user["role"],
            "allowedTabs": self._allowed_tabs(user["role"]),
        }

    def _order_summary(self, connection: sqlite3.Connection, order: sqlite3.Row) -> dict[str, Any]:
        return {
            "orderId": order["id"],
            "customerUserId": order["user_id"],
            "status": order["status"],
            "slotStart": order["slot_start"],
            "slotEnd": order["slot_end"],
            "totalRub": order["total_rub"],
            "createdAt": order["created_at"],
            "itemCount": connection.execute(
                "SELECT COUNT(*) AS count FROM order_items WHERE order_id = ?",
                (order["id"],),
            ).fetchone()["count"],
            "rejectReason": order["reject_reason"],
        }

    def _order_detail(self, connection: sqlite3.Connection, order_id: str) -> dict[str, Any]:
        order = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
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
                "reason": row["reason"],
            }
            for row in connection.execute(
                "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY id",
                (order_id,),
            ).fetchall()
        ]
        return {"order": self._order_summary(connection, order), "items": items, "statusHistory": history}

    def list_backoffice_orders(
        self,
        context: RequestContext,
        status_filter: str | None,
        slot_start_from: str | None,
        page: str | None,
    ) -> dict[str, Any]:
        self._resolve_backoffice(context)
        with self._connect() as connection:
            clauses: list[str] = []
            params: list[Any] = []
            if status_filter:
                clauses.append("status = ?")
                params.append(status_filter)
            if slot_start_from:
                clauses.append("slot_start >= ?")
                params.append(slot_start_from)
            where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            page_size = 25
            page_number = int(page) if page and str(page).isdigit() and int(page) > 0 else 1
            offset = (page_number - 1) * page_size
            orders = [
                self._order_summary(connection, row)
                for row in connection.execute(
                    f"SELECT * FROM orders {where_sql} ORDER BY slot_start, created_at LIMIT ? OFFSET ?",
                    (*params, page_size, offset),
                ).fetchall()
            ]
            counters = {"total": 0}
            for row in connection.execute(
                "SELECT status, COUNT(*) AS count FROM orders GROUP BY status ORDER BY status"
            ).fetchall():
                counters[row["status"]] = row["count"]
                counters["total"] += row["count"]
        return {"orders": orders, "counters": counters}

    def get_backoffice_order_detail(self, context: RequestContext, order_id: str) -> dict[str, Any]:
        self._resolve_backoffice(context)
        with self._connect() as connection:
            return self._order_detail(connection, order_id)

    def _queue_outbox(self, connection: sqlite3.Connection, kind: str, payload: dict[str, Any]) -> None:
        connection.execute(
            "INSERT INTO notification_outbox(kind, payload_json, created_at) VALUES(?, ?, ?)",
            (kind, json.dumps(payload), utc_now()),
        )

    def _emit_order_status_changed(
        self,
        connection: sqlite3.Connection,
        order_id: str,
        status: str,
        changed_by_user_id: str,
        reject_reason: str | None,
    ) -> None:
        order = connection.execute(
            """
            SELECT o.id, o.slot_start, u.telegram_id
            FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE o.id = ?
            """,
            (order_id,),
        ).fetchone()
        if not order:
            raise ApiError(404, "ORDER_NOT_FOUND", "Order was not found.")
        self._queue_outbox(
            connection,
            "order.status.changed",
            {
                "orderId": order["id"],
                "customerTelegramId": order["telegram_id"],
                "status": status,
                "rejectReason": reject_reason,
                "changedByUserId": changed_by_user_id,
            },
        )

    def apply_backoffice_order_action(
        self,
        context: RequestContext,
        order_id: str,
        action: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        actor = self._resolve_backoffice(context, allowed_roles={"barista", "administrator"})
        transitions = {
            "confirm": ("Created", "Confirmed", False),
            "reject": ("Created", "Rejected", True),
            "ready": ("Confirmed", "Ready for pickup", False),
            "close": ("Ready for pickup", "Closed", False),
        }
        if action not in transitions:
            raise ApiError(404, "NOT_FOUND", "Order action was not found.")
        expected_status, next_status, requires_reason = transitions[action]
        reason = str(payload.get("reason", "")).strip() or None
        if requires_reason and not reason:
            raise ApiError(422, "REJECT_REASON_REQUIRED", "Reject reason is required.")
        with self._connect() as connection:
            order = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not order:
                raise ApiError(404, "ORDER_NOT_FOUND", "Order was not found.")
            if order["status"] != expected_status:
                raise ApiError(409, "ORDER_STATUS_TRANSITION_INVALID", "Order status transition is not allowed.")
            acted_at = str(payload.get("actedAt", "")).strip() or utc_now()
            connection.execute(
                "UPDATE orders SET status = ?, reject_reason = ? WHERE id = ?",
                (next_status, reason if next_status == "Rejected" else None, order_id),
            )
            connection.execute(
                """
                INSERT INTO order_status_history(order_id, status, changed_at, changed_by, reason)
                VALUES(?, ?, ?, ?, ?)
                """,
                (order_id, next_status, acted_at, actor["id"], reason),
            )
            self._emit_order_status_changed(connection, order_id, next_status, actor["id"], reason)
            connection.commit()
        return {"orderId": order_id, "status": next_status, "reason": reason}

    def list_availability(self, context: RequestContext, entity_type: str | None, search: str | None) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"barista", "administrator"})
        term = search.strip().lower() if search and search.strip() else None
        with self._connect() as connection:
            entities: list[dict[str, Any]] = []
            if entity_type in {None, "", "categories"}:
                for row in connection.execute("SELECT * FROM categories ORDER BY sort_order").fetchall():
                    if term and term not in row["name"].lower():
                        continue
                    entities.append({"entityType": "categories", "entityId": row["id"], "name": row["name"], "isActive": bool(row["is_active"])})
            if entity_type in {None, "", "products"}:
                for row in connection.execute("SELECT * FROM products ORDER BY sort_order").fetchall():
                    if term and term not in row["name"].lower():
                        continue
                    entities.append({"entityType": "products", "entityId": row["id"], "name": row["name"], "isActive": bool(row["is_active"])})
            if entity_type in {None, "", "modifier-groups"}:
                for row in connection.execute("SELECT * FROM modifier_groups ORDER BY sort_order").fetchall():
                    if term and term not in row["name"].lower():
                        continue
                    entities.append({"entityType": "modifier-groups", "entityId": row["id"], "name": row["name"], "isActive": bool(row["is_active"])})
            if entity_type in {None, "", "modifier-options"}:
                for row in connection.execute("SELECT * FROM modifier_options ORDER BY sort_order").fetchall():
                    if term and term not in row["label"].lower():
                        continue
                    entities.append({"entityType": "modifier-options", "entityId": row["id"], "name": row["label"], "isActive": bool(row["is_active"])})
        return {"entities": entities}

    def update_availability(self, context: RequestContext, entity_type: str, entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"barista", "administrator"})
        if "isActive" not in payload or not isinstance(payload["isActive"], bool):
            raise ApiError(422, "IS_ACTIVE_REQUIRED", "isActive must be provided as a boolean.")
        mapping = {
            "categories": "categories",
            "products": "products",
            "modifier-groups": "modifier_groups",
            "modifier-options": "modifier_options",
        }
        table_name = mapping.get(entity_type)
        if not table_name:
            raise ApiError(404, "ENTITY_TYPE_NOT_FOUND", "Availability entity type is not supported.")
        with self._connect() as connection:
            existing = connection.execute(f"SELECT id FROM {table_name} WHERE id = ?", (entity_id,)).fetchone()
            if not existing:
                raise ApiError(404, "ENTITY_NOT_FOUND", "Availability entity was not found.")
            connection.execute(f"UPDATE {table_name} SET is_active = ? WHERE id = ?", (1 if payload["isActive"] else 0, entity_id))
            connection.commit()
        return {"entityId": entity_id, "entityType": entity_type, "isActive": payload["isActive"]}

    def get_backoffice_menu(self, context: RequestContext) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"administrator"})
        with self._connect() as connection:
            categories = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "sortOrder": row["sort_order"],
                    "isActive": bool(row["is_active"]),
                }
                for row in connection.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
            ]
            products = [self.create_menu_product_response(row["id"])["product"] for row in connection.execute("SELECT id FROM products ORDER BY sort_order").fetchall()]
            modifier_groups = []
            for group in connection.execute("SELECT * FROM modifier_groups ORDER BY sort_order").fetchall():
                options = [
                    {
                        "id": option["id"],
                        "label": option["label"],
                        "priceDeltaRub": option["price_delta_rub"],
                        "sortOrder": option["sort_order"],
                        "isActive": bool(option["is_active"]),
                    }
                    for option in connection.execute("SELECT * FROM modifier_options WHERE group_id = ? ORDER BY sort_order", (group["id"],)).fetchall()
                ]
                modifier_groups.append(
                    {
                        "id": group["id"],
                        "name": group["name"],
                        "minSelect": group["min_select"],
                        "maxSelect": group["max_select"],
                        "sortOrder": group["sort_order"],
                        "isActive": bool(group["is_active"]),
                        "options": options,
                    }
                )
        return {"categories": categories, "products": products, "modifierGroups": modifier_groups}

    def _validate_size_payload(self, sizes: Any) -> list[dict[str, Any]]:
        if not isinstance(sizes, list) or not sizes:
            raise ApiError(422, "SIZES_REQUIRED", "sizes must be a non-empty list.")
        normalized: list[dict[str, Any]] = []
        default_count = 0
        for entry in sizes:
            if not isinstance(entry, dict):
                raise ApiError(422, "SIZES_REQUIRED", "sizes entries must be objects.")
            code = str(entry.get("code", "")).strip()
            label = str(entry.get("label", "")).strip()
            price_rub = entry.get("priceRub")
            is_default = bool(entry.get("isDefault"))
            if not code or not label or not isinstance(price_rub, int) or price_rub < 0:
                raise ApiError(422, "SIZES_REQUIRED", "Each size requires code, label, and non-negative priceRub.")
            default_count += 1 if is_default else 0
            normalized.append({"code": code, "label": label, "priceRub": price_rub, "isDefault": is_default})
        if default_count != 1:
            raise ApiError(422, "SIZES_REQUIRED", "Exactly one size must be marked as default.")
        return normalized

    def _write_product_sizes(self, connection: sqlite3.Connection, product_id: str, sizes: list[dict[str, Any]]) -> None:
        connection.execute("DELETE FROM product_sizes WHERE product_id = ?", (product_id,))
        for size in sizes:
            connection.execute(
                "INSERT INTO product_sizes(id, product_id, code, label, price_rub, is_default) VALUES(?, ?, ?, ?, ?, ?)",
                (f"{product_id}-{size['code']}", product_id, size["code"], size["label"], size["priceRub"], 1 if size["isDefault"] else 0),
            )

    def _write_product_modifier_bindings(self, connection: sqlite3.Connection, product_id: str, modifier_group_ids: list[str]) -> None:
        if any(not isinstance(group_id, str) or not group_id.strip() for group_id in modifier_group_ids):
            raise ApiError(422, "MODIFIER_GROUP_IDS_INVALID", "modifierGroupIds must be a list of IDs.")
        if modifier_group_ids:
            placeholders = ",".join("?" for _ in modifier_group_ids)
            existing = connection.execute(f"SELECT id FROM modifier_groups WHERE id IN ({placeholders})", tuple(modifier_group_ids)).fetchall()
            if len(existing) != len(set(modifier_group_ids)):
                raise ApiError(422, "MODIFIER_GROUP_IDS_INVALID", "Unknown modifier group ID was provided.")
        connection.execute("DELETE FROM product_modifier_bindings WHERE product_id = ?", (product_id,))
        for index, group_id in enumerate(modifier_group_ids, start=1):
            connection.execute(
                "INSERT INTO product_modifier_bindings(product_id, group_id, sort_order) VALUES(?, ?, ?)",
                (product_id, group_id, index),
            )

    def create_menu_category_response(self, category_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
        return {"category": {"id": row["id"], "name": row["name"], "description": row["description"], "sortOrder": row["sort_order"], "isActive": bool(row["is_active"])}}

    def create_menu_category(self, context: RequestContext, payload: dict[str, Any]) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"administrator"})
        name = str(payload.get("name", "")).strip()
        if not name:
            raise ApiError(422, "CATEGORY_NAME_REQUIRED", "Category name is required.")
        sort_order = payload.get("sortOrder")
        if not isinstance(sort_order, int):
            raise ApiError(422, "SORT_ORDER_REQUIRED", "sortOrder must be provided as an integer.")
        category_id = name.lower().replace(" ", "-")
        description = str(payload.get("description", "")).strip()
        with self._connect() as connection:
            connection.execute("INSERT INTO categories(id, name, description, sort_order, is_active) VALUES(?, ?, ?, ?, 1)", (category_id, name, description, sort_order))
            connection.commit()
        return self.create_menu_category_response(category_id)

    def update_menu_category(self, context: RequestContext, category_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"administrator"})
        with self._connect() as connection:
            existing = connection.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
            if not existing:
                raise ApiError(404, "CATEGORY_NOT_FOUND", "Category was not found.")
            name = str(payload.get("name", existing["name"])).strip()
            description = str(payload.get("description", existing["description"])).strip()
            sort_order = payload.get("sortOrder", existing["sort_order"])
            is_active = payload.get("isActive", bool(existing["is_active"]))
            if not name or not isinstance(sort_order, int) or not isinstance(is_active, bool):
                raise ApiError(422, "CATEGORY_UPDATE_INVALID", "Category update payload is invalid.")
            connection.execute(
                "UPDATE categories SET name = ?, description = ?, sort_order = ?, is_active = ? WHERE id = ?",
                (name, description, sort_order, 1 if is_active else 0, category_id),
            )
            connection.commit()
        return self.create_menu_category_response(category_id)

    def create_menu_product_response(self, product_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            sizes = [
                {"code": size["code"], "label": size["label"], "priceRub": size["price_rub"], "isDefault": bool(size["is_default"])}
                for size in connection.execute("SELECT * FROM product_sizes WHERE product_id = ? ORDER BY is_default DESC, price_rub", (product_id,)).fetchall()
            ]
            modifier_group_ids = [
                binding["group_id"]
                for binding in connection.execute("SELECT group_id FROM product_modifier_bindings WHERE product_id = ? ORDER BY sort_order", (product_id,)).fetchall()
            ]
        return {"product": {"id": row["id"], "categoryId": row["category_id"], "name": row["name"], "description": row["description"], "sortOrder": row["sort_order"], "isActive": bool(row["is_active"]), "sizes": sizes, "modifierGroupIds": modifier_group_ids}}

    def create_menu_product(self, context: RequestContext, payload: dict[str, Any]) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"administrator"})
        category_id = str(payload.get("categoryId", "")).strip()
        name = str(payload.get("name", "")).strip()
        description = str(payload.get("description", "")).strip()
        sort_order = payload.get("sortOrder", 100)
        sizes = self._validate_size_payload(payload.get("sizes"))
        modifier_group_ids = payload.get("modifierGroupIds") or []
        if not category_id or not name or not isinstance(sort_order, int):
            raise ApiError(422, "PRODUCT_CREATE_INVALID", "Product payload is invalid.")
        product_id = name.lower().replace(" ", "-")
        with self._connect() as connection:
            category = connection.execute("SELECT id FROM categories WHERE id = ?", (category_id,)).fetchone()
            if not category:
                raise ApiError(422, "CATEGORY_NOT_FOUND", "Category was not found.")
            connection.execute(
                "INSERT INTO products(id, category_id, name, description, sort_order, is_active) VALUES(?, ?, ?, ?, ?, 1)",
                (product_id, category_id, name, description, sort_order),
            )
            self._write_product_sizes(connection, product_id, sizes)
            self._write_product_modifier_bindings(connection, product_id, modifier_group_ids)
            connection.commit()
        return self.create_menu_product_response(product_id)

    def update_menu_product(self, context: RequestContext, product_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"administrator"})
        with self._connect() as connection:
            existing = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not existing:
                raise ApiError(404, "PRODUCT_NOT_FOUND", "Requested product was not found.")
            category_id = str(payload.get("categoryId", existing["category_id"])).strip()
            name = str(payload.get("name", existing["name"])).strip()
            description = str(payload.get("description", existing["description"])).strip()
            sort_order = payload.get("sortOrder", existing["sort_order"])
            is_active = payload.get("isActive", bool(existing["is_active"]))
            if not category_id or not name or not isinstance(sort_order, int) or not isinstance(is_active, bool):
                raise ApiError(422, "PRODUCT_UPDATE_INVALID", "Product update payload is invalid.")
            connection.execute(
                "UPDATE products SET category_id = ?, name = ?, description = ?, sort_order = ?, is_active = ? WHERE id = ?",
                (category_id, name, description, sort_order, 1 if is_active else 0, product_id),
            )
            if "sizes" in payload:
                self._write_product_sizes(connection, product_id, self._validate_size_payload(payload.get("sizes")))
            if "modifierGroupIds" in payload:
                self._write_product_modifier_bindings(connection, product_id, payload.get("modifierGroupIds") or [])
            connection.commit()
        return self.create_menu_product_response(product_id)

    def list_backoffice_users(self, context: RequestContext, search: str | None) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"administrator"})
        term = search.strip().lower() if search and search.strip() else None
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM users ORDER BY display_name").fetchall()
        users = []
        for row in rows:
            haystack = f"{row['display_name']} {row['telegram_id']} {row['role']}".lower()
            if term and term not in haystack:
                continue
            users.append({"id": row["id"], "telegramId": row["telegram_id"], "displayName": row["display_name"], "role": row["role"], "isBlocked": bool(row["is_blocked"])})
        return {"users": users}

    def update_user_role(self, context: RequestContext, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"administrator"})
        role = str(payload.get("role", "")).strip()
        if role not in {"customer", "barista", "administrator"}:
            raise ApiError(422, "ROLE_INVALID", "Role must be customer, barista, or administrator.")
        with self._connect() as connection:
            updated = connection.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            if updated.rowcount == 0:
                raise ApiError(404, "USER_NOT_FOUND", "User was not found.")
            connection.commit()
            row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return {"user": {"id": row["id"], "telegramId": row["telegram_id"], "displayName": row["display_name"], "role": row["role"], "isBlocked": bool(row["is_blocked"])}} 

    def update_user_block(self, context: RequestContext, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"administrator"})
        if "isBlocked" not in payload or not isinstance(payload["isBlocked"], bool):
            raise ApiError(422, "IS_BLOCKED_REQUIRED", "isBlocked must be provided as a boolean.")
        with self._connect() as connection:
            updated = connection.execute("UPDATE users SET is_blocked = ? WHERE id = ?", (1 if payload["isBlocked"] else 0, user_id))
            if updated.rowcount == 0:
                raise ApiError(404, "USER_NOT_FOUND", "User was not found.")
            connection.commit()
            row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return {"user": {"id": row["id"], "telegramId": row["telegram_id"], "displayName": row["display_name"], "role": row["role"], "isBlocked": bool(row["is_blocked"])}} 

    def get_backoffice_settings(self, context: RequestContext) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"administrator"})
        with self._connect() as connection:
            settings = self._settings(connection)
        return {"workingHours": {"openTime": settings["open_time"], "closeTime": settings["close_time"]}, "slotStepMinutes": int(settings["slot_step_minutes"]), "slotCapacity": int(settings["slot_capacity"])}

    def update_backoffice_settings(self, context: RequestContext, payload: dict[str, Any]) -> dict[str, Any]:
        self._resolve_backoffice(context, allowed_roles={"administrator"})
        open_time = payload.get("openTime")
        close_time = payload.get("closeTime")
        slot_capacity = payload.get("slotCapacity")
        if open_time is not None and (not isinstance(open_time, str) or len(open_time.split(":")) != 2):
            raise ApiError(422, "SETTINGS_INVALID", "openTime must be in HH:MM format.")
        if close_time is not None and (not isinstance(close_time, str) or len(close_time.split(":")) != 2):
            raise ApiError(422, "SETTINGS_INVALID", "closeTime must be in HH:MM format.")
        if slot_capacity is not None and (not isinstance(slot_capacity, int) or slot_capacity < 1):
            raise ApiError(422, "SETTINGS_INVALID", "slotCapacity must be a positive integer.")
        with self._connect() as connection:
            if open_time is not None:
                connection.execute("UPDATE settings SET value = ? WHERE key = 'open_time'", (open_time,))
            if close_time is not None:
                connection.execute("UPDATE settings SET value = ? WHERE key = 'close_time'", (close_time,))
            if slot_capacity is not None:
                connection.execute("UPDATE settings SET value = ? WHERE key = 'slot_capacity'", (str(slot_capacity),))
            settings = self._settings(connection)
            if settings["open_time"] >= settings["close_time"]:
                raise ApiError(422, "SETTINGS_INVALID", "closeTime must be later than openTime.")
            connection.commit()
        return self.get_backoffice_settings(context)
