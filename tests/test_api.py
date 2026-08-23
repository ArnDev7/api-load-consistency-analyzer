from fastapi.testclient import TestClient


def test_api_full_lifecycle(client: TestClient):
    """Test full item creation -> reservation -> idempotent replay -> release -> consistency lifecycle."""
    # 1. Create item
    create_res = client.post(
        "/items",
        json={"sku": "SKU-LIFECYCLE-1", "name": "Lifecycle Item", "initial_quantity": 50},
    )
    assert create_res.status_code == 201
    item = create_res.json()
    item_id = item["id"]
    assert item["available_quantity"] == 50

    # 2. Query item detail
    get_res = client.get(f"/items/{item_id}")
    assert get_res.status_code == 200
    assert get_res.json()["sku"] == "SKU-LIFECYCLE-1"

    # 3. Reserve items
    res_payload = {
        "quantity": 15,
        "idempotency_key": "life-cycle-key-001",
        "strategy": "atomic_update",
    }
    reserve_res = client.post(f"/items/{item_id}/reserve", json=res_payload)
    assert reserve_res.status_code == 201
    reservation = reserve_res.json()
    res_id = reservation["id"]
    assert reservation["quantity"] == 15
    assert reservation["status"] == "ACTIVE"

    # Verify inventory deducted
    get_after_res = client.get(f"/items/{item_id}")
    assert get_after_res.json()["available_quantity"] == 35

    # 4. Idempotent replay
    replay_res = client.post(f"/items/{item_id}/reserve", json=res_payload)
    assert replay_res.status_code == 201
    assert replay_res.json()["id"] == res_id

    # 5. Query reservation by ID
    res_detail = client.get(f"/reservations/{res_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == res_id

    # 6. Release reservation
    release_res = client.post(f"/reservations/{res_id}/release")
    assert release_res.status_code == 200
    assert release_res.json()["status"] == "RELEASED"
    assert release_res.json()["available_quantity"] == 50

    # Verify item restored
    get_restored = client.get(f"/items/{item_id}")
    assert get_restored.json()["available_quantity"] == 50

    # 7. Check consistency
    consistency_res = client.get("/metrics/consistency")
    assert consistency_res.status_code == 200
    assert consistency_res.json()["consistent"] is True


def test_api_validation_error_format(client: TestClient):
    """Verify validation errors follow structured error response."""
    res = client.post("/items", json={"sku": "", "name": "Test", "initial_quantity": -5})
    assert res.status_code == 422
    data = res.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "details" in data
