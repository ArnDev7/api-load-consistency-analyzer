import os
import random
import uuid
from typing import Optional


def generate_idempotency_key(prefix: str = "req") -> str:
    """Generate a unique idempotency key for load test requests."""
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def get_random_item_id(item_count: Optional[int] = None) -> int:
    """Get a random item ID within the seeded range."""
    count = item_count or int(os.getenv("LOADTEST_ITEM_COUNT", "10"))
    return random.randint(1, max(1, count))


def get_random_quantity(max_qty: int = 5) -> int:
    """Get random reservation quantity."""
    return random.randint(1, max(1, max_qty))


def get_configured_strategy() -> Optional[str]:
    """Retrieve strategy configured for the load test."""
    strat = os.getenv("LOADTEST_STRATEGY")
    if strat in ["atomic_update", "pessimistic_lock", "naive"]:
        return strat
    return None
