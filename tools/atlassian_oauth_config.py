"""
Atlassian OAuth 2.0 Configuration Manager

This module provides configuration management for Atlassian OAuth authentication,
including loading credentials from environment variables and generating authorization URLs.
"""

import os
import secrets
from typing import List, Optional
from urllib.parse import urlencode


class AtlassianOAuthConfig:
    """OAuth configuration for Atlassian services (JIRA and Confluence)."""

    # Atlassian OAuth endpoints
    AUTHORIZATION_ENDPOINT = "https://auth.atlassian.com/authorize"
    TOKEN_ENDPOINT = "https://auth.atlassian.com/oauth/token"
    ACCESSIBLE_RESOURCES_ENDPOINT = (
        "https://api.atlassian.com/oauth/token/accessible-resources"
    )

    # Default OAuth scopes for JIRA and Confluence
    DEFAULT_SCOPES = [
        # Jira scopes
        "read:jira-work",
        "write:jira-work",
        "read:jira-user",
        # Confluence granular scopes (read-only)
        "read:page:confluence",
        "read:blogpost:confluence",
        "read:space:confluence",
        "read:content:confluence",
        # General
        "offline_access",
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
        agentcore_identity_arn: Optional[str] = None,
        demo_user_id: str = "yetanotherarslan@gmail.com",
    ):
        """
        Initialize Atlassian OAuth configuration.

        Args:
            client_id: OAuth client ID from Atlassian
            client_secret: OAuth client secret from Atlassian
            redirect_uri: Callback URL for OAuth flow
            scopes: List of OAuth scopes (uses defaults if not provided)
            agentcore_identity_arn: AWS AgentCore Identity ARN for token storage
            demo_user_id: User ID for demo implementation

        Raises:
            ValueError: If required configuration values are missing
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or self.DEFAULT_SCOPES
        self.agentcore_identity_arn = agentcore_identity_arn
        self.demo_user_id = demo_user_id

        # Validate required configuration
        self._validate()

    def _validate(self) -> None:
        """
        Validate that all required configuration values are present.

        Raises:
            ValueError: If any required configuration value is missing or invalid
        """
        if not self.client_id:
            raise ValueError("ATLASSIAN_OAUTH_CLIENT_ID is required")

        if not self.client_secret:
            raise ValueError("ATLASSIAN_OAUTH_CLIENT_SECRET is required")

        if not self.redirect_uri:
            raise ValueError("ATLASSIAN_OAUTH_REDIRECT_URI is required")

        if not self.redirect_uri.startswith(
            "https://"
        ) and not self.redirect_uri.startswith("http://localhost"):
            raise ValueError(
                "ATLASSIAN_OAUTH_REDIRECT_URI must use HTTPS (or http://localhost for development)"
            )

        if not self.scopes:
            raise ValueError("At least one OAuth scope is required")

    @classmethod
    def from_env(cls) -> "AtlassianOAuthConfig":
        """
        Load OAuth configuration from environment variables.

        Environment variables:
            - ATLASSIAN_OAUTH_CLIENT_ID: OAuth client ID (required)
            - ATLASSIAN_OAUTH_CLIENT_SECRET: OAuth client secret (required)
            - ATLASSIAN_OAUTH_REDIRECT_URI: Callback URL (required)
            - ATLASSIAN_OAUTH_SCOPES: Comma-separated list of scopes (optional)
            - AGENTCORE_IDENTITY_ARN: AWS AgentCore Identity ARN (optional)
            - ATLASSIAN_DEMO_USER_ID: User ID for demo (optional)

        Returns:
            AtlassianOAuthConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        client_id = os.getenv("ATLASSIAN_OAUTH_CLIENT_ID", "").strip()
        client_secret = os.getenv("ATLASSIAN_OAUTH_CLIENT_SECRET", "").strip()
        redirect_uri = os.getenv("ATLASSIAN_OAUTH_REDIRECT_URI", "").strip()

        # Parse scopes from comma-separated string
        scopes_str = os.getenv("ATLASSIAN_OAUTH_SCOPES", "").strip()
        scopes = [s.strip() for s in scopes_str.split(",")] if scopes_str else None

        agentcore_identity_arn = os.getenv("AGENTCORE_IDENTITY_ARN", "").strip() or None
        demo_user_id = os.getenv(
            "ATLASSIAN_DEMO_USER_ID", "yetanotherarslan@gmail.com"
        ).strip()

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            agentcore_identity_arn=agentcore_identity_arn,
            demo_user_id=demo_user_id,
        )

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL for Atlassian.

        Args:
            state: CSRF protection state parameter. If not provided, a random one is generated.

        Returns:
            Complete authorization URL with all required parameters
        """
        # Generate random state if not provided (for CSRF protection)
        if state is None:
            state = secrets.token_urlsafe(32)

        # Build query parameters
        scope_string = " ".join(self.scopes)

        params = {
            "audience": "api.atlassian.com",
            "client_id": self.client_id,
            "scope": scope_string,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
        }

        # Log the scopes being requested
        import logging

        logger = logging.getLogger(__name__)
        logger.info("=" * 80)
        logger.info("Generating OAuth authorization URL")
        logger.info(f"Requesting scopes: {scope_string}")
        logger.info(f"Scopes list: {self.scopes}")
        logger.info("=" * 80)

        # Construct full authorization URL
        auth_url = f"{self.AUTHORIZATION_ENDPOINT}?{urlencode(params)}"

        return auth_url

    def is_configured(self) -> bool:
        """
        Check if OAuth is properly configured.

        Returns:
            True if all required configuration is present, False otherwise
        """
        try:
            self._validate()
            return True
        except ValueError:
            return False

    def __repr__(self) -> str:
        """String representation (without exposing secrets)."""
        return (
            f"AtlassianOAuthConfig("
            f"client_id={self.client_id[:8]}..., "
            f"redirect_uri={self.redirect_uri}, "
            f"scopes={self.scopes}, "
            f"demo_user_id={self.demo_user_id})"
        )
