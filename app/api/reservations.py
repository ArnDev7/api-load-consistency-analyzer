from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Reservation
from app.schemas import (
    ReleaseResponse,
    ReservationRequest,
    ReservationResponse,
)
from app.services.reservation_service import (
    AlreadyReleasedError,
    DatabaseConflictError,
    DuplicateIdempotencyKeyError,
    InsufficientInventoryError,
    ItemNotFoundError,
    ReservationNotFoundError,
    release_reservation,
    reserve_item,
)

router = APIRouter(tags=["Reservations"])


@router.post(
    "/items/{item_id}/reserve",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation(
    item_id: int,
    req: ReservationRequest,
    db: Session = Depends(get_db),
):
    """Attempt to reserve inventory for a specific item using a chosen or default concurrency strategy."""
    try:
        reservation = reserve_item(
            db=db,
            item_id=item_id,
            quantity=req.quantity,
            idempotency_key=req.idempotency_key,
            strategy=req.strategy,
        )
        return reservation
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ITEM_NOT_FOUND", "message": str(e)},
        )
    except InsufficientInventoryError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "INSUFFICIENT_INVENTORY",
                "message": str(e),
                "item_id": e.item_id,
                "requested": e.requested,
                "available": e.available,
            },
        )
    except DuplicateIdempotencyKeyError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "IDEMPOTENCY_CONFLICT", "message": str(e)},
        )
    except DatabaseConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "TRANSACTION_CONFLICT", "message": str(e)},
        )


@router.post(
    "/reservations/{reservation_id}/release",
    response_model=ReleaseResponse,
    status_code=status.HTTP_200_OK,
)
def release_existing_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
):
    """Release an active reservation and restore available inventory to the item."""
    try:
        reservation, available_qty = release_reservation(db, reservation_id)
        return ReleaseResponse(
            id=reservation.id,
            item_id=reservation.item_id,
            quantity=reservation.quantity,
            status=reservation.status,
            released_at=reservation.released_at,
            available_quantity=available_qty,
        )
    except ReservationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "RESERVATION_NOT_FOUND", "message": str(e)},
        )
    except AlreadyReleasedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "ALREADY_RELEASED", "message": str(e)},
        )
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ITEM_NOT_FOUND", "message": str(e)},
        )


@router.get(
    "/reservations/{reservation_id}",
    response_model=ReservationResponse,
)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve reservation details by ID."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "RESERVATION_NOT_FOUND", "message": f"Reservation {reservation_id} not found."},
        )
    return reservation
