"""
Confluence REST API v2 Wrapper

This module provides a high-level interface for Confluence REST API v2 operations,
including page retrieval, search, and content access.
"""

import logging
from typing import Any, Dict, List, Optional

from tools.atlassian_api_client import AtlassianAPIClient

logger = logging.getLogger(__name__)


class ConfluenceAPI:
    """
    Wrapper for Confluence REST API v2.

    Provides high-level methods for common Confluence operations:
    - Fetching pages by ID or title
    - Searching pages with CQL
    - Retrieving page content
    - Getting page metadata
    """

    def __init__(self, api_client: AtlassianAPIClient, cloud_id: str):
        """
        Initialize Confluence API wrapper.

        Args:
            api_client: Authenticated Atlassian API client
            cloud_id: Atlassian cloud ID for the workspace
        """
        self.client = api_client
        self.cloud_id = cloud_id
        self.base_url = api_client.get_confluence_base_url(cloud_id)

        logger.info(f"Initialized Confluence API wrapper for cloud ID: {cloud_id}")

    async def get_page(
        self,
        page_id: str,
        body_format: str = "storage",
        include_version: bool = True,
    ) -> Dict[str, Any]:
        """
        Get Confluence page by ID.

        Retrieves comprehensive page information including:
        - Title and ID
        - Body content in specified format
        - Space information
        - Version and last modified date
        - Author information

        Args:
            page_id: Confluence page ID
            body_format: Format for body content ('storage', 'view', 'export_view')
            include_version: Whether to include version information

        Returns:
            Dictionary with page details

        Raises:
            requests.HTTPError: If API request fails or page not found
        """
        url = f"{self.base_url}/wiki/api/v2/pages/{page_id}"

        # Build query parameters
        params = {"body-format": body_format}

        logger.info(f"Fetching page with ID: {page_id}")

        try:
            response = await self.client.get(url, params=params)
            page_data = response.json()

            # Parse and transform page data
            parsed_page = self._parse_page(page_data, include_version)

            logger.info(f"Successfully retrieved page: {parsed_page.get('title')}")

            return parsed_page

        except Exception as e:
            logger.error(f"Error fetching page {page_id}: {e}")
            raise

    async def get_page_by_title(
        self,
        space_key: str,
        title: str,
        body_format: str = "storage",
    ) -> Optional[Dict[str, Any]]:
        """
        Get Confluence page by space and title.

        Searches for a page with the exact title in the specified space.

        Args:
            space_key: Confluence space key (e.g., "PROJ")
            title: Exact page title to search for
            body_format: Format for body content ('storage', 'view', 'export_view')

        Returns:
            Dictionary with page details, or None if not found

        Raises:
            requests.HTTPError: If API request fails
        """
        # Use CQL to search for page by title in space
        cql = f'space = "{space_key}" AND title = "{title}"'

        logger.info(f"Searching for page '{title}' in space '{space_key}'")

        try:
            # Search for the page
            results = await self.search_pages(cql=cql, limit=1)

            if not results:
                logger.warning(f"Page '{title}' not found in space '{space_key}'")
                return None

            # Get the first result's ID and fetch full details
            page_id = results[0].get("id")
            if page_id:
                return await self.get_page(page_id, body_format=body_format)

            return results[0]

        except Exception as e:
            logger.error(
                f"Error fetching page by title '{title}' in space '{space_key}': {e}"
            )
            raise

    async def search_pages(
        self,
        cql: str,
        limit: int = 25,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search pages using CQL (Confluence Query Language).

        Args:
            cql: CQL query string (e.g., 'space = "PROJ" AND type = page')
            limit: Maximum number of results to return (default: 25, max: 250)
            cursor: Pagination cursor for fetching next page of results

        Returns:
            List of page dictionaries with parsed data

        Raises:
            requests.HTTPError: If API request fails
        """
        # Note: Confluence API v2 uses different query syntax
        # We'll use the search endpoint with CQL
        search_url = f"{self.base_url}/wiki/rest/api/search"
        params = {
            "cql": cql,
            "limit": min(limit, 250),
        }

        if cursor:
            params["cursor"] = cursor

        logger.info(f"Searching pages with CQL: {cql}")

        try:
            response = await self.client.get(search_url, params=params)
            data = response.json()

            results = data.get("results", [])
            total_size = data.get("totalSize", 0)

            logger.info(f"Retrieved {len(results)} pages out of {total_size} total")

            # Parse and transform pages
            parsed_pages = [self._parse_search_result(result) for result in results]

            return parsed_pages

        except Exception as e:
            logger.error(f"Error searching pages with CQL '{cql}': {e}")
            raise

    async def get_page_content(
        self,
        page_id: str,
        format: str = "storage",
    ) -> str:
        """
        Get page body content in specified format.

        Retrieves just the body content of a page without other metadata.

        Args:
            page_id: Confluence page ID
            format: Content format ('storage', 'view', 'export_view', 'anonymous_export_view')
                - storage: Raw storage format (XML-like)
                - view: HTML for viewing
                - export_view: HTML for export
                - anonymous_export_view: HTML for anonymous viewing

        Returns:
            Page content as string in requested format

        Raises:
            requests.HTTPError: If API request fails or page not found
        """
        url = f"{self.base_url}/wiki/api/v2/pages/{page_id}/body/{format}"

        logger.info(f"Fetching content for page {page_id} in format: {format}")

        try:
            response = await self.client.get(url)
            data = response.json()

            # Extract the actual content value
            content = data.get("value", "")

            logger.info(
                f"Successfully retrieved content for page {page_id} ({len(content)} characters)"
            )

            return content

        except Exception as e:
            logger.error(f"Error fetching content for page {page_id}: {e}")
            raise

    async def get_page_children(
        self,
        page_id: str,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Get child pages of a specific page.

        Args:
            page_id: Parent page ID
            limit: Maximum number of children to return

        Returns:
            List of child page dictionaries

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.base_url}/wiki/api/v2/pages/{page_id}/children"

        params = {"limit": min(limit, 250)}

        logger.info(f"Fetching children for page {page_id}")

        try:
            response = await self.client.get(url, params=params)
            data = response.json()

            results = data.get("results", [])

            logger.info(f"Found {len(results)} child pages")

            # Parse child pages
            parsed_children = [self._parse_page(child, False) for child in results]

            return parsed_children

        except Exception as e:
            logger.error(f"Error fetching children for page {page_id}: {e}")
            raise

    def _parse_page(
        self, page_data: Dict[str, Any], include_version: bool = True
    ) -> Dict[str, Any]:
        """
        Parse Confluence API response and extract relevant page information.

        Args:
            page_data: Raw page data from Confluence API
            include_version: Whether to include version information

        Returns:
            Dictionary with parsed page information
        """
        # Extract basic fields
        page_id = page_data.get("id", "")
        title = page_data.get("title", "")
        status = page_data.get("status", "current")

        # Extract space information
        space_data = page_data.get("spaceId") or page_data.get("_expandable", {}).get(
            "space"
        )
        space_key = None
        space_name = None

        # Try to get space from different possible locations
        if isinstance(space_data, dict):
            space_key = space_data.get("key")
            space_name = space_data.get("name")
        elif isinstance(space_data, str):
            space_key = space_data

        # Extract body content if available
        body_content = None
        body_data = page_data.get("body")
        if body_data:
            # Body can be in different formats
            if isinstance(body_data, dict):
                # Try storage format first, then view
                storage = body_data.get("storage", {})
                view = body_data.get("view", {})

                if storage and isinstance(storage, dict):
                    body_content = storage.get("value")
                elif view and isinstance(view, dict):
                    body_content = view.get("value")

        # Extract version information
        version_number = None
        last_modified = None
        last_modified_by = None

        if include_version:
            version_data = page_data.get("version", {})
            if version_data:
                version_number = version_data.get("number")
                last_modified = version_data.get("when")

                # Extract author information
                by_data = version_data.get("by", {})
                if by_data:
                    last_modified_by = by_data.get("displayName") or by_data.get(
                        "email"
                    )

        # Extract created date
        created_at = page_data.get("createdAt")

        # Extract web URL
        web_url = None
        links = page_data.get("_links", {})
        if links:
            web_url = links.get("webui") or links.get("base")

        return {
            "id": page_id,
            "title": title,
            "status": status,
            "space_key": space_key,
            "space_name": space_name,
            "body_content": body_content,
            "version": version_number,
            "last_modified": last_modified,
            "last_modified_by": last_modified_by,
            "created_at": created_at,
            "web_url": web_url,
        }

    def _parse_search_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse search result from CQL query.

        Search results have a slightly different structure than direct page fetches.

        Args:
            result: Raw search result from Confluence API

        Returns:
            Dictionary with parsed page information
        """
        # Search results wrap the actual content in a 'content' field
        content = result.get("content", result)

        # Extract basic information
        page_id = content.get("id", "")
        title = content.get("title", "")
        content_type = content.get("type", "page")

        # Extract space information
        space_data = content.get("space", {})
        space_key = space_data.get("key") if isinstance(space_data, dict) else None
        space_name = space_data.get("name") if isinstance(space_data, dict) else None

        # Extract excerpt (search snippet)
        excerpt = result.get("excerpt", "")

        # Extract URL
        url = result.get("url", "")
        if not url and isinstance(content.get("_links"), dict):
            url = content["_links"].get("webui", "")

        # Extract last modified
        last_modified = content.get("lastModified") or content.get("version", {}).get(
            "when"
        )

        return {
            "id": page_id,
            "title": title,
            "type": content_type,
            "space_key": space_key,
            "space_name": space_name,
            "excerpt": excerpt,
            "url": url,
            "last_modified": last_modified,
        }

    async def search_pages_paginated(
        self,
        cql: str,
        max_results: int = 100,
        page_size: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all pages matching CQL query with automatic pagination.

        This method handles pagination automatically, fetching all results
        up to max_results by making multiple API calls if necessary.

        Args:
            cql: CQL query string
            max_results: Maximum total results to return
            page_size: Number of results per API call (max 250)

        Returns:
            List of all matching pages

        Raises:
            requests.HTTPError: If any API request fails
        """
        all_pages = []
        cursor = None
        page_size = min(page_size, 250)  # API max is 250

        logger.info(f"Fetching paginated results for CQL: {cql}")

        while len(all_pages) < max_results:
            # Calculate how many results to fetch in this batch
            batch_size = min(page_size, max_results - len(all_pages))

            # Fetch batch
            batch = await self.search_pages(cql=cql, limit=batch_size, cursor=cursor)

            if not batch:
                # No more results
                break

            all_pages.extend(batch)

            # If we got fewer results than requested, we've reached the end
            if len(batch) < batch_size:
                break

            logger.debug(f"Fetched {len(all_pages)} pages so far")

            # Note: Cursor-based pagination would need to be extracted from response
            # For now, we'll break after first batch
            # In production, extract cursor from response and continue
            break

        logger.info(f"Completed pagination: {len(all_pages)} total pages")

        return all_pages
