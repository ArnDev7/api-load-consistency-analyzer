import time
from typing import Any, Dict, Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.config import get_settings

Base = declarative_base()

_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def get_engine(
    database_url: Optional[str] = None,
    pool_size: Optional[int] = None,
    max_overflow: Optional[int] = None,
    pool_timeout: Optional[float] = None,
    pool_recycle: Optional[int] = None,
    echo: Optional[bool] = None,
) -> Engine:
    global _engine
    settings = get_settings()

    url = database_url or settings.DATABASE_URL
    p_size = pool_size if pool_size is not None else settings.DB_POOL_SIZE
    m_overflow = max_overflow if max_overflow is not None else settings.DB_MAX_OVERFLOW
    p_timeout = pool_timeout if pool_timeout is not None else settings.DB_POOL_TIMEOUT
    p_recycle = pool_recycle if pool_recycle is not None else settings.DB_POOL_RECYCLE
    e = echo if echo is not None else settings.DB_ECHO

    # Recreate engine if parameters change or engine not initialized
    if _engine is None:
        _engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=p_size,
            max_overflow=m_overflow,
            pool_timeout=p_timeout,
            pool_recycle=p_recycle,
            pool_pre_ping=True,
            echo=e,
        )
    return _engine


def reset_engine(
    database_url: Optional[str] = None,
    pool_size: Optional[int] = None,
    max_overflow: Optional[int] = None,
    pool_timeout: Optional[float] = None,
    pool_recycle: Optional[int] = None,
) -> Engine:
    """Explicitly dispose existing engine and recreate with new parameters."""
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionFactory = None
    return get_engine(
        database_url=database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
    )


def get_session_factory() -> sessionmaker:
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionFactory


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and safely handles commit/rollback/close."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_health() -> Dict[str, Any]:
    """Verify database connectivity, measure query round-trip latency, and report pool metrics."""
    engine = get_engine()
    start_time = time.perf_counter()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    pool = engine.pool
    pool_status = {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }

    return {
        "healthy": result == 1,
        "latency_ms": round(latency_ms, 3),
        "pool": pool_status,
    }
