# Multi-Finance User Application
## Loan Service - Requirements Document (OpenAPI-Compliant)

---

## 1. Overview
The Loan Service manages loan products, applications, eligibility, underwriting workflows, disbursement readiness, and loan account lifecycle for multiple loan products (two-wheeler, four-wheeler, personal loan, vehicle loan). All APIs must be OpenAPI 3.x compliant, security-first, and integrate with other platform services.

## 2. Architecture Principles
- Single-responsibility microservice with database-per-service or entity-service for metadata
- Stateless service nodes; state in database/cache/storage
- RESTful APIs with OpenAPI 3.0.3
- JWT-based authentication and AuthZ decisions via authz-service (default deny)
- Layered architecture: Routes → Services → Clients → External Systems
- Idempotent, deterministic APIs with strong validation
- Observability-first: metrics, logs, traces with correlation IDs
- Reuse shared utilities via utils-service; shared metadata via entity-service

## 3. Features
- Loan products catalog (two-wheeler, four-wheeler, personal, vehicle loan variants)
- Loan application intake with multipart workflows
- Eligibility checks (identity, KYC, credit criteria)
- Workflow orchestration with maker-checker at key stages
- Role-based task routing (Customer, Loan Officer, Risk Officer, Credit Assessment Officer, Disbursement Officer, Maker, Checker)
- Document collection and verification via document-service
- Integration with authz-service for role/permission validation
- Pre-disbursement checks and disbursement readiness
- Loan account creation and status tracking
- Status transitions with auditability and SLAs
- Idempotent submissions and updates using Idempotency-Key
- Notifications (status changes) via notification-service (future-ready)
- Rate limiting and quota enforcement per tenant/user

## 4. Technology Stack
- Language: Python 3.10+
- Framework: FastAPI (async, OpenAPI-native)
- Data validation: Pydantic
- Persistence: Postgres (or equivalent) for loan metadata; entity-service for standardized metadata if shared
- Caching: Redis for workflow/task caching and idempotency keys
- Messaging (optional/future): lightweight queue for async tasks (e.g., Celery/RQ with Redis)
- Logging: Structured JSON logs via utils-service
- Server: Uvicorn ASGI

## 5. Core APIs / Endpoints
All endpoints under /api/v1 with JWT and authz enforcement.

### 5.1 Health
- GET /health (readiness)
- GET /healthz (liveness)

### 5.2 Loan Products
- GET /loan-products (list products, eligibility rules, rate ranges, fees)
- GET /loan-products/{product_id} (details, required documents, max LTV, tenure options)

### 5.3 Eligibility
- POST /eligibility/check (product, applicant profile, income, obligations) returns eligibility status, max amount, reasons

### 5.4 Loan Applications
- POST /loan-applications (create draft; capture product, applicant, requested amount, tenure, purpose)
- GET /loan-applications (list/filter by status, product, applicant, owner)
- GET /loan-applications/{id} (view application with audit trail and required actions)
- POST /loan-applications/{id}/submit (customer submission; locks customer-editable fields)
- PATCH /loan-applications/{id} (update mutable fields while in editable states)

### 5.5 Workflow Actions (Maker-Checker)
- POST /loan-applications/{id}/tasks/{task_id}/complete (role-bound action; supports approvals/rejections/requests for info)
- POST /loan-applications/{id}/assign (reassign to officer within allowed roles)
- POST /loan-applications/{id}/escalate (workflow escalation with reason)
- POST /loan-applications/{id}/revert (revert to previous step with reason where allowed)

### 5.6 Documents (via document-service integration)
- POST /loan-applications/{id}/documents (initiate upload metadata; delegates file upload to document-service)
- GET /loan-applications/{id}/documents (list metadata; pre-signed URLs from document-service)
- DELETE /loan-applications/{id}/documents/{doc_id} (soft delete metadata; enforce permissions)

### 5.7 Decisions and Disbursement Readiness
- POST /loan-applications/{id}/decision (approve/reject/conditional approve with conditions list)
- POST /loan-applications/{id}/conditions/fulfill (mark conditions fulfilled; attach evidence docs)
- POST /loan-applications/{id}/disbursement/prepare (mark ready-for-disbursement after checks)
- POST /loan-applications/{id}/disbursement/confirm (final confirmation; emits event for disbursement system)

