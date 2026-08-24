import os
import time
from typing import Any, Dict, List, Optional
import httpx

DEFAULT_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


class ApiClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_health(self) -> Dict[str, Any]:
        """Query /health endpoint."""
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(f"{self.base_url}/health")
                duration_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "online": res.status_code == 200,
                    "status_code": res.status_code,
                    "body": res.json() if res.headers.get("content-type", "").startswith("application/json") else res.text,
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            return {
                "online": False,
                "status_code": 0,
                "error": str(e),
                "duration_ms": 0.0,
            }

    def list_items(self, limit: int = 50) -> Dict[str, Any]:
        """Query /items."""
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(f"{self.base_url}/items", params={"limit": limit})
                duration_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "success": res.status_code == 200,
                    "status_code": res.status_code,
                    "data": res.json() if res.status_code == 200 else [],
                    "error": res.text if res.status_code != 200 else None,
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            return {"success": False, "status_code": 0, "error": str(e), "data": [], "duration_ms": 0.0}

    def get_item(self, item_id: int) -> Dict[str, Any]:
        """Query /items/{item_id}."""
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(f"{self.base_url}/items/{item_id}")
                duration_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "success": res.status_code == 200,
                    "status_code": res.status_code,
                    "data": res.json() if res.status_code == 200 else None,
                    "error": res.text if res.status_code != 200 else None,
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            return {"success": False, "status_code": 0, "error": str(e), "duration_ms": 0.0}

    def create_item(self, sku: str, name: str, initial_quantity: int) -> Dict[str, Any]:
        """POST /items."""
        start = time.perf_counter()
        payload = {"sku": sku, "name": name, "initial_quantity": initial_quantity}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/items", json=payload)
                duration_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "success": res.status_code == 201,
                    "status_code": res.status_code,
                    "data": res.json() if res.status_code == 201 else None,
                    "body": res.json() if res.headers.get("content-type", "").startswith("application/json") else res.text,
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            return {"success": False, "status_code": 0, "error": str(e), "duration_ms": 0.0}

    def reserve_item(self, item_id: int, quantity: int, idempotency_key: str, strategy: str = "atomic_update") -> Dict[str, Any]:
        """POST /items/{item_id}/reserve."""
        start = time.perf_counter()
        payload = {"quantity": quantity, "idempotency_key": idempotency_key, "strategy": strategy}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/items/{item_id}/reserve", json=payload)
                duration_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "success": res.status_code in (200, 201),
                    "status_code": res.status_code,
                    "body": res.json() if res.headers.get("content-type", "").startswith("application/json") else res.text,
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            return {"success": False, "status_code": 0, "error": str(e), "duration_ms": 0.0}

    def release_reservation(self, reservation_id: int) -> Dict[str, Any]:
        """POST /reservations/{reservation_id}/release."""
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/reservations/{reservation_id}/release")
                duration_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "success": res.status_code == 200,
                    "status_code": res.status_code,
                    "body": res.json() if res.headers.get("content-type", "").startswith("application/json") else res.text,
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            return {"success": False, "status_code": 0, "error": str(e), "duration_ms": 0.0}

    def check_consistency(self) -> Dict[str, Any]:
        """GET /metrics/consistency."""
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(f"{self.base_url}/metrics/consistency")
                duration_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "success": res.status_code == 200,
                    "status_code": res.status_code,
                    "body": res.json() if res.status_code == 200 else None,
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            return {"success": False, "status_code": 0, "error": str(e), "duration_ms": 0.0}

    def seed_data(self, item_count: int = 10, initial_inventory: int = 100) -> Dict[str, Any]:
        """POST /test/seed."""
        start = time.perf_counter()
        payload = {"item_count": item_count, "initial_inventory_per_item": initial_inventory}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/test/seed", json=payload)
                duration_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "success": res.status_code == 201,
                    "status_code": res.status_code,
                    "body": res.json() if res.headers.get("content-type", "").startswith("application/json") else res.text,
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            return {"success": False, "status_code": 0, "error": str(e), "duration_ms": 0.0}

    def reset_database(self) -> Dict[str, Any]:
        """POST /test/reset."""
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/test/reset")
                duration_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "success": res.status_code == 200,
                    "status_code": res.status_code,
                    "body": res.json() if res.headers.get("content-type", "").startswith("application/json") else res.text,
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            return {"success": False, "status_code": 0, "error": str(e), "duration_ms": 0.0}


# Default singleton instance
api_client = ApiClient()


def check_health(base_url: Optional[str] = None) -> Dict[str, Any]:
    """Helper function for health check."""
    client = ApiClient(base_url) if base_url else api_client
    return client.check_health()
