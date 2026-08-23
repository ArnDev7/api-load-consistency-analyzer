from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Item, Reservation, ReservationStatus
from app.observability.logging import logger


class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        super().__init__(f"Item with ID {item_id} not found.")
        self.item_id = item_id


class InsufficientInventoryError(Exception):
    def __init__(self, item_id: int, requested: int, available: int):
        super().__init__(
            f"Insufficient inventory for item {item_id}: requested {requested}, available {available}."
        )
        self.item_id = item_id
        self.requested = requested
        self.available = available


class DuplicateIdempotencyKeyError(Exception):
    def __init__(self, idempotency_key: str):
        super().__init__(
            f"Duplicate idempotency key '{idempotency_key}' used with conflicting reservation parameters."
        )
        self.idempotency_key = idempotency_key


class ReservationNotFoundError(Exception):
    def __init__(self, reservation_id: int):
        super().__init__(f"Reservation with ID {reservation_id} not found.")
        self.reservation_id = reservation_id


class AlreadyReleasedError(Exception):
    def __init__(self, reservation_id: int):
        super().__init__(f"Reservation with ID {reservation_id} is already released.")
        self.reservation_id = reservation_id


class DatabaseConflictError(Exception):
    def __init__(self, message: str):
        super().__init__(f"Database transaction conflict: {message}")


def check_existing_idempotency(
    db: Session,
    idempotency_key: str,
    item_id: int,
    quantity: int,
) -> Optional[Reservation]:
    """Check if an idempotency key was previously processed.

    Returns the existing Reservation if the payload matches (idempotent replay).
    Raises DuplicateIdempotencyKeyError if payload does not match.
    Returns None if no previous record exists.
    """
    existing = (
        db.query(Reservation)
        .filter(Reservation.idempotency_key == idempotency_key)
        .first()
    )
    if existing:
        if existing.item_id == item_id and existing.quantity == quantity:
            logger.info(
                "Idempotent reservation request detected for key '%s'. Returning existing reservation #%d.",
                idempotency_key,
                existing.id,
            )
            return existing
        else:
            raise DuplicateIdempotencyKeyError(idempotency_key)
    return None


