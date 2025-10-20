"""
Agent Runtime Module for AWS AgentCore.

This module provides the entrypoint for running the orchestrator agent
in AWS AgentCore as a standalone process, separate from the Chainlit UI.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path for absolute imports
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging following Strands best practices
# Strands uses STRANDS_LOG_LEVEL environment variable for configuration
# Set default log level if not already set
if "STRANDS_LOG_LEVEL" not in os.environ:
    os.environ["STRANDS_LOG_LEVEL"] = "INFO"

# Configure Python logging to stderr (required for AgentCore CloudWatch)
# Use force=True to ensure this takes precedence
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    force=True
)

# Get logger for this module
logger = logging.getLogger(__name__)

# Ensure all handlers flush immediately (critical for CloudWatch)
for handler in logging.root.handlers:
    handler.flush = lambda: sys.stderr.flush()

# Log startup information
logger.info("Logging configured for AgentCore (stderr, unbuffered)")

# Import required modules
try:
    from agents.orchestrator import create_orchestrator_agent
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    raise

# Import BedrockAgentCoreApp for AgentCore integration
try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    app = BedrockAgentCoreApp()
    logger.info("BedrockAgentCoreApp initialized")
except ImportError as e:
    logger.warning(f"BedrockAgentCoreApp not available: {e}")
    # Fallback for local testing
    from strands import app
    logger.info("Using strands app for local testing")

# Set BYPASS_TOOL_CONSENT environment variable
os.environ["BYPASS_TOOL_CONSENT"] = "true"
logger.info("BYPASS_TOOL_CONSENT set to 'true'")


@app.entrypoint
def main(payload: dict) -> Optional[str]:
    """
    Main entrypoint function for AgentCore agent runtime.
    
    This function is invoked by AWS AgentCore when the agent receives a request.
    It extracts the user prompt from the payload, processes it through the
    orchestrator agent, and returns the response text.
    
    Args:
        payload: Dictionary containing the request data with the following structure:
            - prompt (str): User's input message (required)
            - session_id (str, optional): Session identifier for context
            - metadata (dict, optional): Additional context information
    
    Returns:
        str: Response text from the orchestrator agent
        None: If the request is not actionable or an error occurs
    
    Raises:
        Exception: Propagates orchestrator errors for AgentCore to handle
    """
    try:
        logger.info("=" * 80)
        logger.info("AgentCore invocation started")
        logger.info(f"Payload received: {payload}")
        
        # Extract prompt from payload
        if not isinstance(payload, dict):
            logger.error(f"Invalid payload type: {type(payload)}. Expected dict.")
            return None
        
        prompt = payload.get("prompt")
        if not prompt:
            logger.warning("No prompt found in payload")
            return None
        
        if not isinstance(prompt, str) or not prompt.strip():
            logger.warning(f"Invalid prompt: {prompt}")
            return None
        
        session_id = payload.get("session_id", "default")
        metadata = payload.get("metadata", {})
        
        logger.info(f"Processing prompt: '{prompt[:100]}...'")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Metadata keys: {list(metadata.keys())}")
        
        # Extract Atlassian access token from metadata if provided
        atlassian_token = metadata.get("atlassian_access_token")
        if atlassian_token:
            # Set as environment variable so tools can access it
            os.environ["ATLASSIAN_ACCESS_TOKEN"] = atlassian_token
            logger.info("✅ Atlassian access token received and set in environment")
        else:
            logger.warning("⚠️ No Atlassian access token in metadata - will use static data")
        
        # Get configuration from environment variables
        model_id = os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-pro-v1:0")
        region = os.getenv("AWS_REGION", "eu-central-1")
        guardrail_id = os.getenv("BEDROCK_GUARDRAIL_ID")
        guardrail_version = os.getenv("BEDROCK_GUARDRAIL_VERSION", "1")
        
        logger.info(f"Initializing orchestrator with model={model_id}, region={region}")
        if guardrail_id:
            logger.info(f"Guardrails enabled: {guardrail_id} v{guardrail_version}")
        
        # Initialize orchestrator agent
        try:
            orchestrator = create_orchestrator_agent(
                model=model_id,
                region=region,
                guardrail_id=guardrail_id,
                guardrail_version=guardrail_version
            )
            logger.info("Orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
            return f"Error: Failed to initialize orchestrator - {str(e)}"
        
        # Invoke orchestrator with the prompt
        try:
            logger.info("Invoking orchestrator...")
            result = orchestrator(prompt)
            logger.info("Orchestrator invocation completed")
            
            # Handle None result (not actionable)
            if result is None:
                logger.info("Request not actionable - no response generated")
                logger.info("=" * 80)
                return None
            
            # Extract response text from result (matching working agent pattern)
            if hasattr(result, "message"):
                message = result.message
                if isinstance(message, dict) and "content" in message:
                    content = message["content"]
                    if isinstance(content, list) and len(content) > 0:
                        # Extract text from first content block
                        first_block = content[0]
                        if isinstance(first_block, dict) and "text" in first_block:
                            response_text = first_block["text"]
                            logger.info(f"\nResponse:")
                            logger.info(response_text)
                            logger.info("=" * 80)
                            return response_text
            
            # Fallback: try string conversion
            response_text = str(result)
            logger.info(f"\nResponse (converted to string):")
            logger.info(response_text)
            logger.info("=" * 80)
            return response_text
            
        except Exception as e:
            logger.error(f"Orchestrator invocation failed: {e}", exc_info=True)
            error_message = f"Error: Orchestrator invocation failed - {str(e)}"
            logger.info("=" * 80)
            return error_message
    
    except Exception as e:
        logger.error(f"Unexpected error in agent runtime: {e}", exc_info=True)
        logger.info("=" * 80)
        return f"Error: Unexpected error - {str(e)}"


if __name__ == "__main__":
    """
    Entry point for AgentCore runtime.
    
    When running in AgentCore, this starts the app server.
    For local testing, you can call main() directly with test payloads.
    """
    logger.info("Starting AgentCore app server...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Start the AgentCore app server
    app.run()
