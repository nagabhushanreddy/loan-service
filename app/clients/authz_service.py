"""Authorization Service client"""
from typing import Dict, Any, List
from app.clients.base import BaseClient
from app.config import settings
from app.models.enums import UserRole


class AuthzServiceClient(BaseClient):
    """Client for Authorization Service integration"""
    
    def __init__(self):
        super().__init__(settings.authz_service_url)
    
    async def check_permission(
        self,
        user_id: str,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        correlation_id: str
    ) -> bool:
        """Check if user has permission for action"""
        data = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action
        }
        try:
            response = await self.post("/api/v1/authz/check", correlation_id, data)
            return response.get("allowed", False)
        except Exception as e:
            # Fail closed on authz service errors
            print(f"AuthZ service error: {e}")
            return False
    
    async def check_role(
        self,
        user_id: str,
        tenant_id: str,
        required_role: UserRole,
        correlation_id: str
    ) -> bool:
        """Check if user has required role"""
        data = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role": required_role.value
        }
        try:
            response = await self.post("/api/v1/authz/check-role", correlation_id, data)
            return response.get("has_role", False)
        except Exception as e:
            # Fail closed on authz service errors
            print(f"AuthZ service error: {e}")
            return False
    
    async def get_user_roles(
        self,
        user_id: str,
        tenant_id: str,
        correlation_id: str
    ) -> List[str]:
        """Get user roles"""
        try:
            params = {"user_id": user_id, "tenant_id": tenant_id}
            response = await self.get("/api/v1/authz/roles", correlation_id, params=params)
            return response.get("roles", [])
        except Exception as e:
            print(f"AuthZ service error: {e}")
            return []


authz_service_client = AuthzServiceClient()
