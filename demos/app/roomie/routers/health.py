"""Health endpoint used by the load balancer. Does not require authentication."""

from fastapi import APIRouter

from roomie import __version__
from roomie.config import SERVICE_NAME

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"service": SERVICE_NAME, "version": __version__, "status": "ok"}
