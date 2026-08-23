from fastapi import APIRouter, HTTPException, status
from app import __version__
from app.config import get_settings
from app.database import check_database_health
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Verify application health and database connection."""
    settings = get_settings()
    try:
        db_health = check_database_health()
        return HealthResponse(
            status="healthy" if db_health.get("healthy") else "degraded",
            environment=settings.ENVIRONMENT,
            database=db_health,
            version=__version__,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error_code": "DATABASE_UNAVAILABLE", "message": str(e)},
        )
