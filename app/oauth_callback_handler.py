"""
OAuth callback handler for Chainlit app.

This module provides a FastAPI route to handle OAuth callbacks from Atlassian.
"""

import logging

from fastapi import Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)


async def handle_oauth_callback(request: Request):
    """
    Handle OAuth callback from Atlassian.

    This endpoint receives the authorization code and state from Atlassian
    after the user authorizes the app.

    Args:
        request: FastAPI request object

    Returns:
        HTML response with instructions for the user
    """
    try:
        # Get query parameters
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        error_description = request.query_params.get("error_description")

        logger.info(
            f"OAuth callback received - code: {code[:20] if code else None}..., state: {state[:20] if state else None}..."
        )

        # Handle OAuth error
        if error:
            logger.error(f"OAuth error: {error} - {error_description}")
            return HTMLResponse(
                content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Failed</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #e74c3c; }}
        .error {{
            background: #fee;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #e74c3c;
            margin: 20px 0;
        }}
        .button {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 20px;
        }}
        .button:hover {{ background: #2980b9; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>❌ Authentication Failed</h1>
        <div class="error">
            <strong>Error:</strong> {error}<br>
            <strong>Description:</strong> {error_description or 'Unknown error'}
        </div>
        <p>The OAuth flow was cancelled or failed. Please try again.</p>

    </div>
</body>
</html>
""",
                status_code=400,
            )

        # Validate required parameters
        if not code or not state:
            logger.error("Missing code or state parameter in OAuth callback")
            return HTMLResponse(
                content="""
<!DOCTYPE html>
<html>
<head>
    <title>Invalid Callback</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #e74c3c; }}
        .button {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 20px;
        }}
        .button:hover {{ background: #2980b9; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>❌ Invalid OAuth Callback</h1>
        <p>Missing required parameters (code or state).</p>
    </div>
</body>
</html>
""",
                status_code=400,
            )

        # Success - provide instructions to complete authentication
        logger.info("OAuth callback successful - providing instructions to user")

        return HTMLResponse(
            content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Successful</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #27ae60; }}
        .success {{
            background: #d4edda;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #27ae60;
            margin: 20px 0;
        }}
        .code-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            margin: 20px 0;
            word-break: break-all;
        }}
        .button {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 20px;
        }}
        .button:hover {{ background: #2980b9; }}
        .copy-button {{
            background: #27ae60;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 10px;
        }}
        .copy-button:hover {{ background: #229954; }}
        ol {{ line-height: 1.8; }}
    </style>
    <script>
        function copyCommand() {{
            const command = document.getElementById('command').textContent;
            navigator.clipboard.writeText(command).then(() => {{
                const btn = document.getElementById('copyBtn');
                btn.textContent = '✓ Copied!';
                setTimeout(() => {{ btn.textContent = 'Copy'; }}, 2000);
            }});
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>✅ Authorization Successful!</h1>
        <div class="success">
            You've successfully authorized the app with Atlassian.
        </div>

        <h2>Complete Authentication</h2>
        <p>To complete the authentication process:</p>

        <ol>
            <li>Return to the <strong>Chainlit chat window</strong></li>
            <li>Copy and paste this command into the chat:</li>
        </ol>

        <div class="code-box">
            <span id="command">/oauth-callback code={code}&state={state}</span>
            <button class="copy-button" id="copyBtn" onclick="copyCommand()">Copy</button>
        </div>

        <p>After pasting the command, you'll be authenticated and can access your JIRA tickets!</p>


    </div>
</body>
</html>
"""
        )

    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}", exc_info=True)
        return HTMLResponse(
            content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #e74c3c; }}
        .button {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 20px;
        }}
        .button:hover {{ background: #2980b9; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>❌ Error</h1>
        <p>An unexpected error occurred: {str(e)}</p>

    </div>
</body>
</html>
""",
            status_code=500,
        )


def register_oauth_routes(app):
    """
    Register OAuth callback routes with the Chainlit FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_api_route(
        "/oauth/callback", handle_oauth_callback, methods=["GET"], name="oauth_callback"
    )
    logger.info("OAuth callback route registered at /oauth/callback")
