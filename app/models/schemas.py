"""Request and response schemas"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.enums import *


# Common schemas
class ErrorDetail(BaseModel):
    """Error detail model"""
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    data: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Loan Product schemas
class LoanProductResponse(BaseModel):
    """Loan product response"""
    id: str
    name: str
    type: LoanProductType
    min_amount: float
    max_amount: float
    min_tenure: int
    max_tenure: int
    interest_rate_min: float
    interest_rate_max: float
    max_ltv: float
    fees: Dict[str, float] = Field(default_factory=dict)
    required_documents: List[str] = Field(default_factory=list)
    eligibility_rules: Dict[str, Any] = Field(default_factory=dict)
    allowed_purposes: List[str] = Field(default_factory=list)
    is_active: bool = True


# Eligibility schemas
class ApplicantProfile(BaseModel):
    """Applicant profile for eligibility check"""
    identity_id: str
    kyc_status: KYCStatus
    monthly_income: float = Field(gt=0)
    employer: Optional[str] = None
    employment_type: Optional[str] = None
    monthly_obligations: float = Field(ge=0, default=0)
    credit_score: Optional[int] = Field(None, ge=300, le=900)
    existing_loans_count: int = Field(ge=0, default=0)


class EligibilityCheckRequest(BaseModel):
    """Eligibility check request"""
    product_id: str
    applicant: ApplicantProfile
    requested_amount: float = Field(gt=0)
    requested_tenure: int = Field(gt=0)
    purpose: Optional[str] = None


class EligibilityCheckResponse(BaseModel):
    """Eligibility check response"""
    status: EligibilityStatus
    eligible: bool
    max_eligible_amount: Optional[float] = None
    reasons: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# Loan Application schemas
class CreateLoanApplicationRequest(BaseModel):
    """Create loan application request"""
    product_id: str
    applicant_id: str
    requested_amount: float = Field(gt=0)
    requested_tenure: int = Field(gt=0)
    purpose: Optional[str] = None
    channel: str = Field(default="web")
    source: Optional[str] = None


class UpdateLoanApplicationRequest(BaseModel):
    """Update loan application request"""
    requested_amount: Optional[float] = Field(None, gt=0)
    requested_tenure: Optional[int] = Field(None, gt=0)
    purpose: Optional[str] = None


class LoanApplicationResponse(BaseModel):
    """Loan application response"""
    id: str
    product_id: str
    product_name: str
    applicant_id: str
    tenant_id: str
    requested_amount: float
    requested_tenure: int
    approved_amount: Optional[float] = None
    approved_tenure: Optional[int] = None
    purpose: Optional[str] = None
    status: LoanStatus
    workflow_step: str
    owner: Optional[str] = None
    assigned_to: Optional[str] = None
    channel: str
    source: Optional[str] = None
    kyc_status: KYCStatus
    credit_score: Optional[int] = None
    risk_grade: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    decision_at: Optional[datetime] = None


# Workflow schemas
class TaskResponse(BaseModel):
    """Task response"""
    id: str
    application_id: str
    type: TaskType
    status: TaskStatus
    role_requirement: UserRole
    assignee: Optional[str] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    decision: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime


class CompleteTaskRequest(BaseModel):
    """Complete task request"""
    decision: str
    comments: Optional[str] = None
    next_assignee: Optional[str] = None


class AssignApplicationRequest(BaseModel):
    """Assign application request"""
    assignee_id: str
    role: UserRole
    reason: Optional[str] = None


class EscalateApplicationRequest(BaseModel):
    """Escalate application request"""
    reason: str
    escalate_to: Optional[str] = None


class RevertApplicationRequest(BaseModel):
    """Revert application request"""
    target_status: LoanStatus
    reason: str


# Decision schemas
class ConditionItem(BaseModel):
    """Condition item"""
    id: Optional[str] = None
    description: str
    severity: ConditionSeverity
    status: ConditionStatus = ConditionStatus.PENDING
    evidence_docs: List[str] = Field(default_factory=list)
    set_by_role: Optional[UserRole] = None
    fulfilled_at: Optional[datetime] = None


class MakeDecisionRequest(BaseModel):
    """Make decision request"""
    outcome: DecisionOutcome
    reasons: List[str] = Field(default_factory=list)
    approved_amount: Optional[float] = Field(None, gt=0)
    approved_tenure: Optional[int] = Field(None, gt=0)
    risk_grade: Optional[str] = None
    conditions: List[ConditionItem] = Field(default_factory=list)
    comments: Optional[str] = None


class FulfillConditionRequest(BaseModel):
    """Fulfill condition request"""
    condition_id: str
    evidence_doc_ids: List[str] = Field(default_factory=list)
    comments: Optional[str] = None


class DisbursementPrepareRequest(BaseModel):
    """Prepare for disbursement request"""
    final_amount: float = Field(gt=0)
    final_tenure: int = Field(gt=0)
    disbursement_method: str
    account_details: Dict[str, Any]
    comments: Optional[str] = None


class DisbursementConfirmRequest(BaseModel):
    """Confirm disbursement request"""
    confirmation_code: str
    disbursed_amount: float = Field(gt=0)
    disbursement_date: datetime
    reference_number: str
    comments: Optional[str] = None


# Document schemas
class DocumentMetadata(BaseModel):
    """Document metadata"""
    id: str
    application_id: str
    type: str
    status: DocumentStatus
    file_name: str
    file_size: int
    content_type: str
    uploaded_by: str
    uploaded_at: datetime
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    presigned_url: Optional[str] = None


class InitiateDocumentUploadRequest(BaseModel):
    """Initiate document upload request"""
    document_type: str
    file_name: str
    file_size: int
    content_type: str


# Loan Account schemas
class LoanAccountResponse(BaseModel):
    """Loan account response"""
    id: str
    application_id: str
    applicant_id: str
    tenant_id: str
    product_id: str
    principal: float
    interest_rate: float
    tenure: int
    status: str
    disbursement_date: Optional[datetime] = None
    disbursement_status: str
    first_emi_date: Optional[datetime] = None
    closure_date: Optional[datetime] = None
    close_reason: Optional[str] = None
    created_at: datetime


# Audit schemas
class AuditEntry(BaseModel):
    """Audit entry"""
    id: str
    application_id: str
    action: str
    actor_id: str
    actor_role: UserRole
    from_status: Optional[LoanStatus] = None
    to_status: Optional[LoanStatus] = None
    notes: Optional[str] = None
    correlation_id: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
