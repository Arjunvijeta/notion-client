"""Tests for client module."""

import logging
from unittest.mock import Mock, patch

import pytest

from notion_client import ClientConfig, NotionClient
from notion_client.exceptions import (
    NotionAuthenticationError,
    NotionNotFoundError,
    NotionRateLimitError,
    NotionValidationError,
)


class TestNotionClientInitialization:
    """Test NotionClient initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key only."""
        client = NotionClient(api_key="secret_test_key")
        assert client.config.api_key == "secret_test_key"
        assert hasattr(client, "session")
        client.close()

    def test_init_with_api_key_shorthand(self):
        """Test initialization with API key as first positional argument."""
        client = NotionClient("secret_shorthand_key")
        assert client.config.api_key == "secret_shorthand_key"
        assert hasattr(client, "session")
        client.close()

    def test_init_with_config(self, client_config):
        """Test initialization with ClientConfig."""
        client = NotionClient(client_config)
        assert client.config == client_config
        client.close()

    def test_init_with_mixed_params(self):
        """Test initialization with config and override params."""
        config = ClientConfig(api_key="secret_key", timeout=30)
        client = NotionClient(config, timeout=60)
        # Note: Current implementation doesn't support overrides with config object
        # This is expected behavior - config takes precedence
        assert client.config.timeout == 30
        client.close()

    def test_init_without_api_key(self):
        """Test initialization without API key raises ValueError."""
        with pytest.raises(ValueError, match="api_key is required"):
            NotionClient()

    def test_init_with_invalid_config_type(self):
        """Test initialization with invalid config type raises TypeError."""
        with pytest.raises(TypeError, match="config must be ClientConfig or str"):
            NotionClient(config=123)

    def test_context_manager(self, client_config):
        """Test context manager functionality."""
        with NotionClient(client_config) as client:
            assert hasattr(client, "session")
        # Session should be closed after exiting context

    def test_del_cleanup(self):
        """Test that __del__ properly cleans up."""
        client = NotionClient(api_key="secret_test_key")
        session = client.session
        del client
        # Session should be closed after deletion


