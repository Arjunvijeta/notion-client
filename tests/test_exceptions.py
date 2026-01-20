"""Tests for exceptions module."""

import pytest

from notion_client import (
    NotionAPIError,
    NotionAuthenticationError,
    NotionConflictError,
    NotionNotFoundError,
    NotionRateLimitError,
    NotionValidationError,
)


class TestNotionExceptions:
    """Test custom exception classes."""

    def test_base_exception(self):
        """Test NotionAPIError base exception."""
        error = NotionAPIError(
            message="Test error", status_code=500, response_data={"error": "test"}
        )
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.response_data == {"error": "test"}
        assert "500" in str(error)

    def test_authentication_error(self):
        """Test NotionAuthenticationError."""
        error = NotionAuthenticationError(message="Invalid API key", status_code=401)
        assert isinstance(error, NotionAPIError)
        assert error.status_code == 401
        assert "Invalid API key" in error.message

    def test_validation_error(self):
        """Test NotionValidationError."""
        error = NotionValidationError(
            message="Invalid property", status_code=400, response_data={"code": "validation_error"}
        )
        assert isinstance(error, NotionAPIError)
        assert error.status_code == 400
        assert error.response_data["code"] == "validation_error"

    def test_rate_limit_error(self):
        """Test NotionRateLimitError."""
        error = NotionRateLimitError(message="Rate limit exceeded", status_code=429)
        assert isinstance(error, NotionAPIError)
        assert error.status_code == 429

    def test_not_found_error(self):
        """Test NotionNotFoundError."""
        error = NotionNotFoundError(message="Page not found", status_code=404)
        assert isinstance(error, NotionAPIError)
        assert error.status_code == 404

    def test_conflict_error(self):
        """Test NotionConflictError."""
        error = NotionConflictError(message="Resource conflict", status_code=409)
        assert isinstance(error, NotionAPIError)
        assert error.status_code == 409

    def test_exception_without_status_code(self):
        """Test exception without status code."""
        error = NotionAPIError(message="Generic error")
        assert error.status_code is None
        assert "None" in str(error)

    def test_exception_can_be_raised(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(NotionAuthenticationError):
            raise NotionAuthenticationError("Auth failed", 401)

        with pytest.raises(NotionAPIError):
            raise NotionValidationError("Validation failed", 400)
