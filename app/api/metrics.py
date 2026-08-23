from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import ConsistencyReportResponse
from app.services.consistency_service import verify_database_consistency

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/consistency", response_model=ConsistencyReportResponse)
def get_consistency_metrics(db: Session = Depends(get_db)):
    """Run an automated consistency check across all items and reservations."""
    return verify_database_consistency(db)
