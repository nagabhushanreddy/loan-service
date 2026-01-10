"""Tests for product service"""
import pytest
from app.services.product_service import product_service
from app.models.enums import LoanProductType


def test_get_all_products():
    """Test getting all products"""
    products = product_service.get_all_products()
    assert len(products) > 0
    assert all(p.is_active for p in products)


def test_get_specific_product():
    """Test getting specific product"""
    product = product_service.get_product("two_wheeler_std")
    assert product is not None
    assert product.type == LoanProductType.TWO_WHEELER
    assert product.min_amount > 0
    assert product.max_amount > product.min_amount


def test_get_nonexistent_product():
    """Test getting nonexistent product"""
    product = product_service.get_product("nonexistent")
    assert product is None


def test_validate_product_params_valid():
    """Test valid product parameters"""
    valid, errors = product_service.validate_product_params(
        "two_wheeler_std",
        50000,
        24
    )
    assert valid is True
    assert len(errors) == 0


def test_validate_product_params_amount_too_low():
    """Test amount below minimum"""
    valid, errors = product_service.validate_product_params(
        "two_wheeler_std",
        5000,  # Too low
        24
    )
    assert valid is False
    assert len(errors) > 0
    assert any("at least" in e.lower() for e in errors)


def test_validate_product_params_amount_too_high():
    """Test amount above maximum"""
    valid, errors = product_service.validate_product_params(
        "two_wheeler_std",
        500000,  # Too high
        24
    )
    assert valid is False
    assert len(errors) > 0
    assert any("not exceed" in e.lower() for e in errors)


def test_validate_product_params_tenure_invalid():
    """Test invalid tenure"""
    valid, errors = product_service.validate_product_params(
        "two_wheeler_std",
        50000,
        100  # Too long
    )
    assert valid is False
    assert len(errors) > 0


def test_validate_product_params_invalid_product():
    """Test invalid product ID"""
    valid, errors = product_service.validate_product_params(
        "invalid_product",
        50000,
        24
    )
    assert valid is False
    assert "Invalid product" in errors[0]


def test_all_products_have_required_fields():
    """Test all products have required fields"""
    products = product_service.get_all_products()
    for product in products:
        assert product.id
        assert product.name
        assert product.type
        assert product.min_amount >= 0
        assert product.max_amount > product.min_amount
        assert product.min_tenure > 0
        assert product.max_tenure >= product.min_tenure
        assert product.interest_rate_min >= 0
        assert product.interest_rate_max >= product.interest_rate_min
        assert len(product.required_documents) > 0
