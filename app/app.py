"""
Chainlit application for SideKick MVP.

Integrates StrandsAgents Orchestrator with Chainlit UI for conversational
daily planning assistance.
"""

# VERSION MARKER - If you see this in logs, you're running the updated version
APP_VERSION = "2024-10-18-v2-agentcore-debug"

import sys
from pathlib import Path

# Ensure project root is in sys.path for absolute imports
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
import logging
import os

import chainlit as cl

logger = logging.getLogger(__name__)

# Import authentication module to register the password_auth_callback
# This must be imported before any Chainlit decorators are processed
try:
    from app import auth
    logger.info("✅ Authentication module loaded")
except ImportError as e:
    logger.warning(f"⚠️ Authentication module not available: {e}")
    auth = None

# Import AgentCore client (after path setup and other imports)
logger = logging.getLogger(__name__)

AgentCoreClient = None
AgentCoreError = None
AgentCoreConnectionError = None
AgentCoreInvocationError = None
AgentCoreTimeoutError = None
AGENTCORE_AVAILABLE = False

try:
    logger.info("Importing AgentCore client...")
    from app.agentcore_client import (AgentCoreClient,
                                      AgentCoreConnectionError, AgentCoreError,
                                      AgentCoreInvocationError,
                                      AgentCoreTimeoutError)

    AGENTCORE_AVAILABLE = True
    logger.info("✅ AgentCore client imported successfully")
except ImportError as e:
    logger.error(f"❌ AgentCore client import failed (ImportError): {e}")
    import traceback

    logger.error("Traceback:")
    traceback.print_exc()
except Exception as e:
    logger.error(f"❌ Unexpected error importing AgentCore client: {e}")
    import traceback

    logger.error("Traceback:")
    traceback.print_exc()


# Register custom routes (OAuth callback and health checks)
# This needs to happen at module import time, before Chainlit's catch-all route
def _register_custom_routes():
    """Register custom FastAPI routes before Chainlit's catch-all."""
    try:
        # Get the FastAPI app instance from Chainlit
        from chainlit.server import app as fastapi_app

        # Remove the catch-all route temporarily if it exists
        catch_all_route = None
        for i, route in enumerate(fastapi_app.routes):
            if hasattr(route, "path") and route.path == "/{full_path:path}":
                catch_all_route = fastapi_app.routes.pop(i)
                logger.info("Temporarily removed catch-all route")
                break

        # Register OAuth callback route
        try:
            from app.oauth_callback_handler import register_oauth_routes

            register_oauth_routes(fastapi_app)
            logger.info("OAuth callback routes registered")
        except ImportError:
            logger.warning("OAuth callback handler not found, skipping")

        # Register health check routes
        try:
            from app.health_routes import register_health_routes

            register_health_routes(fastapi_app)
            logger.info("Health check routes registered")
        except ImportError:
            logger.warning("Health routes not found, skipping")

        # Re-add the catch-all route at the end
        if catch_all_route:
            fastapi_app.routes.append(catch_all_route)
            logger.info("Re-added catch-all route")

        return True
    except Exception as e:
        logger.error(f"Could not register custom routes: {e}", exc_info=True)
        return False


# Register routes at import time
_routes_registered = _register_custom_routes()


