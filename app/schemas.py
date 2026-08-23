from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models import ReservationStatus


class ItemBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64, description="Unique SKU identifier")
    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    initial_quantity: int = Field(..., ge=0, description="Starting inventory quantity")


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int
    available_quantity: int
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemListResponse(BaseModel):
    items: List[ItemResponse]
    total: int


class ReservationRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity to reserve (must be > 0)")
    idempotency_key: str = Field(
        ..., min_length=1, max_length=128, description="Unique client-provided idempotency key"
    )
    strategy: Optional[Literal["atomic_update", "pessimistic_lock", "naive"]] = Field(
        default=None,
        description="Concurrency strategy to apply. If None, uses system default.",
    )


class ReservationResponse(BaseModel):
    id: int
    item_id: int
    quantity: int
    idempotency_key: str
    status: ReservationStatus
    created_at: datetime
    released_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReleaseResponse(BaseModel):
    id: int
    item_id: int
    quantity: int
    status: ReservationStatus
    released_at: datetime
    available_quantity: int

    model_config = ConfigDict(from_attributes=True)


class ItemConsistencyDetail(BaseModel):
    item_id: int
    sku: str
    initial_quantity: int
    available_quantity: int
    active_reserved_quantity: int
    released_reserved_quantity: int
    reconciled_quantity: int
    is_consistent: bool
    violations: List[str]


class ConsistencyReportResponse(BaseModel):
    consistent: bool
    total_items: int
    total_reservations: int
    active_reservations: int
    released_reservations: int
    violations_count: int
    violations: List[str]
    details: List[ItemConsistencyDetail]
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    database: Dict[str, Any]
    version: str


class SeedRequest(BaseModel):
    item_count: int = Field(default=10, ge=1, le=10000, description="Number of items to seed")
    initial_inventory_per_item: int = Field(
        default=100, ge=0, le=1000000, description="Starting inventory for each item"
    )


class ResetResponse(BaseModel):
    status: str
    message: str
    items_deleted: int
    reservations_deleted: int


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Any] = None
