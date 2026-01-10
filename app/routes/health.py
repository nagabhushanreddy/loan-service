"""Health check routes"""
from fastapi import APIRouter
from typing import Dict

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Readiness check"""
    return {
        "status": "healthy",
        "service": "loan-service",
        "version": "1.0.0"
    }


@router.get("/healthz")
async def liveness_check() -> Dict[str, str]:
    """Liveness check"""
    return {
        "status": "alive"
    }
