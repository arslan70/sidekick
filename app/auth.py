"""
Chainlit authentication configuration for SideKick AI.

Provides password-based authentication for hackathon judges and administrators.
Credentials are stored in AWS Secrets Manager for security.
"""

import json
import logging
import os
from typing import Optional

import boto3
import chainlit as cl

logger = logging.getLogger(__name__)

# Cache for credentials to avoid repeated Secrets Manager calls
_credentials_cache = None


def _get_credentials():
    """
    Retrieve authentication credentials from AWS Secrets Manager.
    
    Returns:
        dict: Credentials dictionary with demo and admin usernames/passwords
    """
    global _credentials_cache
    
    # Return cached credentials if available
    if _credentials_cache is not None:
        return _credentials_cache
    
    try:
        # Get secret name from environment or use default
        secret_name = os.getenv(
            "CHAINLIT_AUTH_SECRET_NAME",
            "sidekick/dev/chainlit-auth"
        )
        region = os.getenv("AWS_REGION", "eu-central-1")
        
        logger.info(f"Fetching Chainlit auth credentials from Secrets Manager: {secret_name}")
        
        # Create Secrets Manager client
        client = boto3.client("secretsmanager", region_name=region)
        
        # Retrieve secret value
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response["SecretString"]
        
        # Parse JSON credentials
        credentials = json.loads(secret_string)
        
        # Cache the credentials
        _credentials_cache = credentials
        
        logger.info("✅ Successfully loaded Chainlit auth credentials from Secrets Manager")
        return credentials
        
    except Exception as e:
        logger.error(f"❌ Failed to load credentials from Secrets Manager: {e}")
        logger.warning("⚠️ Falling back to environment variables")
        
        # Fallback to environment variables for local development
        fallback_credentials = {
            "demo_username": os.getenv("DEMO_USERNAME", "demo"),
            "demo_password": os.getenv("DEMO_PASSWORD", ""),
            "admin_username": os.getenv("ADMIN_USERNAME", "admin"),
            "admin_password": os.getenv("ADMIN_PASSWORD", ""),
        }
        
        _credentials_cache = fallback_credentials
        return fallback_credentials


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """
    Authenticate users with username and password.
    
    Credentials are retrieved from AWS Secrets Manager for security.

    Args:
        username: Username provided by user
        password: Password provided by user

    Returns:
        cl.User object if authentication successful, None otherwise
    """
    logger.info(f"Authentication attempt for user: {username}")
    
    # Get credentials from Secrets Manager
    credentials = _get_credentials()
    
    demo_username = credentials.get("demo_username", "demo")
    demo_password = credentials.get("demo_password", "")
    admin_username = credentials.get("admin_username", "admin")
    admin_password = credentials.get("admin_password", "")

    # Check demo credentials
    if username == demo_username and password == demo_password:
        logger.info(f"Demo user authenticated: {username}")
        return cl.User(
            identifier=username,
            metadata={
                "role": "demo",
                "display_name": "Demo User",
                "description": "Hackathon Judge Demo Account",
            },
        )

    # Check admin credentials (if configured)
    if admin_password and username == admin_username and password == admin_password:
        logger.info(f"Admin user authenticated: {username}")
        return cl.User(
            identifier=username,
            metadata={
                "role": "admin",
                "display_name": "Administrator",
                "description": "System Administrator",
            },
        )

    # Authentication failed
    logger.warning(f"Authentication failed for user: {username}")
    return None
