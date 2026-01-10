"""Tests for workflow service"""
import pytest
from datetime import datetime
from app.services.workflow_service import workflow_service
from app.services.application_service import application_service
from app.models.schemas import (
    CreateLoanApplicationRequest,
    MakeDecisionRequest,
    ConditionItem
)
from app.models.enums import (
    TaskType, UserRole, TaskStatus, DecisionOutcome,
    ConditionSeverity, LoanStatus
)


@pytest.mark.asyncio
async def test_create_task():
    """Test creating workflow task"""
    # Create application first
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    app = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    # Create task
    task = await workflow_service.create_task(
        app.id,
        TaskType.VERIFICATION,
        UserRole.LOAN_OFFICER,
        due_hours=24
    )
    
    assert task.id
    assert task.application_id == app.id
    assert task.type == TaskType.VERIFICATION
    assert task.status == TaskStatus.PENDING
    assert task.role_requirement == UserRole.LOAN_OFFICER


@pytest.mark.asyncio
async def test_complete_task():
    """Test completing task"""
    # Create application and task
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    app = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    task = await workflow_service.create_task(
        app.id,
        TaskType.VERIFICATION,
        UserRole.LOAN_OFFICER
    )
    
    # Complete task
    completed = await workflow_service.complete_task(
        task.id,
        "approved",
        "Verification complete",
        "officer-123",
        UserRole.LOAN_OFFICER,
        "corr-789"
    )
    
    assert completed.status == TaskStatus.COMPLETED
    assert completed.decision == "approved"
    assert completed.completed_at is not None


@pytest.mark.asyncio
async def test_complete_task_wrong_role():
    """Test completing task with wrong role"""
    # Create application and task
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    app = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    task = await workflow_service.create_task(
        app.id,
        TaskType.VERIFICATION,
        UserRole.LOAN_OFFICER
    )
    
    # Try to complete with wrong role
    with pytest.raises(ValueError, match="Role.*required"):
        await workflow_service.complete_task(
            task.id,
            "approved",
            "Verification complete",
            "customer-123",
            UserRole.CUSTOMER,  # Wrong role
            "corr-789"
        )


@pytest.mark.asyncio
async def test_make_decision_approve():
    """Test making approval decision"""
    # Create and submit application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    app = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    await application_service.submit_application(
        app.id, "user-123", "corr-789"
    )
    
    # Make approval decision
    decision_req = MakeDecisionRequest(
        outcome=DecisionOutcome.APPROVE,
        reasons=["Good credit score", "Stable income"],
        approved_amount=50000,
        approved_tenure=24,
        risk_grade="A",
        comments="Approved"
    )
    
    await workflow_service.make_decision(
        app.id,
        decision_req,
        "checker-123",
        UserRole.CHECKER,
        "corr-789"
    )
    
    # Check application status
    updated_app = await application_service.get_application(app.id)
    assert updated_app.status == LoanStatus.APPROVED


@pytest.mark.asyncio
async def test_make_decision_reject():
    """Test making rejection decision"""
    # Create and submit application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    app = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    await application_service.submit_application(
        app.id, "user-123", "corr-789"
    )
    
    # Make rejection decision
    decision_req = MakeDecisionRequest(
        outcome=DecisionOutcome.REJECT,
        reasons=["Poor credit score", "Insufficient income"],
        comments="Rejected"
    )
    
    await workflow_service.make_decision(
        app.id,
        decision_req,
        "checker-123",
        UserRole.CHECKER,
        "corr-789"
    )
    
    # Check application status
    updated_app = await application_service.get_application(app.id)
    assert updated_app.status == LoanStatus.REJECTED


@pytest.mark.asyncio
async def test_make_decision_conditional():
    """Test making conditional approval decision"""
    # Create and submit application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    app = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    await application_service.submit_application(
        app.id, "user-123", "corr-789"
    )
    
    # Make conditional decision with conditions
    conditions = [
        ConditionItem(
            description="Submit 3 months bank statements",
            severity=ConditionSeverity.HIGH
        ),
        ConditionItem(
            description="Provide employment verification letter",
            severity=ConditionSeverity.MEDIUM
        )
    ]
    
    decision_req = MakeDecisionRequest(
        outcome=DecisionOutcome.CONDITIONAL,
        reasons=["Additional documents required"],
        approved_amount=50000,
        approved_tenure=24,
        conditions=conditions,
        comments="Conditional approval"
    )
    
    await workflow_service.make_decision(
        app.id,
        decision_req,
        "checker-123",
        UserRole.CHECKER,
        "corr-789"
    )
    
    # Check application status
    updated_app = await application_service.get_application(app.id)
    assert updated_app.status == LoanStatus.CONDITIONAL
    
    # Check conditions created
    app_conditions = await workflow_service.get_conditions(app.id)
    assert len(app_conditions) == 2


