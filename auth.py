"""
Authentication module for Microsoft Graph API.
Handles OAuth 2.0 Client Credentials flow with token caching.
"""
import httpx
import time
from typing import Optional, Dict
from threading import Lock
from config import settings


class TokenCache:
    """In-memory token cache with expiry tracking."""
    
    def __init__(self):
        self._token: Optional[str] = None
        self._expiry: float = 0
        self._lock = Lock()
    
    def get_token(self) -> Optional[str]:
        """Get cached token if still valid."""
        with self._lock:
            if self._token and time.time() < self._expiry:
                return self._token
            return None
    
    def set_token(self, token: str, expires_in: int):
        """
        Cache token with expiry time.
        
        Args:
            token: Access token string
            expires_in: Token lifetime in seconds
        """
        with self._lock:
            self._token = token
            # Subtract 5 minutes (300 seconds) as buffer before actual expiry
            self._expiry = time.time() + expires_in - 300


# Global token cache instance
_token_cache = TokenCache()


async def get_access_token() -> str:
    """
    Obtain access token from Microsoft Identity platform using Client Credentials flow.
    
    Returns:
        str: Valid access token
        
    Raises:
        httpx.HTTPStatusError: If authentication fails
        Exception: For other authentication errors
    """
    # Check cache first
    cached_token = _token_cache.get_token()
    if cached_token:
        return cached_token
    
    # Request new token
    auth_url = settings.auth_url_template.format(tenant_id=settings.tenant_id)
    
    token_data = {
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "scope": settings.graph_scope,
        "grant_type": "client_credentials"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                auth_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            token_response = response.json()
            access_token = token_response["access_token"]
            expires_in = token_response.get("expires_in", 3600)
            
            # Cache the token
            _token_cache.set_token(access_token, expires_in)
            
            return access_token
            
    except httpx.HTTPStatusError as e:
        # TODO: Add structured logging for production
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text
        
        raise Exception(f"Authentication failed: {e.response.status_code} - {error_detail}")
    
    except Exception as e:
        # TODO: Add proper error tracking/monitoring
        raise Exception(f"Failed to obtain access token: {str(e)}")


def clear_token_cache():
    """Clear the cached token. Useful for testing or forced refresh."""
    global _token_cache
    _token_cache = TokenCache()