### 5.8 Loan Accounts
- GET /loans (list active/closed loans)
- GET /loans/{id} (loan account summary, repayment schedule, status)
- GET /loans/{id}/timeline (status history and audit trail)

### 5.9 Audit and Activity
- GET /loan-applications/{id}/audit (timeline of actions, actors, timestamps, reasons)

### 5.10 Admin / Reference Data
- GET /reference/loan-statuses, /reference/workflow-steps, /reference/rejection-reasons, /reference/condition-types

## 6. Data Model Requirements (descriptive)
- Product: id, name, type (two-wheeler, four-wheeler, personal, vehicle), rate ranges, tenure ranges, max LTV, fees, required documents, eligibility rules, allowed purposes
- Application: id, product_id, applicant_id (entity-service ref), tenant_id, requested_amount, tenure, purpose, status, workflow_step, owner (officer), assigned_to, channel, source, correlation_id
- Applicant Profile Snapshot: identity refs, KYC status, income, employer, obligations, credit score snapshot, risk flags
- Documents: list of required/provided documents with doc_id (document-service), type, status, verifier, timestamps
- Tasks: task_id, type (verification, risk review, compliance), role requirement, status, assignee, due_at, completed_at, decision, comments
- Conditions: condition_id, description, severity, status, evidence_docs, set_by_role, fulfilled_at
- Decisions: decision outcome (approve/reject/conditional), reasons, risk_grade, approved_amount, approved_tenure, conditions list
- Audit: action, actor_id, actor_role, timestamp, from_status, to_status, notes, correlation_id, source
- Loan Account: loan_id, linked_application_id, principal, interest terms, repayment schedule link, disbursement_status, close_reason
- Idempotency: idempotency_key, request_fingerprint, response_reference, expiry

## 7. Business Logic & Rules
- KYC must be VERIFIED before approval; eligibility check required before submission
- Maker-checker enforced on risk decisions, final approval, and disbursement readiness
- Role-based workflows: Customer (draft/submit), Loan Officer (review/intake), Risk Officer (risk review), Credit Assessment Officer (financial assessment), Checker (independent validation), Maker (proposal), Disbursement Officer (pre-disbursement checks)
- Status model (example): draft → submitted → intake_review → risk_review → credit_assessment → maker_review → checker_review → decision_pending → approved/rejected/conditional → conditions_pending → ready_for_disbursement → disbursement_confirmed
- Idempotency for create/submit/decision endpoints using Idempotency-Key header
- Validation: product availability, amount/tenure within product limits, income-to-obligation ratios, credit score thresholds, LTV for secured loans
- Conditions management: capture conditions on conditional approval; must be fulfilled before disbursement
- Document completeness checks: required docs per product and stage; block progression if missing or expired
- Ownership and tenancy: tenant isolation; applicant ownership enforced through authz-service
- Reassign/escalate with reason logging; SLA timers per workflow step
- Quotas/rate limits per user/tenant to prevent abuse

## 8. Security Requirements
- Authentication: JWT validation (auth-service); API key support for service-to-service
- Authorization: authz-service for role/permission checks; default deny on errors
- Roles mapped to workflow actions; only permitted roles may transition tasks
- Data protection: no sensitive data in logs; PII masking where displayed
- Input hardening: strict validation, file/type checks via document-service, path traversal prevention delegated to document-service
- Rate limiting: configurable per endpoint/user/tenant
- Audit logging: all status changes, decisions, reassignment, escalations, disbursement readiness
- Correlation IDs: required on all requests and propagated to downstream calls

## 9. Performance Requirements
- P95 latency: metadata reads <150ms; writes <250ms excluding external calls
- Throughput: support 200 concurrent application operations; burst handling with backpressure
- Idempotency storage TTL: configurable (e.g., 24h) without performance degradation
- Pagination defaults and limits to protect database

