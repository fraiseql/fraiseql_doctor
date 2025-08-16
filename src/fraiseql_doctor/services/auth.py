"""Authentication handling for various auth types."""
from abc import ABC, abstractmethod
from typing import Dict, Any
import base64
from datetime import datetime, timedelta

from fraiseql_doctor.models.endpoint import Endpoint, AuthType


class AuthProvider(ABC):
    """Abstract base for authentication providers."""
    
    @abstractmethod
    async def get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        pass
    
    @abstractmethod
    async def is_valid(self) -> bool:
        """Check if authentication is still valid."""
        pass


class BearerTokenAuth(AuthProvider):
    """Bearer token authentication."""
    
    def __init__(self, token: str, expires_at: datetime | None = None):
        self.token = token
        self.expires_at = expires_at
    
    async def get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}
    
    async def is_valid(self) -> bool:
        if self.expires_at:
            return datetime.utcnow() < self.expires_at
        return True


class APIKeyAuth(AuthProvider):
    """API key authentication."""
    
    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        self.api_key = api_key
        self.header_name = header_name
    
    async def get_headers(self) -> Dict[str, str]:
        return {self.header_name: self.api_key}
    
    async def is_valid(self) -> bool:
        return True


class BasicAuth(AuthProvider):
    """Basic authentication."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    async def get_headers(self) -> Dict[str, str]:
        credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}
    
    async def is_valid(self) -> bool:
        return True


class NoAuth(AuthProvider):
    """No authentication provider."""
    
    async def get_headers(self) -> Dict[str, str]:
        return {}
    
    async def is_valid(self) -> bool:
        return True


def create_auth_provider(endpoint: Endpoint) -> AuthProvider:
    """Factory function to create appropriate auth provider."""
    auth_config = endpoint.auth_config or {}
    
    match endpoint.auth_type:
        case AuthType.BEARER:
            return BearerTokenAuth(
                token=auth_config["token"],
                expires_at=auth_config.get("expires_at")
            )
        case AuthType.API_KEY:
            return APIKeyAuth(
                api_key=auth_config["api_key"],
                header_name=auth_config.get("header_name", "X-API-Key")
            )
        case AuthType.BASIC:
            return BasicAuth(
                username=auth_config["username"],
                password=auth_config["password"]
            )
        case AuthType.NONE | _:
            return NoAuth()