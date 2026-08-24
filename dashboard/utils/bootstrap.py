import sys
from pathlib import Path

# Resolve repository root from file location
ROOT = Path(__file__).resolve().parents[2]


def configure_project_path() -> Path:
    """Ensure repository root is present in sys.path."""
    root_str = str(ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return ROOT


# Run bootstrap on module import
configure_project_path()
