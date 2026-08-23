import os
import random
from typing import List, Optional
from locust import HttpUser, between, task

from load_tests.helpers import (
    generate_idempotency_key,
    get_configured_strategy,
    get_random_item_id,
    get_random_quantity,
)
from load_tests.profiles import WORKLOAD_PROFILES


class InventoryUser(HttpUser):
    # Think time between 5ms and 25ms to generate high concurrency pressure
    wait_time = between(0.005, 0.025)

    def on_start(self):
        self.profile_name = os.getenv("LOADTEST_PROFILE", "mixed")
        self.item_count = int(os.getenv("LOADTEST_ITEM_COUNT", "10"))
        self.strategy = get_configured_strategy()
        self.created_reservation_ids: List[int] = []
        self.last_idempotency_key: Optional[str] = None
        self.last_item_id: Optional[int] = None

    @task(30)
    def list_items(self):
        """Task: Read item catalog."""
        self.client.get("/items", name="/items [GET]")

    @task(30)
    def get_item_detail(self):
        """Task: Read single item state."""
        item_id = get_random_item_id(self.item_count)
        self.client.get(f"/items/{item_id}", name="/items/:id [GET]")

    @task(35)
    def reserve_item(self):
        """Task: Attempt reservation with idempotency key and strategy."""
        item_id = get_random_item_id(self.item_count)
        qty = get_random_quantity(max_qty=3)
        key = generate_idempotency_key(prefix=f"u{id(self)}")

        # 5% of the time, simulate intentional duplicate submission
        if random.random() < 0.05 and self.last_idempotency_key and self.last_item_id:
            key = self.last_idempotency_key
            item_id = self.last_item_id

        payload = {
            "quantity": qty,
            "idempotency_key": key,
        }
        if self.strategy:
            payload["strategy"] = self.strategy

        with self.client.post(
            f"/items/{item_id}/reserve",
            json=payload,
            name="/items/:id/reserve [POST]",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                data = response.json()
                res_id = data.get("id")
                if res_id:
                    self.created_reservation_ids.append(res_id)
                self.last_idempotency_key = key
                self.last_item_id = item_id
                response.success()
            elif response.status_code == 409:
                # 409 can be Insufficient Inventory (expected business rejection) or Idempotency conflict
                err_code = response.json().get("detail", {}).get("error_code") if isinstance(response.json().get("detail"), dict) else ""
                if err_code in ["INSUFFICIENT_INVENTORY", "IDEMPOTENCY_CONFLICT"]:
                    response.success()
                else:
                    response.failure(f"Conflict error: {response.text}")
            elif response.status_code in [400, 422]:
                response.failure(f"Client validation error: {response.text}")
            else:
                response.failure(f"Server error HTTP {response.status_code}: {response.text}")

    @task(10)
    def release_reservation(self):
        """Task: Release a previously created reservation."""
        if not self.created_reservation_ids:
            return

        res_id = self.created_reservation_ids.pop(0)
        with self.client.post(
            f"/reservations/{res_id}/release",
            name="/reservations/:id/release [POST]",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 409]:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Release failed: {response.text}")

    @task(5)
    def check_consistency(self):
        """Task: Query database consistency endpoint during load."""
        with self.client.get(
            "/metrics/consistency",
            name="/metrics/consistency [GET]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if not data.get("consistent", False):
                    response.failure(f"Consistency violation detected during run: {data.get('violations')}")
                else:
                    response.success()
            else:
                response.failure(f"Metrics consistency endpoint failed: {response.text}")
