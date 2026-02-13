"""
Tests for HTTP client.
"""

import pytest
import requests
import responses

from yazio_exporter.client import YazioClient
from yazio_exporter.exceptions import APIError, AuthenticationError


def test_client_initialization():
    """Test YazioClient initialization."""
    client = YazioClient()
    assert client.base_url == "https://yzapi.yazio.com"
    assert client.api_version == "v15"
    assert client.session is not None


def test_get_url():
    """Test URL construction."""
    client = YazioClient()
    url = client.get_url("/user")
    assert url == "https://yzapi.yazio.com/v15/user"

    url = client.get_url("user")
    assert url == "https://yzapi.yazio.com/v15/user"


def test_set_token():
    """Test setting authorization token."""
    client = YazioClient()
    client.set_token("test_token")
    assert client.session.headers["Authorization"] == "Bearer test_token"


@responses.activate
def test_set_token_header_sent_in_request():
    """Test that Authorization header is actually sent in HTTP requests."""
    # Mock the API endpoint
    responses.add(
        responses.GET,
        "https://yzapi.yazio.com/v15/user",
        json={"user_id": 123},
        status=200,
    )

    # Create client and set token
    client = YazioClient()
    client.set_token("test_token_12345")

    # Verify header is set
    assert client.session.headers["Authorization"] == "Bearer test_token_12345"

    # Make a request
    url = client.get_url("/user")
    response = client.session.get(url)

    # Verify the request was made with the Authorization header
    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers["Authorization"] == "Bearer test_token_12345"
    assert response.status_code == 200


@responses.activate
def test_http_error_404_includes_status_and_url():
    """Test that 404 errors include status code and URL in error message."""
    # Mock a 404 response
    responses.add(
        responses.GET,
        "https://yzapi.yazio.com/v15/notfound",
        json={"error": "Not found"},
        status=404,
    )

    client = YazioClient()

    # Try to make a request that will fail
    with pytest.raises(APIError) as exc_info:
        client.get("/notfound")

    # Verify the error message contains status code and URL
    error_msg = str(exc_info.value)
    assert "404" in error_msg
    assert "https://yzapi.yazio.com/v15/notfound" in error_msg
    assert exc_info.value.status_code == 404


@responses.activate
def test_http_error_500_includes_status_and_url():
    """Test that 500 errors include status code and URL in error message."""
    # Mock a 500 response
    responses.add(
        responses.GET,
        "https://yzapi.yazio.com/v15/internal/error",
        json={"error": "Internal server error"},
        status=500,
    )

    client = YazioClient()

    # Try to make a request that will fail
    with pytest.raises(APIError) as exc_info:
        client.get("/internal/error")

    # Verify the error message contains status code and URL
    error_msg = str(exc_info.value)
    assert "500" in error_msg
    assert "https://yzapi.yazio.com/v15/internal/error" in error_msg
    assert exc_info.value.status_code == 500


@responses.activate
def test_retry_on_5xx_errors_with_exponential_backoff():
    """Test retry logic with exponential backoff on 5xx errors."""
    import time

    # Mock endpoint to return 503, then 503, then 200
    responses.add(
        responses.GET,
        "https://yzapi.yazio.com/v15/test",
        json={"error": "Service unavailable"},
        status=503,
    )
    responses.add(
        responses.GET,
        "https://yzapi.yazio.com/v15/test",
        json={"error": "Service unavailable"},
        status=503,
    )
    responses.add(
        responses.GET,
        "https://yzapi.yazio.com/v15/test",
        json={"success": True},
        status=200,
    )

    client = YazioClient()

    # Measure time to verify backoff delays
    start_time = time.time()
    response = client.get("/test")
    elapsed = time.time() - start_time

    # Verify 3 attempts were made
    assert len(responses.calls) == 3

    # Verify eventual success
    assert response.status_code == 200
    assert response.json() == {"success": True}

    # Verify delays between attempts: ~1s after first attempt, ~2s after second
    # Total should be at least 3 seconds (1 + 2)
    assert elapsed >= 3.0, f"Expected at least 3s delay, got {elapsed:.2f}s"
    # But not too much more (allow 1s margin for processing)
    assert elapsed < 5.0, f"Expected less than 5s total, got {elapsed:.2f}s"


