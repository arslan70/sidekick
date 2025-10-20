"""
Chainlit authentication configuration for SideKick AI.

Provides password-based authentication for hackathon judges and administrators.
"""

import logging
import os
from typing import Optional

import chainlit as cl

logger = logging.getLogger(__name__)

# Demo credentials for hackathon judges
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "**********"

# Admin credentials from environment
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """
    Authenticate users with username and password.

    Args:
        username: Username provided by user
        password: Password provided by user

    Returns:
        cl.User object if authentication successful, None otherwise
    """
    logger.info(f"Authentication attempt for user: {username}")

    # Check demo credentials
    if username == DEMO_USERNAME and password == DEMO_PASSWORD:
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
    if ADMIN_PASSWORD and username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
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
