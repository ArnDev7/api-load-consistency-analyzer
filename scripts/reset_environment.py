import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database import get_session_factory
from app.observability.logging import logger



def reset_environment():
    """Run database migrations and clean all tables."""
    logger.info("Running alembic migrations to head...")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)

    logger.info("Truncating database tables...")
    session_factory = get_session_factory()
    db = session_factory()
    try:
        db.execute(text("TRUNCATE TABLE reservations, items, experiment_runs RESTART IDENTITY CASCADE"))
        db.commit()
        logger.info("Database reset completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error("Database reset failed: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_environment()
