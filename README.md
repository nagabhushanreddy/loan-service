# Loan Service

Loan application management, approval workflows, and repayment tracking.

## Status
🚧 **Structure Created** - Implementation pending

## Endpoints (Planned)
- `POST /api/v1/loans` - Create loan application
- `GET /api/v1/loans/:id` - Get loan details
- `PUT /api/v1/loans/:id` - Update loan
- `POST /api/v1/loans/:id/approve` - Approve loan
- `POST /api/v1/loans/:id/disburse` - Disburse funds
- `GET /api/v1/loans/:id/schedule` - Get repayment schedule
- `POST /api/v1/loans/:id/repay` - Record repayment
- `GET /api/v1/loans?status=pending` - List loans with filters
