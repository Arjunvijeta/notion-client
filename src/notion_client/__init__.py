"""
Notion Client Package
=====================
A robust, lightweight Python client for the Notion API.

Usage:
    from notion_client import NotionClient, ClientConfig

    config = ClientConfig(api_key="your_key")
    with NotionClient(config) as client:
        databases = client.get_all_databases()

For simple usage:
    from notion_client import SimpleNotionClient

    client = SimpleNotionClient(api_key="your_key")
    databases = client.get_all_databases()
"""

from .client import (
    # Configuration
    ClientConfig,
    # Exceptions
    NotionAPIError,
    NotionAuthenticationError,
    # Main client classes
    NotionClient,
    NotionConflictError,
    NotionNotFoundError,
    NotionRateLimitError,
    NotionValidationError,
)
from .helpers import format_database_title, format_page_title
from .properties import (
    create_checkbox_property,
    create_date_property,
    create_email_property,
    create_multi_select_property,
    create_number_property,
    create_phone_property,
    create_relation_property,
    create_select_property,
    create_text_property,
    create_title_property,
    create_url_property,
)

__version__ = "1.0.0"

__all__ = [
    # Main client classes
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
    # Helper functions - formatters
    "format_database_title",
    "format_page_title",
    # Helper functions - property creators
    "create_text_property",
    "create_title_property",
    "create_number_property",
    "create_checkbox_property",
    "create_select_property",
    "create_multi_select_property",
    "create_date_property",
    "create_url_property",
    "create_email_property",
    "create_phone_property",
    "create_relation_property",
]
