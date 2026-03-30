from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from apps.api.backend import ExpressaBackend


class BackendContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp())
        self.database_path = self.tempdir / "test.sqlite3"
        self.backend = ExpressaBackend(database_url=f"sqlite:///{self.database_path}")
        self.headers = {}

    def tearDown(self) -> None:
        del self.backend
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _request(self, method: str, path: str, body: bytes = b"", headers: dict[str, str] | None = None, query: dict[str, list[str]] | None = None):
        return self.backend.handle(method=method, path=path, query=query or {}, body=body, headers=headers or self.headers)

    def _json_request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        query: dict[str, list[str]] | None = None,
    ):
        body = json.dumps(payload or {}).encode("utf-8")
        return self._request(method, path, body=body, headers=headers, query=query)

    def _backoffice_headers(self, role: str) -> dict[str, str]:
        return {"x-backoffice-role": role}

    def _create_order(self) -> str:
        add_status, add_payload = self._json_request(
            "POST",
            "/api/customer/cart/items",
            {"productId": "flat-white", "sizeCode": "small", "qty": 1, "modifierOptionIds": ["oat"]},
        )
        self.assertEqual(add_status, 201)
        slots_status, slots_payload = self._request("GET", "/api/customer/slots")
        self.assertEqual(slots_status, 200)
        slot = next(item for item in slots_payload["slots"] if item["isAvailable"])
        create_status, create_payload = self._json_request(
            "POST",
            "/api/customer/orders",
            {"slotStart": slot["start"], "cartVersion": add_payload["version"]},
        )
        self.assertEqual(create_status, 201)
        return create_payload["orderId"]

    def test_customer_session_contract(self) -> None:
        status, payload = self._request("GET", "/api/customer/session")
        self.assertEqual(status, 200)
        self.assertEqual(payload["userId"], "customer-1")
        self.assertFalse(payload["isBlocked"])

    def test_menu_contains_only_active_products(self) -> None:
        status, payload = self._request("GET", "/api/customer/menu")
        self.assertEqual(status, 200)
        product_ids = {product["id"] for product in payload["products"]}
        self.assertIn("flat-white", product_ids)
        self.assertNotIn("almond-croissant", product_ids)

    def test_adding_cart_item_requires_size(self) -> None:
        status, payload = self.backend.handle(
            method="POST",
            path="/api/customer/cart/items",
            query={},
            body=b'{"productId":"flat-white","qty":1,"modifierOptionIds":[]}',
            headers=self.headers,
        )
        self.assertEqual(status, 422)
        self.assertEqual(payload["reason"], "SIZE_REQUIRED")

    def test_create_order_clears_cart_and_persists_history(self) -> None:
        add_status, add_payload = self.backend.handle(
            method="POST",
            path="/api/customer/cart/items",
            query={},
            body=b'{"productId":"flat-white","sizeCode":"small","qty":2,"modifierOptionIds":["oat"]}',
            headers=self.headers,
        )
        self.assertEqual(add_status, 201)
        cart_version = add_payload["version"]

        slots_status, slots_payload = self._request("GET", "/api/customer/slots")
        self.assertEqual(slots_status, 200)
        slot = next(item for item in slots_payload["slots"] if item["isAvailable"])

        create_status, create_payload = self.backend.handle(
            method="POST",
            path="/api/customer/orders",
            query={},
            body=f'{{"slotStart":"{slot["start"]}","cartVersion":{cart_version}}}'.encode("utf-8"),
            headers=self.headers,
        )
        self.assertEqual(create_status, 201)
        self.assertEqual(create_payload["status"], "Created")

        cart_status, cart_payload = self._request("GET", "/api/customer/cart")
        self.assertEqual(cart_status, 200)
        self.assertEqual(cart_payload["items"], [])

        orders_status, orders_payload = self._request("GET", "/api/customer/orders")
        self.assertEqual(orders_status, 200)
        self.assertEqual(len(orders_payload["orders"]), 1)

        order_id = orders_payload["orders"][0]["orderId"]
        detail_status, detail_payload = self._request("GET", f"/api/customer/orders/{order_id}")
        self.assertEqual(detail_status, 200)
        self.assertEqual(detail_payload["order"]["itemCount"], 1)
        self.assertEqual(detail_payload["statusHistory"][0]["status"], "Created")

    def test_meta_keeps_stage0_contract(self) -> None:
        status, payload = self._request("GET", "/api/meta")
        self.assertEqual(status, 200)
        self.assertEqual(payload["project"], "expressa-stage0")
        self.assertEqual(payload["backendMode"], "customer-core-live")

    def test_backoffice_session_exposes_role_tabs(self) -> None:
        status, payload = self._request("GET", "/api/backoffice/session", headers=self._backoffice_headers("administrator"))
        self.assertEqual(status, 200)
        self.assertEqual(payload["role"], "administrator")
        self.assertIn("settings", payload["allowedTabs"])

        denied_status, denied_payload = self._request("GET", "/api/backoffice/session", headers=self._backoffice_headers("customer"))
        self.assertEqual(denied_status, 403)
        self.assertEqual(denied_payload["reason"], "INSUFFICIENT_ROLE")

    def test_backoffice_order_actions_persist_audit_and_notifications(self) -> None:
        order_id = self._create_order()

        list_status, list_payload = self._request("GET", "/api/backoffice/orders", headers=self._backoffice_headers("barista"))
        self.assertEqual(list_status, 200)
        self.assertEqual(list_payload["counters"]["Created"], 1)

        confirm_status, confirm_payload = self._json_request(
            "POST",
            f"/api/backoffice/orders/{order_id}/confirm",
            {},
            headers=self._backoffice_headers("barista"),
        )
        self.assertEqual(confirm_status, 200)
        self.assertEqual(confirm_payload["status"], "Confirmed")

        ready_status, _ = self._json_request(
            "POST",
            f"/api/backoffice/orders/{order_id}/ready",
            {},
            headers=self._backoffice_headers("barista"),
        )
        self.assertEqual(ready_status, 200)

        close_status, close_payload = self._json_request(
            "POST",
            f"/api/backoffice/orders/{order_id}/close",
            {},
            headers=self._backoffice_headers("barista"),
        )
        self.assertEqual(close_status, 200)
        self.assertEqual(close_payload["status"], "Closed")

        detail_status, detail_payload = self._request(
            "GET",
            f"/api/backoffice/orders/{order_id}",
            headers=self._backoffice_headers("barista"),
        )
        self.assertEqual(detail_status, 200)
        self.assertEqual(
            [entry["status"] for entry in detail_payload["statusHistory"]],
            ["Created", "Confirmed", "Ready for pickup", "Closed"],
        )
        self.assertEqual(detail_payload["statusHistory"][1]["changedBy"], "barista-1")

        with self.backend._connect() as connection:
            kinds = [
                row["kind"]
                for row in connection.execute(
                    "SELECT kind FROM notification_outbox WHERE json_extract(payload_json, '$.orderId') = ? ORDER BY id",
                    (order_id,),
                ).fetchall()
            ]
        self.assertEqual(kinds.count("order.requires.barista-action"), 1)
        self.assertGreaterEqual(kinds.count("order.status.changed"), 4)

    def test_reject_requires_reason(self) -> None:
        order_id = self._create_order()
        reject_status, reject_payload = self._json_request(
            "POST",
            f"/api/backoffice/orders/{order_id}/reject",
            {},
            headers=self._backoffice_headers("administrator"),
        )
        self.assertEqual(reject_status, 422)
        self.assertEqual(reject_payload["reason"], "REJECT_REASON_REQUIRED")

        ok_status, ok_payload = self._json_request(
            "POST",
            f"/api/backoffice/orders/{order_id}/reject",
            {"reason": "Machine maintenance"},
            headers=self._backoffice_headers("administrator"),
        )
        self.assertEqual(ok_status, 200)
        self.assertEqual(ok_payload["status"], "Rejected")

        detail_status, detail_payload = self._request(
            "GET",
            f"/api/backoffice/orders/{order_id}",
            headers=self._backoffice_headers("administrator"),
        )
        self.assertEqual(detail_status, 200)
        self.assertEqual(detail_payload["order"]["rejectReason"], "Machine maintenance")
        self.assertEqual(detail_payload["statusHistory"][-1]["reason"], "Machine maintenance")

    def test_barista_can_toggle_availability_but_not_admin_surfaces(self) -> None:
        status, payload = self._json_request(
            "PATCH",
            "/api/backoffice/availability/products/flat-white",
            {"isActive": False},
            headers=self._backoffice_headers("barista"),
        )
        self.assertEqual(status, 200)
        self.assertFalse(payload["isActive"])

        menu_status, menu_payload = self._request("GET", "/api/customer/menu")
        self.assertEqual(menu_status, 200)
        product_ids = {product["id"] for product in menu_payload["products"]}
        self.assertNotIn("flat-white", product_ids)

        for path in ("/api/backoffice/menu", "/api/backoffice/users", "/api/backoffice/settings"):
            denied_status, denied_payload = self._request("GET", path, headers=self._backoffice_headers("barista"))
            self.assertEqual(denied_status, 403)
            self.assertEqual(denied_payload["reason"], "INSUFFICIENT_ROLE")

    def test_admin_can_manage_menu_users_and_settings(self) -> None:
        admin_headers = self._backoffice_headers("administrator")

        category_status, category_payload = self._json_request(
            "POST",
            "/api/backoffice/menu/categories",
            {"name": "Seasonal Drinks", "description": "Limited specials", "sortOrder": 4},
            headers=admin_headers,
        )
        self.assertEqual(category_status, 201)
        self.assertEqual(category_payload["category"]["id"], "seasonal-drinks")

        product_status, product_payload = self._json_request(
            "POST",
            "/api/backoffice/menu/products",
            {
                "categoryId": "seasonal-drinks",
                "name": "Orange Tonic",
                "description": "Espresso tonic",
                "sortOrder": 5,
                "sizes": [{"code": "medium", "label": "M / 350 ml", "priceRub": 320, "isDefault": True}],
                "modifierGroupIds": ["extras"],
            },
            headers=admin_headers,
        )
        self.assertEqual(product_status, 201)
        self.assertEqual(product_payload["product"]["id"], "orange-tonic")

        update_status, update_payload = self._json_request(
            "PATCH",
            "/api/backoffice/menu/products/orange-tonic",
            {"isActive": False, "description": "Espresso tonic with orange"},
            headers=admin_headers,
        )
        self.assertEqual(update_status, 200)
        self.assertFalse(update_payload["product"]["isActive"])

        role_status, role_payload = self._json_request(
            "PATCH",
            "/api/backoffice/users/customer-1/role",
            {"role": "barista"},
            headers=admin_headers,
        )
        self.assertEqual(role_status, 200)
        self.assertEqual(role_payload["user"]["role"], "barista")

        block_status, block_payload = self._json_request(
            "PATCH",
            "/api/backoffice/users/customer-1/block",
            {"isBlocked": True},
            headers=admin_headers,
        )
        self.assertEqual(block_status, 200)
        self.assertTrue(block_payload["user"]["isBlocked"])

        settings_status, settings_payload = self._json_request(
            "PATCH",
            "/api/backoffice/settings",
            {"openTime": "08:30", "closeTime": "21:00", "slotCapacity": 7},
            headers=admin_headers,
        )
        self.assertEqual(settings_status, 200)
        self.assertEqual(settings_payload["slotCapacity"], 7)
        self.assertEqual(settings_payload["workingHours"]["openTime"], "08:30")
