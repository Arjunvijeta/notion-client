from typing import Dict, Optional


class NotionAPIError(Exception):
    """Base exception for Notion API errors."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self) -> str:
        return f"{self.message} (status code: {self.status_code})"


class NotionAuthenticationError(NotionAPIError):
    """Raised when authentication fails (401)."""

    pass


class NotionValidationError(NotionAPIError):
    """Raised when request validation fails (400)."""

    pass


class NotionRateLimitError(NotionAPIError):
    """Raised when rate limit is exceeded (429)."""

    pass


class NotionNotFoundError(NotionAPIError):
    """Raised when a resource is not found (404)."""

    pass


class NotionConflictError(NotionAPIError):
    """Raised when there's a conflict (409)."""

    pass
