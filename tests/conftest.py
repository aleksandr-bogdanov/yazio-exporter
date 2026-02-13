"""
Pytest configuration and shared fixtures.
"""

import pytest

from yazio_exporter.client import YazioClient
from yazio_exporter.constants import API_VERSION, BASE_URL


@pytest.fixture
def client():
    """Create an authenticated YazioClient instance for testing."""
    c = YazioClient()
    c.set_token("test_token_12345")
    return c


@pytest.fixture
def mock_token():
    """Mock authentication token."""
    return "test_token_12345"


@pytest.fixture
def base_api_url():
    """Base API URL for constructing mock endpoints."""
    return f"{BASE_URL}/{API_VERSION}"
