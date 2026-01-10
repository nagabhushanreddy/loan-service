"""Loan product routes"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.schemas import LoanProductResponse, SuccessResponse
from app.services.product_service import product_service
from app.auth import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/api/v1/loan-products", tags=["Loan Products"])


@router.get("", response_model=SuccessResponse)
async def list_loan_products(
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """List all available loan products"""
    products = product_service.get_all_products()
    return SuccessResponse(
        success=True,
        data={"products": products}
    )


@router.get("/{product_id}", response_model=SuccessResponse)
async def get_loan_product(
    product_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
) -> SuccessResponse:
    """Get specific loan product details"""
    product = product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return SuccessResponse(
        success=True,
        data={"product": product}
    )