def _get_oauth_handler():
    """
    Initialize and return OAuth handler if configuration is available.

    Returns:
        OAuthHandler instance or None if OAuth is not configured
    """
    try:
        # Check if OAuth is configured
        client_id = os.getenv("ATLASSIAN_OAUTH_CLIENT_ID")
        if not client_id:
            logger.info("❌ ATLASSIAN_OAUTH_CLIENT_ID not set - skipping OAuth initialization")
            return None
        
        logger.info(f"✅ ATLASSIAN_OAUTH_CLIENT_ID found: {client_id[:8]}...")

        # Import OAuth classes (lazy import to avoid module conflicts)
        # Try both import paths to handle different execution contexts
        try:
            from oauth_handler import OAuthHandler
            logger.info("✅ Imported OAuthHandler from oauth_handler")
        except ImportError:
            from app.oauth_handler import OAuthHandler
            logger.info("✅ Imported OAuthHandler from app.oauth_handler")

        from tools.atlassian_oauth_config import AtlassianOAuthConfig
        logger.info("✅ Imported AtlassianOAuthConfig")

        # Initialize OAuth configuration
        oauth_config = AtlassianOAuthConfig.from_env()
        logger.info(f"✅ OAuth config initialized for user: {oauth_config.demo_user_id}")

        # Choose token manager based on whether AgentCore is configured
        agentcore_arn = oauth_config.agentcore_identity_arn

        if agentcore_arn:
            # Use AgentCore token manager for production
            logger.info(f"✅ Using AWS AgentCore for token storage: {agentcore_arn[:50]}...")
            from tools.agentcore_token_manager import AgentCoreTokenManager

            token_manager = AgentCoreTokenManager(
                identity_arn=agentcore_arn,
                user_id=oauth_config.demo_user_id,
                oauth_config=oauth_config,
            )
        else:
            # Use simple in-memory token manager for development
            logger.warning(
                "⚠️ AGENTCORE_IDENTITY_ARN not set - using in-memory token storage (tokens will be lost on restart)"
            )
            from tools.simple_token_manager import SimpleTokenManager

            token_manager = SimpleTokenManager(
                identity_arn="dev-mode",
                user_id=oauth_config.demo_user_id,
                oauth_config=oauth_config,
            )
            logger.info("✅ SimpleTokenManager initialized")

        # Initialize OAuth handler
        oauth_handler = OAuthHandler(
            oauth_config=oauth_config, token_manager=token_manager
        )
        logger.info("✅ OAuth handler created successfully")

        return oauth_handler

    except Exception as e:
        logger.error(f"❌ Failed to initialize OAuth handler: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def _check_and_display_auth_status(oauth_handler) -> None:
    """
    Check authentication status and display appropriate message to user.

    Args:
        oauth_handler: OAuth handler instance
    """
    try:
        logger.info("Starting authentication status check...")

        # Check authentication status
        auth_status = await oauth_handler.check_auth_status()
        logger.info(
            f"Auth status received: is_authenticated={auth_status.get('is_authenticated')}"
        )

        if auth_status.get("is_authenticated"):
            # User is authenticated - display success message
            user_info = auth_status.get("user_info", {})
            display_name = user_info.get(
                "display_name", auth_status.get("user_id", "User")
            )
            email = user_info.get("email", "")
            resource_name = auth_status.get("resource_name", "Atlassian")

            # Format expiration time
            expires_at = auth_status.get("expires_at")
            expiry_info = ""
            if expires_at:
                expiry_info = f"\n🕐 Token expires: {expires_at}"

            success_msg = f"""## ✅ Connected to Atlassian

**User:** {display_name}
**Email:** {email}
**Workspace:** {resource_name}{expiry_info}

You can now access real JIRA issues and Confluence pages through your queries!
"""
            await cl.Message(content=success_msg).send()

            logger.info(f"User {display_name} is authenticated with Atlassian")

        else:
            # User is not authenticated - display login prompt
            error_msg = auth_status.get("error", "No valid tokens found")

            # Generate authorization URL
            auth_url, state = oauth_handler.generate_auth_url()

            # Store state in session for callback validation
            cl.user_session.set("oauth_state", state)

            login_msg = f"""## 🔐 Atlassian Authentication Required

To access real JIRA issues and Confluence pages, please authenticate with Atlassian.

**Status:** Not authenticated
**Reason:** {error_msg}

👉 [**Click here to log in to Atlassian**]({auth_url})

After logging in, you'll be redirected back to Atlassian. Then return here and type:
```
/check-auth
```
to verify your authentication status.

*Note: You can still use other features without authentication.*
"""

            # Create message with action button
            msg = cl.Message(content=login_msg)

            # Add action button to check auth status
            actions = [
                cl.Action(
                    name="check_auth_status",
                    value="check",
                    payload={"action": "check_auth"},
                    label="🔄 Check Auth Status",
                    description="Check if you're authenticated with Atlassian",
                )
            ]
            msg.actions = actions

            await msg.send()

            logger.info(f"User not authenticated: {error_msg}")

    except Exception as e:
        logger.error(f"Error checking authentication status: {e}", exc_info=True)
        error_msg = f"""## ⚠️ Authentication Check Failed

Unable to verify Atlassian authentication status.

**Error:** {str(e)}

You can still use other features, but JIRA and Confluence access may be limited.
"""
        await cl.Message(content=error_msg).send()


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session with orchestrator."""
    # Import settings here to avoid circular import
    # Try both import paths to handle different execution contexts
    try:
        import settings
    except ImportError:
        from app import settings

    # Professional yet friendly welcome message highlighting key capabilities
    welcome_msg = """# 👋 Welcome to SideKick AI

I'm your AI assistant, here to help you maximize productivity across your workday. I coordinate specialized AI agents to handle complex tasks intelligently.

## 🎯 What I Can Do For You

### 📅 Daily Planning & Coordination
- **Morning briefings** with calendar, emails, tasks, and incidents
- **Smart scheduling** with conflict detection
- **Action item extraction** from emails with deadline parsing

### 🎫 Project Management
- **JIRA integration** - view, search, update issues and transition workflows
- **Confluence access** - retrieve and search documentation
- **Priority tracking** - identify critical tasks and blockers

### ☁️ Infrastructure & Data
- **AWS monitoring** (read-only) - EC2, S3, Lambda, CloudWatch, costs
- **DynamoDB queries** - intelligent query construction from natural language
- **Incident tracking** - monitor critical issues and outages

### 📊 Business Intelligence
- **Report generation** - comprehensive sales reports with live data
- **Knowledge base** - semantic search across documents and templates
- **Data analysis** - metrics, trends, and actionable insights

### 🛡️ Security & Safety
- **Bedrock Guardrails** - content filtering and policy compliance
- **Read-only AWS** - strictly enforced for safety
- **OAuth authentication** - secure Atlassian integration

## 💬 Try These Commands

**Daily Planning:**
- "Help me plan my day"
- "What are my priorities today?"

**Project Management:**
- "Show me my JIRA tasks"
- "What critical issues do we have?"
- "Search Confluence for API documentation"

**Infrastructure:**
- "What's our AWS cost this month?"
- "Show S3 buckets"
- "Show critical incidents"

**Reports & Analytics:**
- "Generate a Q3 2025 sales report"
- "Find budget documents for Q4 2025"

---

**Ready to get started?** Just ask me anything, and I'll coordinate the right agents to help you! 🚀
"""
    await cl.Message(content=welcome_msg).send()

    # Check Atlassian authentication status
    try:
        logger.info("=" * 80)
        logger.info("ATLASSIAN OAUTH INITIALIZATION")
        logger.info(f"ATLASSIAN_OAUTH_CLIENT_ID: {'SET' if os.getenv('ATLASSIAN_OAUTH_CLIENT_ID') else 'NOT SET'}")
        logger.info(f"ATLASSIAN_OAUTH_CLIENT_SECRET: {'SET' if os.getenv('ATLASSIAN_OAUTH_CLIENT_SECRET') else 'NOT SET'}")
        logger.info(f"ATLASSIAN_OAUTH_REDIRECT_URI: {os.getenv('ATLASSIAN_OAUTH_REDIRECT_URI', 'NOT SET')}")
        logger.info(f"AGENTCORE_IDENTITY_ARN: {'SET' if os.getenv('AGENTCORE_IDENTITY_ARN') else 'NOT SET (will use in-memory storage)'}")
        logger.info("=" * 80)
        
        oauth_handler = _get_oauth_handler()
        if oauth_handler:
            logger.info("✅ OAuth handler initialized successfully, checking auth status...")
            await _check_and_display_auth_status(oauth_handler)
            # Store OAuth handler in session for callback handling
            cl.user_session.set("oauth_handler", oauth_handler)
            logger.info("✅ Auth status check completed")
        else:
            logger.warning("⚠️ OAuth handler not initialized (credentials not configured)")
            logger.warning("⚠️ Atlassian authentication will not be available")
    except Exception as e:
        logger.error(f"❌ Error during OAuth initialization: {e}", exc_info=True)
        # Show error to user
        error_msg = f"""## ⚠️ OAuth Initialization Error

There was an error initializing Atlassian authentication:

**Error:** {str(e)}

You can still use other features, but JIRA and Confluence access may be limited.
"""
        await cl.Message(content=error_msg).send()

    # Initialize AgentCore client (required)
    logger.info("=" * 80)
    logger.info(f"Agent Initialization - App Version: {APP_VERSION}")
    logger.info(f"USE_AGENTCORE = {settings.USE_AGENTCORE}")
    logger.info(
        f"RUNTIME_ARN = {'SET' if settings.AGENTCORE_RUNTIME_ARN else 'NOT SET'}"
    )
    logger.info(f"AGENTCORE_AVAILABLE = {AGENTCORE_AVAILABLE}")
    logger.info(f"AgentCoreClient = {AgentCoreClient}")
    logger.info("=" * 80)

    # Validate configuration
    if not settings.USE_AGENTCORE or not settings.AGENTCORE_RUNTIME_ARN:
        error_msg = """## ❌ Configuration Error

AgentCore integration is required but not properly configured.

**Required Configuration:**
- `USE_AGENTCORE=true`
- `AGENTCORE_RUNTIME_ARN=<your-agent-runtime-arn>`

**To fix this:**
1. Set the environment variables in your `.env` file
2. Deploy your agent to AWS AgentCore
3. Get the runtime ARN from the stack outputs
4. Restart the application

**Example:**
```bash
USE_AGENTCORE=true
AGENTCORE_RUNTIME_ARN=arn:aws:bedrock:region:account:agent-runtime/agent-id
```

The fallback orchestrator mode has been removed. Please configure AgentCore to continue.
"""
        await cl.Message(content=error_msg).send()
        logger.error(
            "AgentCore not configured - USE_AGENTCORE or AGENTCORE_RUNTIME_ARN missing"
        )
        return

    # Check if AgentCore client is available
    if not AGENTCORE_AVAILABLE or AgentCoreClient is None:
        error_msg = """## ❌ AgentCore Client Not Available

The AgentCore client module could not be imported.

**Possible causes:**
- Missing dependencies (check `requirements.txt`)
- Import errors in `app/agentcore_client.py`
- Python path issues

**To fix this:**
1. Check that `app/agentcore_client.py` exists
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Check the application logs for import errors
4. Restart the application

Please resolve the import issues and try again.
"""
        await cl.Message(content=error_msg).send()
        logger.error(
            f"AgentCore client not available - AGENTCORE_AVAILABLE={AGENTCORE_AVAILABLE}, AgentCoreClient={AgentCoreClient}"
        )
        return

    # Initialize AgentCore client
    logger.info("Initializing AgentCore client...")
    try:
        agentcore_client = AgentCoreClient(
            runtime_arn=settings.AGENTCORE_RUNTIME_ARN, region=settings.AWS_REGION
        )
        cl.user_session.set("agentcore_client", agentcore_client)
        logger.info(
            f"✅ AgentCore client initialized: {settings.AGENTCORE_RUNTIME_ARN}"
        )
    except Exception as e:
        error_msg = f"""## ❌ AgentCore Initialization Failed

Failed to initialize the AgentCore client.

**Error:** {str(e)}

**Possible causes:**
- Invalid runtime ARN
- AWS credentials not configured
- Network connectivity issues
- IAM permissions missing

**To fix this:**
1. Verify the `AGENTCORE_RUNTIME_ARN` is correct
2. Check AWS credentials are configured
3. Verify IAM permissions for `bedrock-agentcore:InvokeAgentRuntime`
4. Check network connectivity to AWS

Please resolve the configuration issues and try again.
"""
        await cl.Message(content=error_msg).send()
        logger.error(f"Failed to initialize AgentCore client: {e}", exc_info=True)
        return


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages with async streaming."""
    # Handle special commands
    if message.content.strip() == "/get-token":
        """Print the current OAuth token for debugging."""
        try:
            logger.info("Get token command received")
            oauth_handler = cl.user_session.get("oauth_handler")

            if not oauth_handler:
                logger.warning("No OAuth handler in session")
                await cl.Message(
                    content="⚠️ OAuth not configured. Please authenticate first."
                ).send()
                return

            logger.info(
                f"OAuth handler found, token manager type: {type(oauth_handler.token_manager).__name__}"
            )
            token = await oauth_handler.token_manager.get_access_token()

            if token:
                logger.info(f"Token retrieved successfully, length: {len(token)}")
                # Show token in a code block for easy copying
                token_msg = f"""## 🔑 Access Token

Copy this token:

```
{token}
```

**Test Confluence access:**
```bash
bash scripts/test_confluence_access.sh {token} 360449
```

**Test JIRA access:**
```bash
bash scripts/test_jira_with_token.sh {token}
```

**Check scopes:**
```bash
bash scripts/check_token_scopes.sh {token}
```
"""
                await cl.Message(content=token_msg).send()
            else:
                logger.warning("No token found in token manager")
                await cl.Message(
                    content="❌ No token found. Please authenticate first by clicking the login link."
                ).send()
            return
        except Exception as e:
            logger.error(f"Error getting token: {e}", exc_info=True)
            await cl.Message(
                content=f"❌ Error getting token: {str(e)}\n\nPlease try authenticating again."
            ).send()
            return

    if message.content.strip() == "/check-auth":
        """Handle check authentication status command."""
        try:
            oauth_handler = cl.user_session.get("oauth_handler")

            if not oauth_handler:
                await cl.Message(
                    content="⚠️ OAuth not configured. Atlassian authentication is not available."
                ).send()
                return

            await _check_and_display_auth_status(oauth_handler)
            return

        except Exception as e:
            logger.error(f"Error checking auth status: {e}", exc_info=True)
            await cl.Message(
                content=f"❌ Error checking authentication: {str(e)}"
            ).send()
            return

    # Check if this is an OAuth callback message (manual handling)
    if message.content.startswith("/oauth-callback"):
        try:
            # Parse OAuth callback parameters from message
            # Format: /oauth-callback code=xxx&state=yyy
            params_str = message.content.replace("/oauth-callback", "").strip()
            params = {}
            for param in params_str.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    params[key.strip()] = value.strip()

            code = params.get("code")
            state = params.get("state")
            error = params.get("error")

            # Handle OAuth error
            if error:
                error_description = params.get("error_description", "Unknown error")
                error_msg = f"""## ❌ Authentication Failed

**Error:** {error}
**Details:** {error_description}

The OAuth flow was cancelled or failed. Please try again.
"""
                await cl.Message(content=error_msg).send()
                return

            # Validate required parameters
            if not code or not state:
                await cl.Message(
                    content="❌ Invalid OAuth callback. Missing code or state parameter."
                ).send()
                return

            # Get OAuth handler from session
            oauth_handler = cl.user_session.get("oauth_handler")

            if not oauth_handler:
                await cl.Message(
                    content="❌ OAuth session expired. Please refresh the page and try again."
                ).send()
                return

            # Validate state parameter
            stored_state = cl.user_session.get("oauth_state")
            if state != stored_state:
                await cl.Message(
                    content="❌ Invalid OAuth state parameter. Possible CSRF attack detected."
                ).send()
                logger.warning(
                    f"OAuth state mismatch: expected {stored_state}, got {state}"
                )
                return

            # Show processing message
            processing_msg = cl.Message(content="🔄 Processing authentication...")
            await processing_msg.send()

            # Handle the callback
            result = await oauth_handler.handle_callback(code=code, state=state)

            # Remove processing message
            await processing_msg.remove()

            if result.get("success"):
                user_info = result.get("user_info", {})
                display_name = user_info.get("display_name", "User")
                email = user_info.get("email", "")
                cloud_id = result.get("cloud_id", "N/A")

                success_msg = f"""## ✅ Successfully Connected to Atlassian!

**Welcome, {display_name}!**
**Email:** {email}
**Cloud ID:** {cloud_id}

You can now access your real JIRA issues and Confluence pages. Try asking:
- "Show me my JIRA issues"
- "What are my high priority tasks?"
- "Show me the contents of confluence page 360449"
"""
                await cl.Message(content=success_msg).send()
                logger.info(f"OAuth authentication successful for {email}")

            else:
                error = result.get("error", "unknown_error")
                error_description = result.get(
                    "error_description", "An unknown error occurred"
                )

                error_msg = f"""## ❌ Authentication Failed

**Error:** {error}
**Details:** {error_description}

Please try again or contact support if the issue persists.
"""
                await cl.Message(content=error_msg).send()
                logger.error(
                    f"OAuth authentication failed: {error} - {error_description}"
                )

            return

        except Exception as e:
            logger.error(f"Error processing OAuth callback: {e}", exc_info=True)
            await cl.Message(
                content=f"❌ Unexpected error during authentication: {str(e)}"
            ).send()
            return

    # Create a Step for loading indication
    loading_step = cl.Step(name="🤔 Analyzing your request...")
    loading_step.show_input = False  # Hide input
    await loading_step.send()

    # Create EMPTY message for streaming (per Chainlit documentation pattern)
    response_msg = cl.Message(content="")
    await response_msg.send()

    # Track which tools are called
    tools_called = []
    accumulated_text = ""

    try:
        # Get AgentCore client from session
        agentcore_client = cl.user_session.get("agentcore_client")

        if not agentcore_client:
            logger.error("AgentCore client not found in session!")
            error_msg = """## ❌ Session Error

AgentCore client is not initialized in your session.

This usually means the application failed to start properly. Please:
1. Refresh the page
2. Check the application logs
3. Verify AgentCore configuration

If the problem persists, contact support.
"""
            response_msg.content = error_msg
            await response_msg.update()
            return

        logger.info(f"Invoking AgentCore for: {message.content}")
        logger.info(f"Invoking AgentCore for: {message.content[:100]}...")

        # Get OAuth access token if available
        metadata = {}
        oauth_handler = cl.user_session.get("oauth_handler")
        if oauth_handler:
            try:
                access_token = await oauth_handler.token_manager.get_access_token()
                if access_token:
                    metadata["atlassian_access_token"] = access_token
                    logger.info("✅ Passing Atlassian access token to agent")
                else:
                    logger.warning("⚠️ No Atlassian access token available")
            except Exception as e:
                logger.warning(f"⚠️ Failed to get access token: {e}")

        try:
            # Invoke agent via AgentCore
            # Note: AgentCore doesn't support streaming yet, so we get the full response
            response_data = await agentcore_client.invoke_agent(
                prompt=message.content, 
                session_id=cl.user_session.get("id"),
                metadata=metadata
            )

            # Get the response text
            response_text = response_data.get("response", "")

            # Stream the response token by token for better UX
            for char in response_text:
                accumulated_text += char
                await response_msg.stream_token(char)
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)

            logger.info(f"AgentCore response completed: {len(response_text)} chars")

        except AgentCoreConnectionError as e:
            error_msg = f"""❌ **Connection Error**

Unable to connect to the agent service. This might be a temporary issue.

**Error:** {str(e)}

**Troubleshooting:**
- Check AWS credentials are configured
- Verify network connectivity to AWS
- Check the agent runtime is deployed
- Review CloudWatch logs for errors

Please try again in a moment."""
            response_msg.content = error_msg
            await response_msg.update()
            logger.error(f"AgentCore connection error: {e}")

        except AgentCoreInvocationError as e:
            error_msg = f"""❌ **Agent Error**

The agent encountered an error while processing your request.

**Error:** {e.message}
**Code:** {e.error_code or 'Unknown'}

"""
            if "502" in str(e):
                error_msg += """
**Note:** This is a known issue with the current AgentCore deployment.
The agent runtime may not be properly configured. Please check CloudWatch logs.

**Troubleshooting:**
1. Check the agent deployment status
2. Review CloudWatch logs at `/aws/bedrock/agentcore/sidekick-agentcore-dev`
3. Verify the container is running correctly
4. Check the agent runtime ARN is correct
"""

            response_msg.content = error_msg
            await response_msg.update()
            logger.error(f"AgentCore invocation error: {e}")

        except AgentCoreTimeoutError as e:
            error_msg = f"""❌ **Timeout Error**

The agent took too long to respond (>20 seconds).

**Error:** {str(e)}

**Please try:**
- Simplifying your request
- Breaking it into smaller parts
- Trying again later

If timeouts persist, the agent may need performance optimization."""
            response_msg.content = error_msg
            await response_msg.update()
            logger.error(f"AgentCore timeout: {e}")

        except AgentCoreError as e:
            error_msg = f"""❌ **Unexpected Error**

An unexpected error occurred while communicating with the agent.

**Error:** {str(e)}

Please try again or contact support if the issue persists."""
            response_msg.content = error_msg
            await response_msg.update()
            logger.error(f"AgentCore error: {e}", exc_info=True)

        # Close the loading step and remove it
        loading_step.output = "✓ Complete"
        await loading_step.update()
        await loading_step.remove()  # Remove from UI

        # Finalize the message (per Chainlit documentation pattern)
        await response_msg.update()
        logger.info(
            f"Streaming completed. Total accumulated: {len(accumulated_text)} chars"
        )

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logger.error(f"Exception occurred: {str(e)}")
        logger.error(f"Traceback: {error_details}")

        error_msg = f"❌ **Error**: {str(e)}\n\n<details>\n<summary>Error Details</summary>\n\n```\n{error_details}\n```\n</details>\n\nPlease try again or rephrase your request."

        if accumulated_text:
            # If we got partial content, append the error
            response_msg.content = accumulated_text + "\n\n" + error_msg
        else:
            response_msg.content = error_msg

        await response_msg.update()

    # Store conversation history
    conversation_history = cl.user_session.get("history", [])
    conversation_history.append(
        {
            "user": message.content,
            "assistant": response_msg.content if response_msg.content else "",
            "tools": tools_called,
        }
    )
    cl.user_session.set("history", conversation_history)
    logger.debug(
        f"Conversation history updated. Total turns: {len(conversation_history)}"
    )


@cl.action_callback("check_auth_status")
async def on_check_auth_status(action: cl.Action):
    """Handle check authentication status action."""
    try:
        oauth_handler = cl.user_session.get("oauth_handler")

        if not oauth_handler:
            await cl.Message(content="⚠️ OAuth not configured for this session.").send()
            return

        await _check_and_display_auth_status(oauth_handler)

    except Exception as e:
        logger.error(f"Error checking auth status: {e}", exc_info=True)
        await cl.Message(content=f"❌ Error checking authentication: {str(e)}").send()


@cl.on_chat_end
async def on_chat_end():
    """Clean up session."""
    conversation_history = cl.user_session.get("history", [])
    # Log conversation stats
    total_turns = len(conversation_history)
    total_tools_used = sum(len(turn["tools"]) for turn in conversation_history)
    logger.info(f"Session ended: {total_turns} turns, {total_tools_used} tool calls")


@cl.on_stop
def on_stop():
    """
    Handle stop button (user interrupts ongoing task).
    """
    logger.info("Task stopped by user")


if __name__ == "__main__":
    # This allows running with: chainlit run app.py
    pass
