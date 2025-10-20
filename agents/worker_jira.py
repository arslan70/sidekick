"""
Jira Worker Agent - Specialized agent for Jira issue management.

Handles fetching, monitoring, and providing details about Jira issues.
Can be called by the Orchestrator using Agents-as-Tools pattern.
"""

import logging
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

# Agent-specific model and region constants
JIRA_MODEL_ID = "eu.amazon.nova-lite-v1:0"
JIRA_REGION = "eu-central-1"

from strands import Agent, tool
from strands.models import BedrockModel

# Configure logging for strands framework
logging.getLogger("strands").setLevel(
    logging.INFO
)  # Set to DEBUG for more detailed logs

# Configure logging for this module
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
from atlassian_exceptions import (AtlassianAuthError, InvalidTokenError,
                                  NetworkError, RateLimitError, ServerError,
                                  TokenExpiredError, TokenRefreshError)
from confluence_adapter import fetch_page
from confluence_adapter import search_confluence_pages as search_confluence
from jira_adapter import (fetch_all_issues, fetch_assigned_issues,
                          fetch_high_priority_issues, fetch_issue_details,
                          fetch_issues_by_status, search_issues)


# Custom exception for authentication errors (for backward compatibility)
class AuthenticationError(AtlassianAuthError):
    """Raised when authentication with Atlassian is required or fails."""

    pass


# --- Place create_jira_worker_agent after all imports ---
def create_jira_worker_agent(*args, **kwargs):
    """
    Create a Jira worker agent using agent-specific model and region constants.
    """
    logger.info("Creating Jira Worker Agent")

    bedrock_model = BedrockModel(
        model_id=JIRA_MODEL_ID,
        region_name=JIRA_REGION,
        temperature=0.2,
        streaming=False,
    )

    agent = Agent(
        model=bedrock_model,
        name="jira_worker",
        tools=[
            get_all_jira_issues,
            get_assigned_jira_issues,
            get_high_priority_jira_issues,
            get_jira_issue_details,
            search_jira_issues,
            get_jira_issues_by_status,
            update_jira_issue,
            add_jira_comment,
            transition_jira_issue,
            get_confluence_page,
            search_confluence_pages,
        ],
        system_prompt="""You are a Jira Worker Agent specialized in project management, issue tracking, and documentation access.

When users ask for "my tasks", "my issues", or "assigned to me", use get_assigned_jira_issues WITHOUT specifying an assignee - it automatically fetches the authenticated user's issues.

Provide clear, actionable Jira insights:
- Prioritize by urgency and due dates
- Highlight blockers and critical issues
- Group by status and assignee when relevant
- Include issue keys for easy reference

You can also UPDATE Jira issues:
- Update issue fields (summary, description, priority) with update_jira_issue
- Add comments to issues with add_jira_comment
- Change issue status (e.g., move to 'In Progress' or 'Done') with transition_jira_issue
- Always confirm the action with the user before making changes

You also have access to Confluence documentation:
- Retrieve specific pages by ID for detailed context
- Search for relevant documentation using CQL queries
- Link documentation to related Jira issues when helpful

Be concise and help users understand their workload, priorities, and access relevant documentation.""",
    )
    return agent


