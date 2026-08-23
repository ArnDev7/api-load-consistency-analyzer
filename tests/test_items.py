from fastapi.testclient import TestClient


def test_create_item_success(client: TestClient):
    """Test creating an item with valid payload."""
    payload = {
        "sku": "SKU-ITEM-ALPHA",
        "name": "Alpha Item",
        "initial_quantity": 50,
    }
    response = client.post("/items", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "SKU-ITEM-ALPHA"
    assert data["available_quantity"] == 50
    assert data["initial_quantity"] == 50
    assert data["version"] == 1
    assert "id" in data


def test_create_duplicate_sku(client: TestClient):
    """Test duplicate SKU creation returns 409 Conflict."""
    payload = {
        "sku": "SKU-DUPE",
        "name": "Original Item",
        "initial_quantity": 10,
    }
    res1 = client.post("/items", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/items", json=payload)
    assert res2.status_code == 409
    assert res2.json()["error_code"] == "DUPLICATE_SKU"


def test_create_item_invalid_quantity(client: TestClient):
    """Test creating an item with negative quantity returns 422 Unprocessable Entity."""
    payload = {
        "sku": "SKU-INVALID",
        "name": "Invalid Item",
        "initial_quantity": -10,
    }
    response = client.post("/items", json=payload)
    assert response.status_code == 422


def test_list_items(client: TestClient):
    """Test listing items."""
    client.post("/items", json={"sku": "SKU-L1", "name": "L1", "initial_quantity": 10})
    client.post("/items", json={"sku": "SKU-L2", "name": "L2", "initial_quantity": 20})

    response = client.get("/items")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


def test_get_item_by_id(client: TestClient, sample_item):
    """Test retrieving item by ID."""
    response = client.get(f"/items/{sample_item.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_item.id
    assert data["sku"] == sample_item.sku


def test_get_missing_item(client: TestClient):
    """Test retrieving non-existent item returns 404."""
    response = client.get("/items/999999")
    assert response.status_code == 404
    assert response.json()["error_code"] == "ITEM_NOT_FOUND"

