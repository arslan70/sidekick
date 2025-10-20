"""
Environment Variable Token Manager for Atlassian OAuth.

This token manager retrieves the access token from an environment variable.
It's used when the token is passed from the Chainlit UI to the agent via metadata.
"""

import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EnvTokenManager:
    """
    Token manager that retrieves access token from environment variable.
    
    This is used when the Chainlit UI passes the user's access token to the agent
    via metadata, and the agent sets it as an environment variable.
    """

    def __init__(self, user_id: str, oauth_config):
        """
        Initialize the environment token manager.
        
        Args:
            user_id: User identifier (for logging)
            oauth_config: OAuth configuration (not used, but kept for compatibility)
        """
        self.user_id = user_id
        self.oauth_config = oauth_config
        logger.info(f"Initialized Environment Token Manager for user: {user_id}")

    async def get_access_token(self) -> Optional[str]:
        """
        Retrieve access token from environment variable.
        
        Returns:
            Access token if available, None otherwise
        """
        token = os.getenv("ATLASSIAN_ACCESS_TOKEN")
        if token:
            logger.info(f"✅ Retrieved access token from environment for user: {self.user_id}")
            return token
        else:
            logger.warning(f"⚠️ No access token in environment for user: {self.user_id}")
            return None

    async def get_refresh_token(self) -> Optional[str]:
        """
        Retrieve refresh token (not supported in this manager).
        
        Returns:
            None (refresh tokens not supported)
        """
        logger.warning("Refresh tokens not supported in EnvTokenManager")
        return None

    async def store_tokens(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: int = 3600,
        token_type: str = "Bearer",
    ) -> bool:
        """
        Store tokens (not supported in this manager).
        
        Returns:
            False (token storage not supported)
        """
        logger.warning("Token storage not supported in EnvTokenManager")
        return False

    async def refresh_access_token(self) -> Optional[str]:
        """
        Refresh access token (not supported in this manager).
        
        Returns:
            None (token refresh not supported)
        """
        logger.warning("Token refresh not supported in EnvTokenManager")
        return None

    async def revoke_tokens(self) -> bool:
        """
        Revoke tokens (not supported in this manager).
        
        Returns:
            False (token revocation not supported)
        """
        logger.warning("Token revocation not supported in EnvTokenManager")
        return False

    async def check_token_status(self) -> Dict[str, any]:
        """
        Check token status.
        
        Returns:
            Dictionary with token status information
        """
        token = await self.get_access_token()
        return {
            "is_valid": token is not None,
            "is_expired": False,  # We don't track expiration
            "expires_at": None,
            "user_id": self.user_id,
        }
