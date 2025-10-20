"""
JIRA REST API v3 Wrapper

This module provides a high-level interface for JIRA REST API v3 operations,
including issue retrieval, search, and user information.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from tools.atlassian_api_client import AtlassianAPIClient

logger = logging.getLogger(__name__)


class JiraAPI:
    """
    Wrapper for JIRA REST API v3.

    Provides high-level methods for common JIRA operations:
    - Fetching issues with filters
    - Searching issues with JQL
    - Getting issue details
    - Retrieving user information
    - Getting accessible resources (cloud IDs)
    """

    def __init__(self, api_client: AtlassianAPIClient, cloud_id: str):
        """
        Initialize JIRA API wrapper.

        Args:
            api_client: Authenticated Atlassian API client
            cloud_id: Atlassian cloud ID for the workspace
        """
        self.client = api_client
        self.cloud_id = cloud_id
        self.base_url = api_client.get_jira_base_url(cloud_id)

        logger.info(f"Initialized JIRA API wrapper for cloud ID: {cloud_id}")

    async def get_issues(
        self,
        jql: Optional[str] = None,
        assignee: Optional[str] = None,
        status: Optional[str] = None,
        max_results: int = 50,
        start_at: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Fetch JIRA issues with optional filters.

        This method constructs a JQL query based on the provided filters
        and retrieves matching issues from JIRA.

        Args:
            jql: Custom JQL query (if provided, other filters are ignored)
            assignee: Filter by assignee username or email
            status: Filter by status (e.g., "In Progress", "To Do")
            max_results: Maximum number of results to return (default: 50)
            start_at: Starting index for pagination (default: 0)

        Returns:
            List of issue dictionaries with parsed data

        Raises:
            requests.HTTPError: If API request fails
        """
        # Build JQL query if not provided
        if not jql:
            jql_parts = []

            if assignee:
                # Handle currentUser() function without quotes
                if assignee == "currentUser()":
                    jql_parts.append(f"assignee = {assignee}")
                else:
                    jql_parts.append(f'assignee = "{assignee}"')

            if status:
                jql_parts.append(f'status = "{status}"')

            # Default to ordering by updated date
            jql = " AND ".join(jql_parts) if jql_parts else "ORDER BY updated DESC"

            if jql_parts:
                jql += " ORDER BY updated DESC"

        logger.info(f"Fetching issues with JQL: {jql}")

        # Use search_issues method for the actual API call
        return await self.search_issues(
            jql=jql, max_results=max_results, start_at=start_at
        )

    async def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        start_at: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search issues using JQL (JIRA Query Language).

        Args:
            jql: JQL query string
            max_results: Maximum number of results to return (default: 50)
            start_at: Starting index for pagination (default: 0)
            fields: List of fields to include in response (default: all relevant fields)

        Returns:
            List of issue dictionaries with parsed data

        Raises:
            requests.HTTPError: If API request fails
        """
        # Default fields to retrieve
        if fields is None:
            fields = [
                "summary",
                "status",
                "description",
                "assignee",
                "duedate",
                "labels",
                "priority",
                "created",
                "updated",
                "comment",
            ]

        # Build query parameters
        params = {
            "jql": jql,
            "maxResults": max_results,
            "startAt": start_at,
            "fields": ",".join(fields),
        }

        # Use the new /search/jql endpoint (old /search was deprecated)
        # See: https://developer.atlassian.com/changelog/#CHANGE-2046
        url = f"{self.base_url}/rest/api/3/search/jql"

        logger.debug(f"Searching issues with params: {params}")

        try:
            response = await self.client.get(url, params=params)
            data = response.json()

            issues = data.get("issues", [])
            total = data.get("total", 0)

            logger.info(f"Retrieved {len(issues)} issues out of {total} total")

            # Parse and transform issues to match JiraIssue schema
            parsed_issues = [self._parse_issue(issue) for issue in issues]

            return parsed_issues

        except Exception as e:
            logger.error(f"Error searching issues with JQL '{jql}': {e}")
            raise

    async def get_issue_details(self, issue_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific issue.

        Retrieves comprehensive issue information including:
        - Summary, description, status
        - Assignee, reporter
        - Due date, priority
        - Labels, components
        - Comments
        - Linked pages

        Args:
            issue_key: JIRA issue key (e.g., "PROJ-123")

        Returns:
            Dictionary with comprehensive issue details

        Raises:
            requests.HTTPError: If API request fails or issue not found
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"

        # Request specific fields
        params = {
            "fields": "summary,status,description,assignee,duedate,labels,priority,created,updated,comment,issuelinks"
        }

        logger.info(f"Fetching details for issue: {issue_key}")

        try:
            response = await self.client.get(url, params=params)
            issue_data = response.json()

            # Parse and transform to match JiraIssue schema
            parsed_issue = self._parse_issue(issue_data)

            logger.info(f"Successfully retrieved details for {issue_key}")

            return parsed_issue

        except Exception as e:
            logger.error(f"Error fetching issue details for {issue_key}: {e}")
            raise

    async def get_current_user(self) -> Dict[str, Any]:
        """
        Get information about the currently authenticated user.

        Returns:
            Dictionary with user information:
            - accountId: User's account ID
            - emailAddress: User's email
            - displayName: User's display name
            - active: Whether user is active
            - timeZone: User's timezone

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.base_url}/rest/api/3/myself"

        logger.info("Fetching current user information")

        try:
            response = await self.client.get(url)
            user_data = response.json()

            logger.info(
                f"Current user: {user_data.get('displayName')} ({user_data.get('emailAddress')})"
            )

            return {
                "account_id": user_data.get("accountId"),
                "email": user_data.get("emailAddress"),
                "display_name": user_data.get("displayName"),
                "active": user_data.get("active", True),
                "timezone": user_data.get("timeZone"),
            }

        except Exception as e:
            logger.error(f"Error fetching current user: {e}")
            raise

    async def get_accessible_resources(self) -> List[Dict[str, Any]]:
        """
        Get list of accessible Atlassian resources (cloud IDs).

        This endpoint returns all Atlassian sites/workspaces that the
        authenticated user has access to. Each resource includes:
        - id: Cloud ID
        - name: Site name
        - url: Site URL
        - scopes: Available scopes
        - avatarUrl: Site avatar

        Returns:
            List of accessible resource dictionaries

        Raises:
            requests.HTTPError: If API request fails
        """
        url = "https://api.atlassian.com/oauth/token/accessible-resources"

        logger.info("Fetching accessible Atlassian resources")

        try:
            response = await self.client.get(url)
            resources = response.json()

            logger.info(f"Found {len(resources)} accessible resources")

            parsed_resources = []
            for resource in resources:
                parsed_resources.append(
                    {
                        "id": resource.get("id"),
                        "name": resource.get("name"),
                        "url": resource.get("url"),
                        "scopes": resource.get("scopes", []),
                        "avatar_url": resource.get("avatarUrl"),
                    }
                )

            return parsed_resources

        except Exception as e:
            logger.error(f"Error fetching accessible resources: {e}")
            raise

    def _parse_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JIRA API response and transform to match JiraIssue schema.

        Extracts relevant fields from the JIRA API response format and
        transforms them into the format expected by the JiraIssue schema.

        Args:
            issue_data: Raw issue data from JIRA API

        Returns:
            Dictionary matching JiraIssue schema format
        """
        fields = issue_data.get("fields", {})

        # Extract key (it's at the root level, not in fields)
        key = issue_data.get("key", "")

        # Extract summary
        summary = fields.get("summary", "")

        # Extract status
        status_obj = fields.get("status", {})
        status = status_obj.get("name", "Unknown")

        # Extract description
        description = self._extract_description(fields.get("description"))

        # Extract assignee
        assignee_obj = fields.get("assignee")
        assignee = None
        if assignee_obj:
            assignee = assignee_obj.get("displayName") or assignee_obj.get(
                "emailAddress"
            )

        # Extract due date
        due_date = None
        due_date_str = fields.get("duedate")
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse due date: {due_date_str}")

        # Extract labels
        labels = fields.get("labels", [])

        # Extract linked Confluence pages from issue links
        linked_pages = self._extract_linked_pages(fields.get("issuelinks", []))

        # Extract priority (optional, for additional context)
        priority_obj = fields.get("priority")
        priority = priority_obj.get("name") if priority_obj else None

        return {
            "key": key,
            "summary": summary,
            "status": status,
            "description": description,
            "assignee": assignee,
            "due_date": due_date,
            "labels": labels,
            "linked_pages": linked_pages,
            "priority": priority,  # Additional field not in base schema but useful
        }

    def _extract_description(self, description_obj: Any) -> Optional[str]:
        """
        Extract description text from JIRA's Atlassian Document Format (ADF).

        JIRA API v3 returns descriptions in ADF format (JSON structure).
        This method extracts plain text from the ADF structure.

        Args:
            description_obj: Description object from JIRA API (can be ADF or string)

        Returns:
            Plain text description or None
        """
        if not description_obj:
            return None

        # If it's already a string, return it
        if isinstance(description_obj, str):
            return description_obj

        # If it's ADF format (dict with 'content' key)
        if isinstance(description_obj, dict):
            content = description_obj.get("content", [])
            text_parts = []

            # Recursively extract text from ADF nodes
            def extract_text(node):
                if isinstance(node, dict):
                    # If node has text, add it
                    if "text" in node:
                        text_parts.append(node["text"])

                    # Recursively process content
                    if "content" in node:
                        for child in node["content"]:
                            extract_text(child)

                elif isinstance(node, list):
                    for item in node:
                        extract_text(item)

            extract_text(content)

            return " ".join(text_parts) if text_parts else None

        return None

    def _extract_linked_pages(self, issue_links: List[Dict[str, Any]]) -> List[str]:
        """
        Extract Confluence page links from issue links.

        Args:
            issue_links: List of issue link objects from JIRA API

        Returns:
            List of Confluence page URLs or identifiers
        """
        linked_pages = []

        # Note: This is a simplified implementation
        # In practice, Confluence links might be in different formats
        # or require additional API calls to resolve

        for link in issue_links:
            # Check if link is to a Confluence page
            # This would need to be adapted based on actual link structure
            _ = link.get("inwardIssue", {})
            _ = link.get("outwardIssue", {})

            # For now, we'll just note that linked pages would be extracted here
            # The actual implementation depends on how Confluence pages are linked
            pass

        return linked_pages

    async def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> bool:
        """
        Update a JIRA issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            fields: Dictionary of fields to update
                   Common fields:
                   - summary: str
                   - description: str
                   - assignee: {"accountId": "xxx"}
                   - priority: {"name": "High"}
                   - labels: ["label1", "label2"]

        Returns:
            bool: True if successful

        Raises:
            APIError: If update fails
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"

        payload = {"fields": fields}

        logger.info(f"Updating issue {issue_key} with fields: {list(fields.keys())}")

        try:
            _ = await self.client.put(url, json=payload)
            logger.info(f"Successfully updated issue {issue_key}")
            return True
        except Exception as e:
            logger.error(f"Error updating issue {issue_key}: {e}")
            raise

    async def add_comment(self, issue_key: str, comment_text: str) -> Dict[str, Any]:
        """
        Add a comment to a JIRA issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            comment_text: Comment text (supports Atlassian Document Format)

        Returns:
            Dict with comment details

        Raises:
            APIError: If adding comment fails
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"

        # Use Atlassian Document Format (ADF)
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment_text}],
                    }
                ],
            }
        }

        logger.info(f"Adding comment to issue {issue_key}")

        try:
            response = await self.client.post(url, json=payload)
            comment_data = response.json()
            logger.info(f"Successfully added comment to {issue_key}")
            return comment_data
        except Exception as e:
            logger.error(f"Error adding comment to {issue_key}: {e}")
            raise

    async def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        fields: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Transition a JIRA issue to a new status.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            transition_id: ID of the transition to perform
            fields: Optional fields to update during transition

        Returns:
            bool: True if successful

        Raises:
            APIError: If transition fails
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"

        payload = {"transition": {"id": transition_id}}

        if fields:
            payload["fields"] = fields

        logger.info(
            f"Transitioning issue {issue_key} with transition ID {transition_id}"
        )

        try:
            _ = await self.client.post(url, json=payload)
            logger.info(f"Successfully transitioned issue {issue_key}")
            return True
        except Exception as e:
            logger.error(f"Error transitioning issue {issue_key}: {e}")
            raise

    async def get_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get available transitions for an issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')

        Returns:
            List of available transitions with IDs and names
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"

        logger.info(f"Fetching available transitions for {issue_key}")

        try:
            response = await self.client.get(url)
            data = response.json()
            transitions = data.get("transitions", [])

            logger.info(
                f"Found {len(transitions)} available transitions for {issue_key}"
            )
            return transitions
        except Exception as e:
            logger.error(f"Error fetching transitions for {issue_key}: {e}")
            raise

    async def get_issues_paginated(
        self, jql: str, max_results: int = 50, page_size: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch all issues matching JQL query with automatic pagination.

        This method handles pagination automatically, fetching all results
        up to max_results by making multiple API calls if necessary.

        Args:
            jql: JQL query string
            max_results: Maximum total results to return
            page_size: Number of results per API call (max 100)

        Returns:
            List of all matching issues

        Raises:
            requests.HTTPError: If any API request fails
        """
        all_issues = []
        start_at = 0
        page_size = min(page_size, 100)  # JIRA API max is 100

        logger.info(f"Fetching paginated results for JQL: {jql}")

        while len(all_issues) < max_results:
            # Calculate how many results to fetch in this batch
            batch_size = min(page_size, max_results - len(all_issues))

            # Fetch batch
            batch = await self.search_issues(
                jql=jql, max_results=batch_size, start_at=start_at
            )

            if not batch:
                # No more results
                break

            all_issues.extend(batch)
            start_at += len(batch)

            # If we got fewer results than requested, we've reached the end
            if len(batch) < batch_size:
                break

            logger.debug(f"Fetched {len(all_issues)} issues so far")

        logger.info(f"Completed pagination: {len(all_issues)} total issues")

        return all_issues
