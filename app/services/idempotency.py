"""Idempotency service using Redis"""
import json
import hashlib
from typing import Optional, Any
import redis.asyncio as redis
from app.config import settings


class IdempotencyService:
    """Service for handling idempotent operations"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.ttl = settings.idempotency_ttl_seconds
    
    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True
            )
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_key(self, idempotency_key: str, tenant_id: str) -> str:
        """Generate Redis key for idempotency"""
        return f"idempotency:{tenant_id}:{idempotency_key}"
    
    async def check_and_store(
        self,
        idempotency_key: str,
        tenant_id: str,
        request_data: dict
    ) -> Optional[Any]:
        """
        Check if request was already processed.
        Returns stored response if duplicate, None if new request.
        """
        if not self.redis_client:
            await self.connect()
        
        key = self._generate_key(idempotency_key, tenant_id)
        
        # Check if key exists
        existing = await self.redis_client.get(key)
        if existing:
            return json.loads(existing)
        
        # Store placeholder to prevent concurrent duplicates
        request_hash = hashlib.sha256(
            json.dumps(request_data, sort_keys=True).encode()
        ).hexdigest()
        
        placeholder = {
            "status": "processing",
            "request_hash": request_hash
        }
        await self.redis_client.setex(
            key,
            self.ttl,
            json.dumps(placeholder)
        )
        
        return None
    
    async def store_response(
        self,
        idempotency_key: str,
        tenant_id: str,
        response_data: Any
    ):
        """Store response for idempotency key"""
        if not self.redis_client:
            await self.connect()
        
        key = self._generate_key(idempotency_key, tenant_id)
        
        response = {
            "status": "completed",
            "response": response_data
        }
        await self.redis_client.setex(
            key,
            self.ttl,
            json.dumps(response)
        )
    
    async def delete_key(self, idempotency_key: str, tenant_id: str):
        """Delete idempotency key (for rollback scenarios)"""
        if not self.redis_client:
            await self.connect()
        
        key = self._generate_key(idempotency_key, tenant_id)
        await self.redis_client.delete(key)


idempotency_service = IdempotencyService()
