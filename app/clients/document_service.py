"""Document Service client"""
from typing import Dict, Any, List
from app.clients.base import BaseClient
from app.config import settings


class DocumentServiceClient(BaseClient):
    """Client for Document Service integration"""
    
    def __init__(self):
        super().__init__(settings.document_service_url)
    
    async def initiate_upload(
        self,
        entity_id: str,
        entity_type: str,
        document_type: str,
        file_name: str,
        file_size: int,
        content_type: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Initiate document upload"""
        data = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "document_type": document_type,
            "file_name": file_name,
            "file_size": file_size,
            "content_type": content_type
        }
        return await self.post("/api/v1/documents/initiate", correlation_id, data)
    
    async def list_documents(
        self,
        entity_id: str,
        entity_type: str,
        correlation_id: str
    ) -> List[Dict[str, Any]]:
        """List documents for entity"""
        params = {"entity_id": entity_id, "entity_type": entity_type}
        response = await self.get("/api/v1/documents", correlation_id, params=params)
        return response.get("documents", [])
    
    async def get_document(
        self,
        document_id: str,
        correlation_id: str,
        generate_presigned_url: bool = True
    ) -> Dict[str, Any]:
        """Get document details with optional presigned URL"""
        params = {"generate_presigned_url": generate_presigned_url}
        return await self.get(f"/api/v1/documents/{document_id}", correlation_id, params=params)
    
    async def delete_document(
        self,
        document_id: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Soft delete document"""
        return await self.delete(f"/api/v1/documents/{document_id}", correlation_id)
    
    async def verify_document(
        self,
        document_id: str,
        verification_status: str,
        verifier_id: str,
        notes: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Verify document"""
        data = {
            "status": verification_status,
            "verifier_id": verifier_id,
            "notes": notes
        }
        return await self.post(f"/api/v1/documents/{document_id}/verify", correlation_id, data)


document_service_client = DocumentServiceClient()
