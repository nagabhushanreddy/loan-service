"""Tests for eligibility service"""
import pytest
from app.services.eligibility_service import eligibility_service
from app.models.schemas import EligibilityCheckRequest, ApplicantProfile
from app.models.enums import KYCStatus, EligibilityStatus


@pytest.fixture
def valid_applicant() -> ApplicantProfile:
    """Create valid applicant profile"""
    return ApplicantProfile(
        identity_id="ID123",
        kyc_status=KYCStatus.VERIFIED,
        monthly_income=50000,
        employer="Test Corp",
        employment_type="salaried",
        monthly_obligations=10000,
        credit_score=750,
        existing_loans_count=1
    )


@pytest.mark.asyncio
async def test_eligibility_check_eligible(valid_applicant):
    """Test eligible applicant"""
    request = EligibilityCheckRequest(
        product_id="two_wheeler_std",
        applicant=valid_applicant,
        requested_amount=50000,
        requested_tenure=24,
        purpose="new_vehicle"
    )
    
    result = await eligibility_service.check_eligibility(request)
    assert result.eligible is True
    assert result.status == EligibilityStatus.ELIGIBLE
    assert len(result.reasons) == 0


@pytest.mark.asyncio
async def test_eligibility_check_kyc_not_verified(valid_applicant):
    """Test KYC not verified"""
    valid_applicant.kyc_status = KYCStatus.NOT_STARTED
    
    request = EligibilityCheckRequest(
        product_id="two_wheeler_std",
        applicant=valid_applicant,
        requested_amount=50000,
        requested_tenure=24
    )
    
    result = await eligibility_service.check_eligibility(request)
    assert result.eligible is False
    assert any("KYC" in reason for reason in result.reasons)


@pytest.mark.asyncio
async def test_eligibility_check_low_income(valid_applicant):
    """Test income too low"""
    valid_applicant.monthly_income = 10000
    
    request = EligibilityCheckRequest(
        product_id="two_wheeler_std",
        applicant=valid_applicant,
        requested_amount=50000,
        requested_tenure=24
    )
    
    result = await eligibility_service.check_eligibility(request)
    assert result.eligible is False
    assert any("income" in reason.lower() for reason in result.reasons)


@pytest.mark.asyncio
async def test_eligibility_check_low_credit_score(valid_applicant):
    """Test credit score too low"""
    valid_applicant.credit_score = 600
    
    request = EligibilityCheckRequest(
        product_id="two_wheeler_std",
        applicant=valid_applicant,
        requested_amount=50000,
        requested_tenure=24
    )
    
    result = await eligibility_service.check_eligibility(request)
    assert result.eligible is False
    assert any("credit score" in reason.lower() for reason in result.reasons)


@pytest.mark.asyncio
async def test_eligibility_check_high_dti(valid_applicant):
    """Test high debt-to-income ratio"""
    valid_applicant.monthly_obligations = 40000  # High obligations
    
    request = EligibilityCheckRequest(
        product_id="two_wheeler_std",
        applicant=valid_applicant,
        requested_amount=100000,
        requested_tenure=24
    )
    
    result = await eligibility_service.check_eligibility(request)
    assert any("debt-to-income" in reason.lower() for reason in result.reasons)


@pytest.mark.asyncio
async def test_eligibility_check_invalid_product(valid_applicant):
    """Test invalid product"""
    request = EligibilityCheckRequest(
        product_id="invalid_product",
        applicant=valid_applicant,
        requested_amount=50000,
        requested_tenure=24
    )
    
    result = await eligibility_service.check_eligibility(request)
    assert result.eligible is False
    assert result.status == EligibilityStatus.NOT_ELIGIBLE


@pytest.mark.asyncio
async def test_eligibility_check_amount_out_of_range(valid_applicant):
    """Test amount out of product range"""
    request = EligibilityCheckRequest(
        product_id="two_wheeler_std",
        applicant=valid_applicant,
        requested_amount=500000,  # Too high for two-wheeler
        requested_tenure=24
    )
    
    result = await eligibility_service.check_eligibility(request)
    assert result.eligible is False
    assert any("exceed" in reason.lower() for reason in result.reasons)


def test_calculate_emi():
    """Test EMI calculation"""
    emi = eligibility_service._calculate_emi(100000, 24, 12.0)
    assert emi > 0
    assert emi < 100000  # EMI should be less than principal
    # Expected EMI around 4707 for 100k @ 12% for 24 months
    assert 4500 < emi < 5000


def test_calculate_principal():
    """Test principal calculation from EMI"""
    emi = 5000
    principal = eligibility_service._calculate_principal(emi, 24, 12.0)
    assert principal > 0
    # Should be around 106k for EMI of 5000 @ 12% for 24 months
    assert 100000 < principal < 110000
