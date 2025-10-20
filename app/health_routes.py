"""
Health check endpoints for Chainlit app.

These endpoints are used by container orchestration (ECS/ALB) to verify
the service is healthy and ready to accept traffic.
"""

import logging
import os

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def health_check(request: Request):
    """
    Health check endpoint.

    Returns 200 OK if the service is healthy.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "daily-planner",
            "region": os.getenv("AWS_REGION", "unknown"),
        },
        status_code=200,
    )


async def readiness_check(request: Request):
    """
    Readiness check endpoint.

    Returns 200 OK if the service is ready to accept traffic.
    """
    # Add checks for dependencies (Bedrock KB, etc.) if needed
    return JSONResponse(
        content={"status": "ready", "service": "daily-planner"}, status_code=200
    )


def register_health_routes(app):
    """
    Register health check routes with the Chainlit FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_api_route("/health", health_check, methods=["GET"], name="health_check")
    app.add_api_route(
        "/readiness", readiness_check, methods=["GET"], name="readiness_check"
    )
    logger.info("Health check routes registered at /health and /readiness")
