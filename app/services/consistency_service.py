from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import Item, Reservation, ReservationStatus
from app.schemas import ConsistencyReportResponse, ItemConsistencyDetail


def verify_database_consistency(db: Session) -> ConsistencyReportResponse:
    """Audit the entire database against all domain and transactional consistency invariants.

    Uses a single MVCC consistent SQL snapshot query across items and reservations
    to prevent cross-query read skew under concurrent workloads.
    """
    violations: List[str] = []
    item_details: List[ItemConsistencyDetail] = []

    # 1. Check for duplicate idempotency keys in reservations
    duplicate_keys = (
        db.query(Reservation.idempotency_key, func.count(Reservation.id))
        .group_by(Reservation.idempotency_key)
        .having(func.count(Reservation.id) > 1)
        .all()
    )
    for key, count in duplicate_keys:
        violations.append(
            f"Duplicate idempotency key '{key}' found with {count} records."
        )

    # 2. Check for orphaned reservations
    orphaned_reservations = (
        db.query(Reservation.id)
        .outerjoin(Item, Reservation.item_id == Item.id)
        .filter(Item.id.is_(None))
        .all()
    )
    if orphaned_reservations:
        violations.append(
            f"Found {len(orphaned_reservations)} reservations referencing non-existent items."
        )

    # 3. Single-query snapshot audit for all items and their aggregated reservations
    snapshot_sql = text(
        """
        SELECT 
            i.id AS item_id,
            i.sku,
            i.initial_quantity,
            i.available_quantity,
            COALESCE(SUM(CASE WHEN r.status = 'ACTIVE' THEN r.quantity ELSE 0 END), 0)::INTEGER AS active_qty,
            COALESCE(SUM(CASE WHEN r.status = 'RELEASED' THEN r.quantity ELSE 0 END), 0)::INTEGER AS released_qty
        FROM items i
        LEFT JOIN reservations r ON r.item_id = i.id
        GROUP BY i.id, i.sku, i.initial_quantity, i.available_quantity
        ORDER BY i.id;
        """
    )
    results = db.execute(snapshot_sql).fetchall()

    total_items = len(results)
    total_active_reservations = 0
    total_released_reservations = 0

    for row in results:
        item_id = row.item_id
        sku = row.sku
        initial_qty = row.initial_quantity
        avail_qty = row.available_quantity
        active_qty = row.active_qty
        released_qty = row.released_qty

        total_active_reservations += active_qty
        total_released_reservations += released_qty

        item_violations: List[str] = []
        expected_available = initial_qty - active_qty

        # Invariant 1: Non-negative available quantity
        if avail_qty < 0:
            msg = f"Item {item_id} ({sku}) has negative available quantity: {avail_qty}."
            item_violations.append(msg)
            violations.append(msg)

        # Invariant 2: Available quantity does not exceed initial quantity
        if avail_qty > initial_qty:
            msg = (
                f"Item {item_id} ({sku}) available quantity ({avail_qty}) "
                f"exceeds initial quantity ({initial_qty})."
            )
            item_violations.append(msg)
            violations.append(msg)

        # Invariant 3: Reconciliation equation: initial - active_reserved == available
        if avail_qty != expected_available:
            msg = (
                f"Reconciliation failure for Item {item_id} ({sku}): "
                f"initial ({initial_qty}) - active_reserved ({active_qty}) = {expected_available}, "
                f"but available_quantity is {avail_qty} (discrepancy: {avail_qty - expected_available})."
            )
            item_violations.append(msg)
            violations.append(msg)

        item_details.append(
            ItemConsistencyDetail(
                item_id=item_id,
                sku=sku,
                initial_quantity=initial_qty,
                available_quantity=avail_qty,
                active_reserved_quantity=active_qty,
                released_reserved_quantity=released_qty,
                reconciled_quantity=expected_available,
                is_consistent=len(item_violations) == 0,
                violations=item_violations,
            )
        )

    total_reservations = db.query(Reservation).count()
    active_count = db.query(Reservation).filter(Reservation.status == ReservationStatus.ACTIVE).count()
    released_count = db.query(Reservation).filter(Reservation.status == ReservationStatus.RELEASED).count()
    is_consistent = len(violations) == 0

    return ConsistencyReportResponse(
        consistent=is_consistent,
        total_items=total_items,
        total_reservations=total_reservations,
        active_reservations=active_count,
        released_reservations=released_count,
        violations_count=len(violations),
        violations=violations,
        details=item_details,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

