"""Authentication and authorization utilities"""
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from typing import Optional
from app.config import settings
from app.models.enums import UserRole


security_bearer = HTTPBearer()
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


class AuthenticatedUser:
    """Authenticated user model"""
    
    def __init__(self, user_id: str, tenant_id: str, roles: list[str], email: Optional[str] = None):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.roles = roles
        self.email = email
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role"""
        return role.value in self.roles


def decode_jwt_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer)
) -> AuthenticatedUser:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    roles = payload.get("roles", [])
    email = payload.get("email")
    
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return AuthenticatedUser(user_id, tenant_id, roles, email)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    """Verify API key for service-to-service calls"""
    if api_key == settings.api_key:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key"
    )


def require_role(required_role: UserRole):
    """Dependency to require specific role"""
    async def role_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' required"
            )
        return user
    return role_checker
