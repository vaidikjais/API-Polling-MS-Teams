"""
Configuration management for the FastAPI application.
Loads environment variables and provides centralized settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Microsoft Azure AD Configuration
    tenant_id: str
    client_id: str
    client_secret: str
    
    # API Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Microsoft Graph API
    graph_api_base_url: str = "https://graph.microsoft.com/v1.0"
    auth_url_template: str = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    graph_scope: str = "https://graph.microsoft.com/.default"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()