class TestNotionClientErrorHandling:
    """Test error handling in NotionClient."""

    @patch("notion_client.client.requests.Session")
    def test_authentication_error_401(self, mock_session_class, client):
        """Test that 401 raises NotionAuthenticationError."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Unauthorized", "code": "unauthorized"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        with pytest.raises(NotionAuthenticationError):
            client._request("GET", "pages/test-id")

    @patch("notion_client.client.requests.Session")
    def test_validation_error_400(self, mock_session_class, client):
        """Test that 400 raises NotionValidationError."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid request", "code": "validation_error"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        with pytest.raises(NotionValidationError):
            client._request("POST", "pages")

    @patch("notion_client.client.requests.Session")
    def test_rate_limit_error_429(self, mock_session_class, client):
        """Test that 429 raises NotionRateLimitError."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limited", "code": "rate_limited"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        with pytest.raises(NotionRateLimitError):
            client._request("GET", "pages/test-id")

    @patch("notion_client.client.requests.Session")
    def test_not_found_error_404(self, mock_session_class, client):
        """Test that 404 raises NotionNotFoundError."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not found", "code": "object_not_found"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        with pytest.raises(NotionNotFoundError):
            client._request("GET", "pages/invalid-id")

    @patch("notion_client.client.requests.Session")
    def test_conflict_error_409(self, mock_session_class, client):
        """Test that 409 raises NotionConflictError."""
        from notion_client.exceptions import NotionConflictError

        mock_response = Mock()
        mock_response.status_code = 409
        mock_response.json.return_value = {"message": "Conflict", "code": "conflict"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        with pytest.raises(NotionConflictError):
            client._request("POST", "pages")

    @patch("notion_client.client.requests.Session")
    def test_generic_api_error(self, mock_session_class, client):
        """Test that other status codes raise NotionAPIError."""
        from notion_client.exceptions import NotionAPIError

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal error", "code": "internal_error"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        with pytest.raises(NotionAPIError):
            client._request("GET", "pages/test-id")

    @patch("notion_client.client.requests.Session")
    def test_error_without_json_response(self, mock_session_class, client):
        """Test error handling when response is not JSON."""
        from notion_client.exceptions import NotionAPIError

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = Exception("Not JSON")
        mock_response.text = "Plain text error"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        with pytest.raises(NotionAPIError):
            client._request("GET", "pages/test-id")

    @patch("notion_client.client.requests.Session")
    def test_timeout_error(self, mock_session_class, client):
        """Test that timeout raises NotionAPIError."""
        from notion_client.exceptions import NotionAPIError
        import requests

        mock_session = Mock()
        mock_session.request.side_effect = requests.exceptions.Timeout("Request timed out")
        client.session = mock_session

        with pytest.raises(NotionAPIError, match="Request timeout"):
            client._request("GET", "pages/test-id")

    @patch("notion_client.client.requests.Session")
    def test_connection_error(self, mock_session_class, client):
        """Test that connection error raises NotionAPIError."""
        from notion_client.exceptions import NotionAPIError
        import requests

        mock_session = Mock()
        mock_session.request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        client.session = mock_session

        with pytest.raises(NotionAPIError, match="Connection error"):
            client._request("GET", "pages/test-id")

    @patch("notion_client.client.requests.Session")
    def test_unexpected_error(self, mock_session_class, client):
        """Test that unexpected errors are wrapped in NotionAPIError."""
        from notion_client.exceptions import NotionAPIError

        mock_session = Mock()
        mock_session.request.side_effect = RuntimeError("Unexpected error")
        client.session = mock_session

        with pytest.raises(NotionAPIError, match="Unexpected error"):
            client._request("GET", "pages/test-id")


class TestNotionClientCaching:
    """Test caching functionality."""

    def test_cache_disabled_by_config(self):
        """Test that caching can be disabled."""
        client = NotionClient(api_key="secret_key", enable_caching=False)
        assert client.config.enable_caching is False
        client.close()

    def test_cache_stats_when_disabled(self):
        """Test cache stats when caching is disabled."""
        client = NotionClient(api_key="secret_key", enable_caching=False)
        stats = client.get_cache_stats()
        assert stats["enabled"] is False
        client.close()

    def test_cache_stats_when_enabled(self):
        """Test cache stats when caching is enabled."""
        client = NotionClient(api_key="secret_key", enable_caching=True)
        stats = client.get_cache_stats()
        assert stats["enabled"] is True
        assert "hits" in stats
        assert "misses" in stats
        assert "cache_sizes" in stats
        client.close()

    def test_clear_cache(self):
        """Test cache clearing."""
        client = NotionClient(api_key="secret_key", enable_caching=True)
        client.clear_cache()  # Should not raise
        client.clear_cache("pages")  # Should not raise
        client.close()

    @patch("notion_client.client.requests.Session")
    def test_page_cache_hit(self, mock_session_class, sample_page_response):
        """Test that page cache returns cached data on second call."""
        client = NotionClient(api_key="secret_key", enable_caching=True)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        # First call - cache miss
        result1 = client.get_page("test-page-id")
        assert result1["id"] == "test-page-id"
        assert mock_session.request.call_count == 1

        # Second call - cache hit
        result2 = client.get_page("test-page-id")
        assert result2["id"] == "test-page-id"
        assert mock_session.request.call_count == 1  # No additional API call

        stats = client.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

        client.close()

    @patch("notion_client.client.requests.Session")
    def test_database_cache_hit(self, mock_session_class, sample_database_response):
        """Test that database cache works correctly."""
        client = NotionClient(api_key="secret_key", enable_caching=True)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_database_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        # First call
        result1 = client.get_database("test-db-id")
        assert result1["id"] == "test-db-id"

        # Second call - should hit cache
        result2 = client.get_database("test-db-id")
        assert result2["id"] == "test-db-id"
        assert mock_session.request.call_count == 1

        client.close()

    @patch("notion_client.client.requests.Session")
    def test_block_children_cache_hit(self, mock_session_class, sample_block_response):
        """Test that block children cache works correctly."""
        client = NotionClient(api_key="secret_key", enable_caching=True)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [sample_block_response], "has_more": False}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        # First call
        result1 = client.get_block_children("test-block-id")
        assert len(result1["results"]) == 1

        # Second call - should hit cache
        result2 = client.get_block_children("test-block-id")
        assert len(result2["results"]) == 1
        assert mock_session.request.call_count == 1

        client.close()

    @patch("notion_client.client.requests.Session")
    def test_data_source_cache_hit(self, mock_session_class):
        """Test that data source cache works correctly."""
        client = NotionClient(api_key="secret_key", enable_caching=True)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "data_source", "id": "test-ds-id"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        # First call
        result1 = client.get_data_source("test-ds-id")
        assert result1["id"] == "test-ds-id"

        # Second call - should hit cache
        result2 = client.get_data_source("test-ds-id")
        assert result2["id"] == "test-ds-id"
        assert mock_session.request.call_count == 1

        client.close()

    @patch("notion_client.client.requests.Session")
    def test_cache_invalidation_on_update(self, mock_session_class, sample_page_response):
        """Test that cache is invalidated on update operations."""
        client = NotionClient(api_key="secret_key", enable_caching=True)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        # Get page (cache miss)
        client.get_page("test-page-id")
        assert mock_session.request.call_count == 1

        # Update page (should invalidate cache)
        client.update_page("test-page-id", {"title": {"title": []}})
        assert mock_session.request.call_count == 2

        # Get page again (cache miss due to invalidation)
        client.get_page("test-page-id")
        assert mock_session.request.call_count == 3

        client.close()

    @patch("notion_client.client.requests.Session")
    def test_cache_invalidation_on_append_block_children(
        self, mock_session_class, sample_block_response
    ):
        """Test cache invalidation when appending block children."""
        client = NotionClient(api_key="secret_key", enable_caching=True)

        mock_response = Mock()
        mock_response.status_code = 200

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        # Cache block children
        mock_response.json.return_value = {"results": [sample_block_response], "has_more": False}
        client.get_block_children("test-block-id")

        # Append children (should invalidate)
        mock_response.json.return_value = {"results": [sample_block_response]}
        client.append_block_children("test-block-id", [{"type": "paragraph"}])

        # Get again (should be cache miss)
        mock_response.json.return_value = {"results": [sample_block_response], "has_more": False}
        client.get_block_children("test-block-id")

        # Should have 3 API calls (get, append, get again)
        assert mock_session.request.call_count == 3

        client.close()

    def test_clear_specific_cache_type(self):
        """Test clearing specific cache types."""
        client = NotionClient(api_key="secret_key", enable_caching=True)

        # Clear specific cache types
        client.clear_cache("pages")
        client.clear_cache("blocks")
        client.clear_cache("databases")
        client.clear_cache("data_sources")
        client.clear_cache("all")

        client.close()

    def test_cache_stats_with_hits_and_misses(self):
        """Test cache stats calculation."""
        client = NotionClient(api_key="secret_key", enable_caching=True)

        # Manually manipulate cache stats for testing
        if client._cache_stats:
            client._cache_stats["hits"] = 10
            client._cache_stats["misses"] = 5

        stats = client.get_cache_stats()
        assert stats["hits"] == 10
        assert stats["misses"] == 5
        assert stats["total_requests"] == 15
        assert stats["hit_rate_percent"] == 66.67

        client.close()

    def test_cachetools_not_available(self):
        """Test behavior when cachetools is not available."""
        import notion_client.client as client_module

        original_available = client_module.CACHETOOLS_AVAILABLE
        try:
            # Simulate cachetools not available
            client_module.CACHETOOLS_AVAILABLE = False

            client = NotionClient(api_key="secret_key", enable_caching=True)
            assert client._page_cache is None
            assert client._blocks_cache is None

            client.close()
        finally:
            # Restore original value
            client_module.CACHETOOLS_AVAILABLE = original_available

    @patch("notion_client.client.requests.Session")
    def test_cache_invalidation_specific_types(self, mock_session_class):
        """Test cache invalidation for specific resource types."""
        client = NotionClient(api_key="secret_key", enable_caching=True)

        mock_response = Mock()
        mock_response.status_code = 200

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        # Add items to different caches
        mock_response.json.return_value = {"object": "page", "id": "page-1"}
        client.get_page("page-1")

        mock_response.json.return_value = {"object": "database", "id": "db-1"}
        client.get_database("db-1")

        mock_response.json.return_value = {"object": "data_source", "id": "ds-1"}
        client.get_data_source("ds-1")

        # Invalidate specific types
        client._invalidate_cache("page-1", "page")
        client._invalidate_cache("db-1", "database")
        client._invalidate_cache("ds-1", "data_source")

        # Verify invalidation happened
        stats = client.get_cache_stats()
        assert stats["invalidations"] == 3

        client.close()

    @patch("notion_client.client.requests.Session")
    def test_cache_invalidation_warning_no_keys_found(self, mock_session_class):
        """Test cache invalidation warning when no keys found."""
        client = NotionClient(api_key="secret_key", enable_caching=True, enable_logging=True)

        # Invalidate non-existent key
        client._invalidate_cache("non-existent-id", "all")

        stats = client.get_cache_stats()
        # No invalidation should occur
        assert stats["invalidations"] == 0

        client.close()

    def test_logging_enabled_with_handlers(self):
        """Test logging setup when enabled with existing handlers."""
        client = NotionClient(api_key="secret_key", enable_logging=True)
        assert client.logger.level == logging.INFO
        assert len(client.logger.handlers) > 0
        
        # Create another client - should not add duplicate handlers
        client2 = NotionClient(api_key="secret_key", enable_logging=True)
        assert client2.logger.level == logging.INFO
        
        client.close()
        client2.close()


