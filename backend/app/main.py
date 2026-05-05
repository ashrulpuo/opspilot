"""FastAPI application entry point."""
import logging
import sys
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import select, update
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings


def _configure_logging() -> None:
    """Configure stdlib logging from settings (call before other app imports log)."""
    level = logging.DEBUG if settings.DEBUG else getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"),
        )
        root.addHandler(handler)
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(name).setLevel(level)


_configure_logging()

from app.core.database import AsyncSessionLocal
from app.core.exceptions import register_exception_handlers
from app.models.server import Server
from app.api.v1 import api_router
from app.api.v1.monitors import start_monitor_checker
from app.api.v1.stream import stream_router
from app.api.v1.salt import salt_router

# Create FastAPI app
app = FastAPI(
    title="OpsPilot API",
    description="DevOps Automation Platform API",
    version="0.1.0",
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Register exception handlers
register_exception_handlers(app)

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(stream_router, prefix=settings.API_V1_STR)
app.include_router(salt_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Identify this process as OpsPilot API (useful when port 8000 is shared/confused with other services)."""
    return {
        "service": "opspilot-api",
        "version": "0.1.0",
        "api_prefix": settings.API_V1_STR,
        "docs": "/docs",
        "health": "/health",
        "routers": ["api/v1", "stream", "salt"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0", "service": "opspilot-api"}


_INTERRUPTED_INSTALL_MSG = (
    "Install was interrupted when the API process restarted "
    "(common with uvicorn --reload during code saves). Use Reinstall again."
)


@app.on_event("startup")
async def startup_event():
    """Recover servers left in ``installing_agent`` when the previous worker died (reload / deploy / crash).

    FastAPI ``BackgroundTasks`` run in-process; they do not survive uvicorn ``--reload`` or SIGTERM,
    so the SSH install never finishes and status would stay ``installing_agent`` forever otherwise.
    """
    log = logging.getLogger(__name__)
    try:
        async with AsyncSessionLocal() as db:
            r = await db.execute(select(Server.id).where(Server.status == "installing_agent"))
            stuck_ids = [row[0] for row in r.all()]
            if stuck_ids:
                await db.execute(
                    update(Server)
                    .where(Server.status == "installing_agent")
                    .values(
                        status="error",
                        agent_install_last_error=_INTERRUPTED_INSTALL_MSG[:8000],
                        updated_at=datetime.utcnow(),
                    ),
                )
                await db.commit()
                log.warning(
                    "Recovered %s server(s) stuck in installing_agent after API restart: %s",
                    len(stuck_ids),
                    stuck_ids,
                )
    except Exception:
        log.exception("Could not recover installing_agent rows on startup")

    start_monitor_checker()
    log.info("Monitor background checker started")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks."""
    # Close database connections
    # Close Redis connection
    pass
