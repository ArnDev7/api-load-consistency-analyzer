import concurrent.futures
import threading
import pytest
from app.database import get_session_factory
from app.models import Item, Reservation
from app.services.reservation_service import (
    InsufficientInventoryError,
    reserve_item_atomic,
    reserve_item_pessimistic,
)
from app.services.consistency_service import verify_database_consistency


@pytest.mark.parametrize("strategy", ["atomic_update", "pessimistic_lock"])
def test_high_concurrency_inventory_depletion(db_session, strategy: str):
    """Under intense concurrent contention, inventory must deplete to exactly 0 without overselling or negative inventory."""
    session_factory = get_session_factory()
    db = session_factory()

    initial_stock = 40
    item = Item(
        sku=f"SKU-CONCUR-{strategy}",
        name=f"Concurrency Item ({strategy})",
        available_quantity=initial_stock,
        initial_quantity=initial_stock,
        version=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    item_id = item.id
    db.close()

    total_threads = 80  # 80 requests for 40 units -> 40 should succeed, 40 should fail
    barrier = threading.Barrier(total_threads)

    def _worker(worker_id: int):
        barrier.wait()  # Synchronize simultaneous execution
        worker_db = session_factory()
        try:
            if strategy == "atomic_update":
                reserve_item_atomic(
                    db=worker_db,
                    item_id=item_id,
                    quantity=1,
                    idempotency_key=f"worker-{strategy}-{worker_id}",
                )
            else:
                reserve_item_pessimistic(
                    db=worker_db,
                    item_id=item_id,
                    quantity=1,
                    idempotency_key=f"worker-{strategy}-{worker_id}",
                )
            return True
        except InsufficientInventoryError:
            return False
        finally:
            worker_db.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=total_threads) as executor:
        futures = [executor.submit(_worker, i) for i in range(total_threads)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_count = sum(1 for r in results if r is True)
    failure_count = sum(1 for r in results if r is False)

    assert success_count == initial_stock
    assert failure_count == total_threads - initial_stock

    # Verify database state
    verify_db = session_factory()
    item_final = verify_db.query(Item).filter(Item.id == item_id).first()
    assert item_final.available_quantity == 0

    active_res_count = (
        verify_db.query(Reservation)
        .filter(Reservation.item_id == item_id)
        .count()
    )
    assert active_res_count == initial_stock

    # Verify consistency invariants
    report = verify_database_consistency(verify_db)
    assert report.consistent is True
    assert report.violations_count == 0
    verify_db.close()
