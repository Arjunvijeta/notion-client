"""
Notion API Client
=================
A robust, production-ready wrapper around the Notion API with best practices:
- Flexible configuration (direct parameters or config object)
- Type hints and validation
- Custom exceptions for better error handling
- Retry logic with exponential backoff
- Built-in caching with TTL support
- Comprehensive logging
- Connection pooling

Usage:
    # Simple usage (recommended for most cases)
    from notion_client import NotionClient

    client = NotionClient(api_key="your_api_key")
    page = client.get_page("page_id")
    databases = client.search(filter_type="database")

    # Advanced usage with custom configuration
    from notion_client import NotionClient, ClientConfig

    config = ClientConfig(
        api_key="your_api_key",
        enable_logging=True,
        cache_ttl_pages=600,
        max_retries=5
    )
    client = NotionClient(config)

    # Or mix both approaches
    client = NotionClient(
        api_key="your_api_key",
        enable_logging=True,
        cache_ttl_pages=600
    )
"""

import logging
from threading import Lock
from typing import Any, Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from cachetools import TTLCache

    CACHETOOLS_AVAILABLE = True
except ImportError:
    CACHETOOLS_AVAILABLE = False
    TTLCache = None  # type: ignore[assignment,misc]


from .config import ClientConfig
from .exceptions import (
    NotionAPIError,
    NotionAuthenticationError,
    NotionConflictError,
    NotionNotFoundError,
    NotionRateLimitError,
    NotionValidationError,
)

# ==================== Main Client ====================


