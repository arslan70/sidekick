"""
Custom exception classes for Atlassian API integration.

This module defines exception hierarchy for handling various error scenarios
in Atlassian OAuth authentication and API operations.
"""


class AtlassianAuthError(Exception):
    """Base exception for Atlassian authentication errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def get_user_message(self) -> str:
        """Get user-friendly error message."""
        return self.message


class TokenExpiredError(AtlassianAuthError):
    """Access token has expired and needs refresh."""

    def __init__(
        self, message: str = "Your Atlassian session has expired", details: dict = None
    ):
        super().__init__(message, details)

    def get_user_message(self) -> str:
        return "Your Atlassian session has expired. Attempting to refresh..."


class TokenRefreshError(AtlassianAuthError):
    """Failed to refresh access token."""

    def __init__(
        self,
        message: str = "Failed to refresh authentication token",
        details: dict = None,
    ):
        super().__init__(message, details)

    def get_user_message(self) -> str:
        return (
            "Unable to refresh your Atlassian session. Please log in again to continue."
        )


class InvalidTokenError(AtlassianAuthError):
    """Token is invalid or has been revoked."""

    def __init__(
        self, message: str = "Authentication token is invalid", details: dict = None
    ):
        super().__init__(message, details)

    def get_user_message(self) -> str:
        return "Your Atlassian authentication is invalid. Please log in again."


class OAuthFlowError(AtlassianAuthError):
    """Error during OAuth authorization flow."""

    def __init__(
        self, message: str = "OAuth authorization failed", details: dict = None
    ):
        super().__init__(message, details)

    def get_user_message(self) -> str:
        error_type = self.details.get("error", "")
        if error_type == "access_denied":
            return "Authorization was cancelled. Please try again if you'd like to connect to Atlassian."
        elif error_type == "invalid_scope":
            return (
                "The requested permissions are not available. Please contact support."
            )
        return f"Authorization failed: {self.message}"


class APIError(Exception):
    """Base exception for Atlassian API errors."""

    def __init__(self, message: str, status_code: int = None, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def get_user_message(self) -> str:
        """Get user-friendly error message."""
        return self.message


class RateLimitError(APIError):
    """API rate limit exceeded."""

    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: int = None,
        details: dict = None,
    ):
        super().__init__(message, status_code=429, details=details)
        self.retry_after = retry_after

    def get_user_message(self) -> str:
        if self.retry_after:
            return f"Too many requests to Atlassian. Please wait {self.retry_after} seconds and try again."
        return "Too many requests to Atlassian. Please wait a moment and try again."


class PermissionError(APIError):
    """Insufficient permissions for requested operation."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_scopes: list = None,
        details: dict = None,
    ):
        super().__init__(message, status_code=403, details=details)
        self.required_scopes = required_scopes or []

    def get_user_message(self) -> str:
        if self.required_scopes:
            scopes_str = ", ".join(self.required_scopes)
            return f"You don't have permission to access this resource. Required permissions: {scopes_str}"
        return "You don't have permission to access this resource. Please check your Atlassian permissions."


class ResourceNotFoundError(APIError):
    """Requested resource was not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str = None,
        details: dict = None,
    ):
        super().__init__(message, status_code=404, details=details)
        self.resource_type = resource_type

    def get_user_message(self) -> str:
        if self.resource_type:
            return f"The requested {self.resource_type} was not found."
        return "The requested resource was not found."


class ServerError(APIError):
    """Atlassian server error (5xx)."""

    def __init__(
        self,
        message: str = "Atlassian service error",
        status_code: int = 500,
        details: dict = None,
    ):
        super().__init__(message, status_code=status_code, details=details)

    def get_user_message(self) -> str:
        return "Atlassian services are experiencing issues. Please try again in a few moments."


class NetworkError(APIError):
    """Network connectivity error."""

    def __init__(
        self, message: str = "Network connection failed", details: dict = None
    ):
        super().__init__(message, status_code=None, details=details)

    def get_user_message(self) -> str:
        return "Unable to connect to Atlassian. Please check your internet connection."
