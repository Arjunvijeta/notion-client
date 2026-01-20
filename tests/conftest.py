"""Pytest configuration and fixtures."""

from unittest.mock import Mock

import pytest

from notion_client import ClientConfig, NotionClient


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return "secret_test_api_key_123456789"


@pytest.fixture
def client_config(mock_api_key):
    """Provide a test ClientConfig."""
    return ClientConfig(
        api_key=mock_api_key,
        enable_caching=False,  # Disable caching for predictable tests
        enable_logging=False,
        max_retries=1,
        timeout=5,
    )


@pytest.fixture
def client(client_config):
    """Provide a NotionClient instance for testing."""
    return NotionClient(client_config)


@pytest.fixture
def mock_response():
    """Provide a mock requests.Response."""
    mock = Mock()
    mock.status_code = 200
    mock.json.return_value = {"object": "page", "id": "test-page-id"}
    return mock


@pytest.fixture
def mock_session(mocker):
    """Provide a mocked requests.Session."""
    return mocker.patch("notion_client.client.requests.Session")


@pytest.fixture
def sample_page_response():
    """Sample page API response."""
    return {
        "object": "page",
        "id": "test-page-id",
        "created_time": "2026-01-01T00:00:00.000Z",
        "last_edited_time": "2026-01-01T00:00:00.000Z",
        "properties": {
            "title": {
                "id": "title",
                "type": "title",
                "title": [
                    {"type": "text", "text": {"content": "Test Page"}, "plain_text": "Test Page"}
                ],
            }
        },
        "url": "https://www.notion.so/test-page-id",
    }


@pytest.fixture
def sample_database_response():
    """Sample database API response."""
    return {
        "object": "database",
        "id": "test-db-id",
        "created_time": "2026-01-01T00:00:00.000Z",
        "last_edited_time": "2026-01-01T00:00:00.000Z",
        "title": [
            {"type": "text", "text": {"content": "Test Database"}, "plain_text": "Test Database"}
        ],
        "properties": {"Name": {"id": "title", "name": "Name", "type": "title", "title": {}}},
        "url": "https://www.notion.so/test-db-id",
    }


@pytest.fixture
def sample_block_response():
    """Sample block API response."""
    return {
        "object": "block",
        "id": "test-block-id",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": "Test paragraph"},
                    "plain_text": "Test paragraph",
                }
            ]
        },
    }
