from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_session_factory
from app.models import Item, Reservation, ReservationStatus
from app.services.consistency_service import verify_database_consistency


def test_consistency_check_clean_state(client: TestClient, sample_item):
    """Test consistency check on fresh database returns consistent=True."""
    response = client.get("/metrics/consistency")
    assert response.status_code == 200
    data = response.json()
    assert data["consistent"] is True
    assert data["violations_count"] == 0
    assert data["total_items"] >= 1


def test_consistency_detects_reconciliation_anomaly(db_session: Session):
    """Corrupt available_quantity manually and ensure consistency check catches violation."""
    item = Item(
        sku="SKU-CORRUPT-1",
        name="Corrupted Item",
        available_quantity=80,  # Should be 100 with no reservations
        initial_quantity=100,
        version=1,
    )
    db_session.add(item)
    db_session.commit()

    report = verify_database_consistency(db_session)
    assert report.consistent is False
    assert report.violations_count >= 1
    assert any("Reconciliation failure" in v for v in report.violations)


def test_consistency_detects_negative_inventory(db_session: Session):
    """Ensure negative available quantity is detected if constraint is bypassed or corrupted."""
    # Temporarily drop constraint or use raw update
    db_session.execute(
        text("ALTER TABLE items DROP CONSTRAINT IF EXISTS chk_item_available_qty_non_negative;")
    )
    db_session.commit()

    item = Item(
        sku="SKU-NEGATIVE-1",
        name="Negative Item",
        available_quantity=-5,
        initial_quantity=50,
        version=1,
    )
    db_session.add(item)
    db_session.commit()

    report = verify_database_consistency(db_session)
    assert report.consistent is False
    assert any("negative available quantity" in v for v in report.violations)

    # Re-apply constraint
    db_session.execute(
        text("DELETE FROM items WHERE sku = 'SKU-NEGATIVE-1';")
    )
    db_session.execute(
        text("ALTER TABLE items ADD CONSTRAINT chk_item_available_qty_non_negative CHECK (available_quantity >= 0);")
    )
    db_session.commit()


def test_test_seed_and_reset_endpoints(client: TestClient):
    """Verify /test/seed and /test/reset endpoints."""
    seed_res = client.post("/test/seed", json={"item_count": 5, "initial_inventory_per_item": 50})
    assert seed_res.status_code == 200
    assert seed_res.json()["seeded_count"] == 5

    items_res = client.get("/items")
    assert items_res.json()["total"] == 5

    reset_res = client.post("/test/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["items_deleted"] == 5

    empty_res = client.get("/items")
    assert empty_res.json()["total"] == 0