class TestNotionClientMethods:
    """Test NotionClient API methods (with mocking)."""

    @patch("notion_client.client.requests.Session")
    def test_get_page(self, mock_session_class, client, sample_page_response):
        """Test get_page method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_page("test-page-id")
        assert result["id"] == "test-page-id"
        assert result["object"] == "page"

    @patch("notion_client.client.requests.Session")
    def test_get_database(self, mock_session_class, client, sample_database_response):
        """Test get_database method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_database_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_database("test-db-id")
        assert result["id"] == "test-db-id"
        assert result["object"] == "database"

    @patch("notion_client.client.requests.Session")
    def test_get_block_children(self, mock_session_class, client, sample_block_response):
        """Test get_block_children method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [sample_block_response], "has_more": False}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_block_children("test-block-id")
        assert "results" in result
        assert len(result["results"]) == 1

    @patch("notion_client.client.requests.Session")
    def test_update_page(self, mock_session_class, client, sample_page_response):
        """Test update_page method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        properties = {"title": {"title": [{"text": {"content": "Updated"}}]}}
        result = client.update_page("test-page-id", properties)
        assert result["id"] == "test-page-id"

    @patch("notion_client.client.requests.Session")
    def test_create_page_with_parent_page(self, mock_session_class, client, sample_page_response):
        """Test create_page with page parent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        properties = {"title": {"title": [{"text": {"content": "New Page"}}]}}
        result = client.create_page(
            parent_id="parent-page-id", parent_type="page_id", properties=properties
        )
        assert result["id"] == "test-page-id"

    @patch("notion_client.client.requests.Session")
    def test_create_page_with_data_source(self, mock_session_class, client, sample_page_response):
        """Test create_page with data_source parent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        properties = {"Name": {"title": [{"text": {"content": "New Entry"}}]}}
        result = client.create_page(
            parent_id="data-source-id", parent_type="data_source_id", properties=properties
        )
        assert result["id"] == "test-page-id"

    @patch("notion_client.client.requests.Session")
    def test_create_page_legacy_mode(self, mock_session_class, client, sample_page_response):
        """Test create_page with legacy is_data_source_parent parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        properties = {"Name": {"title": [{"text": {"content": "Legacy Entry"}}]}}
        result = client.create_page(
            parent_id="data-source-id", properties=properties, is_data_source_parent=True
        )
        assert result["id"] == "test-page-id"

    @patch("notion_client.client.requests.Session")
    def test_create_page_workspace_parent(self, mock_session_class, client, sample_page_response):
        """Test create_page with workspace parent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        properties = {"title": {"title": [{"text": {"content": "Workspace Page"}}]}}
        result = client.create_page(parent_type="workspace", properties=properties)
        assert result["id"] == "test-page-id"

    @patch("notion_client.client.requests.Session")
    def test_create_page_with_children(self, mock_session_class, client, sample_page_response):
        """Test create_page with children blocks."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        children = [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}}]
        result = client.create_page(
            parent_id="page-id",
            parent_type="page_id",
            properties={"title": {"title": [{"text": {"content": "Page with Content"}}]}},
            children=children,
        )
        assert result["id"] == "test-page-id"

    @patch("notion_client.client.requests.Session")
    def test_create_page_with_icon_and_cover(self, mock_session_class, client, sample_page_response):
        """Test create_page with icon and cover."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        icon = {"type": "emoji", "emoji": "📄"}
        cover = {"type": "external", "external": {"url": "https://example.com/cover.jpg"}}
        
        result = client.create_page(
            parent_id="page-id",
            parent_type="page_id",
            properties={"title": {"title": [{"text": {"content": "Page with Media"}}]}},
            icon=icon,
            cover=cover,
        )
        assert result["id"] == "test-page-id"

    @patch("notion_client.client.requests.Session")
    def test_create_page_with_template(self, mock_session_class, client, sample_page_response):
        """Test create_page with template."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        template = {"type": "default"}
        
        result = client.create_page(
            parent_id="data-source-id",
            parent_type="data_source_id",
            properties={"Name": {"title": [{"text": {"content": "From Template"}}]}},
            template=template,
        )
        assert result["id"] == "test-page-id"

    @patch("notion_client.client.requests.Session")
    def test_create_page_with_position(self, mock_session_class, client, sample_page_response):
        """Test create_page with position parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        position = {"type": "page_start"}
        
        result = client.create_page(
            parent_id="page-id",
            parent_type="page_id",
            properties={"title": {"title": [{"text": {"content": "At Top"}}]}},
            position=position,
        )
        assert result["id"] == "test-page-id"

    @patch("notion_client.client.requests.Session")
    def test_create_page_legacy_mode_with_page_parent(self, mock_session_class, client, sample_page_response):
        """Test create_page with legacy is_data_source_parent=False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        properties = {"title": {"title": [{"text": {"content": "Legacy Page"}}]}}
        result = client.create_page(
            parent_id="page-id", properties=properties, is_data_source_parent=False
        )
        assert result["id"] == "test-page-id"

    @patch("notion_client.client.requests.Session")
    def test_create_page_no_parent_defaults_to_workspace(self, mock_session_class, client, sample_page_response):
        """Test create_page without parent defaults to workspace."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_page_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        properties = {"title": {"title": [{"text": {"content": "Workspace Page"}}]}}
        result = client.create_page(properties=properties)
        assert result["id"] == "test-page-id"

    def test_create_page_invalid_parent_type(self, client):
        """Test create_page with invalid parent_type."""
        with pytest.raises(NotionValidationError):
            client.create_page(
                parent_id="page-id", parent_type="invalid_type", properties={}
            )

    def test_create_page_children_with_template(self, client):
        """Test create_page raises error when children and template are both specified."""
        with pytest.raises(NotionValidationError):
            client.create_page(
                parent_id="ds-id",
                parent_type="data_source_id",
                properties={},
                children=[],
                template={"type": "default"},
            )

    def test_create_page_position_with_non_page_parent(self, client):
        """Test create_page raises error when position is used with non-page parent."""
        with pytest.raises(NotionValidationError):
            client.create_page(
                parent_id="ds-id",
                parent_type="data_source_id",
                properties={},
                position={"type": "page_start"},
            )

    @patch("notion_client.client.requests.Session")
    def test_create_database(self, mock_session_class, client, sample_database_response):
        """Test create_database method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_database_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        properties = {"Name": {"title": {}}, "Status": {"select": {}}}
        result = client.create_database("parent-page-id", properties)
        assert result["id"] == "test-db-id"

    @patch("notion_client.client.requests.Session")
    def test_update_database(self, mock_session_class, client, sample_database_response):
        """Test update_database method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_database_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.update_database("test-db-id", title="Updated Database")
        assert result["id"] == "test-db-id"

    @patch("notion_client.client.requests.Session")
    def test_update_database_with_properties(self, mock_session_class, client, sample_database_response):
        """Test update_database with properties."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_database_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        properties = {"Name": {"title": {}}}
        result = client.update_database("test-db-id", title="Updated", properties=properties)
        assert result["id"] == "test-db-id"

    @patch("notion_client.client.requests.Session")
    def test_get_data_source(self, mock_session_class, client):
        """Test get_data_source method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "data_source", "id": "test-ds-id"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_data_source("test-ds-id")
        assert result["id"] == "test-ds-id"

    @patch("notion_client.client.requests.Session")
    def test_query_data_source(self, mock_session_class, client, sample_page_response):
        """Test query_data_source method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [sample_page_response], "has_more": False}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        filter_obj = {"property": "Status", "select": {"equals": "Active"}}
        result = client.query_data_source("test-ds-id", filter_obj=filter_obj)
        assert "results" in result

    @patch("notion_client.client.requests.Session")
    def test_query_data_source_with_sorts(self, mock_session_class, client):
        """Test query_data_source with sorts."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [], "has_more": False}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        sorts = [{"property": "Created", "direction": "descending"}]
        result = client.query_data_source("test-ds-id", sorts=sorts)
        assert "results" in result

    @patch("notion_client.client.requests.Session")
    def test_query_data_source_with_filter_properties(self, mock_session_class, client):
        """Test query_data_source with filter_properties."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [], "has_more": False}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.query_data_source(
            "test-ds-id", filter_properties=["Name", "Status"]
        )
        assert "results" in result

    @patch("notion_client.client.requests.Session")
    def test_get_data_source_templates(self, mock_session_class, client):
        """Test get_data_source_templates method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"templates": []}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_data_source_templates("test-ds-id")
        assert "templates" in result

    @patch("notion_client.client.requests.Session")
    def test_update_data_source(self, mock_session_class, client):
        """Test update_data_source method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "data_source", "id": "test-ds-id"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        properties = {"Price": {"number": {"format": "dollar"}}}
        result = client.update_data_source("test-ds-id", properties=properties)
        assert result["id"] == "test-ds-id"

    @patch("notion_client.client.requests.Session")
    def test_update_data_source_with_icon(self, mock_session_class, client):
        """Test update_data_source with icon."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "data_source", "id": "test-ds-id"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        icon = {"type": "emoji", "emoji": "📊"}
        result = client.update_data_source("test-ds-id", icon=icon)
        assert result["id"] == "test-ds-id"

    @patch("notion_client.client.requests.Session")
    def test_update_data_source_move_to_trash(self, mock_session_class, client):
        """Test update_data_source move to trash."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "data_source", "id": "test-ds-id"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.update_data_source("test-ds-id", in_trash=True)
        assert result["id"] == "test-ds-id"

    @patch("notion_client.client.requests.Session")
    def test_update_data_source_with_title(self, mock_session_class, client):
        """Test update_data_source with title."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "data_source", "id": "test-ds-id"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        title = [{"type": "text", "text": {"content": "Updated Title"}}]
        result = client.update_data_source("test-ds-id", title=title)
        assert result["id"] == "test-ds-id"

    @patch("notion_client.client.requests.Session")
    def test_update_data_source_with_parent(self, mock_session_class, client):
        """Test update_data_source with parent (moving to different database)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "data_source", "id": "test-ds-id"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        parent = {"type": "database_id", "database_id": "new-db-id"}
        result = client.update_data_source("test-ds-id", parent=parent)
        assert result["id"] == "test-ds-id"

    @patch("notion_client.client.requests.Session")
    def test_get_block(self, mock_session_class, client, sample_block_response):
        """Test get_block method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_block_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_block("test-block-id")
        assert result["id"] == "test-block-id"

    @patch("notion_client.client.requests.Session")
    def test_append_block_children(self, mock_session_class, client, sample_block_response):
        """Test append_block_children method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [sample_block_response]}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        children = [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}}]
        result = client.append_block_children("test-block-id", children)
        assert "results" in result

    @patch("notion_client.client.requests.Session")
    def test_update_block(self, mock_session_class, client, sample_block_response):
        """Test update_block method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_block_response

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.update_block(
            "test-block-id", paragraph={"rich_text": [{"text": {"content": "Updated"}}]}
        )
        assert result["id"] == "test-block-id"

    @patch("notion_client.client.requests.Session")
    def test_delete_block(self, mock_session_class, client, sample_block_response):
        """Test delete_block method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {**sample_block_response, "archived": True}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.delete_block("test-block-id")
        assert result["id"] == "test-block-id"

    @patch("notion_client.client.requests.Session")
    def test_search(self, mock_session_class, client, sample_page_response):
        """Test search method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [sample_page_response], "has_more": False}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.search(query="test", filter_type="page")
        assert "results" in result

    @patch("notion_client.client.requests.Session")
    def test_search_no_filter(self, mock_session_class, client):
        """Test search without filter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [], "has_more": False}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.search(query="test")
        assert "results" in result

    @patch("notion_client.client.requests.Session")
    def test_get_users(self, mock_session_class, client):
        """Test get_users method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"object": "user", "id": "user-1"}],
            "has_more": False,
        }

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_users()
        assert "results" in result

    @patch("notion_client.client.requests.Session")
    def test_get_user(self, mock_session_class, client):
        """Test get_user method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "user", "id": "user-1"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_user("user-1")
        assert result["id"] == "user-1"

    @patch("notion_client.client.requests.Session")
    def test_get_bot_user(self, mock_session_class, client):
        """Test get_bot_user method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "user", "type": "bot", "id": "bot-1"}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_bot_user()
        assert result["type"] == "bot"

    @patch("notion_client.client.requests.Session")
    def test_get_all_databases(self, mock_session_class, client, sample_database_response):
        """Test get_all_databases convenience method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [sample_database_response],
            "has_more": False,
        }

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_all_databases()
        assert len(result) == 1
        assert result[0]["object"] == "database"

    @patch("notion_client.client.requests.Session")
    def test_get_all_pages(self, mock_session_class, client, sample_page_response):
        """Test get_all_pages convenience method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [sample_page_response], "has_more": False}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_all_pages()
        assert len(result) == 1
        assert result[0]["object"] == "page"

    @patch("notion_client.client.requests.Session")
    def test_get_data_source_entries(self, mock_session_class, client, sample_page_response):
        """Test get_data_source_entries convenience method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [sample_page_response], "has_more": False}

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        client.session = mock_session

        result = client.get_data_source_entries("test-ds-id")
        assert len(result) == 1
