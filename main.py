"""Main FastAPI application"""
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.middleware import (
    CorrelationIdMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware
)
from app.routes import health, products, eligibility, applications, workflow, documents
from app.services.idempotency import idempotency_service
from utils import logger




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Initialize utils-service configuration and logging
    logger.info("Starting Loan Service...")
    logger.info(f"Service: {settings.app_name}")
    logger.info(f"Environment: {settings.environment}")
    await idempotency_service.connect()
    yield
    # Shutdown
    logger.info("Shutting down Loan Service...")
    await idempotency_service.disconnect()


# Create FastAPI app
app = FastAPI(
    title="Loan Service API",
    description="Multi-Finance Loan Service for loan products, applications, and workflows",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, rate_limit=settings.rate_limit_per_minute)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error_code": "INVALID_REQUEST",
            "message": "Validation error",
            "details": errors,
            "metadata": {
                "correlation_id": getattr(request.state, "correlation_id", "unknown")
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "metadata": {
                "correlation_id": getattr(request.state, "correlation_id", "unknown")
            }
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(products.router)
app.include_router(eligibility.router)
app.include_router(applications.router)
app.include_router(workflow.router)
app.include_router(documents.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "loan-service",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True if settings.environment == "development" else False
    )
