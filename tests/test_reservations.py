from fastapi.testclient import TestClient


def test_reserve_item_success(client: TestClient, sample_item):
    """Test successful inventory reservation."""
    payload = {
        "quantity": 10,
        "idempotency_key": "test-res-1",
        "strategy": "atomic_update",
    }
    response = client.post(f"/items/{sample_item.id}/reserve", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == sample_item.id
    assert data["quantity"] == 10
    assert data["status"] == "ACTIVE"

    # Verify item inventory reduced
    item_res = client.get(f"/items/{sample_item.id}")
    assert item_res.json()["available_quantity"] == 90


def test_reserve_insufficient_inventory(client: TestClient, sample_item):
    """Test reservation exceeding available inventory returns 409."""
    payload = {
        "quantity": 150,
        "idempotency_key": "test-res-excess",
    }
    response = client.post(f"/items/{sample_item.id}/reserve", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["error_code"] == "INSUFFICIENT_INVENTORY"


def test_reserve_missing_item(client: TestClient):
    """Test reserving missing item returns 404."""
    payload = {
        "quantity": 5,
        "idempotency_key": "test-res-missing",
    }
    response = client.post("/items/999999/reserve", json=payload)
    assert response.status_code == 404
    assert response.json()["error_code"] == "ITEM_NOT_FOUND"


def test_reserve_invalid_quantity(client: TestClient, sample_item):
    """Test reserving 0 or negative quantity returns 422."""
    response = client.post(
        f"/items/{sample_item.id}/reserve",
        json={"quantity": 0, "idempotency_key": "test-zero"},
    )
    assert response.status_code == 422


def test_release_reservation_success(client: TestClient, sample_item):
    """Test creating and releasing a reservation."""
    res = client.post(
        f"/items/{sample_item.id}/reserve",
        json={"quantity": 25, "idempotency_key": "test-rel-1"},
    )
    assert res.status_code == 201
    reservation_id = res.json()["id"]

    # Release
    rel_res = client.post(f"/reservations/{reservation_id}/release")
    assert rel_res.status_code == 200
    rel_data = rel_res.json()
    assert rel_data["status"] == "RELEASED"
    assert rel_data["available_quantity"] == 100

    # Verify item available quantity restored
    item_res = client.get(f"/items/{sample_item.id}")
    assert item_res.json()["available_quantity"] == 100


def test_double_release_prevention(client: TestClient, sample_item):
    """Test releasing an already released reservation fails with 409."""
    res = client.post(
        f"/items/{sample_item.id}/reserve",
        json={"quantity": 15, "idempotency_key": "test-dbl-rel"},
    )
    res_id = res.json()["id"]

    # First release succeeds
    r1 = client.post(f"/reservations/{res_id}/release")
    assert r1.status_code == 200

    # Second release rejected
    r2 = client.post(f"/reservations/{res_id}/release")
    assert r2.status_code == 409
    assert r2.json()["error_code"] == "ALREADY_RELEASED"

    # Inventory must not have been double incremented
    item_res = client.get(f"/items/{sample_item.id}")
    assert item_res.json()["available_quantity"] == 100

