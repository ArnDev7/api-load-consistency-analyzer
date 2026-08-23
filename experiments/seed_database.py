import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Optional
from sqlalchemy import text
from app.database import get_session_factory

from app.models import Item, Reservation
from app.observability.logging import logger


def seed_database(
    item_count: int = 20,
    initial_inventory_per_item: int = 200,
    database_url: Optional[str] = None,
) -> int:
    """Reset and seed the PostgreSQL database with deterministic items."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        logger.info(
            "Seeding database with %d items, %d units each...",
            item_count,
            initial_inventory_per_item,
        )
        db.execute(text("TRUNCATE TABLE reservations, items RESTART IDENTITY CASCADE"))
        db.commit()

        items = []
        for i in range(1, item_count + 1):
            item = Item(
                sku=f"SKU-BENCH-{i:04d}",
                name=f"Standard Benchmark Item #{i}",
                available_quantity=initial_inventory_per_item,
                initial_quantity=initial_inventory_per_item,
                version=1,
            )
            items.append(item)

        db.add_all(items)
        db.commit()
        logger.info("Successfully seeded %d items.", len(items))
        return len(items)
    except Exception as e:
        db.rollback()
        logger.error("Database seeding failed: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed database for load experiments")
    parser.add_argument("--items", type=int, default=20, help="Number of items to seed")
    parser.add_argument("--inventory", type=int, default=200, help="Initial inventory per item")
    args = parser.parse_args()

    seed_database(item_count=args.items, initial_inventory_per_item=args.inventory)
