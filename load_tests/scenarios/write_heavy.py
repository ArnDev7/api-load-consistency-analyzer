from locust import between, task
from load_tests.helpers import (
    generate_idempotency_key,
    get_random_item_id,
    get_random_quantity,
)
from load_tests.locustfile import InventoryUser


class WriteHeavyUser(InventoryUser):
    wait_time = between(0.005, 0.02)

    @task(70)
    def reserve_item(self):
        super().reserve_item()

    @task(20)
    def release_reservation(self):
        super().release_reservation()

    @task(5)
    def get_item_detail(self):
        item_id = get_random_item_id(self.item_count)
        self.client.get(f"/items/{item_id}", name="/items/:id [GET]")

    @task(5)
    def list_items(self):
        self.client.get("/items", name="/items [GET]")
