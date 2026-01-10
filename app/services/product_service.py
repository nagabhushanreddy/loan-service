"""Product service for loan products"""
from typing import List, Optional, Dict, Any
from app.models.schemas import LoanProductResponse
from app.models.enums import LoanProductType
from app.config import config_data


class ProductService:
    """Service for loan product operations"""
    
    def __init__(self):
        self.products = self._initialize_products()
    
    def _initialize_products(self) -> Dict[str, LoanProductResponse]:
        """Initialize loan products from config"""
        products = {}
        product_config = config_data.get("loan_products", {})
        
        product_definitions = [
            {
                "id": "two_wheeler_std",
                "name": "Two Wheeler Loan - Standard",
                "type": LoanProductType.TWO_WHEELER,
                "config_key": "two_wheeler",
                "required_documents": ["identity_proof", "address_proof", "income_proof", "vehicle_quotation"],
                "allowed_purposes": ["new_vehicle", "used_vehicle"]
            },
            {
                "id": "four_wheeler_std",
                "name": "Four Wheeler Loan - Standard",
                "type": LoanProductType.FOUR_WHEELER,
                "config_key": "four_wheeler",
                "required_documents": ["identity_proof", "address_proof", "income_proof", "employment_proof", "vehicle_quotation", "bank_statements"],
                "allowed_purposes": ["new_vehicle", "used_vehicle"]
            },
            {
                "id": "personal_loan_std",
                "name": "Personal Loan - Standard",
                "type": LoanProductType.PERSONAL_LOAN,
                "config_key": "personal_loan",
                "required_documents": ["identity_proof", "address_proof", "income_proof", "employment_proof", "bank_statements"],
                "allowed_purposes": ["education", "medical", "wedding", "home_renovation", "debt_consolidation", "other"]
            },
            {
                "id": "vehicle_loan_commercial",
                "name": "Vehicle Loan - Commercial",
                "type": LoanProductType.VEHICLE_LOAN,
                "config_key": "vehicle_loan",
                "required_documents": ["identity_proof", "address_proof", "income_proof", "business_proof", "vehicle_quotation", "bank_statements", "gst_returns"],
                "allowed_purposes": ["new_commercial_vehicle", "used_commercial_vehicle"]
            }
        ]
        
        for prod_def in product_definitions:
            config_key = prod_def["config_key"]
            prod_config = product_config.get(config_key, {})
            
            product = LoanProductResponse(
                id=prod_def["id"],
                name=prod_def["name"],
                type=prod_def["type"],
                min_amount=prod_config.get("min_amount", 0),
                max_amount=prod_config.get("max_amount", 0),
                min_tenure=prod_config.get("min_tenure", 0),
                max_tenure=prod_config.get("max_tenure", 0),
                interest_rate_min=prod_config.get("interest_rate_min", 0),
                interest_rate_max=prod_config.get("interest_rate_max", 0),
                max_ltv=prod_config.get("max_ltv", 0),
                fees={
                    "processing_fee_percent": 2.0,
                    "documentation_fee": 500.0,
                    "prepayment_penalty_percent": 3.0
                },
                required_documents=prod_def["required_documents"],
                eligibility_rules=config_data.get("eligibility", {}),
                allowed_purposes=prod_def["allowed_purposes"],
                is_active=True
            )
            products[product.id] = product
        
        return products
    
    def get_all_products(self) -> List[LoanProductResponse]:
        """Get all active loan products"""
        return [p for p in self.products.values() if p.is_active]
    
    def get_product(self, product_id: str) -> Optional[LoanProductResponse]:
        """Get specific loan product"""
        return self.products.get(product_id)
    
    def validate_product_params(
        self,
        product_id: str,
        amount: float,
        tenure: int
    ) -> tuple[bool, List[str]]:
        """Validate loan parameters against product rules"""
        product = self.get_product(product_id)
        if not product:
            return False, ["Invalid product ID"]
        
        errors = []
        
        if amount < product.min_amount:
            errors.append(f"Amount must be at least {product.min_amount}")
        if amount > product.max_amount:
            errors.append(f"Amount must not exceed {product.max_amount}")
        if tenure < product.min_tenure:
            errors.append(f"Tenure must be at least {product.min_tenure} months")
        if tenure > product.max_tenure:
            errors.append(f"Tenure must not exceed {product.max_tenure} months")
        
        return len(errors) == 0, errors


product_service = ProductService()
