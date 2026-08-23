"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-23 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Items table
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("available_quantity", sa.Integer(), nullable=False),
        sa.Column("initial_quantity", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("available_quantity >= 0", name="chk_item_available_qty_non_negative"),
        sa.CheckConstraint("initial_quantity >= 0", name="chk_item_initial_qty_non_negative"),
        sa.CheckConstraint("available_quantity <= initial_quantity", name="chk_item_available_lte_initial"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_items_id", "items", ["id"], unique=False)
    op.create_index("ix_items_sku", "items", ["sku"], unique=True)
    op.create_index("idx_items_sku", "items", ["sku"], unique=False)

    # Reservations table
    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("quantity > 0", name="chk_reservation_qty_positive"),
        sa.CheckConstraint("status IN ('ACTIVE', 'RELEASED')", name="chk_reservation_status_valid"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reservations_id", "reservations", ["id"], unique=False)
    op.create_index("ix_reservations_item_id", "reservations", ["item_id"], unique=False)
    op.create_index("ix_reservations_idempotency_key", "reservations", ["idempotency_key"], unique=True)
    op.create_index("idx_reservations_idempotency_key", "reservations", ["idempotency_key"], unique=True)
    op.create_index("idx_reservations_item_status", "reservations", ["item_id", "status"], unique=False)

    # ExperimentRuns table
    op.create_table(
        "experiment_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scenario", sa.String(length=64), nullable=False),
        sa.Column("strategy", sa.String(length=64), nullable=False),
        sa.Column("concurrency", sa.Integer(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consistency_passed", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_experiment_runs_id", "experiment_runs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("experiment_runs")
    op.drop_table("reservations")
    op.drop_table("items")
