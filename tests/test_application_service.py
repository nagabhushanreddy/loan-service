"""Tests for application service"""
import pytest
from app.services.application_service import application_service
from app.models.schemas import CreateLoanApplicationRequest, UpdateLoanApplicationRequest
from app.models.enums import LoanStatus, UserRole


@pytest.mark.asyncio
async def test_create_application():
    """Test creating loan application"""
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24,
        purpose="new_vehicle",
        channel="web"
    )
    
    app = await application_service.create_application(
        request,
        "user-123",
        "tenant-456",
        "corr-789"
    )
    
    assert app.id
    assert app.product_id == "two_wheeler_std"
    assert app.status == LoanStatus.DRAFT
    assert app.requested_amount == 50000
    assert app.tenant_id == "tenant-456"


@pytest.mark.asyncio
async def test_create_application_invalid_product():
    """Test creating application with invalid product"""
    request = CreateLoanApplicationRequest(
        product_id="invalid_product",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    with pytest.raises(ValueError, match="Invalid product"):
        await application_service.create_application(
            request,
            "user-123",
            "tenant-456",
            "corr-789"
        )


@pytest.mark.asyncio
async def test_create_application_invalid_amount():
    """Test creating application with invalid amount"""
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=1000000,  # Too high
        requested_tenure=24
    )
    
    with pytest.raises(ValueError):
        await application_service.create_application(
            request,
            "user-123",
            "tenant-456",
            "corr-789"
        )


@pytest.mark.asyncio
async def test_get_application():
    """Test getting application"""
    # Create application first
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    created = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    # Get application
    app = await application_service.get_application(created.id)
    assert app is not None
    assert app.id == created.id


@pytest.mark.asyncio
async def test_get_nonexistent_application():
    """Test getting nonexistent application"""
    app = await application_service.get_application("nonexistent")
    assert app is None


@pytest.mark.asyncio
async def test_update_application():
    """Test updating application"""
    # Create application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    created = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    # Update application
    update_req = UpdateLoanApplicationRequest(
        requested_amount=60000,
        purpose="updated purpose"
    )
    
    updated = await application_service.update_application(
        created.id,
        update_req,
        "user-123",
        "corr-789"
    )
    
    assert updated.requested_amount == 60000
    assert updated.purpose == "updated purpose"


@pytest.mark.asyncio
async def test_update_application_not_in_draft():
    """Test updating application not in draft state"""
    # Create and submit application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    created = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    # Submit application
    await application_service.submit_application(
        created.id, "user-123", "corr-789"
    )
    
    # Try to update
    update_req = UpdateLoanApplicationRequest(
        requested_amount=60000
    )
    
    with pytest.raises(ValueError, match="cannot be edited"):
        await application_service.update_application(
            created.id,
            update_req,
            "user-123",
            "corr-789"
        )


@pytest.mark.asyncio
async def test_submit_application():
    """Test submitting application"""
    # Create application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    created = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    # Submit application
    submitted = await application_service.submit_application(
        created.id, "user-123", "corr-789"
    )
    
    assert submitted.status == LoanStatus.SUBMITTED
    assert submitted.submitted_at is not None


@pytest.mark.asyncio
async def test_list_applications():
    """Test listing applications"""
    # Create multiple applications
    for i in range(3):
        request = CreateLoanApplicationRequest(
            product_id="two_wheeler_std",
            applicant_id=f"applicant-{i}",
            requested_amount=50000,
            requested_tenure=24
        )
        await application_service.create_application(
            request, "user-123", "tenant-test", "corr-789"
        )
    
    # List applications
    apps, total = await application_service.list_applications(
        "tenant-test",
        page=1,
        page_size=10
    )
    
    assert total >= 3
    assert len(apps) >= 3


@pytest.mark.asyncio
async def test_list_applications_with_filter():
    """Test listing applications with status filter"""
    # Create and submit one application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-filter",
        requested_amount=50000,
        requested_tenure=24
    )
    
    created = await application_service.create_application(
        request, "user-123", "tenant-filter", "corr-789"
    )
    
    await application_service.submit_application(
        created.id, "user-123", "corr-789"
    )
    
    # List submitted applications
    apps, total = await application_service.list_applications(
        "tenant-filter",
        status=LoanStatus.SUBMITTED
    )
    
    assert all(app.status == LoanStatus.SUBMITTED for app in apps)


@pytest.mark.asyncio
async def test_transition_status():
    """Test status transition"""
    # Create application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    created = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    # Transition status
    transitioned = await application_service.transition_status(
        created.id,
        LoanStatus.INTAKE_REVIEW,
        "officer-123",
        UserRole.LOAN_OFFICER,
        "Moving to intake review",
        "corr-789"
    )
    
    assert transitioned.status == LoanStatus.INTAKE_REVIEW


@pytest.mark.asyncio
async def test_audit_trail():
    """Test audit trail logging"""
    # Create and update application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    created = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    await application_service.submit_application(
        created.id, "user-123", "corr-789"
    )
    
    # Get audit trail
    audit = await application_service.get_audit_trail(created.id)
    
    assert len(audit) >= 2  # Create and submit
    assert any(entry.action == "create_application" for entry in audit)
    assert any(entry.action == "submit_application" for entry in audit)
