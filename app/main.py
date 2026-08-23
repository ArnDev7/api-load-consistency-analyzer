from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import __version__
from app.api.health import router as health_router
from app.api.items import router as items_router
from app.api.metrics import router as metrics_router
from app.api.reservations import router as reservations_router
from app.api.testing import router as testing_router
from app.config import get_settings
from app.database import get_engine
from app.observability.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database connection is initialized
    logger.info("Initializing API Load & Consistency Analyzer application...")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            logger.info("Successfully connected to PostgreSQL engine at startup.")
    except Exception as exc:
        logger.warning("Could not connect to database on startup: %s", exc)
    yield
    # Shutdown: Dispose engine
    logger.info("Shutting down application, disposing connection pools...")
    engine = get_engine()
    engine.dispose()


settings = get_settings()

app = FastAPI(
    title="API Load & Consistency Analyzer",
    description=(
        "An educational backend engineering platform to evaluate API latency, "
        "throughput, failure modes, and PostgreSQL database consistency under concurrent workloads."
    ),
    version=__version__,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Structured validation error response avoiding raw stack traces."""
    logger.warning("Request validation failed for %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Invalid request payload or parameters.",
            "details": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure HTTP exceptions follow standardized structured format."""
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {
            "error_code": "HTTP_ERROR",
            "message": str(exc.detail),
        }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled internal errors without exposing internal traces."""
    logger.error("Unhandled internal server error on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred while processing the request.",
        },
    )


# Include Routers
app.include_router(health_router)
app.include_router(items_router)
app.include_router(reservations_router)
app.include_router(metrics_router)
app.include_router(testing_router)
