"""
Authentication: login and token management.
"""

import os

import requests

from yazio_exporter.client import YazioClient
from yazio_exporter.exceptions import AuthenticationError

# Hardcoded Yazio client credentials (from API spec)
CLIENT_ID = "1_4hiybetvfksgw40o0sog4s884kwc840wwso8go4k8c04goo4c"
CLIENT_SECRET = "6rok2m65xuskgkgogw40wkkk8sw0osg84s8cggsc4woos4s8o"


def login(email: str, password: str, client: YazioClient = None) -> str:
    """
    Authenticate with Yazio API and return access token.

    Args:
        email: User email
        password: User password
        client: Optional YazioClient (uses its base_url/api_version)

    Returns:
        Access token string

    Raises:
        AuthenticationError: If authentication fails
    """
    if client is None:
        client = YazioClient()

    url = f"{client.base_url}/{client.api_version}/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": email,
        "password": password,
        "grant_type": "password",
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.HTTPError as e:
        raise AuthenticationError(str(e)) from e

    data = response.json()
    return data["access_token"]


def login_and_save(email: str, password: str, token_file: str) -> str:
    """
    Login and save token to file with restrictive permissions.

    Args:
        email: User email
        password: User password
        token_file: Path to save token

    Returns:
        Access token string

    Note:
        File is created with 0600 permissions (owner read/write only)
    """
    token = login(email, password)

    # Write token to file
    with open(token_file, "w") as f:
        f.write(token)

    # Set restrictive permissions: owner read/write only (0600)
    os.chmod(token_file, 0o600)

    return token


def load_token(token_file: str) -> str:
    """
    Load access token from a file.

    Args:
        token_file: Path to token file

    Returns:
        Access token string

    Raises:
        FileNotFoundError: If token file does not exist
        ValueError: If token file is empty
    """
    with open(token_file) as f:
        token = f.read().strip()

    if not token:
        raise ValueError(f"Token file is empty: {token_file}")

    return token


def make_authenticated_client(token_file: str) -> YazioClient:
    """
    Create an authenticated YazioClient from a token file.

    Args:
        token_file: Path to token file

    Returns:
        Authenticated YazioClient instance
    """
    token = load_token(token_file)
    client = YazioClient()
    client.set_token(token)
    return client
