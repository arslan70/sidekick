"""
AgentCore client module for invoking agents via AWS Bedrock AgentCore.

This module provides a wrapper around the boto3 bedrock-agentcore client
with proper error handling, retry logic, and async support.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

logger = logging.getLogger(__name__)


class AgentCoreError(Exception):
    """Base exception for AgentCore client errors."""

    pass


class AgentCoreConnectionError(AgentCoreError):
    """Raised when connection to AgentCore fails."""

    pass


class AgentCoreInvocationError(AgentCoreError):
    """Raised when agent invocation fails."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class AgentCoreTimeoutError(AgentCoreError):
    """Raised when agent invocation times out."""

    pass


class AgentCoreClient:
    """
    Wrapper for boto3 bedrock-agentcore client.

    Provides async interface for invoking agents deployed in AWS AgentCore
    with proper error handling and retry logic.
    """

    def __init__(self, runtime_arn: str, region: str):
        """
        Initialize AgentCore client.

        Args:
            runtime_arn: ARN of the deployed agent runtime
            region: AWS region
        """
        self.runtime_arn = runtime_arn
        self.region = region

        # Configure boto3 client with extended timeout
        config = Config(
            read_timeout=20000,  # 20 seconds for agent response
            connect_timeout=5000,  # 5 seconds for connection
            retries={"max_attempts": 3, "mode": "adaptive"},
        )

        try:
            self.client = boto3.client(
                "bedrock-agentcore", config=config, region_name=region
            )
            logger.info(f"AgentCore client initialized for runtime: {runtime_arn}")
        except Exception as e:
            logger.error(f"Failed to initialize AgentCore client: {e}")
            raise AgentCoreConnectionError(
                f"Failed to initialize AgentCore client: {e}"
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(AgentCoreConnectionError),
    )
    async def invoke_agent(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Invoke agent via AgentCore with retry logic.

        Args:
            prompt: User's input message
            session_id: Optional session identifier (generated if not provided)
            metadata: Optional additional context

        Returns:
            dict: Response from agent containing:
                - response: str - Agent's response text
                - session_id: str - Session identifier
                - metadata: dict - Additional response data

        Raises:
            AgentCoreConnectionError: If connection fails (retryable)
            AgentCoreInvocationError: If invocation fails (not retryable)
            AgentCoreTimeoutError: If invocation times out
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # Prepare payload as JSON bytes (required by boto3)
        import json

        payload_dict = {"prompt": prompt}

        if metadata:
            payload_dict["metadata"] = metadata

        # Convert to JSON bytes
        payload_bytes = json.dumps(payload_dict).encode("utf-8")

        logger.info(
            f"Invoking AgentCore runtime {self.runtime_arn} with session {session_id}"
        )
        logger.debug(f"Prompt: {prompt[:100]}...")

        try:
            # Run boto3 call in thread pool (boto3 is synchronous)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.invoke_agent_runtime(
                    agentRuntimeArn=self.runtime_arn, payload=payload_bytes
                ),
            )

            logger.info(f"AgentCore invocation successful for session {session_id}")
            logger.debug(f"Response keys: {response.keys()}")

            # Parse response - the 'response' key contains a StreamingBody that needs to be read
            import json

            response_body = response.get("response")
            if response_body:
                # Read the streaming body
                response_text = response_body.read().decode("utf-8")
                logger.debug(f"Response text: {response_text[:200]}...")

                # Try to parse as JSON
                try:
                    response_json = json.loads(response_text)
                    # If it's a dict, try to get the 'response' field
                    if isinstance(response_json, dict):
                        response_content = response_json.get("response", response_text)
                    else:
                        # If it's not a dict (e.g., a string), use it directly
                        response_content = response_json
                except json.JSONDecodeError:
                    # If not JSON, use the raw text
                    response_content = response_text
            else:
                # Fallback if no response body
                response_content = ""

            # Get additional metadata from response
            runtime_session_id = response.get("runtimeSessionId", session_id)
            trace_id = response.get("traceId", "")

            response_data = {
                "response": response_content,
                "session_id": runtime_session_id,
                "metadata": {
                    "trace_id": trace_id,
                    "status_code": response.get("statusCode", 200),
                    "content_type": response.get("contentType", "text/plain"),
                },
            }

            return response_data

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            status_code = e.response.get("ResponseMetadata", {}).get(
                "HTTPStatusCode", 0
            )

            logger.error(
                f"AgentCore invocation failed: {error_code} - {error_message} "
                f"(HTTP {status_code})"
            )

            # Handle specific error types
            if error_code == "RuntimeClientError" and "502" in error_message:
                # 502 error from runtime - likely configuration issue
                raise AgentCoreInvocationError(
                    "Agent runtime error (502). The agent may not be properly configured. "
                    "Please check CloudWatch logs for details.",
                    error_code="RuntimeError",
                )
            elif error_code in ["ThrottlingException", "TooManyRequestsException"]:
                # Throttling - retryable
                raise AgentCoreConnectionError(f"AgentCore throttling: {error_message}")
            elif error_code in ["ServiceUnavailableException", "InternalServerError"]:
                # Service unavailable - retryable
                raise AgentCoreConnectionError(
                    f"AgentCore service unavailable: {error_message}"
                )
            elif status_code == 408 or "timeout" in error_message.lower():
                # Timeout
                raise AgentCoreTimeoutError(
                    f"Agent invocation timed out: {error_message}"
                )
            else:
                # Other errors - not retryable
                raise AgentCoreInvocationError(
                    f"Agent invocation failed: {error_message}", error_code=error_code
                )

        except BotoCoreError as e:
            logger.error(f"Boto3 error during AgentCore invocation: {e}")
            # Network/connection errors are retryable
            raise AgentCoreConnectionError(f"Connection error: {e}")

        except asyncio.TimeoutError:
            logger.error("AgentCore invocation timed out")
            raise AgentCoreTimeoutError("Agent invocation timed out after 20 seconds")

        except Exception as e:
            logger.error(
                f"Unexpected error during AgentCore invocation: {e}", exc_info=True
            )
            raise AgentCoreInvocationError(f"Unexpected error: {e}")

    async def invoke_agent_streaming(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Invoke agent via AgentCore with streaming response (if supported).

        Note: This is a placeholder for future streaming support.
        Currently falls back to non-streaming invocation.

        Args:
            prompt: User's input message
            session_id: Optional session identifier
            metadata: Optional additional context

        Yields:
            str: Response chunks as they arrive

        Raises:
            AgentCoreError: If invocation fails
        """
        logger.warning(
            "Streaming not yet supported by AgentCore, using non-streaming invocation"
        )

        # Fall back to non-streaming
        response = await self.invoke_agent(prompt, session_id, metadata)

        # Yield the complete response
        yield response["response"]

    def get_runtime_info(self) -> Dict[str, str]:
        """
        Get information about the configured runtime.

        Returns:
            dict: Runtime information
        """
        return {"runtime_arn": self.runtime_arn, "region": self.region}