@tool
async def get_all_jira_issues(limit: int = 20) -> dict:
    """
    Retrieve all Jira issues across all projects.

    Returns comprehensive issue data including status, priority, and assignee.
    Use this for broad project visibility and workload assessment.

    Args:
        limit: Maximum number of issues to retrieve (default: 20, max: 100)

    Returns:
        Dictionary with issue summaries, metadata, and total count
    """
    logger.info(f"Fetching all Jira issues with limit={limit}")
    try:
        result = await fetch_all_issues(limit=limit)
        logger.info(f"Successfully fetched {result.get('total_count', 0)} Jira issues")
        return result
    except (
        TokenExpiredError,
        TokenRefreshError,
        InvalidTokenError,
        AtlassianAuthError,
    ) as e:
        logger.error(f"Authentication error: {e}")
        return {
            "error": "authentication_required",
            "message": e.get_user_message(),
            "details": str(e),
            "action": "Please log in to your Atlassian account to continue",
        }
    except RateLimitError as e:
        logger.warning(f"Rate limit error: {e}")
        return {
            "error": "rate_limit_exceeded",
            "message": e.get_user_message(),
            "retry_after": e.retry_after,
            "action": "Please wait a moment before trying again",
        }
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        return {
            "error": "permission_denied",
            "message": e.get_user_message(),
            "details": str(e),
            "action": "Please check your Atlassian permissions or contact your administrator",
        }
    except ServerError as e:
        logger.error(f"Server error: {e}")
        return {
            "error": "server_error",
            "message": e.get_user_message(),
            "details": str(e),
            "action": "Please try again in a few moments",
        }
    except NetworkError as e:
        logger.error(f"Network error: {e}")
        return {
            "error": "network_error",
            "message": e.get_user_message(),
            "details": str(e),
            "action": "Please check your internet connection and try again",
        }
    except ValueError as e:
        # Handle configuration errors
        error_msg = str(e)
        if "not properly configured" in error_msg or "not initialized" in error_msg:
            logger.error(f"Configuration error: {e}")
            return {
                "error": "configuration_error",
                "message": "JIRA integration is not properly configured",
                "details": error_msg,
                "action": "Please contact your administrator to configure JIRA integration",
            }
        logger.error(f"Error fetching all Jira issues: {e}", exc_info=True)
        return {"error": f"Failed to fetch Jira issues: {str(e)}"}
    except Exception as e:
        logger.error(f"Error fetching all Jira issues: {e}", exc_info=True)
        return {"error": f"Failed to fetch Jira issues: {str(e)}"}


@tool
async def get_assigned_jira_issues() -> dict:
    """
    Retrieve Jira issues assigned to the authenticated user.

    Use this when users ask for "my tasks", "my issues", or "what's assigned to me".
    Automatically fetches issues for the currently authenticated user - no username needed.

    Particularly useful for daily planning and workload management.

    Returns:
        Dictionary with assigned issues, priorities, and due dates for the current user
    """
    logger.info("Fetching assigned Jira issues for authenticated user")
    try:
        result = await fetch_assigned_issues(
            assignee=None
        )  # Always use authenticated user
        logger.info(
            f"Successfully fetched {result.get('total_count', 0)} assigned issues"
        )
        return result
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        return {
            "error": "authentication_required",
            "message": "Please authenticate with Atlassian to access JIRA issues",
            "details": str(e),
            "action": "Please log in to your Atlassian account to continue",
        }
    except ValueError as e:
        # Handle configuration errors
        error_msg = str(e)
        if "not properly configured" in error_msg or "not initialized" in error_msg:
            logger.error(f"Configuration error: {e}")
            return {
                "error": "configuration_error",
                "message": "JIRA integration is not properly configured",
                "details": error_msg,
                "action": "Please contact your administrator to configure JIRA integration",
            }
        logger.error(f"Error fetching assigned Jira issues: {e}", exc_info=True)
        return {"error": f"Failed to fetch assigned issues: {str(e)}"}
    except Exception as e:
        logger.error(f"Error fetching assigned Jira issues: {e}", exc_info=True)
        return {"error": f"Failed to fetch assigned issues: {str(e)}"}


@tool
async def get_high_priority_jira_issues() -> dict:
    """
    Retrieve high-priority and urgent Jira issues requiring immediate attention.

    Returns issues marked as Critical, High priority, or nearing their due date.
    Use this to identify time-sensitive work and potential blockers.

    Returns:
        Dictionary with high-priority issues sorted by urgency
    """
    logger.info("Fetching high-priority Jira issues")
    try:
        result = await fetch_high_priority_issues()
        logger.info(
            f"Successfully fetched {result.get('total_count', 0)} high-priority issues"
        )
        return result
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        return {
            "error": "authentication_required",
            "message": "Please authenticate with Atlassian to access JIRA issues",
            "details": str(e),
            "action": "Please log in to your Atlassian account to continue",
        }
    except ValueError as e:
        # Handle configuration errors
        error_msg = str(e)
        if "not properly configured" in error_msg or "not initialized" in error_msg:
            logger.error(f"Configuration error: {e}")
            return {
                "error": "configuration_error",
                "message": "JIRA integration is not properly configured",
                "details": error_msg,
                "action": "Please contact your administrator to configure JIRA integration",
            }
        logger.error(f"Error fetching high-priority issues: {e}", exc_info=True)
        return {"error": f"Failed to fetch high-priority issues: {str(e)}"}
    except Exception as e:
        logger.error(f"Error fetching high-priority issues: {e}", exc_info=True)
        return {"error": f"Failed to fetch high-priority issues: {str(e)}"}


