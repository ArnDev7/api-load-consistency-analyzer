import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Boolean,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class ReservationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sku = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    available_quantity = Column(Integer, nullable=False)
    initial_quantity = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    reservations = relationship("Reservation", back_populates="item", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("available_quantity >= 0", name="chk_item_available_qty_non_negative"),
        CheckConstraint("initial_quantity >= 0", name="chk_item_initial_qty_non_negative"),
        CheckConstraint("available_quantity <= initial_quantity", name="chk_item_available_lte_initial"),
        Index("idx_items_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, sku='{self.sku}', available={self.available_quantity}/{self.initial_quantity})>"


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    status = Column(
        SQLEnum(ReservationStatus, native_enum=False, length=20),
        nullable=False,
        default=ReservationStatus.ACTIVE,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    released_at = Column(DateTime(timezone=True), nullable=True)

    item = relationship("Item", back_populates="reservations")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_reservation_qty_positive"),
        Index("idx_reservations_idempotency_key", "idempotency_key", unique=True),
        Index("idx_reservations_item_status", "item_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Reservation(id={self.id}, item_id={self.item_id}, qty={self.quantity}, status='{self.status}')>"


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scenario = Column(String(64), nullable=False)
    strategy = Column(String(64), nullable=False)
    concurrency = Column(Integer, nullable=False)
    request_count = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    consistency_passed = Column(Boolean, nullable=True)

    def __repr__(self) -> str:
        return f"<ExperimentRun(id={self.id}, scenario='{self.scenario}', concurrency={self.concurrency})>"
