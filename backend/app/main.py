"""FastAPI application entry point."""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import async_session
from app.api.v1.router import api_router

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with DB readiness check."""
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    # Verify database connectivity at startup
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database connection verified at startup")
    except Exception as e:
        logger.error("Database connection failed at startup: %s", str(e))
        # Don't crash - allow app to start so health checks can report status
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Request logging middleware (register first so CORS wraps it as outermost)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request with duration, status, and capture exceptions."""
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "[%s] %s %s → %s (%sms)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "[%s] %s %s → 500 (%sms) - %s: %s",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
            type(exc).__name__,
            str(exc),
        )
        # Return JSONResponse — response then passes through CORS middleware
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": request_id,
                "error_type": type(exc).__name__,
            },
        )


# CORS middleware (register last so it's outermost — wraps logging middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics middleware (optional)
if settings.PROMETHEUS_ENABLED:
    try:
        from prometheus_client import make_asgi_app

        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        logger.info("Prometheus metrics enabled at /metrics")
    except ImportError:
        logger.warning("prometheus_client not installed, metrics disabled")

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint redirecting to docs."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