@tool
async def get_jira_issue_details(issue_key: str) -> dict:
    """
    Retrieve comprehensive details for a specific Jira issue.

    Returns complete issue information including description, comments,
    linked pages, subtasks, and full history. Use this when you need
    in-depth understanding of a particular issue.

    Args:
        issue_key: Jira issue identifier (e.g., 'ENG-123', 'PROJ-456')

    Returns:
        Dictionary with full issue details, linked resources, and metadata
    """
    logger.info(f"Fetching details for Jira issue: {issue_key}")
    try:
        result = await fetch_issue_details(issue_key)
        logger.info(f"Successfully fetched details for {issue_key}")
        return result
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        return {
            "error": "authentication_required",
            "message": "Please authenticate with Atlassian to access JIRA issues",
            "details": str(e),
            "action": "Please log in to your Atlassian account to continue",
        }
    except ValueError as e:
        # Handle configuration errors
        error_msg = str(e)
        if "not properly configured" in error_msg or "not initialized" in error_msg:
            logger.error(f"Configuration error: {e}")
            return {
                "error": "configuration_error",
                "message": "JIRA integration is not properly configured",
                "details": error_msg,
                "action": "Please contact your administrator to configure JIRA integration",
            }
        logger.error(
            f"Error fetching issue details for {issue_key}: {e}", exc_info=True
        )
        return {"error": f"Failed to fetch issue details: {str(e)}"}
    except Exception as e:
        logger.error(
            f"Error fetching issue details for {issue_key}: {e}", exc_info=True
        )
        return {"error": f"Failed to fetch issue details: {str(e)}"}


@tool
async def search_jira_issues(keyword: str) -> dict:
    """
    Search for Jira issues by keyword in title/summary.

    Performs text search across issue summaries to find relevant work items.
    Use this to locate issues related to specific topics, features, or bugs.

    Args:
        keyword: Search term to find in issue summaries

    Returns:
        Dictionary with matching issues and relevance ranking
    """
    logger.info(f"Searching Jira issues with keyword: {keyword}")
    try:
        result = await search_issues(keyword)
        logger.info(f"Search found {result.get('total_count', 0)} matching issues")
        return result
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        return {
            "error": "authentication_required",
            "message": "Please authenticate with Atlassian to access JIRA issues",
            "details": str(e),
            "action": "Please log in to your Atlassian account to continue",
        }
    except ValueError as e:
        # Handle configuration errors
        error_msg = str(e)
        if "not properly configured" in error_msg or "not initialized" in error_msg:
            logger.error(f"Configuration error: {e}")
            return {
                "error": "configuration_error",
                "message": "JIRA integration is not properly configured",
                "details": error_msg,
                "action": "Please contact your administrator to configure JIRA integration",
            }
        logger.error(f"Error searching Jira issues: {e}", exc_info=True)
        return {"error": f"Failed to search issues: {str(e)}"}
    except Exception as e:
        logger.error(f"Error searching Jira issues: {e}", exc_info=True)
        return {"error": f"Failed to search issues: {str(e)}"}


