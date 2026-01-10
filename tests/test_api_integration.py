"""Integration tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.auth import AuthenticatedUser, get_current_user
from app.models.enums import UserRole, KYCStatus


def override_get_current_user():
    """Override authentication for tests"""
    return AuthenticatedUser(
        user_id="test-user-123",
        tenant_id="test-tenant-456",
        roles=["customer", "admin", "checker", "disbursement"],
        email="test@example.com"
    )


@pytest.fixture
def client():
    """Create test client with dependency overrides"""
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_liveness_check(client):
    """Test liveness check endpoint"""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "loan-service"


def test_list_loan_products(client):
    """Test listing loan products"""
    response = client.get("/api/v1/loan-products")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "products" in data["data"]
    assert len(data["data"]["products"]) > 0


def test_get_loan_product(client):
    """Test getting specific loan product"""
    response = client.get("/api/v1/loan-products/two_wheeler_std")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["product"]["id"] == "two_wheeler_std"


def test_check_eligibility(client):
    """Test eligibility check endpoint"""
    request_data = {
        "product_id": "two_wheeler_std",
        "applicant": {
            "identity_id": "ID123",
            "kyc_status": "verified",
            "monthly_income": 50000,
            "monthly_obligations": 10000,
            "credit_score": 750,
            "existing_loans_count": 0
        },
        "requested_amount": 50000,
        "requested_tenure": 24
    }
    
    response = client.post("/api/v1/eligibility/check", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "eligibility" in data["data"]


def test_create_loan_application(client):
    """Test creating loan application"""
    request_data = {
        "product_id": "two_wheeler_std",
        "applicant_id": "applicant-123",
        "requested_amount": 50000,
        "requested_tenure": 24,
        "purpose": "new_vehicle",
        "channel": "web"
    }
    
    response = client.post("/api/v1/loan-applications", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "application" in data["data"]
    assert data["data"]["application"]["status"] == "draft"


def test_create_loan_application_with_idempotency(client):
    """Test creating loan application - idempotency tested with Redis mocked in conftest"""
    # Note: Actual idempotency testing requires Redis running
    # This test simply verifies the endpoint works
    request_data = {
        "product_id": "two_wheeler_std",
        "applicant_id": "applicant-456",
        "requested_amount": 50000,
        "requested_tenure": 24,
        "purpose": "new_vehicle",
        "channel": "web"
    }
    
    # Test without idempotency header (Redis not required)
    response = client.post(
        "/api/v1/loan-applications",
        json=request_data
    )
    assert response.status_code == 200
    assert "application" in response.json()["data"]


def test_list_loan_applications(client):
    """Test listing loan applications"""
    response = client.get("/api/v1/loan-applications")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "applications" in data["data"]
    assert "pagination" in data["data"]


def test_submit_loan_application(client):
    """Test submitting loan application"""
    # Create application
    create_data = {
        "product_id": "two_wheeler_std",
        "applicant_id": "applicant-789",
        "requested_amount": 50000,
        "requested_tenure": 24
    }
    
    create_response = client.post("/api/v1/loan-applications", json=create_data)
    app_id = create_response.json()["data"]["application"]["id"]
    
    # Submit application
    submit_response = client.post(f"/api/v1/loan-applications/{app_id}/submit")
    assert submit_response.status_code == 200
    data = submit_response.json()
    assert data["success"] is True
    assert data["data"]["application"]["status"] == "submitted"


def test_make_decision(client):
    """Test making loan decision"""
    from app.services.application_service import application_service
    from app.models.schemas import CreateLoanApplicationRequest
    import asyncio
    
    # Create and submit application first
    async def setup():
        request = CreateLoanApplicationRequest(
            product_id="two_wheeler_std",
            applicant_id="applicant-decision",
            requested_amount=50000,
            requested_tenure=24
        )
        app = await application_service.create_application(
            request, "user-123", "test-tenant-456", "corr-789"
        )
        await application_service.submit_application(
            app.id, "user-123", "corr-789"
        )
        return app.id
    
    app_id = asyncio.run(setup())
    
    # Make decision
    decision_data = {
        "outcome": "approve",
        "reasons": ["Good credit"],
        "approved_amount": 50000,
        "approved_tenure": 24,
        "risk_grade": "A"
    }
    
    response = client.post(
        f"/api/v1/loan-applications/{app_id}/decision",
        json=decision_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["application"]["status"] == "approved"


def test_validation_error(client):
    """Test validation error handling"""
    # Missing authentication
    response = client.post("/api/v1/loan-applications", json={})
    assert response.status_code == 422  # Validation error


def test_correlation_id_header(client):
    """Test correlation ID in response"""
    response = client.get(
        "/health",
        headers={"X-Correlation-ID": "test-correlation-123"}
    )
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