@pytest.mark.asyncio
async def test_fulfill_condition():
    """Test fulfilling condition"""
    # Create application with conditions
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    app = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    await application_service.submit_application(
        app.id, "user-123", "corr-789"
    )
    
    # Make conditional decision
    conditions = [
        ConditionItem(
            description="Submit bank statements",
            severity=ConditionSeverity.HIGH
        )
    ]
    
    decision_req = MakeDecisionRequest(
        outcome=DecisionOutcome.CONDITIONAL,
        approved_amount=50000,
        approved_tenure=24,
        conditions=conditions
    )
    
    await workflow_service.make_decision(
        app.id, decision_req, "checker-123", UserRole.CHECKER, "corr-789"
    )
    
    # Get conditions
    app_conditions = await workflow_service.get_conditions(app.id)
    condition_id = app_conditions[0].id
    
    # Fulfill condition
    await workflow_service.fulfill_condition(
        condition_id,
        ["doc-123", "doc-456"],
        "user-123",
        "corr-789"
    )
    
    # Check condition fulfilled
    updated_conditions = await workflow_service.get_conditions(app.id)
    assert updated_conditions[0].status.value == "fulfilled"


@pytest.mark.asyncio
async def test_check_all_conditions_fulfilled():
    """Test checking if all conditions fulfilled"""
    # Create application with conditions
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    app = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    await application_service.submit_application(
        app.id, "user-123", "corr-789"
    )
    
    # Make conditional decision
    conditions = [
        ConditionItem(
            description="Condition 1",
            severity=ConditionSeverity.HIGH
        ),
        ConditionItem(
            description="Condition 2",
            severity=ConditionSeverity.MEDIUM
        )
    ]
    
    decision_req = MakeDecisionRequest(
        outcome=DecisionOutcome.CONDITIONAL,
        approved_amount=50000,
        approved_tenure=24,
        conditions=conditions
    )
    
    await workflow_service.make_decision(
        app.id, decision_req, "checker-123", UserRole.CHECKER, "corr-789"
    )
    
    # Check not all fulfilled
    all_fulfilled = await workflow_service.check_all_conditions_fulfilled(app.id)
    assert all_fulfilled is False
    
    # Fulfill all conditions
    app_conditions = await workflow_service.get_conditions(app.id)
    for cond in app_conditions:
        await workflow_service.fulfill_condition(
            cond.id, ["doc-123"], "user-123", "corr-789"
        )
    
    # Check all fulfilled
    all_fulfilled = await workflow_service.check_all_conditions_fulfilled(app.id)
    assert all_fulfilled is True


@pytest.mark.asyncio
async def test_prepare_disbursement():
    """Test preparing for disbursement"""
    # Create and approve application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    app = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    await application_service.submit_application(
        app.id, "user-123", "corr-789"
    )
    
    # Approve
    decision_req = MakeDecisionRequest(
        outcome=DecisionOutcome.APPROVE,
        approved_amount=50000,
        approved_tenure=24
    )
    
    await workflow_service.make_decision(
        app.id, decision_req, "checker-123", UserRole.CHECKER, "corr-789"
    )
    
    # Prepare disbursement
    await workflow_service.prepare_disbursement(
        app.id,
        50000,
        24,
        "bank_transfer",
        {"account_number": "1234567890", "ifsc": "TEST0001"},
        "disbursement-officer-123",
        UserRole.DISBURSEMENT_OFFICER,
        "corr-789"
    )
    
    # Check status
    updated_app = await application_service.get_application(app.id)
    assert updated_app.status == LoanStatus.READY_FOR_DISBURSEMENT


@pytest.mark.asyncio
async def test_confirm_disbursement():
    """Test confirming disbursement"""
    # Create, approve, and prepare application
    request = CreateLoanApplicationRequest(
        product_id="two_wheeler_std",
        applicant_id="applicant-123",
        requested_amount=50000,
        requested_tenure=24
    )
    
    app = await application_service.create_application(
        request, "user-123", "tenant-456", "corr-789"
    )
    
    await application_service.submit_application(
        app.id, "user-123", "corr-789"
    )
    
    decision_req = MakeDecisionRequest(
        outcome=DecisionOutcome.APPROVE,
        approved_amount=50000,
        approved_tenure=24
    )
    
    await workflow_service.make_decision(
        app.id, decision_req, "checker-123", UserRole.CHECKER, "corr-789"
    )
    
    await workflow_service.prepare_disbursement(
        app.id, 50000, 24, "bank_transfer", {},
        "officer-123", UserRole.DISBURSEMENT_OFFICER, "corr-789"
    )
    
    # Confirm disbursement
    await workflow_service.confirm_disbursement(
        app.id,
        50000,
        datetime.utcnow(),
        "REF123456",
        "disbursement-officer-123",
        UserRole.DISBURSEMENT_OFFICER,
        "corr-789"
    )
    
    # Check status
    updated_app = await application_service.get_application(app.id)
    assert updated_app.status == LoanStatus.DISBURSEMENT_CONFIRMED
