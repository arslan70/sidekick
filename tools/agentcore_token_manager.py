"""
AWS AgentCore Identity Token Manager for Atlassian OAuth.

This module provides token management functionality using AWS Bedrock AgentCore Identity
to securely store, retrieve, and manage OAuth tokens for Atlassian services.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import boto3
import requests
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class AgentCoreTokenManager:
    """
    Manages OAuth tokens using AWS AgentCore Identity.

    This class provides methods to store, retrieve, refresh, and revoke OAuth tokens
    for Atlassian services using AWS Bedrock AgentCore Identity service.
    """

    def __init__(self, identity_arn: str, user_id: str, oauth_config=None):
        """
        Initialize the AgentCore Token Manager.

        Args:
            identity_arn: AWS AgentCore Identity resource ARN
            user_id: User identifier for token association
            oauth_config: Optional AtlassianOAuthConfig instance for token refresh
        """
        self.identity_arn = identity_arn
        self.user_id = user_id
        self.oauth_config = oauth_config

        try:
            self.bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime")
            logger.info(f"Initialized AgentCore Token Manager for user: {user_id}")
        except Exception as e:
            logger.error(f"Failed to initialize boto3 client: {e}")
            raise

    async def store_tokens(
        self,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        token_type: str = "Bearer",
    ) -> bool:
        """
        Store OAuth tokens in AgentCore Identity.

        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token expiration time in seconds
            token_type: Token type (default: "Bearer")

        Returns:
            bool: True if tokens were stored successfully, False otherwise

        Raises:
            ClientError: If AWS API call fails
        """
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            # Prepare token data for storage
            token_data = {
                "accessToken": access_token,
                "refreshToken": refresh_token,
                "tokenType": token_type,
                "expiresAt": expires_at.isoformat(),
                "userId": self.user_id,
            }

            # Store tokens using AgentCore Identity
            # Note: The actual API call structure depends on AWS AgentCore Identity implementation
            # This is a placeholder for the actual implementation
            _ = self.bedrock_agent_runtime_client.invoke_agent(
                agentId=self.identity_arn,
                sessionId=f"oauth-session-{self.user_id}",
                inputText=f"STORE_TOKENS:{token_data}",
            )

            logger.info(f"Successfully stored tokens for user: {self.user_id}")
            logger.debug(f"Token expires at: {expires_at.isoformat()}")
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(
                f"AWS ClientError storing tokens: {error_code} - {error_message}"
            )
            raise
        except BotoCoreError as e:
            logger.error(f"BotoCoreError storing tokens: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error storing tokens: {e}", exc_info=True)
            return False

    async def get_access_token(self) -> Optional[str]:
        """
        Retrieve current access token from AgentCore Identity.

        Returns:
            Optional[str]: Access token if available and valid, None otherwise

        Raises:
            ClientError: If AWS API call fails
        """
        try:
            # Retrieve token data from AgentCore Identity
            response = self.bedrock_agent_runtime_client.invoke_agent(
                agentId=self.identity_arn,
                sessionId=f"oauth-session-{self.user_id}",
                inputText=f"GET_ACCESS_TOKEN:{self.user_id}",
            )

            # Parse response to extract access token
            # Note: Actual parsing depends on AgentCore Identity response format
            access_token = response.get("accessToken")

            if access_token:
                logger.info(
                    f"Successfully retrieved access token for user: {self.user_id}"
                )
                return access_token
            else:
                logger.warning(f"No access token found for user: {self.user_id}")
                return None

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "ResourceNotFoundException":
                logger.info(f"No tokens found for user: {self.user_id}")
                return None
            logger.error(f"AWS ClientError retrieving access token: {error_code}")
            raise
        except BotoCoreError as e:
            logger.error(f"BotoCoreError retrieving access token: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving access token: {e}", exc_info=True
            )
            return None

    async def get_refresh_token(self) -> Optional[str]:
        """
        Retrieve refresh token from AgentCore Identity.

        Returns:
            Optional[str]: Refresh token if available, None otherwise

        Raises:
            ClientError: If AWS API call fails
        """
        try:
            # Retrieve token data from AgentCore Identity
            response = self.bedrock_agent_runtime_client.invoke_agent(
                agentId=self.identity_arn,
                sessionId=f"oauth-session-{self.user_id}",
                inputText=f"GET_REFRESH_TOKEN:{self.user_id}",
            )

            # Parse response to extract refresh token
            refresh_token = response.get("refreshToken")

            if refresh_token:
                logger.info(
                    f"Successfully retrieved refresh token for user: {self.user_id}"
                )
                return refresh_token
            else:
                logger.warning(f"No refresh token found for user: {self.user_id}")
                return None

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "ResourceNotFoundException":
                logger.info(f"No tokens found for user: {self.user_id}")
                return None
            logger.error(f"AWS ClientError retrieving refresh token: {error_code}")
            raise
        except BotoCoreError as e:
            logger.error(f"BotoCoreError retrieving refresh token: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving refresh token: {e}", exc_info=True
            )
            return None

    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token using the refresh token.

        This method implements the OAuth token refresh flow by:
        1. Retrieving the current refresh token from AgentCore Identity
        2. Making a POST request to Atlassian's token endpoint with refresh_token grant type
        3. Updating the stored tokens in AgentCore Identity with the new tokens

        Returns:
            Dict[str, Any]: Dictionary containing:
                - success (bool): Whether refresh was successful
                - access_token (str): New access token (if successful)
                - expires_in (int): Token expiration time in seconds (if successful)
                - error (str): Error message (if failed)
                - error_description (str): Detailed error description (if failed)

        Raises:
            ValueError: If OAuth config is not provided or refresh token is not available
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
                new_refresh_token = token_data.get(
                    "refresh_token", refresh_token
                )  # Use old if not provided
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

                # Store the new tokens in AgentCore Identity
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
                # Handle error response from Atlassian
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

        except requests.exceptions.Timeout:
            error_msg = "Token refresh request timed out"
            logger.error(f"{error_msg} for user: {self.user_id}")
            return {
                "success": False,
                "error": "timeout",
                "error_description": error_msg,
            }

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error during token refresh: {str(e)}"
            logger.error(f"{error_msg} for user: {self.user_id}")
            return {
                "success": False,
                "error": "connection_error",
                "error_description": error_msg,
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"Request error during token refresh: {str(e)}"
            logger.error(f"{error_msg} for user: {self.user_id}")
            return {
                "success": False,
                "error": "request_error",
                "error_description": error_msg,
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(
                f"AWS ClientError during token refresh: {error_code} - {error_message}"
            )
            return {
                "success": False,
                "error": "aws_error",
                "error_description": f"AWS error: {error_code} - {error_message}",
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
            Dict[str, Any]: Dictionary containing:
                - is_valid (bool): Whether valid tokens exist
                - expires_at (str): Token expiration timestamp (ISO format)
                - is_expired (bool): Whether token has expired
                - user_id (str): Associated user ID
                - error (str): Error message if check failed

        Raises:
            ClientError: If AWS API call fails
        """
        try:
            # Retrieve token status from AgentCore Identity
            response = self.bedrock_agent_runtime_client.invoke_agent(
                agentId=self.identity_arn,
                sessionId=f"oauth-session-{self.user_id}",
                inputText=f"CHECK_TOKEN_STATUS:{self.user_id}",
            )

            # Parse response to extract token status
            expires_at_str = response.get("expiresAt")

            if not expires_at_str:
                logger.info(f"No tokens found for user: {self.user_id}")
                return {
                    "is_valid": False,
                    "expires_at": None,
                    "is_expired": True,
                    "user_id": self.user_id,
                    "error": "No tokens found",
                }

            # Check if token is expired
            expires_at = datetime.fromisoformat(expires_at_str)
            is_expired = datetime.utcnow() >= expires_at

            status = {
                "is_valid": not is_expired,
                "expires_at": expires_at_str,
                "is_expired": is_expired,
                "user_id": self.user_id,
            }

            logger.info(
                f"Token status for user {self.user_id}: valid={status['is_valid']}, expired={is_expired}"
            )
            return status

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            if error_code == "ResourceNotFoundException":
                logger.info(f"No tokens found for user: {self.user_id}")
                return {
                    "is_valid": False,
                    "expires_at": None,
                    "is_expired": True,
                    "user_id": self.user_id,
                    "error": "No tokens found",
                }

            logger.error(
                f"AWS ClientError checking token status: {error_code} - {error_message}"
            )
            return {
                "is_valid": False,
                "expires_at": None,
                "is_expired": True,
                "user_id": self.user_id,
                "error": f"AWS error: {error_code}",
            }

        except BotoCoreError as e:
            logger.error(f"BotoCoreError checking token status: {e}")
            return {
                "is_valid": False,
                "expires_at": None,
                "is_expired": True,
                "user_id": self.user_id,
                "error": f"BotoCore error: {str(e)}",
            }

        except Exception as e:
            logger.error(f"Unexpected error checking token status: {e}", exc_info=True)
            return {
                "is_valid": False,
                "expires_at": None,
                "is_expired": True,
                "user_id": self.user_id,
                "error": f"Unexpected error: {str(e)}",
            }

    async def revoke_tokens(self) -> bool:
        """
        Revoke and delete tokens from AgentCore Identity.

        This method removes all stored OAuth tokens for the user from AgentCore Identity.

        Returns:
            bool: True if tokens were revoked successfully, False otherwise

        Raises:
            ClientError: If AWS API call fails
        """
        try:
            # Delete tokens from AgentCore Identity
            _ = self.bedrock_agent_runtime_client.invoke_agent(
                agentId=self.identity_arn,
                sessionId=f"oauth-session-{self.user_id}",
                inputText=f"REVOKE_TOKENS:{self.user_id}",
            )

            logger.info(f"Successfully revoked tokens for user: {self.user_id}")
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            if error_code == "ResourceNotFoundException":
                logger.info(f"No tokens to revoke for user: {self.user_id}")
                return True  # Consider it successful if no tokens exist

            logger.error(
                f"AWS ClientError revoking tokens: {error_code} - {error_message}"
            )
            raise

        except BotoCoreError as e:
            logger.error(f"BotoCoreError revoking tokens: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error revoking tokens: {e}", exc_info=True)
            return False
