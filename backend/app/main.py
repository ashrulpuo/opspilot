"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.api.v1 import api_router

# Create FastAPI app
app = FastAPI(
    title="OpsPilot API",
    description="DevOps Automation Platform API",
    version="0.1.0",
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

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Identify this process as OpsPilot API (useful when port 8000 is shared/confused with other services)."""
    return {
        "service": "opspilot-api",
        "version": "0.1.0",
        "api_prefix": settings.API_V1_STR,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0", "service": "opspilot-api"}


@app.on_event("startup")
async def startup_event():
    """Startup tasks."""
    # Initialize database connections
    # Initialize Redis connection
    # Initialize Vault connection
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks."""
    # Close database connections
    # Close Redis connection
    pass
