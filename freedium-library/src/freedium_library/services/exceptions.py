"""Standardized exception hierarchy across all Freedium services and decoders.

Defines domain-level exceptions that map cleanly to HTTP status codes
and user-facing error categories.
"""
from __future__ import annotations


class BaseServiceError(Exception):
    """Root exception for all service-related errors."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "An error occurred while processing the request"):
        super().__init__(message)
        self.message = message


class InvalidServiceError(BaseServiceError):
    """Raised when a requested service identifier is invalid or not registered."""
    status_code: int = 404
    error_code: str = "SERVICE_NOT_FOUND"


class ArticleNotFoundError(BaseServiceError):
    """Raised when an article cannot be found at the upstream provider (HTTP 404, post deleted, etc.)."""
    status_code: int = 404
    error_code: str = "ARTICLE_NOT_FOUND"


class UnsupportedContentError(BaseServiceError):
    """Raised when an article or URL type cannot be rendered (video shows, interactives without body, etc.)."""
    status_code: int = 422
    error_code: str = "UNSUPPORTED_CONTENT"


class UpstreamBlockedError(BaseServiceError):
    """Raised when the upstream provider blocks the request (bot challenge, proxy block, 401/403)."""
    status_code: int = 502
    error_code: str = "UPSTREAM_BLOCKED"


class UpstreamRateLimitError(BaseServiceError):
    """Raised when the upstream provider rate-limits requests (HTTP 429)."""
    status_code: int = 429
    error_code: str = "RATE_LIMITED"
