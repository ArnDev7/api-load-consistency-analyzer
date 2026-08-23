from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Item
from app.schemas import ItemCreate, ItemListResponse, ItemResponse

router = APIRouter(prefix="/items", tags=["Items"])


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)):
    """Create a new inventory item with initial available quantity."""
    item = Item(
        sku=item_in.sku,
        name=item_in.name,
        available_quantity=item_in.initial_quantity,
        initial_quantity=item_in.initial_quantity,
        version=1,
    )
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
        return item
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "DUPLICATE_SKU", "message": f"Item with SKU '{item_in.sku}' already exists."},
        )


@router.get("", response_model=ItemListResponse)
def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List inventory items."""
    total = db.query(Item).count()
    items = db.query(Item).order_by(Item.id).offset(skip).limit(limit).all()
    return ItemListResponse(items=items, total=total)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Retrieve an item by ID."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ITEM_NOT_FOUND", "message": f"Item with ID {item_id} not found."},
        )
    return item
