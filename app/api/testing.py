from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dependencies import get_db
from app.models import Item, Reservation
from app.schemas import ResetResponse, SeedRequest

router = APIRouter(prefix="/test", tags=["Testing & Experiments"])


def verify_test_endpoint_enabled():
    settings = get_settings()
    if not settings.ENABLE_TEST_ENDPOINTS or settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "TEST_ENDPOINT_DISABLED", "message": "Test endpoints are disabled in production environment."},
        )


@router.post("/reset", response_model=ResetResponse, dependencies=[Depends(verify_test_endpoint_enabled)])
def reset_test_database(db: Session = Depends(get_db)):
    """Reset the database by truncating items and reservations for clean experiment runs."""
    try:
        reservations_count = db.query(Reservation).count()
        items_count = db.query(Item).count()

        # Disable FK checks temporarily or truncate with cascade
        db.execute(text("TRUNCATE TABLE reservations, items RESTART IDENTITY CASCADE"))
        db.commit()

        return ResetResponse(
            status="success",
            message="Database reset completed successfully.",
            items_deleted=items_count,
            reservations_deleted=reservations_count,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "RESET_FAILED", "message": str(e)},
        )


@router.post("/seed", dependencies=[Depends(verify_test_endpoint_enabled)])
def seed_test_database(req: SeedRequest = SeedRequest(), db: Session = Depends(get_db)):
    """Seed deterministic dataset for load and consistency experiments."""
    try:
        # Clear existing
        db.execute(text("TRUNCATE TABLE reservations, items RESTART IDENTITY CASCADE"))
        db.commit()

        seeded_items = []
        for i in range(1, req.item_count + 1):
            item = Item(
                sku=f"SKU-ITEM-{i:04d}",
                name=f"Standard Benchmark Item #{i}",
                available_quantity=req.initial_inventory_per_item,
                initial_quantity=req.initial_inventory_per_item,
                version=1,
            )
            db.add(item)
            seeded_items.append(item)

        db.commit()
        return {
            "status": "success",
            "message": f"Successfully seeded {len(seeded_items)} items with {req.initial_inventory_per_item} initial units each.",
            "seeded_count": len(seeded_items),
            "initial_inventory_per_item": req.initial_inventory_per_item,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "SEED_FAILED", "message": str(e)},
        )
