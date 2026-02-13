"""
Tests for authentication.
"""

import os
import tempfile

import pytest
import responses

from yazio_exporter.auth import (
    CLIENT_ID,
    CLIENT_SECRET,
    login,
    login_and_save,
)
from yazio_exporter.exceptions import AuthenticationError

BASE_URL = "https://yzapi.yazio.com"


@responses.activate
def test_login_with_valid_credentials_returns_access_token():
    """
    Feature #7: Login with valid credentials returns access token.

    Verify the login function successfully authenticates:
    1. Mock POST /v15/oauth/token to return access token
    2. Call login() with credentials
    3. Verify request includes client_id/client_secret
    4. Verify request includes username/password
    5. Verify grant_type is 'password'
    6. Verify access_token is returned
    """
    # Mock successful token response
    responses.add(
        responses.POST,
        f"{BASE_URL}/v15/oauth/token",
        json={"access_token": "abc123", "expires_in": 172800, "token_type": "bearer"},
        status=200,
    )

    # Call login with credentials
    token = login(email="test@example.com", password="test123")

    # Verify the access token is returned
    assert token == "abc123"

    # Verify the request was made correctly
    assert len(responses.calls) == 1
    request = responses.calls[0].request

    # Verify request body includes all required fields
    import json

    body = json.loads(request.body)

    assert body["client_id"] == CLIENT_ID
    assert body["client_secret"] == CLIENT_SECRET
    assert body["username"] == "test@example.com"
    assert body["password"] == "test123"
    assert body["grant_type"] == "password"


@responses.activate
def test_login_and_save_creates_file_with_token():
    """
    Feature #8: Login saves token to file.

    Verify login_and_save() function:
    1. Mock successful login response
    2. Call login_and_save() with credentials and file path
    3. Verify token file is created
    4. Verify file contains the access_token
    5. Verify file permissions are restrictive (0600)
    """
    # Mock successful token response
    responses.add(
        responses.POST,
        f"{BASE_URL}/v15/oauth/token",
        json={
            "access_token": "test_token_xyz",
            "expires_in": 172800,
            "token_type": "bearer",
        },
        status=200,
    )

    # Use temporary file for testing
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        token_file = tmp.name

    try:
        # Call login_and_save
        login_and_save(email="user@test.com", password="pass123", token_file=token_file)

        # Verify file was created
        assert os.path.exists(token_file), "Token file was not created"

        # Verify file contains the access token
        with open(token_file) as f:
            content = f.read()
        assert content == "test_token_xyz", f"Expected 'test_token_xyz', got '{content}'"

        # Verify file permissions are 0600 (owner read/write only)
        file_stat = os.stat(token_file)
        permissions = file_stat.st_mode & 0o777
        assert permissions == 0o600, f"Expected permissions 0600, got {oct(permissions)}"

    finally:
        # Clean up temporary file
        if os.path.exists(token_file):
            os.remove(token_file)


@responses.activate
def test_login_with_invalid_credentials_raises_error():
    """
    Feature #9: Login with invalid credentials raises error.

    Verify authentication fails with wrong password:
    1. Mock POST /v15/oauth/token to return 401 with error message
    2. Call login() with invalid credentials
    3. Verify it raises an HTTPError
    4. Verify error message mentions authentication failure
    """
    # Mock 401 unauthorized response
    responses.add(
        responses.POST,
        f"{BASE_URL}/v15/oauth/token",
        json={"error": "invalid_grant", "error_description": "Invalid credentials"},
        status=401,
    )

    # Verify login raises AuthenticationError with invalid credentials
    with pytest.raises(AuthenticationError) as exc_info:
        login(email="test@example.com", password="wrong_password")

    # Verify it's an authentication error
    assert (
        "401" in str(exc_info.value) or "Unauthorized" in str(exc_info.value) or "Client Error" in str(exc_info.value)
    )
