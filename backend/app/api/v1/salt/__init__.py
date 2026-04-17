"""Salt ingestion router package."""
from fastapi import APIRouter

from app.api.v1.salt import heartbeat as salt_heartbeat
from app.api.v1.salt import metrics as salt_metrics

router = APIRouter()
router.include_router(salt_heartbeat.router)
router.include_router(salt_metrics.router)
