"""Eligibility check routes"""
from fastapi import APIRouter, Depends, Request
from app.models.schemas import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    SuccessResponse
)
from app.services.eligibility_service import eligibility_service
from app.auth import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/api/v1/eligibility", tags=["Eligibility"])


@router.post("/check", response_model=SuccessResponse)
async def check_eligibility(
    request_data: EligibilityCheckRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Check loan eligibility for applicant"""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    result = await eligibility_service.check_eligibility(request_data)
    
    return SuccessResponse(
        success=True,
        data={"eligibility": result},
        metadata={
            "correlation_id": correlation_id
        }
    )
