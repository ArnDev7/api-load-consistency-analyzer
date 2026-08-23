import pytest
from sqlalchemy.orm import Session
from app.database import get_session_factory
from app.models import Item, Reservation
from app.services.reservation_service import InsufficientInventoryError, reserve_item_pessimistic


def test_transaction_rollback_on_failure(db_session):
    """Verify failed reservation rolls back and leaves no partial committed state."""
    session_factory = get_session_factory()
    db = session_factory()

    item = Item(
        sku="SKU-ROLLBACK-TEST",
        name="Rollback Item",
        available_quantity=10,
        initial_quantity=10,
        version=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    item_id = item.id

    # Attempt reservation of 20 (exceeds 10)
    with pytest.raises(InsufficientInventoryError):
        reserve_item_pessimistic(
            db=db,
            item_id=item_id,
            quantity=20,
            idempotency_key="rollback-key-1",
        )

    # Verify inventory is untouched
    db.close()
    verify_db = session_factory()
    item_after = verify_db.query(Item).filter(Item.id == item_id).first()
    assert item_after.available_quantity == 10
    assert item_after.version == 1

    # Verify no reservation record persisted
    res_count = (
        verify_db.query(Reservation)
        .filter(Reservation.item_id == item_id)
        .count()
    )
    assert res_count == 0
    verify_db.close()
