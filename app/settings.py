"""
Chainlit settings configuration for the SideKick application.
"""

import logging
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load environment variables from project root
# Get the project root (parent of app directory)
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

# Load .env file with explicit path
load_dotenv(dotenv_path=env_file, override=True)

# Configure logging
logger = logging.getLogger(__name__)

# Debug: Log what was loaded
if os.getenv("USE_AGENTCORE"):
    logger.info(f"USE_AGENTCORE loaded: {os.getenv('USE_AGENTCORE')}")
    logger.info(
        f"AGENTCORE_RUNTIME_ARN loaded: {os.getenv('AGENTCORE_RUNTIME_ARN', 'NOT SET')[:50]}..."
    )
else:
    logger.warning("USE_AGENTCORE not found in environment")
    logger.info(f".env file path: {env_file}")
    logger.info(f".env file exists: {env_file.exists()}")

# Chainlit configuration
CHAINLIT_CONFIG = {
    "project": {
        "name": "SideKick",
        "description": "AI-powered daily planning assistant",
    },
    "ui": {
        "name": "SideKick Assistant",
        "default_collapse_content": True,
        "hide_cot": False,
    },
    "features": {
        "prompt_playground": False,
        "multi_modal": False,
    },
}

# Chainlit Authentication Configuration
CHAINLIT_AUTH_SECRET = os.getenv("CHAINLIT_AUTH_SECRET", "").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-pro-v1:0")

# Bedrock Guardrails Configuration
BEDROCK_GUARDRAIL_ID = os.getenv("BEDROCK_GUARDRAIL_ID", "zd4xbra1lval")
BEDROCK_GUARDRAIL_VERSION = os.getenv("BEDROCK_GUARDRAIL_VERSION", "1")

# Application settings
MAX_CONVERSATION_HISTORY = 10
ENABLE_STREAMING = True

# JIRA Mode Configuration
JIRA_MODE = os.getenv("JIRA_MODE", "fake").lower()

# AgentCore Configuration
AGENTCORE_RUNTIME_ARN = os.getenv("AGENTCORE_RUNTIME_ARN", "").strip()
USE_AGENTCORE = os.getenv("USE_AGENTCORE", "false").lower() == "true"

# Atlassian OAuth Configuration
ATLASSIAN_OAUTH_CLIENT_ID = os.getenv("ATLASSIAN_OAUTH_CLIENT_ID", "").strip()
ATLASSIAN_OAUTH_CLIENT_SECRET = os.getenv("ATLASSIAN_OAUTH_CLIENT_SECRET", "").strip()
ATLASSIAN_OAUTH_REDIRECT_URI = os.getenv("ATLASSIAN_OAUTH_REDIRECT_URI", "").strip()
ATLASSIAN_OAUTH_SCOPES = os.getenv("ATLASSIAN_OAUTH_SCOPES", "").strip()
AGENTCORE_IDENTITY_ARN = os.getenv("AGENTCORE_IDENTITY_ARN", "").strip()
ATLASSIAN_DEMO_USER_ID = os.getenv(
    "ATLASSIAN_DEMO_USER_ID", "yetanotherarslan@gmail.com"
).strip()
ATLASSIAN_CLOUD_ID = os.getenv("ATLASSIAN_CLOUD_ID", "").strip()


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


def validate_atlassian_oauth_config() -> bool:
    """
    Validate Atlassian OAuth configuration.

    Returns:
        True if configuration is valid, False if not configured

    Raises:
        ConfigurationError: If configuration is partially set but invalid
    """
    # Check if any OAuth variables are set
    oauth_vars_set = any(
        [
            ATLASSIAN_OAUTH_CLIENT_ID,
            ATLASSIAN_OAUTH_CLIENT_SECRET,
            ATLASSIAN_OAUTH_REDIRECT_URI,
        ]
    )

    # If no OAuth variables are set, OAuth is not configured (valid for fake mode)
    if not oauth_vars_set:
        return False

    # If some OAuth variables are set, validate all required ones
    missing_vars = []

    if not ATLASSIAN_OAUTH_CLIENT_ID:
        missing_vars.append("ATLASSIAN_OAUTH_CLIENT_ID")

    if not ATLASSIAN_OAUTH_CLIENT_SECRET:
        missing_vars.append("ATLASSIAN_OAUTH_CLIENT_SECRET")

    if not ATLASSIAN_OAUTH_REDIRECT_URI:
        missing_vars.append("ATLASSIAN_OAUTH_REDIRECT_URI")

    if missing_vars:
        raise ConfigurationError(
            f"Incomplete Atlassian OAuth configuration. Missing required environment variables: {', '.join(missing_vars)}. "
            f"Either set all required OAuth variables or remove them to use fake mode."
        )

    # Validate redirect URI format
    if not ATLASSIAN_OAUTH_REDIRECT_URI.startswith(
        "https://"
    ) and not ATLASSIAN_OAUTH_REDIRECT_URI.startswith("http://localhost"):
        raise ConfigurationError(
            f"ATLASSIAN_OAUTH_REDIRECT_URI must use HTTPS or http://localhost for development. "
            f"Got: {ATLASSIAN_OAUTH_REDIRECT_URI}"
        )

    # Validate scopes if provided
    if ATLASSIAN_OAUTH_SCOPES:
        scopes = [s.strip() for s in ATLASSIAN_OAUTH_SCOPES.split(",")]
        if "offline_access" not in scopes:
            logger.warning(
                "ATLASSIAN_OAUTH_SCOPES does not include 'offline_access'. "
                "Refresh tokens may not be available."
            )

    return True


