"""Tests for config module."""

import logging

import pytest

from notion_client import ClientConfig


class TestClientConfig:
    """Test ClientConfig dataclass."""

    def test_minimal_config(self):
        """Test config with only required parameters."""
        config = ClientConfig(api_key="secret_test_key")
        assert config.api_key == "secret_test_key"
        assert config.notion_version == "2025-09-03"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_custom_config(self):
        """Test config with custom parameters."""
        config = ClientConfig(
            api_key="secret_test_key",
            timeout=60,
            max_retries=5,
            enable_caching=True,
            cache_ttl_pages=600,
        )
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.enable_caching is True
        assert config.cache_ttl_pages == 600

    def test_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="api_key is required"):
            ClientConfig(api_key="")

    def test_invalid_api_key_type(self):
        """Test that invalid API key type raises TypeError."""
        with pytest.raises(TypeError, match="api_key must be a string"):
            ClientConfig(api_key=123)

    def test_api_key_format_warning(self, caplog):
        """Test warning for unusual API key format."""
        with caplog.at_level(logging.WARNING):
            ClientConfig(api_key="invalid_format_key")
        assert "API key format looks unusual" in caplog.text

    def test_valid_api_key_formats(self):
        """Test valid API key formats don't trigger warnings."""
        # Should not raise or warn
        config1 = ClientConfig(api_key="secret_test_key_123")
        config2 = ClientConfig(api_key="ntn_test_key_123")
        assert config1.api_key.startswith("secret_")
        assert config2.api_key.startswith("ntn_")

    def test_invalid_timeout(self):
        """Test that invalid timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            ClientConfig(api_key="secret_key", timeout=0)

    def test_invalid_max_retries(self):
        """Test that invalid max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            ClientConfig(api_key="secret_key", max_retries=-1)

    def test_invalid_cache_max_size(self):
        """Test that invalid cache_max_size raises ValueError."""
        with pytest.raises(ValueError, match="cache_max_size must be positive"):
            ClientConfig(api_key="secret_key", cache_max_size=0)

    def test_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {"api_key": "secret_test_key", "timeout": 45, "max_retries": 4}
        config = ClientConfig.from_dict(config_dict)
        assert config.api_key == "secret_test_key"
        assert config.timeout == 45
        assert config.max_retries == 4

    def test_default_cache_settings(self):
        """Test default cache settings."""
        config = ClientConfig(api_key="secret_key")
        assert config.enable_caching is True
        assert config.cache_ttl_pages == 300
        assert config.cache_ttl_blocks == 600
        assert config.cache_ttl_databases == 1800
        assert config.cache_max_size == 100
