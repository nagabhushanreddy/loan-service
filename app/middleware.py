"""Middleware components"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import uuid
from app.config import settings


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to all requests"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        
        # Log request
        print(f"Request: {request.method} {request.url.path} | Correlation-ID: {correlation_id}")
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        print(f"Response: {response.status_code} | Duration: {duration:.3f}s | Correlation-ID: {correlation_id}")
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, rate_limit: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.requests = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next: Callable):
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/healthz"]:
            return await call_next(request)
        
        client_id = request.client.host if request.client else "unknown"
        current_minute = int(time.time() / 60)
        key = f"{client_id}:{current_minute}"
        
        count = self.requests.get(key, 0)
        if count >= self.rate_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error_code": "RATE_LIMITED",
                    "message": "Too many requests. Please try again later.",
                }
            )
        
        self.requests[key] = count + 1
        
        # Clean up old entries (simple implementation)
        if len(self.requests) > 10000:
            old_keys = [k for k in self.requests if int(k.split(":")[1]) < current_minute - 5]
            for old_key in old_keys:
                del self.requests[old_key]
        
        return await call_next(request)
