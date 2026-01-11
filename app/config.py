"""Application configuration management using utils.config defaults."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from utils import config, init_utils

CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "config"))
init_utils(CONFIG_DIR)


def _get_bool(key: str, default: bool) -> bool:
    value = config.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return bool(value)


def _get_int(key: str, default: int) -> int:
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


REDIS_HOST = config.get("redis.host", "localhost")
REDIS_PORT = _get_int("redis.port", 6379)
REDIS_DB = _get_int("redis.db", 0)


class Settings(BaseSettings):
    """Application settings pulled from config/app.yaml with env overrides."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Application
    app_name: str = config.get("service.name", "loan-service")
    app_version: str = config.get("service.version", "1.0.0")
    host: str = config.get("server.host", "0.0.0.0")
    port: int = _get_int("server.port", 8005)
    workers: int = _get_int("service.workers", 4)

    # Security
    jwt_secret_key: str = config.get("jwt.access_secret", "your-super-secret-access-key-min-32-chars")
    jwt_algorithm: str = config.get("jwt.algorithm", "HS256")
    api_key_header: str = config.get("api_key.header", "X-API-Key")
    api_key: str = config.get("api_key.secret", "change-me")

    # Database
    database_url: str = config.get("database.url", "postgresql+asyncpg://user:password@localhost:5432/loan_db")
    db_pool_size: int = _get_int("database.pool_size", 10)
    db_max_overflow: int = _get_int("database.max_overflow", 20)

    # Redis
    redis_host: str = REDIS_HOST
    redis_port: int = REDIS_PORT
    redis_db: int = REDIS_DB
    redis_password: Optional[str] = config.get("redis.password")
    redis_url: str = config.get("redis.url", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    redis_pool_size: int = _get_int("redis.pool_size", 10)

    # Idempotency
    idempotency_key_header: str = config.get("idempotency.header", "Idempotency-Key")
    idempotency_ttl_seconds: int = _get_int("idempotency.ttl_seconds", 86400)

    # Rate Limiting
    rate_limit_enabled: bool = _get_bool("rate_limiting.enabled", True)
    rate_limit_per_minute: int = _get_int("rate_limiting.max_requests_per_user", 60)

    # External Services
    entity_service_url: str = config.get("external_services.entity_service.url", "http://localhost:8000")
    document_service_url: str = config.get("external_services.document_service.url", "http://localhost:8001")
    authz_service_url: str = config.get("external_services.authz_service.url", "http://localhost:3002")
    utils_service_url: str = config.get("external_services.utils_service.url", "http://localhost:8080")

    # Service Timeouts
    service_timeout: int = _get_int("external_services.timeout", 30)
    service_max_retries: int = _get_int("external_services.max_retries", 3)

    # Logging
    log_level: str = config.get("logging.level", "INFO")
    log_format: str = config.get("logging.format", "json")

    # Environment
    environment: str = config.get("service.environment", "development")


settings = Settings()

# Backward compatibility: expose `config_data` expected by services/tests
class ConfigData:
    def __init__(self, settings_obj: Settings):
        self._settings = settings_obj

        
    def get(self, key: str, default=None):
        # Try to resolve from Settings attributes if present
        if hasattr(self._settings, key):
            return getattr(self._settings, key)
        # Fallback to underlying utils config store
        return config.get(key, default)


config_data = ConfigData(settings)