class NotionClient:
    """Production-ready Notion API client with flexible configuration.

    This client provides a complete wrapper around the Notion API with:
    - Automatic retry with exponential backoff
    - Built-in caching for improved performance
    - Custom exceptions for different error types
    - Type hints throughout
    - Optional logging
    - Session management with connection pooling
    - Context manager support

    Usage:
        # Simple initialization
        client = NotionClient(api_key="your_key")

        # With custom parameters
        client = NotionClient(
            api_key="your_key",
            enable_logging=True,
            enable_caching=True,
            cache_ttl_pages=600
        )

        # With a config object (advanced)
        config = ClientConfig(api_key="your_key", max_retries=5)
        client = NotionClient(config)

        # As context manager
        with NotionClient(api_key="your_key") as client:
            databases = client.get_all_databases()
    """

    def __init__(
        self,
        config: Optional[Union[ClientConfig, str]] = None,
        *,
        api_key: Optional[str] = None,
        notion_version: str = "2025-09-03",
        base_url: str = "https://api.notion.com/v1",
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.3,
        retry_status_forcelist: Optional[List[int]] = None,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        enable_logging: bool = False,
        log_level: int = logging.INFO,
        enable_caching: bool = True,
        cache_ttl_pages: int = 300,
        cache_ttl_blocks: int = 600,
        cache_ttl_databases: int = 1800,
        cache_ttl_data_sources: int = 1800,
        cache_max_size: int = 100,
    ):
        """
        Initialize the Notion client with flexible configuration.

        You can initialize the client in multiple ways:
        1. Pass a ClientConfig object
        2. Pass the API key as the first positional argument
        3. Pass individual parameters as keyword arguments
        4. Mix config object with parameter overrides

        Args:
            config: ClientConfig object or API key string. If string, treated as api_key
            api_key: Notion API integration token (required if config not provided)
            notion_version: Notion API version to use
            base_url: Base URL for the Notion API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff_factor: Exponential backoff factor for retries
            retry_status_forcelist: List of HTTP status codes to retry on
            pool_connections: Number of connection pool connections
            pool_maxsize: Maximum size of connection pool
            enable_logging: Whether to enable logging
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            enable_caching: Whether to enable response caching
            cache_ttl_pages: TTL in seconds for page cache
            cache_ttl_blocks: TTL in seconds for block cache
            cache_ttl_databases: TTL in seconds for database metadata cache
            cache_ttl_data_sources: TTL in seconds for data source schema cache
            cache_max_size: Maximum number of items in each cache

        Raises:
            ValueError: If api_key is not provided
            TypeError: If invalid types are provided

        Examples:
            >>> client = NotionClient(api_key="secret_xxx")
            >>> client = NotionClient("secret_xxx")  # Shorthand
            >>> config = ClientConfig(api_key="secret_xxx")
            >>> client = NotionClient(config)
        """
        # Handle flexible initialization patterns
        if config is not None:
            if isinstance(config, str):
                # Shorthand: NotionClient("secret_xxx")
                api_key = config
                config = None
            elif not isinstance(config, ClientConfig):
                raise TypeError(f"config must be ClientConfig or str, got {type(config).__name__}")

        # Build configuration
        if config is not None:
            # Use provided config as base
            self.config = config
        else:
            # Build config from parameters
            if api_key is None:
                raise ValueError(
                    "api_key is required. Pass it as: "
                    "NotionClient(api_key='xxx') or NotionClient('xxx')"
                )

            self.config = ClientConfig(
                api_key=api_key,
                notion_version=notion_version,
                base_url=base_url,
                timeout=timeout,
                max_retries=max_retries,
                retry_backoff_factor=retry_backoff_factor,
                retry_status_forcelist=retry_status_forcelist or [429, 500, 502, 503, 504],
                pool_connections=pool_connections,
                pool_maxsize=pool_maxsize,
                enable_logging=enable_logging,
                log_level=log_level,
                enable_caching=enable_caching,
                cache_ttl_pages=cache_ttl_pages,
                cache_ttl_blocks=cache_ttl_blocks,
                cache_ttl_databases=cache_ttl_databases,
                cache_ttl_data_sources=cache_ttl_data_sources,
                cache_max_size=cache_max_size,
            )

        # Initialize components
        self._setup_logging()
        self._setup_session()
        self._setup_cache()

        self.logger.info(f"NotionClient initialized with version {self.config.notion_version}")
        if self.config.enable_caching:
            self.logger.info(
                f"Caching enabled: pages={self.config.cache_ttl_pages}s, "
                f"blocks={self.config.cache_ttl_blocks}s, "
                f"databases={self.config.cache_ttl_databases}s"
            )

    def _setup_logging(self) -> None:
        """Configure logging for the client."""
        self.logger = logging.getLogger(__name__)
        if self.config.enable_logging:
            self.logger.setLevel(self.config.log_level)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
        else:
            # Set to WARNING to suppress info messages
            self.logger.setLevel(logging.WARNING)

    def _setup_session(self) -> None:
        """Configure requests session with retry logic and connection pooling."""
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_backoff_factor,
            status_forcelist=self.config.retry_status_forcelist,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PATCH", "DELETE"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.config.pool_connections,
            pool_maxsize=self.config.pool_maxsize,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.config.api_key}",
                "Notion-Version": self.config.notion_version,
                "Content-Type": "application/json",
            }
        )

    def _setup_cache(self) -> None:
        """Initialize caches if caching is enabled."""
        if self.config.enable_caching and CACHETOOLS_AVAILABLE:
            self._page_cache: Any = TTLCache(
                maxsize=self.config.cache_max_size, ttl=self.config.cache_ttl_pages
            )
            self._blocks_cache: Any = TTLCache(
                maxsize=self.config.cache_max_size, ttl=self.config.cache_ttl_blocks
            )
            self._db_cache: Any = TTLCache(
                maxsize=self.config.cache_max_size, ttl=self.config.cache_ttl_databases
            )
            self._data_source_cache: Any = TTLCache(
                maxsize=self.config.cache_max_size, ttl=self.config.cache_ttl_data_sources
            )
            self._cache_lock: Any = Lock()
            self._cache_stats: Any = {"hits": 0, "misses": 0, "invalidations": 0}
        else:
            self._page_cache = None
            self._blocks_cache = None
            self._db_cache = None
            self._data_source_cache = None
            self._cache_lock = None
            self._cache_stats = None

    def _get_from_cache(self, cache: Any, key: str, cache_type: str) -> Optional[Dict[str, Any]]:
        """
        Get item from cache if available.

        Args:
            cache: The cache to check
            key: Cache key
            cache_type: Type of cache for logging (pages/blocks/databases)

        Returns:
            Cached data or None if not found
        """
        if not self.config.enable_caching or cache is None:
            return None

        with self._cache_lock:
            if key in cache:
                self._cache_stats["hits"] += 1
                self.logger.debug(f"Cache HIT [{cache_type}]: {key}")
                return cache[key]

        self._cache_stats["misses"] += 1
        self.logger.debug(f"Cache MISS [{cache_type}]: {key}")
        return None

    def _store_in_cache(self, cache: Any, key: str, value: Dict[str, Any], cache_type: str) -> None:
        """
        Store item in cache.

        Args:
            cache: The cache to store in
            key: Cache key
            value: Data to cache
            cache_type: Type of cache for logging
        """
        if not self.config.enable_caching or cache is None:
            return

        with self._cache_lock:
            cache[key] = value
            self.logger.debug(f"Cache STORE [{cache_type}]: {key}")

    def _invalidate_cache(self, resource_id: str, resource_type: str = "all") -> None:
        """
        Invalidate cache entries for a specific resource across all relevant caches.

        Key insight: In Notion, a page_id IS a block_id. Resources can exist in multiple
        cache types. When resource_type="all", we invalidate the ID from ALL caches to
        ensure no stale data remains.

        Args:
            resource_id: ID of the resource to invalidate
            resource_type: Type of resource (page/block/database/data_source/all)
                          "all" invalidates the ID from all cache types
        """
        if not self.config.enable_caching or self._cache_lock is None:
            return

        self.logger.info(
            f"_invalidate_cache called: resource_id={resource_id}, resource_type={resource_type}"
        )

        with self._cache_lock:
            invalidated = False

            # Invalidate from page cache
            if resource_type in ["page", "all"] and self._page_cache is not None:
                if resource_id in self._page_cache:
                    del self._page_cache[resource_id]
                    invalidated = True
                    self.logger.debug(f"Invalidated from page cache: {resource_id}")

            # Invalidate from blocks cache (including composite keys like "id:page_size")
            if resource_type in ["block", "all"] and self._blocks_cache is not None:
                self.logger.info(f"Checking blocks cache for resource_id={resource_id}")
                self.logger.info(f"Current blocks cache keys: {list(self._blocks_cache.keys())}")

                # Find all cache keys that reference this resource_id
                keys_to_delete = [
                    k
                    for k in self._blocks_cache.keys()
                    if k == resource_id or k.startswith(f"{resource_id}:")
                ]

                self.logger.info(f"Keys matching pattern: {keys_to_delete}")

                for key in keys_to_delete:
                    del self._blocks_cache[key]
                    invalidated = True
                    self.logger.info(f"DELETED from blocks cache: {key}")

            # Invalidate from database cache
            if resource_type in ["database", "all"] and self._db_cache is not None:
                if resource_id in self._db_cache:
                    del self._db_cache[resource_id]
                    invalidated = True
                    self.logger.debug(f"Invalidated from database cache: {resource_id}")

            # Invalidate from data_source cache
            if resource_type in ["data_source", "all"] and self._data_source_cache is not None:
                if resource_id in self._data_source_cache:
                    del self._data_source_cache[resource_id]
                    invalidated = True
                    self.logger.debug(f"Invalidated from data_source cache: {resource_id}")

            if invalidated:
                self._cache_stats["invalidations"] += 1
                self.logger.info(f"Cache invalidation COMPLETED for resource: {resource_id}")
            else:
                self.logger.warning(
                    f"Cache invalidation: NO keys found to invalidate for resource: {resource_id}"
                )

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache hit/miss/invalidation counts and hit rate
        """
        if not self.config.enable_caching:
            return {"enabled": False}

        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (self._cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "enabled": True,
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "invalidations": self._cache_stats["invalidations"],
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_sizes": {
                "pages": len(self._page_cache) if self._page_cache else 0,
                "blocks": len(self._blocks_cache) if self._blocks_cache else 0,
                "databases": len(self._db_cache) if self._db_cache else 0,
                "data_sources": len(self._data_source_cache) if self._data_source_cache else 0,
            },
        }

    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """
        Clear all caches or a specific cache.

        Args:
            cache_type: Type of cache to clear (pages/blocks/databases/data_sources/all or None for all)
        """
        if not self.config.enable_caching or self._cache_lock is None:
            return

        with self._cache_lock:
            if cache_type in ["pages", "all", None] and self._page_cache is not None:
                self._page_cache.clear()
                self.logger.info("Page cache cleared")

            if cache_type in ["blocks", "all", None] and self._blocks_cache is not None:
                self._blocks_cache.clear()
                self.logger.info("Blocks cache cleared")

            if cache_type in ["databases", "all", None] and self._db_cache is not None:
                self._db_cache.clear()
                self.logger.info("Database cache cleared")

            if cache_type in ["data_sources", "all", None] and self._data_source_cache is not None:
                self._data_source_cache.clear()
                self.logger.info("Data source cache cleared")

    def _handle_error(self, response: requests.Response) -> None:
        """Handle API errors and raise appropriate exceptions.

        Args:
            response: Response object from requests

        Raises:
            NotionAuthenticationError: For 401 errors
            NotionValidationError: For 400 errors
            NotionRateLimitError: For 429 errors
            NotionNotFoundError: For 404 errors
            NotionConflictError: For 409 errors
            NotionAPIError: For other errors
        """
        try:
            error_data = response.json()
            error_message = error_data.get("message", "Unknown error")
            error_code = error_data.get("code", "unknown")
        except Exception:
            error_data = {}
            error_message = response.text or "Unknown error"
            error_code = "unknown"

        status_code = response.status_code

        self.logger.error(f"API Error {status_code}: {error_message}")

        # Map status codes to specific exceptions
        error_classes = {
            401: (NotionAuthenticationError, "Authentication failed"),
            400: (NotionValidationError, "Validation error"),
            429: (NotionRateLimitError, "Rate limit exceeded"),
            404: (NotionNotFoundError, "Resource not found"),
            409: (NotionConflictError, "Conflict"),
        }

        if status_code in error_classes:
            error_class, error_prefix = error_classes[status_code]
            raise error_class(
                f"{error_prefix}: {error_message}",
                status_code=status_code,
                response_data=error_data,
            )
        else:
            raise NotionAPIError(
                f"API error ({error_code}): {error_message}",
                status_code=status_code,
                response_data=error_data,
            )

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to Notion API with error handling.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests (json, params, etc.)

        Returns:
            Response data as dict

        Raises:
            NotionAPIError: If the request fails
        """
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        self.logger.debug(f"{method} {url}")

        try:
            response = self.session.request(method, url, timeout=self.config.timeout, **kwargs)

            if response.status_code >= 400:
                self._handle_error(response)

            self.logger.debug(f"Response {response.status_code}: Success")
            return response.json()

        except requests.exceptions.Timeout:
            self.logger.error(f"Request timeout after {self.config.timeout}s")
            raise NotionAPIError(f"Request timeout after {self.config.timeout} seconds") from None

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            raise NotionAPIError(f"Connection error: {e}") from e

        except NotionAPIError:
            raise  # Re-raise our custom exceptions

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise NotionAPIError(f"Unexpected error: {e}") from e

    def close(self) -> None:
        """Close the session and clean up resources."""
        if hasattr(self, "session"):
            self.session.close()
            self.logger.info("NotionClient session closed")

    def __enter__(self) -> "NotionClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Cleanup when object is garbage collected."""
        self.close()

    # ==================== Pages ====================

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Retrieve a page by ID (with caching).

        Args:
            page_id: The ID of the page to retrieve

        Returns:
            Page object as dictionary
        """
        # Check cache first
        cached = self._get_from_cache(self._page_cache, page_id, "pages")
        if cached is not None:
            return cached

        # Cache miss - fetch from API
        result = self._request("GET", f"pages/{page_id}")

        # Store in cache
        self._store_in_cache(self._page_cache, page_id, result, "pages")

        return result

    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update page properties (invalidates cache).

        Args:
            page_id: The ID of the page to update
            properties: Dictionary of properties to update

        Returns:
            Updated page object
        """
        result = self._request("PATCH", f"pages/{page_id}", json={"properties": properties})

        # Invalidate cache for this page across all cache types
        # (page_id is also a block_id in Notion)
        self._invalidate_cache(page_id, "all")

        return result

    def create_page(
        self,
        parent_id: Optional[str] = None,
        parent_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        children: Optional[List[Dict[str, Any]]] = None,
        icon: Optional[Dict[str, Any]] = None,
        cover: Optional[Dict[str, Any]] = None,
        template: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, Any]] = None,
        # Legacy parameter for backward compatibility
        is_data_source_parent: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Create a new page as a child of an existing page or data source.

        This method follows the Notion API v2025-09-03 specification for creating pages.

        Args:
            parent_id: ID of parent page, data_source, or None for workspace-level (public integrations only).
                      If is_data_source_parent is provided (legacy), this is used with that flag.
            parent_type: Explicitly specify parent type: "page_id", "data_source_id", or "workspace".
                        If not provided, determined from is_data_source_parent or defaults to "page_id".
            properties: Page properties. If parent is a page, only "title" is valid.
                       If parent is a data_source, must match the data source's property schema.
            children: Optional list of block objects to add as initial page content.
                     Not allowed when using a template (template.type != "none").
            icon: Optional page icon (emoji or file object).
                 Example: {"type": "emoji", "emoji": "🥬"}
            cover: Optional page cover image (file object).
                  Example: {"type": "external", "external": {"url": "https://..."}}
            template: Optional template configuration for data source pages.
                     - {"type": "none"} - no template (default)
                     - {"type": "default"} - use data source's default template
                     - {"type": "template_id", "template_id": "page_id"} - use specific template
            position: Optional position within parent page. Only valid when parent is a page.
                     - {"type": "page_start"} - insert at top
                     - {"type": "page_end"} - insert at bottom (default)
                     - {"type": "after_block", "after_block": {"id": "block_id"}} - after specific block
            is_data_source_parent: [LEGACY] If True, parent_id is treated as data_source_id.
                                  If False, treated as page_id. Use parent_type instead.

        Returns:
            Created page object

        Raises:
            NotionValidationError: If invalid parameters are provided

        Examples:
            # Create page in data source
            page = client.create_page(
                parent_id="data_source_id",
                parent_type="data_source_id",
                properties={"Name": {"title": [{"text": {"content": "New Entry"}}]}}
            )

            # Create child page with content
            page = client.create_page(
                parent_id="page_id",
                parent_type="page_id",
                properties={"title": {"title": [{"text": {"content": "New Page"}}]}},
                children=[{"object": "block", "type": "paragraph", "paragraph": {...}}],
                icon={"type": "emoji", "emoji": "📄"}
            )

            # Create page from template
            page = client.create_page(
                parent_id="data_source_id",
                parent_type="data_source_id",
                properties={"Name": {"title": [{"text": {"content": "From Template"}}]}},
                template={"type": "default"}
            )

            # Legacy usage (still supported)
            page = client.create_page(
                parent_id="data_source_id",
                properties={...},
                is_data_source_parent=True
            )
        """
        # Build payload
        payload = {}

        # Handle parent parameter
        if is_data_source_parent is not None:
            # Legacy mode for backward compatibility
            if is_data_source_parent:
                payload["parent"] = {"type": "data_source_id", "data_source_id": parent_id}
            else:
                payload["parent"] = {"type": "page_id", "page_id": parent_id}
        elif parent_id is not None:
            # New API mode with explicit parent_type
            if parent_type is None:
                parent_type = "page_id"  # Default to page

            if parent_type not in ["page_id", "data_source_id", "workspace"]:
                raise NotionValidationError(
                    f"Invalid parent_type: {parent_type}. Must be 'page_id', 'data_source_id', or 'workspace'."
                )

            if parent_type == "workspace":
                payload["parent"] = {"type": "workspace", "workspace": True}  # type: ignore[dict-item]
            else:
                payload["parent"] = {"type": parent_type, parent_type: parent_id}
        else:
            # No parent_id provided - workspace-level page for public integrations
            payload["parent"] = {"type": "workspace", "workspace": True}  # type: ignore[dict-item]

        # Add properties
        if properties:
            payload["properties"] = properties

        # Add optional parameters
        if children is not None:
            if template and template.get("type") != "none":
                raise NotionValidationError(
                    "Cannot specify 'children' when using a template. The template overrides page content."
                )
            payload["children"] = children  # type: ignore[assignment]

        if icon is not None:
            payload["icon"] = icon

        if cover is not None:
            payload["cover"] = cover

        if template is not None:
            payload["template"] = template

        if position is not None:
            # Validate position is only used with page parent
            parent_obj = payload.get("parent", {})
            if parent_obj.get("type") != "page_id":
                raise NotionValidationError(
                    "The 'position' parameter is only valid when the parent is a page (parent_type='page_id')."
                )
            payload["position"] = position

        # Make API request
        result = self._request("POST", "pages", json=payload)

        # Invalidate parent cache since new entry was added
        if parent_id:
            self._invalidate_cache(parent_id, "all")

        return result

    # ==================== Databases ====================

    def get_database(self, database_id: str) -> Dict[str, Any]:
        """
        Retrieve a database metadata by ID (with caching).

        Note: In the new Notion API, databases contain multiple data_sources (tables).
        This method returns only metadata (title, description, icon, data_sources list).
        Use get_data_source() to get the actual schema and query_data_source() to query data.

        Args:
            database_id: The ID of the database to retrieve

        Returns:
            Database metadata object with list of data_sources
        """
        # Check cache first
        cached = self._get_from_cache(self._db_cache, database_id, "databases")
        if cached is not None:
            return cached

        # Cache miss - fetch from API
        result = self._request("GET", f"databases/{database_id}")

        # Store in cache
        self._store_in_cache(self._db_cache, database_id, result, "databases")

        return result

    def create_database(
        self,
        parent_page_id: str,
        initial_data_source_properties: Dict[str, Any],
        title: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new database with initial data source in a page.

        In the new API, databases are created with an initial_data_source containing properties.

        Args:
            parent_page_id: ID of the parent page
            initial_data_source_properties: Properties schema for the initial data source
            title: Optional title for the database (list of rich text objects)

        Returns:
            Created database object

        Example:
            properties = {
                "Name": {"title": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Not Started", "color": "red"},
                            {"name": "In Progress", "color": "yellow"},
                            {"name": "Completed", "color": "green"}
                        ]
                    }
                },
                "Due Date": {"date": {}}
            }
            db = client.create_database(page_id, properties)
        """
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "initial_data_source": {"properties": initial_data_source_properties},
        }

        if title:
            payload["title"] = title

        result = self._request("POST", "databases", json=payload)

        # Invalidate parent page cache (parent_page_id is also a block_id)
        self.logger.info(f"create_database: Invalidating cache for parent_page_id={parent_page_id}")
        self._invalidate_cache(parent_page_id, "all")
        self.logger.info("create_database: Cache invalidation completed")

        return result

    def update_database(
        self,
        database_id: str,
        title: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update database metadata (title, description, icon, or cover).

        Note: This updates only database metadata, not the data_source schema.

        Args:
            database_id: Database ID
            title: New title (optional)
            properties: New properties schema (optional)

        Returns:
            Updated database object
        """
        payload: Dict[str, Any] = {}
        if title:
            payload["title"] = [{"text": {"content": title}}]
        if properties:
            payload["properties"] = properties

        result = self._request("PATCH", f"databases/{database_id}", json=payload)

        # Invalidate cache across all types
        self._invalidate_cache(database_id, "all")

        return result

    # ==================== Data Sources ====================

    def get_data_source(self, data_source_id: str) -> Dict[str, Any]:
        """
        Retrieve a data source (table) schema by ID (with caching).

        Data sources are the actual tables within a database. They contain
        the properties (columns) and can be queried for data.

        Args:
            data_source_id: The ID of the data source to retrieve

        Returns:
            Data source object with properties schema
        """
        # Check cache first
        cached = self._get_from_cache(self._data_source_cache, data_source_id, "data_sources")
        if cached is not None:
            return cached

        # Cache miss - fetch from API
        result = self._request("GET", f"data_sources/{data_source_id}")

        # Store in cache
        self._store_in_cache(self._data_source_cache, data_source_id, result, "data_sources")

        return result

    def query_data_source(
        self,
        data_source_id: str,
        filter_obj: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100,
        filter_properties: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Query a data source (table) for entries.

        Args:
            data_source_id: Data source ID
            filter_obj: Filter object with 'and'/'or' conditions (optional)
            sorts: List of sort objects (optional)
            page_size: Number of results per page (max 100)
            filter_properties: List of property names to include in results (optional)

        Returns:
            Query results with 'results' list and pagination info

        Example:
            # Filter with OR condition
            filter_obj = {
                "or": [
                    {"property": "Stage", "status": {"equals": "Rejected"}},
                    {"property": "Stage", "status": {"equals": "No Answer"}}
                ]
            }
            results = client.query_data_source(data_source_id, filter_obj=filter_obj)
        """
        payload: Dict[str, Any] = {"page_size": min(page_size, 100)}
        if filter_obj:
            payload["filter"] = filter_obj
        if sorts:
            payload["sorts"] = sorts

        # Handle filter_properties as query parameter if provided
        params = {}
        if filter_properties:
            params["filter_properties[]"] = filter_properties

        return self._request(
            "POST",
            f"data_sources/{data_source_id}/query",
            json=payload,
            params=params if params else None,
        )

    def get_data_source_templates(self, data_source_id: str) -> Dict[str, Any]:
        """
        Get templates for a data source.

        Args:
            data_source_id: Data source ID

        Returns:
            Templates object
        """
        return self._request("GET", f"data_sources/{data_source_id}/templates")

    def update_data_source(
        self,
        data_source_id: str,
        properties: Optional[Dict[str, Any]] = None,
        title: Optional[List[Dict[str, Any]]] = None,
        icon: Optional[Dict[str, Any]] = None,
        in_trash: Optional[bool] = None,
        parent: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update a data source (table) within a database.

        This method updates the data source object — properties, title, description, icon,
        or whether it's in the trash. You can also move the data source to a different database.

        Args:
            data_source_id: ID of the data source to update
            properties: Dictionary of property updates. Structure:
                       {
                           "PropertyName": {
                               "name": "New Name",  # optional: rename property
                               "description": "Property description",  # optional
                               "type": "property_type",  # e.g., "number", "select", etc.
                               # Type-specific configuration (number, select, relation, etc.)
                           },
                           "PropertyToRemove": None  # Set to None to remove property
                       }
            title: Optional title as list of rich text objects.
                  Example: [{"type": "text", "text": {"content": "New Title"}}]
            icon: Optional icon object (emoji, external, file_upload, custom_emoji).
                 Example: {"type": "emoji", "emoji": "🎉"}
                 Set to None to remove existing icon.
            in_trash: True to move data source to trash, False to restore from trash.
            parent: Optional parent to move data source to different database.
                   Example: {"type": "database_id", "database_id": "new_db_id"}
                   When moving, existing views become linked views and a new table view is created.

        Returns:
            Updated data source object

        Raises:
            NotionValidationError: If invalid parameters are provided
            NotionAPIError: If the update fails

        Examples:
            # Update property configuration
            client.update_data_source(
                data_source_id="ds_id",
                properties={
                    "Price": {
                        "number": {"format": "dollar"}
                    }
                }
            )

            # Rename a property
            client.update_data_source(
                data_source_id="ds_id",
                properties={
                    "OldName": {
                        "name": "NewName",
                        "type": "text"
                    }
                }
            )

            # Remove a property
            client.update_data_source(
                data_source_id="ds_id",
                properties={
                    "UnusedColumn": None
                }
            )

            # Update title and icon
            client.update_data_source(
                data_source_id="ds_id",
                title=[{"type": "text", "text": {"content": "Updated Table"}}],
                icon={"type": "emoji", "emoji": "📊"}
            )

            # Move to different database
            client.update_data_source(
                data_source_id="ds_id",
                parent={"type": "database_id", "database_id": "new_db_id"}
            )

            # Move to trash
            client.update_data_source(
                data_source_id="ds_id",
                in_trash=True
            )

        Note:
            - Cannot update formula, status, synced content, or place properties via API
            - To update data source rows (entries), use update_page() instead
            - To update relation properties, the related database must be shared with your integration
            - Data source schema size should be kept under 50KB (manage number of properties)
            - When moving data sources between databases, views in the original database become linked views
        """
        # Build payload with only provided parameters
        payload: Dict[str, Any] = {}

        if properties is not None:
            payload["properties"] = properties

        if title is not None:
            payload["title"] = title

        if icon is not None:
            payload["icon"] = icon

        if in_trash is not None:
            payload["in_trash"] = in_trash

        if parent is not None:
            payload["parent"] = parent

        # Make API request
        result = self._request("PATCH", f"data_sources/{data_source_id}", json=payload)

        # Invalidate cache for this data source
        self._invalidate_cache(data_source_id, "data_sources")

        # If parent was changed, also invalidate the old and new parent database caches
        if parent and "database_id" in parent:
            self._invalidate_cache(parent["database_id"], "databases")

        return result

    # ==================== Blocks ====================

    def get_block(self, block_id: str) -> Dict[str, Any]:
        """
        Retrieve a block by ID.

        Args:
            block_id: The ID of the block to retrieve

        Returns:
            Block object as dictionary
        """
        return self._request("GET", f"blocks/{block_id}")

    def get_block_children(self, block_id: str, page_size: int = 100) -> Dict[str, Any]:
        """
        Get children of a block (with caching).

        Args:
            block_id: The ID of the parent block
            page_size: Number of results per page (max 100)

        Returns:
            Dictionary with 'results' list of child blocks
        """
        cache_key = f"{block_id}:{page_size}"

        # Check cache first
        cached = self._get_from_cache(self._blocks_cache, cache_key, "blocks")
        if cached is not None:
            return cached

        # Cache miss - fetch from API
        result = self._request(
            "GET", f"blocks/{block_id}/children", params={"page_size": min(page_size, 100)}
        )

        # Store in cache
        self._store_in_cache(self._blocks_cache, cache_key, result, "blocks")

        return result

    def append_block_children(
        self, block_id: str, children: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Append children blocks to a block (invalidates cache).

        Args:
            block_id: The ID of the parent block
            children: List of block objects to append

        Returns:
            Response with appended blocks
        """
        result = self._request("PATCH", f"blocks/{block_id}/children", json={"children": children})

        # Invalidate cache across all types (block_id is also a page_id)
        self._invalidate_cache(block_id, "all")

        return result

    def update_block(self, block_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update a block's content (invalidates cache).

        Args:
            block_id: The ID of the block to update
            **kwargs: Block update parameters

        Returns:
            Updated block object
        """
        result = self._request("PATCH", f"blocks/{block_id}", json=kwargs)

        # Invalidate cache across all types
        self._invalidate_cache(block_id, "all")

        return result

    def delete_block(self, block_id: str) -> Dict[str, Any]:
        """
        Delete (archive) a block (invalidates cache).

        Args:
            block_id: The ID of the block to delete

        Returns:
            Deleted block object
        """
        result = self._request("DELETE", f"blocks/{block_id}")

        # Invalidate cache across all types
        self._invalidate_cache(block_id, "all")

        return result

    # ==================== Search ====================

    def search(
        self, query: str = "", filter_type: Optional[str] = None, page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Search for pages and databases.

        Args:
            query: Search query string
            filter_type: 'page' or 'database' to filter by type
            page_size: Number of results (max 100)

        Returns:
            Search results with 'results' list
        """
        payload: Dict[str, Any] = {"page_size": min(page_size, 100)}
        if query:
            payload["query"] = query
        if filter_type:
            payload["filter"] = {"value": filter_type, "property": "object"}

        return self._request("POST", "search", json=payload)

    # ==================== Users ====================

    def get_users(self, page_size: int = 100) -> Dict[str, Any]:
        """
        List all users.

        Args:
            page_size: Number of results (max 100)

        Returns:
            Dictionary with 'results' list of users
        """
        return self._request("GET", "users", params={"page_size": min(page_size, 100)})

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get a specific user.

        Args:
            user_id: The ID of the user

        Returns:
            User object
        """
        return self._request("GET", f"users/{user_id}")

    def get_bot_user(self) -> Dict[str, Any]:
        """
        Get the bot user (current integration).

        Returns:
            Bot user object
        """
        return self._request("GET", "users/me")

    # ==================== Convenience Methods ====================

    def get_all_databases(self) -> List[Dict[str, Any]]:
        """
        Get all databases accessible to the integration.

        Returns:
            List of database objects
        """
        result = self.search(filter_type="database")
        return result.get("results", [])

    def get_all_pages(self) -> List[Dict[str, Any]]:
        """
        Get all pages accessible to the integration.

        Returns:
            List of page objects
        """
        result = self.search(filter_type="page")
        return result.get("results", [])

    def get_data_source_entries(self, data_source_id: str) -> List[Dict[str, Any]]:
        """
        Get all entries from a data source (convenience method).

        Args:
            data_source_id: The ID of the data source

        Returns:
            List of page objects (data source entries)
        """
        result = self.query_data_source(data_source_id)
        return result.get("results", [])


# ==================== Module Exports ====================

__all__ = [
    # Main client class
    "NotionClient",
    # Configuration
    "ClientConfig",
    # Exceptions
    "NotionAPIError",
    "NotionAuthenticationError",
    "NotionValidationError",
    "NotionRateLimitError",
    "NotionNotFoundError",
    "NotionConflictError",
]
