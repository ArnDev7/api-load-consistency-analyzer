import concurrent.futures
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import get_session_factory
from app.models import Reservation, Item
from app.services.reservation_service import reserve_item


def test_idempotent_replay_same_payload(client: TestClient, sample_item):
    """Repeating a completed request with the same idempotency key returns the original reservation."""
    payload = {
        "quantity": 10,
        "idempotency_key": "idemp-key-repeat",
    }
    res1 = client.post(f"/items/{sample_item.id}/reserve", json=payload)
    assert res1.status_code == 201
    data1 = res1.json()

    res2 = client.post(f"/items/{sample_item.id}/reserve", json=payload)
    assert res2.status_code == 201
    data2 = res2.json()

    assert data1["id"] == data2["id"]
    assert data1["idempotency_key"] == data2["idempotency_key"]

    # Ensure inventory was only deducted once
    item_res = client.get(f"/items/{sample_item.id}")
    assert item_res.json()["available_quantity"] == 90


def test_idempotent_key_conflict_payload(client: TestClient, sample_item):
    """Reusing same idempotency key with mismatched payload returns 409 Conflict."""
    payload1 = {
        "quantity": 10,
        "idempotency_key": "idemp-conflict-key",
    }
    res1 = client.post(f"/items/{sample_item.id}/reserve", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "quantity": 20,  # Different quantity
        "idempotency_key": "idemp-conflict-key",
    }
    res2 = client.post(f"/items/{sample_item.id}/reserve", json=payload2)
    assert res2.status_code == 409
    assert res2.json()["error_code"] == "IDEMPOTENCY_CONFLICT"



def test_concurrent_identical_idempotency_keys(db_session):
    """Simultaneous requests with identical idempotency keys create exactly one database record."""
    session_factory = get_session_factory()
    db = session_factory()
    item = Item(
        sku="SKU-IDEMP-CONCUR",
        name="Idemp Item",
        available_quantity=100,
        initial_quantity=100,
        version=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    item_id = item.id
    db.close()

    def _worker():
        worker_db = session_factory()
        try:
            res = reserve_item(
                db=worker_db,
                item_id=item_id,
                quantity=5,
                idempotency_key="simultaneous-key-xyz",
                strategy="atomic_update",
            )
            return res.id
        finally:
            worker_db.close()

    # Execute 10 simultaneous threads with the same key
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_worker) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All threads must receive the exact same reservation ID
    assert len(set(results)) == 1

    # Verify only 1 reservation row in database
    verify_db = session_factory()
    count = verify_db.query(Reservation).filter(Reservation.idempotency_key == "simultaneous-key-xyz").count()
    assert count == 1

    final_item = verify_db.query(Item).filter(Item.id == item_id).first()
    assert final_item.available_quantity == 95
    verify_db.close()
