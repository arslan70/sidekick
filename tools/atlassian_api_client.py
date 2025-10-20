"""
Atlassian API HTTP Client with OAuth Authentication

This module provides an HTTP client for making authenticated requests to Atlassian APIs
(JIRA and Confluence) with automatic token refresh and retry logic.
"""

import logging
from typing import Dict

import requests
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

from tools.agentcore_token_manager import AgentCoreTokenManager
from tools.atlassian_exceptions import (APIError, InvalidTokenError,
                                        NetworkError, PermissionError,
                                        RateLimitError, ResourceNotFoundError,
                                        ServerError, TokenExpiredError,
                                        TokenRefreshError)
from tools.atlassian_oauth_config import AtlassianOAuthConfig

logger = logging.getLogger(__name__)


def _sanitize_for_logging(data: dict) -> dict:
    """
    Sanitize sensitive data for logging.

    Removes or masks tokens, secrets, and other sensitive information.

    Args:
        data: Dictionary that may contain sensitive data

    Returns:
        Sanitized dictionary safe for logging
    """
    if not isinstance(data, dict):
        return data

    sanitized = data.copy()
    sensitive_keys = [
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "secret",
        "password",
    ]

    for key in sanitized:
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"

    return sanitized


class AtlassianAPIClient:
    """
    HTTP client for Atlassian APIs with OAuth authentication.

    This client handles:
    - OAuth token management and automatic refresh
    - Automatic retry on 401 (unauthorized) responses
    - Network error retry with exponential backoff
    - Base URL management for JIRA and Confluence APIs
    """

    # Base URLs for Atlassian APIs
    BASE_URL_JIRA = "https://api.atlassian.com/ex/jira"
    BASE_URL_CONFLUENCE = "https://api.atlassian.com/ex/confluence"

    def __init__(
        self, token_manager: AgentCoreTokenManager, oauth_config: AtlassianOAuthConfig
    ):
        """
        Initialize the Atlassian API client.

        Args:
            token_manager: AgentCore token manager for OAuth token operations
            oauth_config: OAuth configuration for Atlassian services
        """
        self.token_manager = token_manager
        self.oauth_config = oauth_config
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )

        logger.info("Initialized Atlassian API client")

    async def _get_auth_header(self) -> Dict[str, str]:
        """
        Retrieve access token and format Authorization header.

        Returns:
            Dict containing Authorization header with Bearer token

        Raises:
            InvalidTokenError: If no valid access token is available
        """
        access_token = await self.token_manager.get_access_token()

        if not access_token:
            error_msg = "No valid access token available"
            logger.error(error_msg)
            raise InvalidTokenError(error_msg)

        return {"Authorization": f"Bearer {access_token}"}

    async def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make authenticated HTTP request with automatic token refresh on 401.

        This method:
        1. Retrieves the current access token
        2. Makes the HTTP request with the token
        3. If 401 response, attempts to refresh the token and retry once
        4. Handles various error responses with appropriate exceptions
        5. Returns the response or raises a specific exception

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Full URL for the request
            **kwargs: Additional arguments to pass to requests

        Returns:
            requests.Response object

        Raises:
            TokenExpiredError: If token has expired
            TokenRefreshError: If token refresh fails
            InvalidTokenError: If token is invalid
            RateLimitError: If rate limit is exceeded (429)
            PermissionError: If insufficient permissions (403)
            ResourceNotFoundError: If resource not found (404)
            ServerError: If server error occurs (5xx)
            NetworkError: If network connectivity fails
            APIError: For other API errors
        """
        # Get authorization header
        try:
            auth_header = await self._get_auth_header()
        except InvalidTokenError as e:
            logger.error(f"Failed to get auth header: {e}")
            raise

        # Merge auth header with any existing headers
        headers = kwargs.pop("headers", {})
        headers.update(auth_header)

        # Sanitize kwargs for logging (remove sensitive data)
        safe_kwargs = _sanitize_for_logging(kwargs)
        logger.debug(f"Making {method} request to {url} with params: {safe_kwargs}")

        # Make the request with retry logic for network errors
        try:
            response = await self._make_request_with_retry(
                method=method, url=url, headers=headers, **kwargs
            )

            # Check for 401 Unauthorized - token may have expired
            if response.status_code == 401:
                logger.warning("Received 401 Unauthorized, attempting token refresh")

                # Raise TokenExpiredError to signal expiration
                raise TokenExpiredError(
                    "Access token expired", details={"url": url, "method": method}
                )

            # Handle other error status codes before raising for status
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                retry_seconds = (
                    int(retry_after) if retry_after and retry_after.isdigit() else None
                )

                logger.warning(f"Rate limit exceeded. Retry after: {retry_seconds}s")
                raise RateLimitError(
                    "API rate limit exceeded",
                    retry_after=retry_seconds,
                    details={"url": url, "method": method},
                )

            if response.status_code == 403:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass

                logger.error(f"Permission denied for {url}: {error_data}")
                raise PermissionError(
                    "Insufficient permissions for this operation",
                    details={"url": url, "method": method, "response": error_data},
                )

            if response.status_code == 404:
                logger.warning(f"Resource not found: {url}")
                raise ResourceNotFoundError(
                    "Requested resource not found",
                    details={"url": url, "method": method},
                )

            if response.status_code >= 500:
                logger.error(f"Server error {response.status_code} for {url}")
                raise ServerError(
                    f"Atlassian server error: {response.status_code}",
                    status_code=response.status_code,
                    details={"url": url, "method": method},
                )

            # Raise exception for other HTTP errors
            response.raise_for_status()

            return response

        except TokenExpiredError:
            # Handle token expiration with automatic refresh
            logger.info("Attempting automatic token refresh")

            try:
                refresh_result = await self.token_manager.refresh_access_token()

                if not refresh_result.get("success"):
                    error_msg = refresh_result.get("error_description", "Unknown error")
                    logger.error(f"Token refresh failed: {error_msg}")
                    raise TokenRefreshError(
                        f"Failed to refresh token: {error_msg}",
                        details={"original_url": url},
                    )

                logger.info("Token refreshed successfully, retrying request")

                # Get new auth header and retry the request once
                auth_header = await self._get_auth_header()
                headers.update(auth_header)

                response = await self._make_request_with_retry(
                    method=method, url=url, headers=headers, **kwargs
                )

                # Check response status after retry
                if response.status_code == 401:
                    logger.error("Still unauthorized after token refresh")
                    raise InvalidTokenError(
                        "Token invalid even after refresh", details={"url": url}
                    )

                # Handle error responses after retry
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_seconds = (
                        int(retry_after)
                        if retry_after and retry_after.isdigit()
                        else None
                    )
                    raise RateLimitError(
                        "API rate limit exceeded",
                        retry_after=retry_seconds,
                        details={"url": url, "method": method},
                    )

                if response.status_code == 403:
                    raise PermissionError(
                        "Insufficient permissions for this operation",
                        details={"url": url, "method": method},
                    )

                if response.status_code == 404:
                    raise ResourceNotFoundError(
                        "Requested resource not found",
                        details={"url": url, "method": method},
                    )

                if response.status_code >= 500:
                    raise ServerError(
                        f"Atlassian server error: {response.status_code}",
                        status_code=response.status_code,
                        details={"url": url, "method": method},
                    )

                response.raise_for_status()
                return response

            except TokenRefreshError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error during token refresh: {e}")
                raise TokenRefreshError(
                    f"Token refresh failed: {str(e)}", details={"original_url": url}
                )

        except (RateLimitError, PermissionError, ResourceNotFoundError, ServerError):
            # Re-raise our custom exceptions
            raise

        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout for {url}: {e}")
            raise NetworkError(
                f"Request timed out: {str(e)}", details={"url": url, "method": method}
            )

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            raise NetworkError(
                f"Connection failed: {str(e)}", details={"url": url, "method": method}
            )

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during request to {url}: {e}")
            raise APIError(
                f"API request failed: {str(e)}",
                status_code=e.response.status_code if e.response else None,
                details={"url": url, "method": method},
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during request to {url}: {e}")
            raise APIError(
                f"Request failed: {str(e)}", details={"url": url, "method": method}
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
        ),
    )
    async def _make_request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with automatic retry for network errors.

        Uses tenacity library to retry on:
        - Connection errors
        - Timeout errors

        Retry strategy:
        - Maximum 3 attempts
        - Exponential backoff: 2s, 4s, 8s (capped at 10s)

        Note: Rate limiting (429) is NOT retried here - it's handled at a higher level
        with proper Retry-After header respect.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request arguments

        Returns:
            requests.Response object
        """
        logger.debug(f"Making {method} request to {url}")

        response = self.session.request(
            method=method, url=url, timeout=30, **kwargs  # 30 second timeout
        )

        return response

    async def get(self, url: str, **kwargs) -> requests.Response:
        """
        Make authenticated GET request.

        Args:
            url: Request URL
            **kwargs: Additional arguments (params, headers, etc.)

        Returns:
            requests.Response object
        """
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> requests.Response:
        """
        Make authenticated POST request.

        Args:
            url: Request URL
            **kwargs: Additional arguments (json, data, headers, etc.)

        Returns:
            requests.Response object
        """
        return await self._request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> requests.Response:
        """
        Make authenticated PUT request.

        Args:
            url: Request URL
            **kwargs: Additional arguments (json, data, headers, etc.)

        Returns:
            requests.Response object
        """
        return await self._request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> requests.Response:
        """
        Make authenticated DELETE request.

        Args:
            url: Request URL
            **kwargs: Additional arguments (headers, etc.)

        Returns:
            requests.Response object
        """
        return await self._request("DELETE", url, **kwargs)

    def get_jira_base_url(self, cloud_id: str) -> str:
        """
        Get base URL for JIRA API with cloud ID.

        Args:
            cloud_id: Atlassian cloud ID

        Returns:
            Full base URL for JIRA API
        """
        return f"{self.BASE_URL_JIRA}/{cloud_id}"

    def get_confluence_base_url(self, cloud_id: str) -> str:
        """
        Get base URL for Confluence API with cloud ID.

        Args:
            cloud_id: Atlassian cloud ID

        Returns:
            Full base URL for Confluence API
        """
        return f"{self.BASE_URL_CONFLUENCE}/{cloud_id}"