@responses.activate
def test_retry_fails_after_max_retries():
    """Test that retries fail after max attempts on persistent 5xx errors."""
    # Mock endpoint to always return 503
    for _ in range(3):
        responses.add(
            responses.GET,
            "https://yzapi.yazio.com/v15/test",
            json={"error": "Service unavailable"},
            status=503,
        )

    client = YazioClient()

    # Should fail after 3 attempts
    with pytest.raises(APIError) as exc_info:
        client.get("/test")

    # Verify 3 attempts were made
    assert len(responses.calls) == 3

    # Verify error message and status code
    error_msg = str(exc_info.value)
    assert "503" in error_msg
    assert exc_info.value.status_code == 503


def test_timeout_after_30_seconds():
    """Test that requests timeout after 30 seconds."""
    import time
    from unittest.mock import patch

    client = YazioClient()

    # Mock a hanging endpoint that raises Timeout
    with patch.object(client.session, "get") as mock_get:
        mock_get.side_effect = requests.Timeout("Request timed out after 30 seconds")

        start_time = time.time()

        # Should raise timeout exception
        with pytest.raises(requests.Timeout) as exc_info:
            client.get("/hanging")

        elapsed = time.time() - start_time

        # Verify timeout exception is raised
        assert "timed out" in str(exc_info.value).lower()

        # Verify it happens quickly (mocked, so should be instant)
        assert elapsed < 1.0, "Mocked timeout should be instant"


def test_timeout_configuration():
    """Test that timeout is properly configured in requests."""
    from unittest.mock import patch

    import responses

    client = YazioClient()

    # Verify session timeout is set
    assert client.session.timeout == 30

    # Verify timeout is passed to requests
    with patch.object(client.session, "get", wraps=client.session.get) as mock_get:
        responses.add(
            responses.GET,
            "https://yzapi.yazio.com/v15/test",
            json={"success": True},
            status=200,
        )

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "https://yzapi.yazio.com/v15/test",
                json={"success": True},
                status=200,
            )

            client.get("/test")

            # Verify timeout was passed in kwargs
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs.get("timeout") == 30


@responses.activate
def test_expired_token_detected_with_helpful_message():
    """Test that expired token errors include helpful message."""
    # Mock 401 response with expired token indication
    responses.add(
        responses.GET,
        "https://yzapi.yazio.com/v15/user",
        json={"error": "invalid_grant", "error_description": "Token expired"},
        status=401,
    )

    client = YazioClient()
    client.set_token("expired_token")

    # Should raise AuthenticationError with helpful message
    with pytest.raises(AuthenticationError) as exc_info:
        client.get("/user")

    # Verify exception mentions token expiry
    error_msg = str(exc_info.value)
    assert "401" in error_msg or "Unauthorized" in error_msg
    assert "expired" in error_msg.lower() or "token" in error_msg.lower()

    # Verify message suggests running login again
    assert "login" in error_msg.lower()


@responses.activate
def test_expired_token_without_json_response():
    """Test that 401 errors without JSON still get helpful message."""
    # Mock 401 response with plain text (no JSON)
    responses.add(
        responses.GET,
        "https://yzapi.yazio.com/v15/user",
        body="Unauthorized",
        status=401,
    )

    client = YazioClient()
    client.set_token("expired_token")

    # Should raise AuthenticationError with helpful message
    with pytest.raises(AuthenticationError) as exc_info:
        client.get("/user")

    # Verify exception mentions token expiry
    error_msg = str(exc_info.value)
    assert "401" in error_msg or "Unauthorized" in error_msg
    assert "token" in error_msg.lower() or "expired" in error_msg.lower()

    # Verify message suggests running login again
    assert "login" in error_msg.lower()
