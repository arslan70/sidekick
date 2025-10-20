"""
Simple in-memory token manager for development/testing.

This is a simplified token manager that stores tokens in memory instead of AWS AgentCore.
Use this for local development and testing. For production, use AgentCoreTokenManager.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SimpleTokenManager:
    """
    Simple in-memory token manager for development.

    WARNING: Tokens are stored in memory and will be lost when the application restarts.
    This is suitable for development/testing only. For production, use AgentCoreTokenManager.
    """

    # Class-level storage (shared across instances)
    _token_storage: Dict[str, Dict[str, Any]] = {}

    def __init__(self, identity_arn: str, user_id: str, oauth_config=None):
        """
        Initialize the Simple Token Manager.

        Args:
            identity_arn: Not used in simple manager (for compatibility)
            user_id: User identifier for token association
            oauth_config: Optional AtlassianOAuthConfig instance for token refresh
        """
        self.identity_arn = identity_arn
        self.user_id = user_id
        self.oauth_config = oauth_config

        logger.info(f"Initialized Simple Token Manager for user: {user_id}")
        logger.warning(
            "Using in-memory token storage - tokens will be lost on restart!"
        )

    async def store_tokens(
        self,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        token_type: str = "Bearer",
    ) -> bool:
        """
        Store OAuth tokens in memory.

        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token expiration time in seconds
            token_type: Token type (default: "Bearer")

        Returns:
            bool: True if tokens were stored successfully
        """
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            # Store tokens in class-level dictionary
            self._token_storage[self.user_id] = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": token_type,
                "expires_at": expires_at,
                "stored_at": datetime.utcnow(),
            }

            logger.info(f"Successfully stored tokens for user: {self.user_id}")
            logger.info(f"Total users in storage: {len(self._token_storage)}")
            logger.info(f"Storage keys: {list(self._token_storage.keys())}")
            logger.debug(f"Token expires at: {expires_at.isoformat()}")
            return True

        except Exception as e:
            logger.error(f"Error storing tokens: {e}", exc_info=True)
            return False

    async def get_access_token(self) -> Optional[str]:
        """
        Retrieve current access token from memory.

        Returns:
            Optional[str]: Access token if available and valid, None otherwise
        """
        try:
            logger.debug(f"Looking for tokens for user: {self.user_id}")
            logger.debug(
                f"Available users in storage: {list(self._token_storage.keys())}"
            )
            token_data = self._token_storage.get(self.user_id)

            if not token_data:
                logger.info(f"No tokens found for user: {self.user_id}")
                return None

            # Check if token is expired
            expires_at = token_data.get("expires_at")
            if expires_at and datetime.utcnow() >= expires_at:
                logger.warning(f"Access token expired for user: {self.user_id}")
                return None

            access_token = token_data.get("access_token")

            if access_token:
                logger.info(
                    f"Successfully retrieved access token for user: {self.user_id}"
                )
                # Print token to console for debugging (first time only)
                if not hasattr(self, "_token_printed"):
                    logger.info("=" * 80)
                    logger.info("ACCESS TOKEN (for debugging):")
                    logger.info(access_token)
                    logger.info("=" * 80)
                    logger.info("To check scopes, run:")
                    logger.info(f"  bash scripts/check_token_scopes.sh {access_token}")
                    logger.info("=" * 80)
                    self._token_printed = True
                return access_token
            else:
                logger.warning(f"No access token found for user: {self.user_id}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving access token: {e}", exc_info=True)
            return None

    async def get_refresh_token(self) -> Optional[str]:
        """
        Retrieve refresh token from memory.

        Returns:
            Optional[str]: Refresh token if available, None otherwise
        """
        try:
            token_data = self._token_storage.get(self.user_id)

            if not token_data:
                logger.info(f"No tokens found for user: {self.user_id}")
                return None

            refresh_token = token_data.get("refresh_token")

            if refresh_token:
                logger.info(
                    f"Successfully retrieved refresh token for user: {self.user_id}"
                )
                return refresh_token
            else:
                logger.warning(f"No refresh token found for user: {self.user_id}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving refresh token: {e}", exc_info=True)
            return None

    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token using the refresh token.

        Returns:
            Dict[str, Any]: Dictionary containing success status and token info or error
        """
        try:
            # Validate that OAuth config is available
            if not self.oauth_config:
                error_msg = "OAuth configuration is required for token refresh"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": "configuration_error",
                    "error_description": error_msg,
                }

            # Retrieve the refresh token
            refresh_token = await self.get_refresh_token()

            if not refresh_token:
                error_msg = f"No refresh token available for user: {self.user_id}"
                logger.warning(error_msg)
                return {
                    "success": False,
                    "error": "no_refresh_token",
                    "error_description": error_msg,
                }

            logger.info(f"Attempting to refresh access token for user: {self.user_id}")

            # Import here to avoid circular dependency
            import requests

            # Prepare token refresh request
            token_url = self.oauth_config.TOKEN_ENDPOINT

            payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.oauth_config.client_id,
                "client_secret": self.oauth_config.client_secret,
            }

            headers = {"Content-Type": "application/json"}

            # Make POST request to Atlassian token endpoint
            response = requests.post(
                token_url, json=payload, headers=headers, timeout=10
            )

            # Check if request was successful
            if response.status_code == 200:
                token_data = response.json()

                # Extract token information
                new_access_token = token_data.get("access_token")
                new_refresh_token = token_data.get("refresh_token", refresh_token)
                expires_in = token_data.get("expires_in", 3600)
                token_type = token_data.get("token_type", "Bearer")

                if not new_access_token:
                    error_msg = "No access token in refresh response"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": "invalid_response",
                        "error_description": error_msg,
                    }

                # Store the new tokens
                store_success = await self.store_tokens(
                    access_token=new_access_token,
                    refresh_token=new_refresh_token,
                    expires_in=expires_in,
                    token_type=token_type,
                )

                if store_success:
                    logger.info(
                        f"Successfully refreshed and stored tokens for user: {self.user_id}"
                    )
                    return {
                        "success": True,
                        "access_token": new_access_token,
                        "expires_in": expires_in,
                        "token_type": token_type,
                    }
                else:
                    error_msg = "Failed to store refreshed tokens"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": "storage_error",
                        "error_description": error_msg,
                    }

            else:
                # Handle error response
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass

                error = error_data.get("error", "unknown_error")
                error_description = error_data.get(
                    "error_description", f"HTTP {response.status_code}"
                )

                logger.error(
                    f"Token refresh failed for user {self.user_id}: "
                    f"{error} - {error_description} (status: {response.status_code})"
                )

                return {
                    "success": False,
                    "error": error,
                    "error_description": error_description,
                    "status_code": response.status_code,
                }

        except Exception as e:
            error_msg = f"Unexpected error during token refresh: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": "unexpected_error",
                "error_description": error_msg,
            }

    async def check_token_status(self) -> Dict[str, Any]:
        """
        Check if valid tokens exist and their expiration status.

        Returns:
            Dict[str, Any]: Dictionary containing token status information
        """
        try:
            token_data = self._token_storage.get(self.user_id)

            if not token_data:
                logger.info(f"No tokens found for user: {self.user_id}")
                return {
                    "is_valid": False,
                    "expires_at": None,
                    "is_expired": True,
                    "user_id": self.user_id,
                    "error": "No tokens found",
                }

            # Check if token is expired
            expires_at = token_data.get("expires_at")
            is_expired = datetime.utcnow() >= expires_at if expires_at else True

            status = {
                "is_valid": not is_expired,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "is_expired": is_expired,
                "user_id": self.user_id,
            }

            logger.info(
                f"Token status for user {self.user_id}: valid={status['is_valid']}, expired={is_expired}"
            )
            return status

        except Exception as e:
            logger.error(f"Error checking token status: {e}", exc_info=True)
            return {
                "is_valid": False,
                "expires_at": None,
                "is_expired": True,
                "user_id": self.user_id,
                "error": f"Error: {str(e)}",
            }

    async def revoke_tokens(self) -> bool:
        """
        Revoke and delete tokens from memory.

        Returns:
            bool: True if tokens were revoked successfully
        """
        try:
            if self.user_id in self._token_storage:
                del self._token_storage[self.user_id]
                logger.info(f"Successfully revoked tokens for user: {self.user_id}")
            else:
                logger.info(f"No tokens to revoke for user: {self.user_id}")

            return True

        except Exception as e:
            logger.error(f"Error revoking tokens: {e}", exc_info=True)
            return False
