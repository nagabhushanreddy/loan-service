"""Application service for loan applications (in-memory storage for demo)"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.models.schemas import (
    CreateLoanApplicationRequest,
    UpdateLoanApplicationRequest,
    LoanApplicationResponse,
    AuditEntry
)
from app.models.enums import LoanStatus, KYCStatus, UserRole
from app.services.product_service import product_service


class ApplicationService:
    """Service for loan application operations"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.applications: Dict[str, Dict[str, Any]] = {}
        self.audit_log: Dict[str, List[AuditEntry]] = {}
    
    async def create_application(
        self,
        request: CreateLoanApplicationRequest,
        user_id: str,
        tenant_id: str,
        correlation_id: str
    ) -> LoanApplicationResponse:
        """Create new loan application"""
        
        # Validate product
        product = product_service.get_product(request.product_id)
        if not product:
            raise ValueError("Invalid product ID")
        
        # Validate parameters
        valid, errors = product_service.validate_product_params(
            request.product_id,
            request.requested_amount,
            request.requested_tenure
        )
        if not valid:
            raise ValueError("; ".join(errors))
        
        app_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        application = {
            "id": app_id,
            "product_id": request.product_id,
            "product_name": product.name,
            "applicant_id": request.applicant_id,
            "tenant_id": tenant_id,
            "requested_amount": request.requested_amount,
            "requested_tenure": request.requested_tenure,
            "approved_amount": None,
            "approved_tenure": None,
            "purpose": request.purpose,
            "status": LoanStatus.DRAFT,
            "workflow_step": "draft",
            "owner": user_id,
            "assigned_to": None,
            "channel": request.channel,
            "source": request.source,
            "kyc_status": KYCStatus.NOT_STARTED,
            "credit_score": None,
            "risk_grade": None,
            "created_at": now,
            "updated_at": now,
            "submitted_at": None,
            "decision_at": None
        }
        
        self.applications[app_id] = application
        
        # Log audit entry
        await self._log_audit(
            app_id,
            "create_application",
            user_id,
            UserRole.CUSTOMER,
            None,
            LoanStatus.DRAFT,
            "Application created",
            correlation_id
        )
        
        return LoanApplicationResponse(**application)
    
    async def get_application(self, app_id: str) -> Optional[LoanApplicationResponse]:
        """Get application by ID"""
        app = self.applications.get(app_id)
        if app:
            return LoanApplicationResponse(**app)
        return None
    
    async def list_applications(
        self,
        tenant_id: str,
        status: Optional[LoanStatus] = None,
        product_id: Optional[str] = None,
        applicant_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[LoanApplicationResponse], int]:
        """List applications with filters"""
        filtered = []
        
        for app in self.applications.values():
            if app["tenant_id"] != tenant_id:
                continue
            if status and app["status"] != status:
                continue
            if product_id and app["product_id"] != product_id:
                continue
            if applicant_id and app["applicant_id"] != applicant_id:
                continue
            filtered.append(app)
        
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated = filtered[start:end]
        applications = [LoanApplicationResponse(**app) for app in paginated]
        
        return applications, total
    
    async def update_application(
        self,
        app_id: str,
        request: UpdateLoanApplicationRequest,
        user_id: str,
        correlation_id: str
    ) -> LoanApplicationResponse:
        """Update application (only in editable states)"""
        app = self.applications.get(app_id)
        if not app:
            raise ValueError("Application not found")
        
        # Check if application is in editable state
        editable_states = [LoanStatus.DRAFT]
        if app["status"] not in editable_states:
            raise ValueError(f"Application cannot be edited in {app['status']} state")
        
        # Update fields
        if request.requested_amount is not None:
            app["requested_amount"] = request.requested_amount
        if request.requested_tenure is not None:
            app["requested_tenure"] = request.requested_tenure
        if request.purpose is not None:
            app["purpose"] = request.purpose
        
        app["updated_at"] = datetime.utcnow()
        
        await self._log_audit(
            app_id,
            "update_application",
            user_id,
            UserRole.CUSTOMER,
            app["status"],
            app["status"],
            "Application updated",
            correlation_id
        )
        
        return LoanApplicationResponse(**app)
    
    async def submit_application(
        self,
        app_id: str,
        user_id: str,
        correlation_id: str
    ) -> LoanApplicationResponse:
        """Submit application"""
        app = self.applications.get(app_id)
        if not app:
            raise ValueError("Application not found")
        
        if app["status"] != LoanStatus.DRAFT:
            raise ValueError(f"Application cannot be submitted from {app['status']} state")
        
        now = datetime.utcnow()
        app["status"] = LoanStatus.SUBMITTED
        app["workflow_step"] = "submitted"
        app["submitted_at"] = now
        app["updated_at"] = now
        
        await self._log_audit(
            app_id,
            "submit_application",
            user_id,
            UserRole.CUSTOMER,
            LoanStatus.DRAFT,
            LoanStatus.SUBMITTED,
            "Application submitted for review",
            correlation_id
        )
        
        return LoanApplicationResponse(**app)
    
    async def transition_status(
        self,
        app_id: str,
        new_status: LoanStatus,
        user_id: str,
        user_role: UserRole,
        notes: Optional[str],
        correlation_id: str
    ) -> LoanApplicationResponse:
        """Transition application status"""
        app = self.applications.get(app_id)
        if not app:
            raise ValueError("Application not found")
        
        old_status = app["status"]
        now = datetime.utcnow()
        
        app["status"] = new_status
        app["workflow_step"] = new_status.value
        app["updated_at"] = now
        
        if new_status in [LoanStatus.APPROVED, LoanStatus.REJECTED, LoanStatus.CONDITIONAL]:
            app["decision_at"] = now
        
        await self._log_audit(
            app_id,
            "status_transition",
            user_id,
            user_role,
            old_status,
            new_status,
            notes or f"Status changed to {new_status.value}",
            correlation_id
        )
        
        return LoanApplicationResponse(**app)
    
    async def assign_application(
        self,
        app_id: str,
        assignee_id: str,
        user_id: str,
        user_role: UserRole,
        reason: Optional[str],
        correlation_id: str
    ):
        """Assign application to officer"""
        app = self.applications.get(app_id)
        if not app:
            raise ValueError("Application not found")
        
        app["assigned_to"] = assignee_id
        app["updated_at"] = datetime.utcnow()
        
        await self._log_audit(
            app_id,
            "assign_application",
            user_id,
            user_role,
            app["status"],
            app["status"],
            reason or f"Assigned to {assignee_id}",
            correlation_id
        )
    
    async def get_audit_trail(self, app_id: str) -> List[AuditEntry]:
        """Get audit trail for application"""
        return self.audit_log.get(app_id, [])
    
    async def _log_audit(
        self,
        app_id: str,
        action: str,
        actor_id: str,
        actor_role: UserRole,
        from_status: Optional[LoanStatus],
        to_status: Optional[LoanStatus],
        notes: str,
        correlation_id: str
    ):
        """Log audit entry"""
        if app_id not in self.audit_log:
            self.audit_log[app_id] = []
        
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            application_id=app_id,
            action=action,
            actor_id=actor_id,
            actor_role=actor_role,
            from_status=from_status,
            to_status=to_status,
            notes=notes,
            correlation_id=correlation_id,
            source="api",
            timestamp=datetime.utcnow(),
            metadata={}
        )
        
        self.audit_log[app_id].append(entry)


application_service = ApplicationService()
