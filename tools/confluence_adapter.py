"""
Confluence adapter for MVP.

Provides interface to fetch and process Confluence pages.
Automatically detects whether to use real Atlassian API or static demo data based on credential availability.
"""

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ConfluenceAdapter:
    """
    Unified Confluence adapter with automatic data source detection.

    Automatically uses real Atlassian Confluence API when OAuth credentials are configured,
    otherwise falls back to static demo data.
    """

    def __init__(self):
        """
        Initialize the Confluence adapter with automatic credential detection.

        Checks for Atlassian OAuth credentials and initializes the appropriate data source.
        """
        self.confluence_api = None
        self.use_static_data = True

        # Try to initialize real API if credentials are available
        if self._has_credentials():
            try:
                self.confluence_api = self._initialize_real_api()
                self.use_static_data = False
                logger.info("Confluence adapter initialized with real Atlassian API")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Confluence API, using static data: {e}"
                )
                self.use_static_data = True
        else:
            logger.info(
                "Confluence adapter initialized with static data (no credentials configured)"
            )

    def _has_credentials(self) -> bool:
        """
        Check if required OAuth credentials are available.

        Returns:
            True if Atlassian OAuth credentials are configured, False otherwise
        """
        client_id = os.getenv("ATLASSIAN_OAUTH_CLIENT_ID", "").strip()
        cloud_id = os.getenv("ATLASSIAN_CLOUD_ID", "").strip()
        return bool(client_id and cloud_id)

    def _initialize_real_api(self):
        """
        Initialize real Confluence API client with OAuth.

        Returns:
            ConfluenceAPI instance configured with OAuth authentication

        Raises:
            ValueError: If OAuth configuration is missing or invalid
            ImportError: If required modules are not available
        """
        from tools.atlassian_api_client import AtlassianAPIClient
        from tools.atlassian_confluence_api import ConfluenceAPI
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
            logger.info("✅ Using Environment Token Manager for Confluence (token from Chainlit UI)")
        elif oauth_config.agentcore_identity_arn:
            # Use AgentCore for production
            from tools.agentcore_token_manager import AgentCoreTokenManager

            token_manager = AgentCoreTokenManager(
                identity_arn=oauth_config.agentcore_identity_arn,
                user_id=oauth_config.demo_user_id,
                oauth_config=oauth_config,
            )
            logger.info("Using AgentCore Token Manager for Confluence")
        else:
            # Use simple in-memory token manager for development
            from tools.simple_token_manager import SimpleTokenManager

            token_manager = SimpleTokenManager(
                identity_arn="dev-mode",
                user_id=oauth_config.demo_user_id,
                oauth_config=oauth_config,
            )
            logger.info("Using Simple Token Manager for Confluence (in-memory storage)")

        # Initialize API client
        api_client = AtlassianAPIClient(
            token_manager=token_manager, oauth_config=oauth_config
        )

        # Get cloud ID from environment
        cloud_id = os.getenv("ATLASSIAN_CLOUD_ID", "").strip()

        if not cloud_id:
            raise ValueError(
                "ATLASSIAN_CLOUD_ID environment variable is required for real mode"
            )

        # Initialize Confluence API wrapper
        confluence_api = ConfluenceAPI(api_client=api_client, cloud_id=cloud_id)

        return confluence_api

    async def get_page(
        self, page_id: str, body_format: str = "storage"
    ) -> Dict[str, Any]:
        """
        Fetch a Confluence page by ID.

        Args:
            page_id: Confluence page ID
            body_format: Format for body content ('storage', 'view', 'export_view')

        Returns:
            Dictionary with page details
        """
        if self.use_static_data:
            return self._load_page_from_static_data(page_id)
        return await self._fetch_page_from_api(page_id, body_format)

    async def _fetch_page_from_api(
        self, page_id: str, body_format: str = "storage"
    ) -> Dict[str, Any]:
        """Fetch page using real Confluence API."""
        if not self.confluence_api:
            raise ValueError("Confluence API not initialized")

        logger.info(f"Fetching Confluence page {page_id} via real API")

        try:
            page = await self.confluence_api.get_page(page_id, body_format=body_format)

            return {"success": True, "page": page}
        except Exception as e:
            logger.error(f"Error fetching page {page_id}: {e}")
            return {"success": False, "error": str(e), "page_id": page_id}

    def _load_page_from_static_data(self, page_id: str) -> Dict[str, Any]:
        """Load page from static demo data."""
        logger.info(f"Loading Confluence page {page_id} from static data")

        # Return mock page data
        return {
            "success": True,
            "page": {
                "id": page_id,
                "title": f"Sample Page {page_id}",
                "status": "current",
                "space_key": "DEMO",
                "space_name": "Demo Space",
                "body_content": "<p>This is sample content for demonstration purposes.</p>",
                "version": 1,
                "last_modified": "2024-01-15T10:30:00Z",
                "last_modified_by": "Demo User",
                "created_at": "2024-01-01T09:00:00Z",
                "web_url": f"https://demo.atlassian.net/wiki/spaces/DEMO/pages/{page_id}",
            },
        }

    async def search_pages(self, cql: str, limit: int = 25) -> Dict[str, Any]:
        """
        Search Confluence pages using CQL.

        Args:
            cql: Confluence Query Language query string
            limit: Maximum number of results to return

        Returns:
            Dictionary with search results
        """
        if self.use_static_data:
            return self._search_pages_from_static_data(cql, limit)
        return await self._search_pages_from_api(cql, limit)

    async def _search_pages_from_api(self, cql: str, limit: int = 25) -> Dict[str, Any]:
        """Search pages using real Confluence API."""
        if not self.confluence_api:
            raise ValueError("Confluence API not initialized")

        logger.info(f"Searching Confluence pages with CQL: {cql}")

        try:
            pages = await self.confluence_api.search_pages(cql=cql, limit=limit)

            return {
                "success": True,
                "total_count": len(pages),
                "pages": pages,
                "query": cql,
            }
        except Exception as e:
            logger.error(f"Error searching pages with CQL '{cql}': {e}")
            return {
                "success": False,
                "error": str(e),
                "query": cql,
                "total_count": 0,
                "pages": [],
            }

    def _search_pages_from_static_data(
        self, cql: str, limit: int = 25
    ) -> Dict[str, Any]:
        """Load search results from static demo data."""
        logger.info(f"Searching Confluence pages from static data with CQL: {cql}")

        # Return mock search results
        mock_pages = [
            {
                "id": "12345",
                "title": "Project Documentation",
                "type": "page",
                "space_key": "DEMO",
                "space_name": "Demo Space",
                "excerpt": "This page contains project documentation...",
                "url": "https://demo.atlassian.net/wiki/spaces/DEMO/pages/12345",
                "last_modified": "2024-01-15T10:30:00Z",
            },
            {
                "id": "12346",
                "title": "API Reference",
                "type": "page",
                "space_key": "DEMO",
                "space_name": "Demo Space",
                "excerpt": "API reference documentation for developers...",
                "url": "https://demo.atlassian.net/wiki/spaces/DEMO/pages/12346",
                "last_modified": "2024-01-14T14:20:00Z",
            },
        ]

        # Limit results
        limited_pages = mock_pages[:limit]

        return {
            "success": True,
            "total_count": len(limited_pages),
            "pages": limited_pages,
            "query": cql,
        }


# Convenience functions for use in tools
async def fetch_page(page_id: str, body_format: str = "storage") -> Dict[str, Any]:
    """
    Fetch a Confluence page by ID.

    Args:
        page_id: Confluence page ID
        body_format: Format for body content ('storage', 'view', 'export_view')

    Returns:
        Dictionary with page details
    """
    adapter = ConfluenceAdapter()
    return await adapter.get_page(page_id, body_format)


async def search_confluence_pages(cql: str, limit: int = 25) -> Dict[str, Any]:
    """
    Search Confluence pages using CQL.

    Args:
        cql: Confluence Query Language query string
        limit: Maximum number of results to return

    Returns:
        Dictionary with search results
    """
    adapter = ConfluenceAdapter()
    return await adapter.search_pages(cql, limit)
