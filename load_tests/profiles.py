from typing import Dict, Any


WORKLOAD_PROFILES: Dict[str, Dict[str, Any]] = {
    "read_heavy": {
        "description": "80% reads, 15% reservations, 5% consistency checks",
        "weights": {
            "get_items": 40,
            "get_item_detail": 40,
            "reserve_item": 15,
            "check_consistency": 5,
            "release_reservation": 0,
        },
    },
    "write_heavy": {
        "description": "70% reservations, 20% releases, 10% reads",
        "weights": {
            "get_items": 5,
            "get_item_detail": 5,
            "reserve_item": 70,
            "check_consistency": 0,
            "release_reservation": 20,
        },
    },
    "mixed": {
        "description": "40% reads, 40% reservations, 15% releases, 5% consistency checks",
        "weights": {
            "get_items": 20,
            "get_item_detail": 20,
            "reserve_item": 40,
            "check_consistency": 5,
            "release_reservation": 15,
        },
    },
    "spike": {
        "description": "Burst workload with high concurrency reservation spikes",
        "weights": {
            "get_items": 15,
            "get_item_detail": 15,
            "reserve_item": 55,
            "check_consistency": 5,
            "release_reservation": 10,
        },
    },
}
