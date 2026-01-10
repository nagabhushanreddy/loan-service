"""Document routes"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from app.models.schemas import (
    InitiateDocumentUploadRequest,
    DocumentMetadata,
    SuccessResponse
)
from app.services.application_service import application_service
from app.clients.document_service import document_service_client
from app.auth import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/api/v1/loan-applications", tags=["Documents"])


@router.post("/{application_id}/documents", response_model=SuccessResponse)
async def initiate_document_upload(
    application_id: str,
    request_data: InitiateDocumentUploadRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Initiate document upload"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Check application exists
    application = await application_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.tenant_id != user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Delegate to document service
        result = await document_service_client.initiate_upload(
            entity_id=application_id,
            entity_type="loan_application",
            document_type=request_data.document_type,
            file_name=request_data.file_name,
            file_size=request_data.file_size,
            content_type=request_data.content_type,
            correlation_id=correlation_id
        )
        
        return SuccessResponse(
            success=True,
            data=result,
            metadata={"correlation_id": correlation_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document service error: {str(e)}")


@router.get("/{application_id}/documents", response_model=SuccessResponse)
async def list_documents(
    application_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """List documents for application"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Check application exists
    application = await application_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.tenant_id != user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        documents = await document_service_client.list_documents(
            entity_id=application_id,
            entity_type="loan_application",
            correlation_id=correlation_id
        )
        
        return SuccessResponse(
            success=True,
            data={"documents": documents},
            metadata={"correlation_id": correlation_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document service error: {str(e)}")


@router.delete("/{application_id}/documents/{document_id}", response_model=SuccessResponse)
async def delete_document(
    application_id: str,
    document_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Delete document"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Check application exists
    application = await application_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.tenant_id != user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await document_service_client.delete_document(
            document_id=document_id,
            correlation_id=correlation_id
        )
        
        return SuccessResponse(
            success=True,
            data=result,
            metadata={"correlation_id": correlation_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document service error: {str(e)}")
