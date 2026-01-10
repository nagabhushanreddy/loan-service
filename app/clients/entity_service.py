"""Entity Service client"""
from typing import Dict, Any, Optional
from app.clients.base import BaseClient
from app.config import settings


class EntityServiceClient(BaseClient):
    """Client for Entity Service integration"""
    
    def __init__(self):
        super().__init__(settings.entity_service_url)
    
    async def get_entity(self, entity_id: str, correlation_id: str) -> Dict[str, Any]:
        """Get entity details"""
        return await self.get(f"/api/v1/entities/{entity_id}", correlation_id)
    
    async def get_applicant_profile(self, applicant_id: str, correlation_id: str) -> Dict[str, Any]:
        """Get applicant profile"""
        return await self.get(f"/api/v1/applicants/{applicant_id}", correlation_id)
    
    async def update_entity_metadata(
        self,
        entity_id: str,
        metadata: Dict[str, Any],
        correlation_id: str
    ) -> Dict[str, Any]:
        """Update entity metadata"""
        return await self.put(
            f"/api/v1/entities/{entity_id}/metadata",
            correlation_id,
            metadata
        )
    
    async def store_loan_metadata(
        self,
        application_id: str,
        metadata: Dict[str, Any],
        correlation_id: str
    ) -> Dict[str, Any]:
        """Store loan application metadata"""
        return await self.post(
            f"/api/v1/metadata/loan-applications/{application_id}",
            correlation_id,
            metadata
        )


entity_service_client = EntityServiceClient()