@tool
async def get_jira_issues_by_status(status: str) -> dict:
    """
    Retrieve Jira issues filtered by workflow status.

    Use this to track work in specific stages of completion.
    Common statuses: 'To Do', 'In Progress', 'Code Review', 'Testing', 'Done'

    Args:
        status: Workflow status to filter by (e.g., 'In Progress', 'Code Review')

    Returns:
        Dictionary with issues in the specified status
    """
    logger.info(f"Fetching Jira issues with status: {status}")
    try:
        result = await fetch_issues_by_status(status)
        logger.info(
            f"Successfully fetched {result.get('total_count', 0)} issues with status '{status}'"
        )
        return result
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        return {
            "error": "authentication_required",
            "message": "Please authenticate with Atlassian to access JIRA issues",
            "details": str(e),
            "action": "Please log in to your Atlassian account to continue",
        }
    except ValueError as e:
        # Handle configuration errors
        error_msg = str(e)
        if "not properly configured" in error_msg or "not initialized" in error_msg:
            logger.error(f"Configuration error: {e}")
            return {
                "error": "configuration_error",
                "message": "JIRA integration is not properly configured",
                "details": error_msg,
                "action": "Please contact your administrator to configure JIRA integration",
            }
        logger.error(f"Error fetching issues by status: {e}", exc_info=True)
        return {"error": f"Failed to fetch issues by status: {str(e)}"}
    except Exception as e:
        logger.error(f"Error fetching issues by status: {e}", exc_info=True)
        return {"error": f"Failed to fetch issues by status: {str(e)}"}


@tool
async def get_confluence_page(page_id: str, body_format: str = "storage") -> dict:
    """
    Retrieve a Confluence page by its ID.

    Use this to fetch detailed documentation, specifications, or meeting notes
    that are referenced in Jira issues or needed for context.

    Args:
        page_id: Confluence page ID (e.g., '12345')
        body_format: Content format - 'storage' (default), 'view', or 'export_view'

    Returns:
        Dictionary with page title, content, space info, and metadata
    """
    logger.info(f"Fetching Confluence page: {page_id}")
    try:
        result = await fetch_page(page_id, body_format)

        if result.get("success"):
            logger.info(
                f"Successfully fetched Confluence page: {result.get('page', {}).get('title')}"
            )
        else:
            logger.warning(
                f"Failed to fetch Confluence page {page_id}: {result.get('error')}"
            )

        return result
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        return {
            "error": "authentication_required",
            "message": "Please authenticate with Atlassian to access Confluence pages",
            "details": str(e),
            "action": "Please log in to your Atlassian account to continue",
        }
    except ValueError as e:
        # Handle configuration errors
        error_msg = str(e)
        if "not properly configured" in error_msg or "not initialized" in error_msg:
            logger.error(f"Configuration error: {e}")
            return {
                "error": "configuration_error",
                "message": "Confluence integration is not properly configured",
                "details": error_msg,
                "action": "Please contact your administrator to configure Confluence integration",
            }
        logger.error(f"Error fetching Confluence page: {e}", exc_info=True)
        return {"error": f"Failed to fetch Confluence page: {str(e)}"}
    except Exception as e:
        logger.error(f"Error fetching Confluence page {page_id}: {e}", exc_info=True)
        return {"error": f"Failed to fetch Confluence page: {str(e)}"}


@tool
async def search_confluence_pages(query: str, limit: int = 25) -> dict:
    """
    Search Confluence pages using CQL (Confluence Query Language).

    Use this to find relevant documentation, specifications, or meeting notes
    related to projects, features, or specific topics.

    Common CQL patterns:
    - Search by text: 'text ~ "keyword"'
    - Search in space: 'space = "PROJ" AND text ~ "keyword"'
    - Search by type: 'type = page AND text ~ "keyword"'
    - Recent pages: 'space = "PROJ" order by lastmodified desc'

    Args:
        query: CQL query string to search for pages
        limit: Maximum number of results to return (default: 25, max: 250)

    Returns:
        Dictionary with matching pages, excerpts, and metadata
    """
    logger.info(f"Searching Confluence pages with query: {query}")
    try:
        result = await search_confluence(query, limit)

        if result.get("success"):
            logger.info(f"Search found {result.get('total_count', 0)} Confluence pages")
        else:
            logger.warning(f"Confluence search failed: {result.get('error')}")

        return result
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        return {
            "error": "authentication_required",
            "message": "Please authenticate with Atlassian to search Confluence pages",
            "details": str(e),
            "action": "Please log in to your Atlassian account to continue",
        }
    except ValueError as e:
        # Handle configuration errors
        error_msg = str(e)
        if "not properly configured" in error_msg or "not initialized" in error_msg:
            logger.error(f"Configuration error: {e}")
            return {
                "error": "configuration_error",
                "message": "Confluence integration is not properly configured",
                "details": error_msg,
                "action": "Please contact your administrator to configure Confluence integration",
            }
        logger.error(f"Error searching Confluence pages: {e}", exc_info=True)
        return {"error": f"Failed to search Confluence pages: {str(e)}"}
    except Exception as e:
        logger.error(f"Error searching Confluence pages: {e}", exc_info=True)
        return {"error": f"Failed to search Confluence pages: {str(e)}"}


