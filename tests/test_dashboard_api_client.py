"""Test ApiClient error handling and methods with live/mock scenarios."""
from dashboard.utils.api_client import ApiClient


def test_api_client_unreachable_endpoint():
    """Verify that ApiClient handles connection failures gracefully without raising uncaught exceptions."""
    client = ApiClient(base_url="http://127.0.0.1:59999", timeout=0.1)

    health = client.check_health()
    assert health["online"] is False
    assert health["status_code"] == 0
    assert "error" in health

    list_res = client.list_items()
    assert list_res["success"] is False
    assert list_res["data"] == []

    reserve_res = client.reserve_item(item_id=1, quantity=1, idempotency_key="k1")
    assert reserve_res["success"] is False
