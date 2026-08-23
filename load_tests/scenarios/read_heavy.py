from locust import between, task
from load_tests.helpers import (
    generate_idempotency_key,
    get_configured_strategy,
    get_random_item_id,
    get_random_quantity,
)
from load_tests.locustfile import InventoryUser


class ReadHeavyUser(InventoryUser):
    wait_time = between(0.005, 0.02)

    @task(45)
    def list_items(self):
        self.client.get("/items", name="/items [GET]")

    @task(45)
    def get_item_detail(self):
        item_id = get_random_item_id(self.item_count)
        self.client.get(f"/items/{item_id}", name="/items/:id [GET]")

    @task(8)
    def reserve_item(self):
        item_id = get_random_item_id(self.item_count)
        qty = get_random_quantity(max_qty=2)
        key = generate_idempotency_key(prefix="rh")
        payload = {"quantity": qty, "idempotency_key": key}
        if self.strategy:
            payload["strategy"] = self.strategy
        self.client.post(f"/items/{item_id}/reserve", json=payload, name="/items/:id/reserve [POST]")

    @task(2)
    def check_consistency(self):
        self.client.get("/metrics/consistency", name="/metrics/consistency [GET]")
