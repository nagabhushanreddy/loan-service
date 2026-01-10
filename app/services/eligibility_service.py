"""Eligibility service for loan eligibility checks"""
from typing import List
from app.models.schemas import ApplicantProfile, EligibilityCheckRequest, EligibilityCheckResponse
from app.models.enums import EligibilityStatus, KYCStatus
from app.services.product_service import product_service
from app.config import config_data


class EligibilityService:
    """Service for eligibility checks"""
    
    def __init__(self):
        self.eligibility_rules = config_data.get("eligibility", {})
    
    async def check_eligibility(self, request: EligibilityCheckRequest) -> EligibilityCheckResponse:
        """Check loan eligibility for applicant"""
        reasons = []
        eligible = True
        max_eligible_amount = request.requested_amount
        
        # Check KYC status
        if request.applicant.kyc_status != KYCStatus.VERIFIED:
            reasons.append("KYC verification required")
            eligible = False
        
        # Check product validity
        product = product_service.get_product(request.product_id)
        if not product:
            reasons.append("Invalid loan product")
            return EligibilityCheckResponse(
                status=EligibilityStatus.NOT_ELIGIBLE,
                eligible=False,
                reasons=reasons
            )
        
        # Check product parameters
        valid, errors = product_service.validate_product_params(
            request.product_id,
            request.requested_amount,
            request.requested_tenure
        )
        if not valid:
            reasons.extend(errors)
            eligible = False
        
        # Check minimum income
        min_income = self.eligibility_rules.get("min_monthly_income", 15000)
        if request.applicant.monthly_income < min_income:
            reasons.append(f"Minimum monthly income of {min_income} required")
            eligible = False
        
        # Check credit score
        min_credit_score = self.eligibility_rules.get("min_credit_score", 650)
        if request.applicant.credit_score and request.applicant.credit_score < min_credit_score:
            reasons.append(f"Minimum credit score of {min_credit_score} required")
            eligible = False
        
        # Check debt-to-income ratio
        max_dti = self.eligibility_rules.get("max_debt_to_income_ratio", 0.5)
        total_obligations = request.applicant.monthly_obligations
        estimated_emi = self._calculate_emi(
            request.requested_amount,
            request.requested_tenure,
            product.interest_rate_max
        )
        
        new_dti = (total_obligations + estimated_emi) / request.applicant.monthly_income
        if new_dti > max_dti:
            reasons.append(f"Debt-to-income ratio ({new_dti:.2%}) exceeds maximum ({max_dti:.2%})")
            # Calculate max eligible amount based on DTI
            max_emi = (request.applicant.monthly_income * max_dti) - total_obligations
            if max_emi > 0:
                max_eligible_amount = self._calculate_principal(
                    max_emi,
                    request.requested_tenure,
                    product.interest_rate_max
                )
                if max_eligible_amount < product.min_amount:
                    eligible = False
            else:
                eligible = False
        
        # Determine status
        if not eligible:
            status = EligibilityStatus.NOT_ELIGIBLE
        elif len(reasons) > 0:
            status = EligibilityStatus.CONDITIONAL
        else:
            status = EligibilityStatus.ELIGIBLE
        
        recommendations = []
        if not eligible and max_eligible_amount < request.requested_amount:
            if max_eligible_amount >= product.min_amount:
                recommendations.append(f"Consider applying for amount up to {max_eligible_amount:.2f}")
        
        return EligibilityCheckResponse(
            status=status,
            eligible=eligible,
            max_eligible_amount=max_eligible_amount if eligible else None,
            reasons=reasons,
            recommendations=recommendations
        )
    
    def _calculate_emi(self, principal: float, tenure_months: int, annual_rate: float) -> float:
        """Calculate EMI"""
        monthly_rate = annual_rate / (12 * 100)
        if monthly_rate == 0:
            return principal / tenure_months
        
        emi = principal * monthly_rate * (
            (1 + monthly_rate) ** tenure_months
        ) / (
            ((1 + monthly_rate) ** tenure_months) - 1
        )
        return emi
    
    def _calculate_principal(self, emi: float, tenure_months: int, annual_rate: float) -> float:
        """Calculate principal from EMI"""
        monthly_rate = annual_rate / (12 * 100)
        if monthly_rate == 0:
            return emi * tenure_months
        
        principal = emi * (
            ((1 + monthly_rate) ** tenure_months) - 1
        ) / (
            monthly_rate * ((1 + monthly_rate) ** tenure_months)
        )
        return principal


eligibility_service = EligibilityService()