def reserve_item_atomic(
    db: Session,
    item_id: int,
    quantity: int,
    idempotency_key: str,
) -> Reservation:
    """Strategy 1: Atomic Conditional Update.

    Executes a single atomic UPDATE with conditional inventory check:
    UPDATE items SET available_quantity = available_quantity - :qty WHERE id = :id AND available_quantity >= :qty
    Verifies success via affected row count.
    """
    # 1. Check idempotency first
    existing = check_existing_idempotency(db, idempotency_key, item_id, quantity)
    if existing:
        return existing

    # 2. Perform conditional atomic update
    update_stmt = text(
        """
        UPDATE items
        SET available_quantity = available_quantity - :qty,
            version = version + 1,
            updated_at = NOW()
        WHERE id = :item_id AND available_quantity >= :qty
        RETURNING available_quantity, initial_quantity
        """
    )

    try:
        result = db.execute(update_stmt, {"qty": quantity, "item_id": item_id}).fetchone()
        if result is None:
            # Check if item exists to return accurate error code
            item = db.query(Item).filter(Item.id == item_id).first()
            if not item:
                db.rollback()
                raise ItemNotFoundError(item_id)
            db.rollback()
            raise InsufficientInventoryError(item_id, quantity, item.available_quantity)

        # 3. Insert reservation record
        reservation = Reservation(
            item_id=item_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
            status=ReservationStatus.ACTIVE,
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return reservation

    except IntegrityError as e:
        db.rollback()
        # Handle concurrent race on idempotency key
        existing = db.query(Reservation).filter(Reservation.idempotency_key == idempotency_key).first()
        if existing and existing.item_id == item_id and existing.quantity == quantity:
            return existing
        elif existing:
            raise DuplicateIdempotencyKeyError(idempotency_key)
        raise DatabaseConflictError(str(e))
    except Exception:
        db.rollback()
        raise


def reserve_item_pessimistic(
    db: Session,
    item_id: int,
    quantity: int,
    idempotency_key: str,
) -> Reservation:
    """Strategy 2: Pessimistic Row Locking.

    Acquires an exclusive row lock via SELECT ... FOR UPDATE within transaction.
    """
    # 1. Check idempotency
    existing = check_existing_idempotency(db, idempotency_key, item_id, quantity)
    if existing:
        return existing

    try:
        # 2. Lock item row
        item = (
            db.query(Item)
            .filter(Item.id == item_id)
            .with_for_update()
            .first()
        )
        if not item:
            db.rollback()
            raise ItemNotFoundError(item_id)

        if item.available_quantity < quantity:
            db.rollback()
            raise InsufficientInventoryError(item_id, quantity, item.available_quantity)

        # 3. Update inventory & create reservation
        item.available_quantity -= quantity
        item.version += 1

        reservation = Reservation(
            item_id=item_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
            status=ReservationStatus.ACTIVE,
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return reservation

    except IntegrityError as e:
        db.rollback()
        existing = db.query(Reservation).filter(Reservation.idempotency_key == idempotency_key).first()
        if existing and existing.item_id == item_id and existing.quantity == quantity:
            return existing
        elif existing:
            raise DuplicateIdempotencyKeyError(idempotency_key)
        raise DatabaseConflictError(str(e))
    except Exception:
        db.rollback()
        raise


def reserve_item_naive(
    db: Session,
    item_id: int,
    quantity: int,
    idempotency_key: str,
) -> Reservation:
    """Strategy 3 (UNSAFE / EXPERIMENT ONLY): Naive Read-Modify-Write.

    Performs a standard SELECT without row locking or conditional updates.
    Subject to lost-update race conditions under concurrent workloads.
    """
    existing = check_existing_idempotency(db, idempotency_key, item_id, quantity)
    if existing:
        return existing

    try:
        # Standard select without lock
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            db.rollback()
            raise ItemNotFoundError(item_id)

        if item.available_quantity < quantity:
            db.rollback()
            raise InsufficientInventoryError(item_id, quantity, item.available_quantity)

        # In-memory deduction and flush without locking or version check
        item.available_quantity = item.available_quantity - quantity
        item.version += 1

        reservation = Reservation(
            item_id=item_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
            status=ReservationStatus.ACTIVE,
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return reservation

    except IntegrityError as e:
        db.rollback()
        existing = db.query(Reservation).filter(Reservation.idempotency_key == idempotency_key).first()
        if existing and existing.item_id == item_id and existing.quantity == quantity:
            return existing
        elif existing:
            raise DuplicateIdempotencyKeyError(idempotency_key)
        raise DatabaseConflictError(str(e))
    except Exception:
        db.rollback()
        raise


def reserve_item(
    db: Session,
    item_id: int,
    quantity: int,
    idempotency_key: str,
    strategy: Optional[str] = None,
) -> Reservation:
    """Dispatcher for reservation strategies."""
    settings = get_settings()
    strat = strategy or settings.DEFAULT_CONCURRENCY_STRATEGY

    if strat == "atomic_update":
        return reserve_item_atomic(db, item_id, quantity, idempotency_key)
    elif strat == "pessimistic_lock":
        return reserve_item_pessimistic(db, item_id, quantity, idempotency_key)
    elif strat == "naive":
        return reserve_item_naive(db, item_id, quantity, idempotency_key)
    else:
        # Default fallback to atomic
        return reserve_item_atomic(db, item_id, quantity, idempotency_key)


def release_reservation(db: Session, reservation_id: int) -> Tuple[Reservation, int]:
    """Release an active reservation and restore inventory to the item."""
    try:
        reservation = (
            db.query(Reservation)
            .filter(Reservation.id == reservation_id)
            .with_for_update()
            .first()
        )
        if not reservation:
            db.rollback()
            raise ReservationNotFoundError(reservation_id)

        if reservation.status == ReservationStatus.RELEASED:
            db.rollback()
            raise AlreadyReleasedError(reservation_id)

        item = (
            db.query(Item)
            .filter(Item.id == reservation.item_id)
            .with_for_update()
            .first()
        )
        if not item:
            db.rollback()
            raise ItemNotFoundError(reservation.item_id)

        # Restore inventory
        item.available_quantity += reservation.quantity
        item.version += 1

        reservation.status = ReservationStatus.RELEASED
        reservation.released_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(reservation)
        db.refresh(item)
        return reservation, item.available_quantity

    except Exception:
        db.rollback()
        raise
