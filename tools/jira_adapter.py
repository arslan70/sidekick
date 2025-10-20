"""
Jira adapter for MVP.

Provides interface to fetch and process Jira issues.
Automatically detects OAuth credentials and uses real Atlassian JIRA API when available,
falling back to static JSON data when credentials are not configured.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from tools.schemas import JiraIssue

logger = logging.getLogger(__name__)


class JiraAdapter:
    """
    Unified JIRA adapter with automatic data source detection.

    Automatically detects available credentials and uses:
    - Real Atlassian JIRA REST API v3 with OAuth when credentials are configured
    - Local JSON data from configs/jira_data.json when credentials are not available
    """

    def __init__(self):
        """
        Initialize the Jira adapter with automatic credential detection.

        The adapter checks for OAuth credentials and automatically uses the real API
        when available, falling back to static data otherwise.
        """
        self.data_path = Path(__file__).parent.parent / "configs" / "jira_data.json"
        self.jira_api = None
        self.use_static_data = True

        # Try to initialize real API if credentials are available
        if self._has_credentials():
            try:
                self.jira_api = self._initialize_real_api()
                self.use_static_data = False
                logger.info(
                    "JIRA adapter initialized with real API (OAuth credentials detected)"
                )
            except Exception as e:
                logger.error(
                    f"Failed to initialize real JIRA API, using static data: {e}",
                    exc_info=True,
                )
                self.use_static_data = True
        else:
            logger.info(
                "JIRA adapter initialized with static data (no OAuth credentials configured)"
            )

    def _has_credentials(self) -> bool:
        """
        Check if required OAuth credentials are available.

        Returns:
            True if OAuth credentials are configured, False otherwise
        """
        client_id = os.getenv("ATLASSIAN_OAUTH_CLIENT_ID", "").strip()
        cloud_id = os.getenv("ATLASSIAN_CLOUD_ID", "").strip()
        has_creds = bool(client_id and cloud_id)

        if not has_creds:
            logger.debug(
                f"Credentials check: client_id={'present' if client_id else 'missing'}, cloud_id={'present' if cloud_id else 'missing'}"
            )

        return has_creds

    def _initialize_real_api(self):
        """
        Initialize real JIRA API client with OAuth.

        Returns:
            JiraAPI instance configured with OAuth authentication

        Raises:
            ValueError: If OAuth configuration is missing or invalid
            ImportError: If required modules are not available
        """
        from tools.atlassian_api_client import AtlassianAPIClient
        from tools.atlassian_jira_api import JiraAPI
        from tools.atlassian_oauth_config import AtlassianOAuthConfig

        # Load OAuth configuration from environment
        oauth_config = AtlassianOAuthConfig.from_env()

        if not oauth_config.is_configured():
            raise ValueError("Atlassian OAuth is not properly configured")

        # Initialize token manager based on available token source
        # Priority: 1) Environment variable (from Chainlit UI), 2) AgentCore Identity, 3) In-memory
        if os.getenv("ATLASSIAN_ACCESS_TOKEN"):
            # Use environment variable token manager (token passed from Chainlit UI)
            from tools.env_token_manager import EnvTokenManager

            token_manager = EnvTokenManager(
                user_id=oauth_config.demo_user_id,
                oauth_config=oauth_config,
            )
            logger.info("✅ Using Environment Token Manager for JIRA (token from Chainlit UI)")
        elif oauth_config.agentcore_identity_arn:
            # Use AgentCore for production
            from tools.agentcore_token_manager import AgentCoreTokenManager

            token_manager = AgentCoreTokenManager(
                identity_arn=oauth_config.agentcore_identity_arn,
                user_id=oauth_config.demo_user_id,
                oauth_config=oauth_config,
            )
            logger.info("Using AgentCore Token Manager for JIRA")
        else:
            # Use simple in-memory token manager for development
            from tools.simple_token_manager import SimpleTokenManager

            token_manager = SimpleTokenManager(
                identity_arn="dev-mode",
                user_id=oauth_config.demo_user_id,
                oauth_config=oauth_config,
            )
            logger.info("Using Simple Token Manager for JIRA (in-memory storage)")

        # Initialize API client
        api_client = AtlassianAPIClient(
            token_manager=token_manager, oauth_config=oauth_config
        )

        # Get cloud ID from environment or fetch from accessible resources
        cloud_id = os.getenv("ATLASSIAN_CLOUD_ID", "").strip()

        if not cloud_id:
            raise ValueError(
                "ATLASSIAN_CLOUD_ID environment variable is required for real mode"
            )

        # Initialize JIRA API wrapper
        jira_api = JiraAPI(api_client=api_client, cloud_id=cloud_id)

        return jira_api

    def _load_from_static_data(self, limit: int = 100) -> List[JiraIssue]:
        """
        Load issues from static JSON data file.

        Args:
            limit: Maximum number of issues to return

        Returns:
            List of JiraIssue objects from local JSON file
        """
        if self.data_path.exists():
            with open(self.data_path, "r") as f:
                data = json.load(f)
                issues = []
                for issue_data in data[:limit]:
                    # Parse due_date
                    if issue_data.get("due_date"):
                        issue_data["due_date"] = datetime.fromisoformat(
                            issue_data["due_date"]
                        )
                    issues.append(JiraIssue(**issue_data))
                return issues
        return []

    async def _fetch_from_api(
        self, method: str, **kwargs
    ) -> List[JiraIssue] | Optional[JiraIssue]:
        """
        Fetch data from real JIRA API based on the specified method.

        Args:
            method: The type of fetch operation to perform
            **kwargs: Additional parameters for the specific method

        Returns:
            List of JiraIssue objects or a single JiraIssue (for get_details)
        """
        if not self.jira_api:
            raise ValueError("JIRA API not initialized")

        if method == "get_all":
            limit = kwargs.get("limit", 50)
            # Add a bounded query - get all issues from any project
            jql = "project is not EMPTY ORDER BY updated DESC"
            issues_data = await self.jira_api.search_issues(jql=jql, max_results=limit)
            return [
                self._convert_api_to_schema(issue_data) for issue_data in issues_data
            ]

        elif method == "get_assigned":
            assignee = kwargs.get("assignee")
            if not assignee:
                # Use currentUser() in JQL instead of fetching account ID
                # This is more reliable and works across all Jira instances
                assignee = "currentUser()"

            issues_data = await self.jira_api.get_issues(
                assignee=assignee, max_results=100
            )
            return [
                self._convert_api_to_schema(issue_data) for issue_data in issues_data
            ]

        elif method == "get_by_status":
            status = kwargs.get("status")
            issues_data = await self.jira_api.get_issues(status=status, max_results=100)
            return [
                self._convert_api_to_schema(issue_data) for issue_data in issues_data
            ]

        elif method == "get_high_priority":
            # Build JQL for high priority issues
            jql_parts = [
                "priority in (High, Highest, Critical)",
                "duedate <= 3d",
                "labels in (high-priority, critical, urgent)",
            ]
            jql = f"({' OR '.join(jql_parts)}) ORDER BY priority DESC, duedate ASC"
            issues_data = await self.jira_api.search_issues(jql=jql, max_results=100)
            return [
                self._convert_api_to_schema(issue_data) for issue_data in issues_data
            ]

        elif method == "get_details":
            issue_key = kwargs.get("issue_key")
            try:
                issue_data = await self.jira_api.get_issue_details(issue_key)
                return self._convert_api_to_schema(issue_data)
            except Exception as e:
                logger.error(f"Error fetching issue details for {issue_key}: {e}")
                return None

        elif method == "search":
            keyword = kwargs.get("keyword")
            jql = f'text ~ "{keyword}" ORDER BY updated DESC'
            issues_data = await self.jira_api.search_issues(jql=jql, max_results=100)
            return [
                self._convert_api_to_schema(issue_data) for issue_data in issues_data
            ]

        else:
            raise ValueError(f"Unknown method: {method}")

    async def get_all_issues(self, limit: int = 50) -> List[JiraIssue]:
        """
        Fetch all Jira issues from real API or static data.

        Args:
            limit: Maximum number of issues to return

        Returns:
            List of JiraIssue objects.
        """
        if self.use_static_data:
            return self._load_from_static_data(limit=limit)
        return await self._fetch_from_api(method="get_all", limit=limit)

    async def get_assigned_issues(
        self, assignee: Optional[str] = None
    ) -> List[JiraIssue]:
        """
        Fetch issues assigned to a specific user from real API or static data.

        Args:
            assignee: Username to filter by. If None, returns all issues.

        Returns:
            List of assigned JiraIssue objects.
        """
        if self.use_static_data:
            all_issues = self._load_from_static_data(limit=100)
            if assignee:
                return [issue for issue in all_issues if issue.assignee == assignee]
            return all_issues

        try:
            return await self._fetch_from_api(method="get_assigned", assignee=assignee)
        except Exception as e:
            # If API fails with 410, fall back to static data
            if "410" in str(e):
                logger.warning(
                    "Jira API returned 410 Gone - falling back to static data. This may indicate the Jira instance has restricted API access or is using a different product (Jira Work Management/Service Management)."
                )
                logger.warning("Using static demo data instead.")
                all_issues = self._load_from_static_data(limit=100)
                if assignee and assignee != "currentUser()":
                    return [issue for issue in all_issues if issue.assignee == assignee]
                return all_issues
            raise

    async def get_issues_by_status(self, status: str) -> List[JiraIssue]:
        """
        Fetch issues filtered by status from real API or static data.

        Args:
            status: Status to filter by (e.g., 'In Progress', 'To Do', 'Code Review')

        Returns:
            List of JiraIssue objects matching the status.
        """
        if self.use_static_data:
            all_issues = self._load_from_static_data(limit=100)
            return [
                issue for issue in all_issues if issue.status.lower() == status.lower()
            ]
        return await self._fetch_from_api(method="get_by_status", status=status)

    async def get_high_priority_issues(self) -> List[JiraIssue]:
        """
        Fetch high-priority issues (based on labels or due date) from real API or static data.

        Returns:
            List of high-priority JiraIssue objects.
        """
        if self.use_static_data:
            all_issues = self._load_from_static_data(limit=100)
            high_priority = []
            for issue in all_issues:
                # Consider high priority if:
                # - Has 'high-priority' or 'critical' label
                # - Due date is within 3 days
                is_priority_label = any(
                    label.lower() in ["high-priority", "critical", "urgent"]
                    for label in issue.labels
                )
                is_due_soon = False
                if issue.due_date:
                    days_until_due = (issue.due_date - datetime.now()).days
                    is_due_soon = days_until_due <= 3

                if is_priority_label or is_due_soon:
                    high_priority.append(issue)

            return high_priority
        return await self._fetch_from_api(method="get_high_priority")

    async def get_issue_details(self, issue_key: str) -> Optional[JiraIssue]:
        """
        Get detailed information about a specific Jira issue from real API or static data.

        Args:
            issue_key: The Jira issue key (e.g., 'ENG-123')

        Returns:
            JiraIssue object or None if not found.
        """
        if self.use_static_data:
            all_issues = self._load_from_static_data(limit=100)
            for issue in all_issues:
                if issue.key.upper() == issue_key.upper():
                    return issue
            return None
        return await self._fetch_from_api(method="get_details", issue_key=issue_key)

    async def search_issues_by_summary(self, keyword: str) -> List[JiraIssue]:
        """
        Search for issues by keyword in summary from real API or static data.

        Args:
            keyword: Keyword to search for in issue summaries

        Returns:
            List of matching JiraIssue objects.
        """
        if self.use_static_data:
            all_issues = self._load_from_static_data(limit=100)
            keyword_lower = keyword.lower()
            return [
                issue for issue in all_issues if keyword_lower in issue.summary.lower()
            ]
        return await self._fetch_from_api(method="search", keyword=keyword)

    async def update_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        assignee_account_id: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> bool:
        """
        Update a JIRA issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            summary: New summary/title
            description: New description
            assignee_account_id: Account ID of new assignee
            priority: Priority name (e.g., 'High', 'Medium', 'Low')
            labels: List of labels

        Returns:
            bool: True if successful
        """
        if self.use_static_data:
            logger.warning("Cannot update issues in static data mode")
            return False

        fields = {}

        if summary:
            fields["summary"] = summary

        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            }

        if assignee_account_id:
            fields["assignee"] = {"accountId": assignee_account_id}

        if priority:
            fields["priority"] = {"name": priority}

        if labels is not None:
            fields["labels"] = labels

        if not fields:
            logger.warning("No fields to update")
            return False

        return await self.jira_api.update_issue(issue_key, fields)

    async def add_comment(self, issue_key: str, comment: str) -> bool:
        """
        Add a comment to a JIRA issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            comment: Comment text

        Returns:
            bool: True if successful
        """
        if self.use_static_data:
            logger.warning("Cannot add comments in static data mode")
            return False

        try:
            await self.jira_api.add_comment(issue_key, comment)
            return True
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return False

    async def transition_issue(self, issue_key: str, status_name: str) -> bool:
        """
        Transition a JIRA issue to a new status.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            status_name: Target status name (e.g., 'In Progress', 'Done')

        Returns:
            bool: True if successful
        """
        if self.use_static_data:
            logger.warning("Cannot transition issues in static data mode")
            return False

        try:
            # Get available transitions
            transitions = await self.jira_api.get_transitions(issue_key)

            # Find matching transition
            transition = next(
                (t for t in transitions if t["name"].lower() == status_name.lower()),
                None,
            )

            if not transition:
                logger.error(
                    f"No transition found for status '{status_name}'. Available: {[t['name'] for t in transitions]}"
                )
                return False

            # Perform transition
            return await self.jira_api.transition_issue(issue_key, transition["id"])
        except Exception as e:
            logger.error(f"Error transitioning issue: {e}")
            return False

    def _convert_api_to_schema(self, api_data: dict) -> JiraIssue:
        """
        Convert JIRA API response format to JiraIssue schema.

        Args:
            api_data: Issue data from JIRA API (already parsed by JiraAPI wrapper)

        Returns:
            JiraIssue object matching the schema
        """
        # The JiraAPI wrapper already parses the data into the correct format
        # We just need to ensure it matches the JiraIssue schema
        return JiraIssue(
            key=api_data.get("key", ""),
            summary=api_data.get("summary", ""),
            status=api_data.get("status", "Unknown"),
            description=api_data.get("description"),
            assignee=api_data.get("assignee"),
            due_date=api_data.get("due_date"),
            labels=api_data.get("labels", []),
            linked_pages=api_data.get("linked_pages", []),
        )


# Convenience functions for direct use
async def fetch_all_issues(limit: int = 50) -> dict:
    """
    Fetch all Jira issues.

    Returns:
        Dictionary with issue summaries and metadata.
    """
    adapter = JiraAdapter()
    issues = await adapter.get_all_issues(limit=limit)

    return {
        "total_count": len(issues),
        "issues": [
            {
                "key": issue.key,
                "summary": issue.summary,
                "status": issue.status,
                "assignee": issue.assignee,
                "due_date": issue.due_date.isoformat() if issue.due_date else None,
                "labels": issue.labels,
            }
            for issue in issues
        ],
    }


async def fetch_assigned_issues(assignee: Optional[str] = None) -> dict:
    """
    Fetch issues assigned to a specific user.

    Args:
        assignee: Username to filter by. If None, fetches issues for the authenticated user.

    Returns:
        Dictionary with assigned issue summaries.
    """
    adapter = JiraAdapter()
    issues = await adapter.get_assigned_issues(assignee)

    # Get demo user ID for display
    demo_user = os.getenv("DEMO_USER_ID", "current user")
    display_assignee = assignee if assignee else demo_user

    return {
        "assignee": display_assignee,
        "total_count": len(issues),
        "issues": [
            {
                "key": issue.key,
                "summary": issue.summary,
                "status": issue.status,
                "due_date": issue.due_date.isoformat() if issue.due_date else None,
                "labels": issue.labels,
            }
            for issue in issues
        ],
    }


async def fetch_high_priority_issues() -> dict:
    """
    Fetch high-priority Jira issues.

    Returns:
        Dictionary with high-priority issue summaries.
    """
    adapter = JiraAdapter()
    issues = await adapter.get_high_priority_issues()

    return {
        "total_count": len(issues),
        "issues": [
            {
                "key": issue.key,
                "summary": issue.summary,
                "status": issue.status,
                "assignee": issue.assignee,
                "due_date": issue.due_date.isoformat() if issue.due_date else None,
                "labels": issue.labels,
                "description": (
                    issue.description[:200] + "..."
                    if len(issue.description or "") > 200
                    else issue.description
                ),
            }
            for issue in issues
        ],
    }


async def fetch_issue_details(issue_key: str) -> dict:
    """
    Get detailed information about a specific Jira issue.

    Returns:
        Dictionary with full issue details.
    """
    adapter = JiraAdapter()
    issue = await adapter.get_issue_details(issue_key)

    if not issue:
        return {"error": f"Issue {issue_key} not found"}

    return {
        "key": issue.key,
        "summary": issue.summary,
        "status": issue.status,
        "description": issue.description,
        "assignee": issue.assignee,
        "due_date": issue.due_date.isoformat() if issue.due_date else None,
        "labels": issue.labels,
        "linked_pages": issue.linked_pages,
    }


async def search_issues(keyword: str) -> dict:
    """
    Search for Jira issues by keyword.

    Returns:
        Dictionary with matching issues.
    """
    adapter = JiraAdapter()
    issues = await adapter.search_issues_by_summary(keyword)

    return {
        "keyword": keyword,
        "total_count": len(issues),
        "issues": [
            {
                "key": issue.key,
                "summary": issue.summary,
                "status": issue.status,
                "assignee": issue.assignee,
            }
            for issue in issues
        ],
    }


async def fetch_issues_by_status(status: str) -> dict:
    """
    Fetch issues filtered by status.

    Returns:
        Dictionary with issues matching the status.
    """
    adapter = JiraAdapter()
    issues = await adapter.get_issues_by_status(status)

    return {
        "status": status,
        "total_count": len(issues),
        "issues": [
            {
                "key": issue.key,
                "summary": issue.summary,
                "assignee": issue.assignee,
                "due_date": issue.due_date.isoformat() if issue.due_date else None,
                "labels": issue.labels,
            }
            for issue in issues
        ],
    }
