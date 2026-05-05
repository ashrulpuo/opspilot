"""Salt ingestion router package."""
from fastapi import APIRouter

from app.api.v1.salt import heartbeat as salt_heartbeat

router = APIRouter()
# ``metrics`` duplicated POST paths with ``heartbeat``; single router avoids collisions.
router.include_router(salt_heartbeat.router)

salt_router = router
