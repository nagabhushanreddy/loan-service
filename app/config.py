"""Application configuration management"""
from pydantic_settings import BaseSettings
from typing import Optional
import yaml
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "loan-service"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    api_key_header: str = "X-API-Key"
    api_key: str
    
    # Database
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # Redis
    redis_url: str
    redis_pool_size: int = 10
    
    # Idempotency
    idempotency_key_header: str = "Idempotency-Key"
    idempotency_ttl_seconds: int = 86400
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    # External Services
    entity_service_url: str
    document_service_url: str
    authz_service_url: str
    utils_service_url: str
    
    # Service Timeouts
    service_timeout: int = 30
    service_max_retries: int = 3
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config_file() -> dict:
    """Load configuration from YAML file"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


settings = Settings()
config_data = load_config_file()
