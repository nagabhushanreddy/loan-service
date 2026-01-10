"""Enumeration types for loan service"""
from enum import Enum


class LoanProductType(str, Enum):
    """Loan product types"""
    TWO_WHEELER = "two_wheeler"
    FOUR_WHEELER = "four_wheeler"
    PERSONAL_LOAN = "personal_loan"
    VEHICLE_LOAN = "vehicle_loan"


class LoanStatus(str, Enum):
    """Loan application statuses"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    INTAKE_REVIEW = "intake_review"
    RISK_REVIEW = "risk_review"
    CREDIT_ASSESSMENT = "credit_assessment"
    MAKER_REVIEW = "maker_review"
    CHECKER_REVIEW = "checker_review"
    DECISION_PENDING = "decision_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"
    CONDITIONS_PENDING = "conditions_pending"
    READY_FOR_DISBURSEMENT = "ready_for_disbursement"
    DISBURSEMENT_CONFIRMED = "disbursement_confirmed"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    """User roles for workflow"""
    CUSTOMER = "customer"
    LOAN_OFFICER = "loan_officer"
    RISK_OFFICER = "risk_officer"
    CREDIT_ASSESSMENT_OFFICER = "credit_assessment_officer"
    DISBURSEMENT_OFFICER = "disbursement_officer"
    MAKER = "maker"
    CHECKER = "checker"
    ADMIN = "admin"


class TaskStatus(str, Enum):
    """Task statuses"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task types"""
    VERIFICATION = "verification"
    RISK_REVIEW = "risk_review"
    CREDIT_ASSESSMENT = "credit_assessment"
    COMPLIANCE = "compliance"
    APPROVAL = "approval"


class DecisionOutcome(str, Enum):
    """Decision outcomes"""
    APPROVE = "approve"
    REJECT = "reject"
    CONDITIONAL = "conditional"


class DocumentStatus(str, Enum):
    """Document statuses"""
    PENDING = "pending"
    UPLOADED = "uploaded"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ConditionSeverity(str, Enum):
    """Condition severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConditionStatus(str, Enum):
    """Condition statuses"""
    PENDING = "pending"
    FULFILLED = "fulfilled"
    WAIVED = "waived"


class KYCStatus(str, Enum):
    """KYC verification statuses"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    REJECTED = "rejected"


class EligibilityStatus(str, Enum):
    """Eligibility check statuses"""
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    CONDITIONAL = "conditional"