## 10. Error Handling
- Standard error envelope: success flag, error code, message, optional details, metadata with timestamp and correlation_id
- Common error codes: INVALID_REQUEST, UNAUTHORIZED, FORBIDDEN, NOT_FOUND, CONFLICT, RATE_LIMITED, IDENTITY_UNVERIFIED, KYC_NOT_VERIFIED, DOCUMENT_MISSING, WORKFLOW_INVALID_STATE, DUPLICATE_REQUEST, AUTHZ_SERVICE_ERROR, ENTITY_SERVICE_ERROR, DOCUMENT_SERVICE_ERROR
- Fail closed on AuthZ or policy evaluation errors
- Validation errors must list field-level issues

## 11. External Service Integration
- entity-service: store and query loan-related metadata where shared; maintain canonical applicant/entity references
- document-service: upload/list/delete loan documents; use pre-signed URLs; store only metadata in loan-service
- authz-service: authorize workflow actions and role-based transitions; cache short-lived decisions
- utils-service: logging, configuration helpers, correlation IDs
- notification-service (future): send status change notifications
- credit bureau / scoring adapter (future): pluggable client for credit data

## 12. Testing Requirements
- Unit tests: validation, status transitions, idempotency handling, maker-checker enforcement, eligibility calculations
- Integration tests: entity-service interactions, document-service flows, authz-service decisions, idempotency behavior, role-based access
- Performance tests: concurrent submissions and approvals, pagination under load
- Security tests: authz bypass attempts, improper state transitions, rate limit enforcement
- Coverage target: minimum 80% statements/branches

## 13. Configuration Requirements
- Application/server: host, port, workers
- Security: JWT settings, API key header, authz-service endpoints/timeouts/retries
- Storage: database connection, pool sizes, migration strategy
- Caching: Redis endpoints, TTLs for idempotency and workflow caches
- Idempotency: header name, TTL, storage backend
- Rate limiting: per-endpoint and per-user/tenant limits
- Workflow: configurable SLA thresholds, escalation rules, allowed transitions per role
- External services: URLs, timeouts, retries for entity-service, document-service, authz-service
- Logging: level, JSON format, output; init via utils-service

## 14. Deployment
- Containerized service with health/readiness probes (/healthz, /health)
- At least 2 replicas for HA; HPA on CPU/latency
- Blue/green or rolling deploys; backward-compatible schema changes
- Database migrations executed safely with rollback plan

## 15. OpenAPI Requirements
- OpenAPI 3.0.3; title: Loan Service API; versioned under /api/v1
- Security schemes: Bearer JWT and API key header (X-API-Key)
- Idempotency-Key header documented for mutating endpoints
- Standardized error model and pagination schema
- Clear enums for statuses, roles, workflow steps, decision outcomes

## 16. Monitoring & Observability
- Metrics: request rate, latency, error rate, workflow step durations, idempotency hits/misses, AuthZ failures, document calls, entity-service calls
- Logs: structured with correlation_id, tenant_id, application_id, user_id, action, from_status, to_status
- Tracing: propagate correlation IDs to downstream services
- Alerts: elevated error rates, AuthZ failures, SLA breaches per workflow step

## 17. Project Structure (logical, no code)
- Root entrypoint main.py
- app/ package with config, middleware, cache/idempotency, models, routes, services, clients
- routes: health, products, eligibility, applications, workflow, documents, decisions, loans
- services: product, application, workflow/maker-checker, eligibility, decision, idempotency, audit helpers
- clients: entity-service, document-service, authz-service, optional notification/credit adapters
- models: Pydantic schemas for requests/responses and domain models (no code here)
- tests: unit, integration, e2e; reports directory for junit/coverage; logs directory
- config: app/logging YAML files; requirements.txt and requirements-dev.txt; README and this Requirements document
- Use absolute imports from app.* and shared logger/config from utils-service

## 18. Future Enhancements
- Automated credit bureau pulls and real-time scoring
- Dynamic pricing based on risk grade and channel
- Pre-approved offers and campaign-driven eligibility
- Rule engine integration for product/offer decisioning
- Event-driven notifications and webhooks for status changes
- Repayment schedule generation and EMI calculators
- Fraud signals integration and anomaly detection

---
End of Document
