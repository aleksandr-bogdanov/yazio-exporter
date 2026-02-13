"""
Custom exception hierarchy for yazio-exporter.
"""


class YazioExporterError(Exception):
    """Base exception for all yazio-exporter errors."""


class AuthenticationError(YazioExporterError):
    """Raised when authentication fails (invalid credentials, expired token)."""


class APIError(YazioExporterError):
    """Raised when an API request fails with an HTTP error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        url: str | None = None,
    ):
        self.status_code = status_code
        self.url = url
        super().__init__(message)