@tool
async def update_jira_issue(
    issue_key: str, summary: str = None, description: str = None, priority: str = None
) -> dict:
    """
    Update a JIRA issue's fields.

    Use this to modify issue details like summary, description, or priority.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        summary: New title/summary (optional)
        description: New description (optional)
        priority: New priority - 'Highest', 'High', 'Medium', 'Low', 'Lowest' (optional)

    Returns:
        Dictionary with update status
    """
    logger.info(f"Updating JIRA issue {issue_key}")
    try:
        from tools.jira_adapter import JiraAdapter

        adapter = JiraAdapter()

        success = await adapter.update_issue(
            issue_key=issue_key,
            summary=summary,
            description=description,
            priority=priority,
        )

        if success:
            logger.info(f"Successfully updated issue {issue_key}")
            return {
                "success": True,
                "message": f"Successfully updated {issue_key}",
                "issue_key": issue_key,
            }
        else:
            return {"success": False, "error": "Update failed", "issue_key": issue_key}
    except Exception as e:
        logger.error(f"Error updating issue {issue_key}: {e}", exc_info=True)
        return {"success": False, "error": str(e), "issue_key": issue_key}


@tool
async def add_jira_comment(issue_key: str, comment: str) -> dict:
    """
    Add a comment to a JIRA issue.

    Use this to add notes, updates, or feedback to an issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        comment: Comment text to add

    Returns:
        Dictionary with comment status
    """
    logger.info(f"Adding comment to JIRA issue {issue_key}")
    try:
        from tools.jira_adapter import JiraAdapter

        adapter = JiraAdapter()

        success = await adapter.add_comment(issue_key, comment)

        if success:
            logger.info(f"Successfully added comment to {issue_key}")
            return {
                "success": True,
                "message": f"Successfully added comment to {issue_key}",
                "issue_key": issue_key,
            }
        else:
            return {
                "success": False,
                "error": "Failed to add comment",
                "issue_key": issue_key,
            }
    except Exception as e:
        logger.error(f"Error adding comment to {issue_key}: {e}", exc_info=True)
        return {"success": False, "error": str(e), "issue_key": issue_key}


@tool
async def transition_jira_issue(issue_key: str, status: str) -> dict:
    """
    Change the status of a JIRA issue (e.g., move to 'In Progress' or 'Done').

    Use this to update the workflow status of an issue.
    Common statuses: 'To Do', 'In Progress', 'In Review', 'Done', 'Closed'

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        status: Target status name

    Returns:
        Dictionary with transition status
    """
    logger.info(f"Transitioning JIRA issue {issue_key} to {status}")
    try:
        from tools.jira_adapter import JiraAdapter

        adapter = JiraAdapter()

        success = await adapter.transition_issue(issue_key, status)

        if success:
            logger.info(f"Successfully transitioned {issue_key} to {status}")
            return {
                "success": True,
                "message": f"Successfully moved {issue_key} to {status}",
                "issue_key": issue_key,
                "new_status": status,
            }
        else:
            return {
                "success": False,
                "error": f"Could not transition to '{status}'. Status may not be available for this issue.",
                "issue_key": issue_key,
            }
    except Exception as e:
        logger.error(f"Error transitioning {issue_key}: {e}", exc_info=True)
        return {"success": False, "error": str(e), "issue_key": issue_key}


if __name__ == "__main__":
    # Test the Jira Worker Agent
    agent = create_jira_worker_agent()
    response = agent("What are my assigned tasks?")
    print(response)
