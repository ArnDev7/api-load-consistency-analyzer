from locust import between, task
from load_tests.locustfile import InventoryUser


class MixedWorkloadUser(InventoryUser):
    wait_time = between(0.005, 0.02)

    @task(30)
    def list_items(self):
        super().list_items()

    @task(30)
    def get_item_detail(self):
        super().get_item_detail()

    @task(25)
    def reserve_item(self):
        super().reserve_item()

    @task(10)
    def release_reservation(self):
        super().release_reservation()

    @task(5)
    def check_consistency(self):
        super().check_consistency()
