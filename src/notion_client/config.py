import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

try:
    from cachetools import TTLCache

    CACHETOOLS_AVAILABLE = True
except ImportError:
    CACHETOOLS_AVAILABLE = False
    TTLCache = None


@dataclass
class ClientConfig:
    """Configuration for the Notion API client.

    This dataclass provides a structured way to configure the client with validation.
    You can either pass this to NotionClient or use individual parameters.

    Attributes:
        api_key: Your Notion API integration token (required)
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
        cache_ttl_pages: TTL in seconds for page cache (default: 5 minutes)
        cache_ttl_blocks: TTL in seconds for block cache (default: 10 minutes)
        cache_ttl_databases: TTL in seconds for database schema cache (default: 30 minutes)
        cache_ttl_data_sources: TTL in seconds for data source schema cache (default: 30 minutes)
        cache_max_size: Maximum number of items in each cache
    """

    api_key: str
    notion_version: str = "2025-09-03"
    base_url: str = "https://api.notion.com/v1"
    timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 0.3
    retry_status_forcelist: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    pool_connections: int = 10
    pool_maxsize: int = 10
    enable_logging: bool = False
    log_level: int = logging.INFO
    enable_caching: bool = True
    cache_ttl_pages: int = 300  # 5 minutes
    cache_ttl_blocks: int = 600  # 10 minutes
    cache_ttl_databases: int = 1800  # 30 minutes (metadata only)
    cache_ttl_data_sources: int = 1800  # 30 minutes (schema/properties)
    cache_max_size: int = 100

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError("api_key is required")

        if not isinstance(self.api_key, str):
            raise TypeError("api_key must be a string")

        if not self.api_key.startswith("secret_") and not self.api_key.startswith("ntn_"):
            logging.warning(
                "API key format looks unusual. Expected to start with 'secret_' or 'ntn_'. "
                "Please verify you're using a valid Notion integration token."
            )

        if self.enable_caching and not CACHETOOLS_AVAILABLE:
            logging.warning(
                "Caching is enabled but 'cachetools' is not installed. "
                "Caching will be disabled. Install with: pip install cachetools"
            )
            self.enable_caching = False

        # Validate numeric parameters
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.cache_max_size <= 0:
            raise ValueError("cache_max_size must be positive")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ClientConfig":
        """Create a ClientConfig from a dictionary.

        Args:
            config_dict: Dictionary with configuration parameters

        Returns:
            ClientConfig instance
        """
        return cls(**config_dict)
