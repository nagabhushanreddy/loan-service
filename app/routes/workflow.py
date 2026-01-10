"""Workflow and decision routes"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Optional
from app.models.schemas import (
    CompleteTaskRequest,
    MakeDecisionRequest,
    FulfillConditionRequest,
    DisbursementPrepareRequest,
    DisbursementConfirmRequest,
    SuccessResponse
)
from app.models.enums import UserRole
from app.services.workflow_service import workflow_service
from app.services.application_service import application_service
from app.auth import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/api/v1/loan-applications", tags=["Workflow & Decisions"])


@router.post("/{application_id}/tasks/{task_id}/complete", response_model=SuccessResponse)
async def complete_task(
    application_id: str,
    task_id: str,
    request_data: CompleteTaskRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Complete workflow task"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        # Determine user role (simplified - should come from token or authz service)
        user_role = UserRole.LOAN_OFFICER if "officer" in user.roles else UserRole.CUSTOMER
        
        task = await workflow_service.complete_task(
            task_id,
            request_data.decision,
            request_data.comments,
            user.user_id,
            user_role,
            correlation_id
        )
        
        return SuccessResponse(
            success=True,
            data={"task": task},
            metadata={"correlation_id": correlation_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{application_id}/decision", response_model=SuccessResponse)
async def make_decision(
    application_id: str,
    request_data: MakeDecisionRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> SuccessResponse:
    """Make loan decision (approve/reject/conditional)"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Check idempotency
    if idempotency_key:
        from app.services.idempotency import idempotency_service
        existing = await idempotency_service.check_and_store(
            idempotency_key,
            user.tenant_id,
            request_data.dict()
        )
        if existing and existing.get("status") == "completed":
            return SuccessResponse(**existing["response"])
    
    try:
        # Determine user role
        user_role = UserRole.CHECKER if "checker" in user.roles else UserRole.ADMIN
        
        await workflow_service.make_decision(
            application_id,
            request_data,
            user.user_id,
            user_role,
            correlation_id
        )
        
        application = await application_service.get_application(application_id)
        
        response = SuccessResponse(
            success=True,
            data={"application": application},
            metadata={"correlation_id": correlation_id}
        )
        
        if idempotency_key:
            from app.services.idempotency import idempotency_service
            await idempotency_service.store_response(
                idempotency_key,
                user.tenant_id,
                response.dict()
            )
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{application_id}/conditions", response_model=SuccessResponse)
async def get_conditions(
    application_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Get conditions for application"""
    conditions = await workflow_service.get_conditions(application_id)
    
    return SuccessResponse(
        success=True,
        data={"conditions": conditions}
    )


@router.post("/{application_id}/conditions/fulfill", response_model=SuccessResponse)
async def fulfill_condition(
    application_id: str,
    request_data: FulfillConditionRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Fulfill loan condition"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        await workflow_service.fulfill_condition(
            request_data.condition_id,
            request_data.evidence_doc_ids,
            user.user_id,
            correlation_id
        )
        
        conditions = await workflow_service.get_conditions(application_id)
        
        return SuccessResponse(
            success=True,
            data={"conditions": conditions},
            metadata={"correlation_id": correlation_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{application_id}/disbursement/prepare", response_model=SuccessResponse)
async def prepare_disbursement(
    application_id: str,
    request_data: DisbursementPrepareRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Prepare application for disbursement"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        user_role = UserRole.DISBURSEMENT_OFFICER if "disbursement" in user.roles else UserRole.ADMIN
        
        await workflow_service.prepare_disbursement(
            application_id,
            request_data.final_amount,
            request_data.final_tenure,
            request_data.disbursement_method,
            request_data.account_details,
            user.user_id,
            user_role,
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


@router.post("/{application_id}/disbursement/confirm", response_model=SuccessResponse)
async def confirm_disbursement(
    application_id: str,
    request_data: DisbursementConfirmRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> SuccessResponse:
    """Confirm loan disbursement"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Check idempotency
    if idempotency_key:
        from app.services.idempotency import idempotency_service
        existing = await idempotency_service.check_and_store(
            idempotency_key,
            user.tenant_id,
            request_data.dict()
        )
        if existing and existing.get("status") == "completed":
            return SuccessResponse(**existing["response"])
    
    try:
        user_role = UserRole.DISBURSEMENT_OFFICER if "disbursement" in user.roles else UserRole.ADMIN
        
        await workflow_service.confirm_disbursement(
            application_id,
            request_data.disbursed_amount,
            request_data.disbursement_date,
            request_data.reference_number,
            user.user_id,
            user_role,
            correlation_id
        )
        
        application = await application_service.get_application(application_id)
        
        response = SuccessResponse(
            success=True,
            data={"application": application},
            metadata={"correlation_id": correlation_id}
        )
        
        if idempotency_key:
            from app.services.idempotency import idempotency_service
            await idempotency_service.store_response(
                idempotency_key,
                user.tenant_id,
                response.dict()
            )
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
