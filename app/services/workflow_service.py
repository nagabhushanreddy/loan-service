"""Workflow service for maker-checker operations"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from app.models.schemas import TaskResponse, MakeDecisionRequest, ConditionItem
from app.models.enums import (
    LoanStatus, UserRole, TaskStatus, TaskType, 
    DecisionOutcome, ConditionStatus
)
from app.services.application_service import application_service


class WorkflowService:
    """Service for workflow and maker-checker operations"""
    
    def __init__(self):
        # In-memory storage
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.conditions: Dict[str, Dict[str, Any]] = {}
        self.decisions: Dict[str, Dict[str, Any]] = {}
    
    async def create_task(
        self,
        application_id: str,
        task_type: TaskType,
        role_requirement: UserRole,
        assignee: Optional[str] = None,
        due_hours: int = 24
    ) -> TaskResponse:
        """Create workflow task"""
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        task = {
            "id": task_id,
            "application_id": application_id,
            "type": task_type,
            "status": TaskStatus.PENDING,
            "role_requirement": role_requirement,
            "assignee": assignee,
            "due_at": now + timedelta(hours=due_hours),
            "completed_at": None,
            "decision": None,
            "comments": None,
            "created_at": now
        }
        
        self.tasks[task_id] = task
        return TaskResponse(**task)
    
    async def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """Get task by ID"""
        task = self.tasks.get(task_id)
        if task:
            return TaskResponse(**task)
        return None
    
    async def complete_task(
        self,
        task_id: str,
        decision: str,
        comments: Optional[str],
        user_id: str,
        user_role: UserRole,
        correlation_id: str
    ) -> TaskResponse:
        """Complete task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError("Task not found")
        
        if task["status"] == TaskStatus.COMPLETED:
            raise ValueError("Task already completed")
        
        # Verify user has required role
        if user_role != task["role_requirement"] and user_role != UserRole.ADMIN:
            raise ValueError(f"Role {task['role_requirement'].value} required")
        
        task["status"] = TaskStatus.COMPLETED
        task["decision"] = decision
        task["comments"] = comments
        task["completed_at"] = datetime.utcnow()
        
        return TaskResponse(**task)
    
    async def make_decision(
        self,
        application_id: str,
        request: MakeDecisionRequest,
        user_id: str,
        user_role: UserRole,
        correlation_id: str
    ):
        """Make loan decision"""
        app = await application_service.get_application(application_id)
        if not app:
            raise ValueError("Application not found")
        
        decision_id = str(uuid.uuid4())
        decision = {
            "id": decision_id,
            "application_id": application_id,
            "outcome": request.outcome,
            "reasons": request.reasons,
            "approved_amount": request.approved_amount,
            "approved_tenure": request.approved_tenure,
            "risk_grade": request.risk_grade,
            "comments": request.comments,
            "decided_by": user_id,
            "decided_at": datetime.utcnow()
        }
        
        self.decisions[decision_id] = decision
        
        # Update application status based on decision
        if request.outcome == DecisionOutcome.APPROVE:
            new_status = LoanStatus.APPROVED
        elif request.outcome == DecisionOutcome.REJECT:
            new_status = LoanStatus.REJECTED
        else:
            new_status = LoanStatus.CONDITIONAL
        
        # Create conditions if conditional approval
        if request.outcome == DecisionOutcome.CONDITIONAL:
            for cond in request.conditions:
                await self._create_condition(
                    application_id,
                    cond,
                    user_role
                )
        
        # Transition application status
        await application_service.transition_status(
            application_id,
            new_status,
            user_id,
            user_role,
            request.comments,
            correlation_id
        )
    
    async def _create_condition(
        self,
        application_id: str,
        condition: ConditionItem,
        set_by_role: UserRole
    ):
        """Create condition"""
        condition_id = str(uuid.uuid4())
        cond = {
            "id": condition_id,
            "application_id": application_id,
            "description": condition.description,
            "severity": condition.severity,
            "status": ConditionStatus.PENDING,
            "evidence_docs": [],
            "set_by_role": set_by_role,
            "fulfilled_at": None,
            "created_at": datetime.utcnow()
        }
        
        self.conditions[condition_id] = cond
    
    async def get_conditions(self, application_id: str) -> List[ConditionItem]:
        """Get conditions for application"""
        conditions = [
            ConditionItem(**c) 
            for c in self.conditions.values() 
            if c["application_id"] == application_id
        ]
        return conditions
    
    async def fulfill_condition(
        self,
        condition_id: str,
        evidence_doc_ids: List[str],
        user_id: str,
        correlation_id: str
    ):
        """Fulfill condition"""
        condition = self.conditions.get(condition_id)
        if not condition:
            raise ValueError("Condition not found")
        
        if condition["status"] == ConditionStatus.FULFILLED:
            raise ValueError("Condition already fulfilled")
        
        condition["status"] = ConditionStatus.FULFILLED
        condition["evidence_docs"] = evidence_doc_ids
        condition["fulfilled_at"] = datetime.utcnow()
    
    async def check_all_conditions_fulfilled(self, application_id: str) -> bool:
        """Check if all conditions are fulfilled"""
        conditions = [
            c for c in self.conditions.values()
            if c["application_id"] == application_id
        ]
        
        return all(
            c["status"] == ConditionStatus.FULFILLED 
            for c in conditions
        )
    
    async def prepare_disbursement(
        self,
        application_id: str,
        final_amount: float,
        final_tenure: int,
        disbursement_method: str,
        account_details: Dict[str, Any],
        user_id: str,
        user_role: UserRole,
        correlation_id: str
    ):
        """Prepare for disbursement"""
        app = await application_service.get_application(application_id)
        if not app:
            raise ValueError("Application not found")
        
        # Check conditions fulfilled
        if app.status == LoanStatus.CONDITIONAL:
            all_fulfilled = await self.check_all_conditions_fulfilled(application_id)
            if not all_fulfilled:
                raise ValueError("All conditions must be fulfilled before disbursement")
        
        # Transition to ready for disbursement
        await application_service.transition_status(
            application_id,
            LoanStatus.READY_FOR_DISBURSEMENT,
            user_id,
            user_role,
            "Ready for disbursement",
            correlation_id
        )
    
    async def confirm_disbursement(
        self,
        application_id: str,
        disbursed_amount: float,
        disbursement_date: datetime,
        reference_number: str,
        user_id: str,
        user_role: UserRole,
        correlation_id: str
    ):
        """Confirm disbursement"""
        await application_service.transition_status(
            application_id,
            LoanStatus.DISBURSEMENT_CONFIRMED,
            user_id,
            user_role,
            f"Disbursement confirmed: {reference_number}",
            correlation_id
        )


workflow_service = WorkflowService()
