"""
OAuth Flow Handler for Atlassian Authentication.

This module handles the OAuth 2.0 authorization flow for Atlassian services,
including authorization URL generation, callback processing, and authentication
status checking.
"""

import logging
import secrets
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests

# Ensure project root is in sys.path for absolute imports
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.agentcore_token_manager import AgentCoreTokenManager
from tools.atlassian_exceptions import NetworkError, OAuthFlowError
from tools.atlassian_oauth_config import AtlassianOAuthConfig

logger = logging.getLogger(__name__)


class OAuthHandler:
    """
    Handles OAuth flow for Atlassian authentication.

    This class manages the complete OAuth 2.0 authorization flow including:
    - Generating authorization URLs with CSRF protection
    - Processing OAuth callbacks and exchanging authorization codes for tokens
    - Checking authentication status and retrieving user information
    """

    def __init__(
        self, oauth_config: AtlassianOAuthConfig, token_manager: AgentCoreTokenManager
    ):
        """
        Initialize the OAuth handler.

        Args:
            oauth_config: Atlassian OAuth configuration
            token_manager: Token manager for storing and retrieving tokens
        """
        self.oauth_config = oauth_config
        self.token_manager = token_manager
        self._state_cache: Dict[str, datetime] = {}  # Simple in-memory state cache

        logger.info(f"Initialized OAuth handler for user: {token_manager.user_id}")

    def generate_auth_url(self) -> Tuple[str, str]:
        """
        Generate authorization URL with CSRF state parameter.

        This method creates a secure authorization URL for the OAuth flow,
        including a randomly generated state parameter for CSRF protection.

        Returns:
            Tuple[str, str]: A tuple containing:
                - Authorization URL (str): Complete URL to redirect user to
                - State parameter (str): CSRF token to validate callback

        Example:
            >>> handler = OAuthHandler(config, token_manager)
            >>> auth_url, state = handler.generate_auth_url()
            >>> print(f"Redirect user to: {auth_url}")
            >>> # Store state for validation during callback
        """
        # Generate cryptographically secure random state parameter
        state = secrets.token_urlsafe(32)

        # Store state with timestamp for validation (expires after 10 minutes)
        self._state_cache[state] = datetime.utcnow()

        # Generate authorization URL using OAuth config
        auth_url = self.oauth_config.get_authorization_url(state=state)

        logger.info(
            f"Generated authorization URL for user: {self.token_manager.user_id}"
        )
        logger.debug(f"State parameter: {state[:8]}... (truncated)")

        return auth_url, state

    def _validate_state(self, state: str) -> bool:
        """
        Validate state parameter for CSRF protection.

        Args:
            state: State parameter from OAuth callback

        Returns:
            bool: True if state is valid, False otherwise
        """
        if state not in self._state_cache:
            logger.warning(f"Invalid state parameter received: {state[:8]}...")
            return False

        # Check if state has expired (10 minutes)
        state_timestamp = self._state_cache[state]
        age_seconds = (datetime.utcnow() - state_timestamp).total_seconds()

        if age_seconds > 600:  # 10 minutes
            logger.warning(
                f"Expired state parameter: {state[:8]}... (age: {age_seconds}s)"
            )
            del self._state_cache[state]
            return False

        # Remove state after validation (one-time use)
        del self._state_cache[state]
        return True

    async def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange authorization code for tokens.

        This method processes the OAuth callback by:
        1. Validating the state parameter for CSRF protection
        2. Exchanging the authorization code for access and refresh tokens
        3. Retrieving accessible Atlassian resources (cloud ID)
        4. Fetching user information
        5. Storing tokens using AgentCore Token Manager

        Args:
            code: Authorization code from OAuth callback
            state: State parameter from OAuth callback

        Returns:
            Dict[str, Any]: Dictionary containing:
                - success (bool): Whether callback was processed successfully
                - user_info (dict): User information (if successful)
                - cloud_id (str): Atlassian cloud ID (if successful)
                - error (str): Error type (if failed)
                - error_description (str): Detailed error message (if failed)

        Example:
            >>> result = await handler.handle_callback(code="abc123", state="xyz789")
            >>> if result['success']:
            ...     print(f"Authenticated as: {result['user_info']['email']}")
            ... else:
            ...     print(f"Error: {result['error_description']}")
        """
        try:
            # Validate state parameter for CSRF protection
            if not self._validate_state(state):
                error_msg = "Invalid or expired state parameter"
                logger.error(f"OAuth callback validation failed: {error_msg}")
                return {
                    "success": False,
                    "error": "invalid_state",
                    "error_description": error_msg,
                }

            logger.info(
                f"Processing OAuth callback for user: {self.token_manager.user_id}"
            )

            # Exchange authorization code for tokens
            token_response = await self._exchange_code_for_tokens(code)

            if not token_response.get("success"):
                return token_response

            # Extract token information
            access_token = token_response["access_token"]
            refresh_token = token_response["refresh_token"]
            expires_in = token_response["expires_in"]
            token_type = token_response.get("token_type", "Bearer")

            # Retrieve accessible Atlassian resources (cloud ID)
            resources_result = await self._get_accessible_resources(access_token)

            if not resources_result.get("success"):
                logger.warning(
                    "Failed to retrieve accessible resources, continuing anyway"
                )
                cloud_id = None
            else:
                cloud_id = resources_result.get("cloud_id")

            # Retrieve user information
            user_info_result = await self._get_user_info(access_token, cloud_id)

            if not user_info_result.get("success"):
                logger.warning("Failed to retrieve user info, continuing anyway")
                user_info = {"email": self.token_manager.user_id}
            else:
                user_info = user_info_result.get("user_info", {})

            # Store tokens using AgentCore Token Manager
            store_success = await self.token_manager.store_tokens(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                token_type=token_type,
            )

            if not store_success:
                error_msg = "Failed to store tokens in AgentCore Identity"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": "storage_error",
                    "error_description": error_msg,
                }

            logger.info(
                f"Successfully completed OAuth flow for user: {self.token_manager.user_id}"
            )

            return {
                "success": True,
                "user_info": user_info,
                "cloud_id": cloud_id,
                "expires_in": expires_in,
            }

        except OAuthFlowError as e:
            logger.error(f"OAuth flow error: {e.message}")
            return {
                "success": False,
                "error": "oauth_flow_error",
                "error_description": e.get_user_message(),
            }

        except NetworkError as e:
            logger.error(f"Network error during OAuth: {e.message}")
            return {
                "success": False,
                "error": "network_error",
                "error_description": e.get_user_message(),
            }

        except Exception as e:
            error_msg = f"Unexpected error during OAuth callback: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": "unexpected_error",
                "error_description": error_msg,
            }

    async def _exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Dict[str, Any]: Token response or error information
        """
        try:
            token_url = self.oauth_config.TOKEN_ENDPOINT

            payload = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.oauth_config.redirect_uri,
                "client_id": self.oauth_config.client_id,
                "client_secret": self.oauth_config.client_secret,
            }

            headers = {"Content-Type": "application/json"}

            logger.debug(f"Exchanging authorization code for tokens at: {token_url}")

            response = requests.post(
                token_url, json=payload, headers=headers, timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()

                access_token = token_data.get("access_token")
                refresh_token = token_data.get(
                    "refresh_token"
                )  # May be None if offline_access not requested
                expires_in = token_data.get("expires_in", 3600)
                token_type = token_data.get("token_type", "Bearer")

                if not access_token:
                    error_msg = "Missing access_token in response"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": "invalid_response",
                        "error_description": error_msg,
                    }

                if not refresh_token:
                    logger.warning("No refresh_token in response - using dummy token")
                    refresh_token = "no-refresh-token"

                logger.info("Successfully exchanged authorization code for tokens")

                return {
                    "success": True,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": expires_in,
                    "token_type": token_type,
                }

            else:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass

                error = error_data.get("error", "token_exchange_failed")
                error_description = error_data.get(
                    "error_description", f"HTTP {response.status_code}"
                )

                logger.error(f"Token exchange failed: {error} - {error_description}")

                return {
                    "success": False,
                    "error": error,
                    "error_description": error_description,
                    "status_code": response.status_code,
                }

        except requests.exceptions.Timeout:
            error_msg = "Token exchange request timed out"
            logger.error(error_msg)
            raise NetworkError(error_msg, details={"endpoint": "token_exchange"})

        except requests.exceptions.RequestException as e:
            error_msg = f"Request error during token exchange: {str(e)}"
            logger.error(error_msg)
            raise NetworkError(error_msg, details={"endpoint": "token_exchange"})

        except Exception as e:
            error_msg = f"Unexpected error during token exchange: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": "unexpected_error",
                "error_description": error_msg,
            }

    async def _get_accessible_resources(self, access_token: str) -> Dict[str, Any]:
        """
        Retrieve accessible Atlassian resources (cloud ID).

        Args:
            access_token: OAuth access token

        Returns:
            Dict[str, Any]: Resources information or error
        """
        try:
            resources_url = self.oauth_config.ACCESSIBLE_RESOURCES_ENDPOINT

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            logger.debug("Retrieving accessible Atlassian resources")

            response = requests.get(resources_url, headers=headers, timeout=10)

            if response.status_code == 200:
                resources = response.json()

                if not resources or len(resources) == 0:
                    error_msg = "No accessible Atlassian resources found"
                    logger.warning(error_msg)
                    return {
                        "success": False,
                        "error": "no_resources",
                        "error_description": error_msg,
                    }

                # Use the first resource (typically the user's primary workspace)
                first_resource = resources[0]
                cloud_id = first_resource.get("id")
                resource_name = first_resource.get("name", "Unknown")

                logger.info(
                    f"Found accessible resource: {resource_name} (cloud_id: {cloud_id})"
                )

                return {
                    "success": True,
                    "cloud_id": cloud_id,
                    "resource_name": resource_name,
                    "resources": resources,
                }

            else:
                error_msg = f"Failed to retrieve resources: HTTP {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": "resources_request_failed",
                    "error_description": error_msg,
                }

        except Exception as e:
            error_msg = f"Error retrieving accessible resources: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": "unexpected_error",
                "error_description": error_msg,
            }

    async def _get_user_info(
        self, access_token: str, cloud_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Retrieve authenticated user information from JIRA.

        Args:
            access_token: OAuth access token
            cloud_id: Atlassian cloud ID

        Returns:
            Dict[str, Any]: User information or error
        """
        try:
            if not cloud_id:
                logger.warning("No cloud_id available, skipping user info retrieval")
                return {
                    "success": False,
                    "error": "no_cloud_id",
                    "error_description": "Cloud ID not available",
                }

            # Use JIRA API to get current user information
            user_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            logger.debug("Retrieving user information from JIRA")

            response = requests.get(user_url, headers=headers, timeout=10)

            if response.status_code == 200:
                user_data = response.json()

                user_info = {
                    "account_id": user_data.get("accountId"),
                    "email": user_data.get("emailAddress"),
                    "display_name": user_data.get("displayName"),
                    "avatar_url": user_data.get("avatarUrls", {}).get("48x48"),
                    "active": user_data.get("active", True),
                }

                logger.info(
                    f"Retrieved user info: {user_info.get('display_name')} ({user_info.get('email')})"
                )

                return {"success": True, "user_info": user_info}

            else:
                error_msg = f"Failed to retrieve user info: HTTP {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": "user_info_request_failed",
                    "error_description": error_msg,
                }

        except Exception as e:
            error_msg = f"Error retrieving user info: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": "unexpected_error",
                "error_description": error_msg,
            }

    async def check_auth_status(self) -> Dict[str, Any]:
        """
        Check current authentication status and retrieve user information.

        This method verifies whether the user has valid OAuth tokens and
        retrieves information about the authenticated user and token expiration.

        Returns:
            Dict[str, Any]: Dictionary containing:
                - is_authenticated (bool): Whether user has valid tokens
                - user_id (str): User identifier
                - expires_at (str): Token expiration timestamp (ISO format)
                - is_expired (bool): Whether token has expired
                - user_info (dict): User information (if available)
                - cloud_id (str): Atlassian cloud ID (if available)
                - error (str): Error message (if check failed)

        Example:
            >>> status = await handler.check_auth_status()
            >>> if status['is_authenticated']:
            ...     print(f"Authenticated until: {status['expires_at']}")
            ... else:
            ...     print("Not authenticated")
        """
        try:
            logger.info(
                f"Checking authentication status for user: {self.token_manager.user_id}"
            )

            # Check token status using token manager
            token_status = await self.token_manager.check_token_status()

            is_valid = token_status.get("is_valid", False)
            is_expired = token_status.get("is_expired", True)
            expires_at = token_status.get("expires_at")

            # Base response
            auth_status = {
                "is_authenticated": is_valid and not is_expired,
                "user_id": self.token_manager.user_id,
                "expires_at": expires_at,
                "is_expired": is_expired,
            }

            # If not authenticated, return early
            if not auth_status["is_authenticated"]:
                logger.info(f"User {self.token_manager.user_id} is not authenticated")
                auth_status["error"] = token_status.get("error", "No valid tokens")
                return auth_status

            # Try to retrieve additional user information
            try:
                access_token = await self.token_manager.get_access_token()

                if access_token:
                    # Get accessible resources
                    resources_result = await self._get_accessible_resources(
                        access_token
                    )

                    if resources_result.get("success"):
                        cloud_id = resources_result.get("cloud_id")
                        auth_status["cloud_id"] = cloud_id
                        auth_status["resource_name"] = resources_result.get(
                            "resource_name"
                        )

                        # Get user info
                        user_info_result = await self._get_user_info(
                            access_token, cloud_id
                        )

                        if user_info_result.get("success"):
                            auth_status["user_info"] = user_info_result.get("user_info")

            except Exception as e:
                logger.warning(f"Failed to retrieve additional user information: {e}")
                # Continue without additional info

            logger.info(
                f"Authentication status for {self.token_manager.user_id}: authenticated={auth_status['is_authenticated']}"
            )

            return auth_status

        except Exception as e:
            error_msg = f"Error checking authentication status: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "is_authenticated": False,
                "user_id": self.token_manager.user_id,
                "expires_at": None,
                "is_expired": True,
                "error": error_msg,
            }
