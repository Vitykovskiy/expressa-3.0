from __future__ import annotations

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

    def _request(self, method: str, path: str, body: bytes = b""):
        return self.backend.handle(method=method, path=path, query={}, body=body, headers=self.headers)

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