def validate_jira_mode_config() -> None:
    """
    Validate JIRA mode configuration.

    Raises:
        ConfigurationError: If JIRA mode is invalid or incompatible with OAuth config
    """
    if JIRA_MODE not in ["fake", "real"]:
        raise ConfigurationError(
            f"JIRA_MODE must be either 'fake' or 'real'. Got: {JIRA_MODE}"
        )

    # If JIRA mode is "real", OAuth must be configured
    if JIRA_MODE == "real":
        try:
            oauth_configured = validate_atlassian_oauth_config()
            if not oauth_configured:
                raise ConfigurationError(
                    "JIRA_MODE is set to 'real' but Atlassian OAuth is not configured. "
                    "Please set ATLASSIAN_OAUTH_CLIENT_ID, ATLASSIAN_OAUTH_CLIENT_SECRET, "
                    "and ATLASSIAN_OAUTH_REDIRECT_URI environment variables, or set JIRA_MODE to 'fake'."
                )
        except ConfigurationError:
            # Re-raise with additional context
            raise


def validate_aws_config() -> None:
    """
    Validate AWS configuration.

    Raises:
        ConfigurationError: If AWS configuration is invalid
    """
    if not AWS_REGION:
        raise ConfigurationError("AWS_REGION environment variable is required")

    if not BEDROCK_MODEL_ID:
        raise ConfigurationError("BEDROCK_MODEL_ID environment variable is required")


def validate_agentcore_config() -> None:
    """
    Validate AgentCore configuration.

    Raises:
        ConfigurationError: If AgentCore is enabled but not properly configured
    """
    if USE_AGENTCORE and not AGENTCORE_RUNTIME_ARN:
        raise ConfigurationError(
            "USE_AGENTCORE is set to 'true' but AGENTCORE_RUNTIME_ARN is not configured. "
            "Please set AGENTCORE_RUNTIME_ARN environment variable with the agent runtime ARN, "
            "or set USE_AGENTCORE to 'false' to disable AgentCore integration."
        )

    if not USE_AGENTCORE:
        raise ConfigurationError(
            "AgentCore integration is required. Please set USE_AGENTCORE=true and "
            "AGENTCORE_RUNTIME_ARN to your agent runtime ARN. "
            "The fallback orchestrator mode has been removed."
        )


def validate_required_config() -> None:
    """
    Validate all required configuration on application startup.

    This function should be called during application initialization to ensure
    all required configuration is present and valid.

    Raises:
        ConfigurationError: If any required configuration is missing or invalid
    """
    errors: List[str] = []

    # Validate AWS configuration (always required)
    try:
        validate_aws_config()
    except ConfigurationError as e:
        errors.append(str(e))

    # Validate AgentCore configuration (now required)
    try:
        validate_agentcore_config()
    except ConfigurationError as e:
        errors.append(str(e))

    # Validate JIRA mode configuration
    try:
        validate_jira_mode_config()
    except ConfigurationError as e:
        errors.append(str(e))

    # If there are errors, raise with all error messages
    if errors:
        error_message = "Configuration validation failed:\n" + "\n".join(
            f"  - {err}" for err in errors
        )
        raise ConfigurationError(error_message)

    # Log configuration status
    logger.info("Configuration validated successfully")
    logger.info(f"USE_AGENTCORE: {USE_AGENTCORE}")
    logger.info(
        f"AGENTCORE_RUNTIME_ARN: {'SET' if AGENTCORE_RUNTIME_ARN else 'NOT SET'}"
    )
    logger.info(f"JIRA_MODE: {JIRA_MODE}")

    if JIRA_MODE == "real":
        logger.info("Atlassian OAuth is configured for real API mode")
    else:
        logger.info("Using fake data mode for JIRA")


def get_config_summary() -> dict:
    """
    Get a summary of current configuration (without sensitive data).

    Returns:
        Dictionary containing configuration summary
    """
    oauth_configured = False
    try:
        oauth_configured = validate_atlassian_oauth_config()
    except ConfigurationError:
        pass

    return {
        "aws_region": AWS_REGION,
        "bedrock_model_id": BEDROCK_MODEL_ID,
        "use_agentcore": USE_AGENTCORE,
        "agentcore_runtime_arn": (
            AGENTCORE_RUNTIME_ARN[:50] + "..." if AGENTCORE_RUNTIME_ARN else None
        ),
        "jira_mode": JIRA_MODE,
        "oauth_configured": oauth_configured,
        "oauth_client_id": (
            ATLASSIAN_OAUTH_CLIENT_ID[:8] + "..." if ATLASSIAN_OAUTH_CLIENT_ID else None
        ),
        "oauth_redirect_uri": ATLASSIAN_OAUTH_REDIRECT_URI or None,
        "demo_user_id": ATLASSIAN_DEMO_USER_ID,
        "cloud_id": ATLASSIAN_CLOUD_ID[:8] + "..." if ATLASSIAN_CLOUD_ID else None,
    }
