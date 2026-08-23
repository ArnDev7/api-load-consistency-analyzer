from locust import between, task
from load_tests.locustfile import InventoryUser


class SpikeWorkloadUser(InventoryUser):
    # Very low think time to emulate high sudden bursts
    wait_time = between(0.001, 0.01)

    @task(60)
    def reserve_item(self):
        super().reserve_item()

    @task(20)
    def get_item_detail(self):
        super().get_item_detail()

    @task(15)
    def release_reservation(self):
        super().release_reservation()

    @task(5)
    def check_consistency(self):
        super().check_consistency()
