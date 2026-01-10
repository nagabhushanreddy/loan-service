"""Loan application routes"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Optional, List
from app.models.schemas import (
    CreateLoanApplicationRequest,
    UpdateLoanApplicationRequest,
    LoanApplicationResponse,
    SuccessResponse,
    PaginationParams,
    AssignApplicationRequest,
    EscalateApplicationRequest,
    AuditEntry
)
from app.models.enums import LoanStatus, UserRole
from app.services.application_service import application_service
from app.services.idempotency import idempotency_service
from app.auth import get_current_user, AuthenticatedUser, require_role

router = APIRouter(prefix="/api/v1/loan-applications", tags=["Loan Applications"])


@router.post("", response_model=SuccessResponse)
async def create_loan_application(
    request_data: CreateLoanApplicationRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> SuccessResponse:
    """Create new loan application"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Check idempotency
    if idempotency_key:
        existing = await idempotency_service.check_and_store(
            idempotency_key,
            user.tenant_id,
            request_data.dict()
        )
        if existing and existing.get("status") == "completed":
            return SuccessResponse(**existing["response"])
    
    try:
        application = await application_service.create_application(
            request_data,
            user.user_id,
            user.tenant_id,
            correlation_id
        )
        
        response = SuccessResponse(
            success=True,
            data={"application": application},
            metadata={"correlation_id": correlation_id}
        )
        
        # Store response for idempotency
        if idempotency_key:
            await idempotency_service.store_response(
                idempotency_key,
                user.tenant_id,
                response.dict()
            )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=SuccessResponse)
async def list_loan_applications(
    status: Optional[LoanStatus] = None,
    product_id: Optional[str] = None,
    applicant_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """List loan applications with filters"""
    applications, total = await application_service.list_applications(
        user.tenant_id,
        status,
        product_id,
        applicant_id,
        page,
        page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return SuccessResponse(
        success=True,
        data={
            "applications": applications,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
    )


@router.get("/{application_id}", response_model=SuccessResponse)
async def get_loan_application(
    application_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Get loan application details"""
    application = await application_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check tenant access
    if application.tenant_id != user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return SuccessResponse(
        success=True,
        data={"application": application}
    )


@router.patch("/{application_id}", response_model=SuccessResponse)
async def update_loan_application(
    application_id: str,
    request_data: UpdateLoanApplicationRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Update loan application"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        application = await application_service.update_application(
            application_id,
            request_data,
            user.user_id,
            correlation_id
        )
        
        return SuccessResponse(
            success=True,
            data={"application": application},
            metadata={"correlation_id": correlation_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{application_id}/submit", response_model=SuccessResponse)
async def submit_loan_application(
    application_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Submit loan application for review"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        application = await application_service.submit_application(
            application_id,
            user.user_id,
            correlation_id
        )
        
        return SuccessResponse(
            success=True,
            data={"application": application},
            metadata={"correlation_id": correlation_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{application_id}/assign", response_model=SuccessResponse)
async def assign_loan_application(
    application_id: str,
    request_data: AssignApplicationRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Assign loan application to officer"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        await application_service.assign_application(
            application_id,
            request_data.assignee_id,
            user.user_id,
            request_data.role,
            request_data.reason,
            correlation_id
        )
        
        application = await application_service.get_application(application_id)
        
        return SuccessResponse(
            success=True,
            data={"application": application},
            metadata={"correlation_id": correlation_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{application_id}/audit", response_model=SuccessResponse)
async def get_application_audit_trail(
    application_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Get application audit trail"""
    application = await application_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.tenant_id != user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    audit_trail = await application_service.get_audit_trail(application_id)
    
    return SuccessResponse(
        success=True,
        data={"audit_trail": audit_trail}
    )
