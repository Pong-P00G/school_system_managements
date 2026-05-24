import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

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
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    # Verify database connectivity at startup
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            # Ensure withdrawal_requests table exists
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS withdrawal_requests (
                    request_id SERIAL PRIMARY KEY,
                    enrollment_id INTEGER NOT NULL REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
                    student_id UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
                    reason TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    reviewed_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
                    reviewed_at TIMESTAMP,
                    reviewer_note TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            # Ensure announcements table exists
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS announcements (
                    announcement_id SERIAL PRIMARY KEY,
                    section_id INTEGER NOT NULL REFERENCES course_sections(section_id) ON DELETE CASCADE,
                    author_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            await session.commit()
        logger.info("Database connection verified at startup")
    except Exception as e:
        logger.error("Database connection failed at startup: %s", str(e))
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Global exception handler for database integrity errors
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning(
        "IntegrityError on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "A database constraint was violated. The record may already exist.",
            "error_type": "IntegrityError",
        },
    )


# Request logging middleware (register first so CORS wraps it as outermost)
@app.middleware("http")
async def log_requests(request: Request, call_next):
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
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
