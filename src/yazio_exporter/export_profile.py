"""
User profile export: profile, settings, dietary preferences.
"""

from typing import Any

from yazio_exporter.client import YazioClient


def fetch_user(client: YazioClient) -> dict[str, Any]:
    """
    Fetch user profile.

    Args:
        client: YazioClient instance

    Returns:
        User profile data including email, sex, first_name, body_height,
        start_weight, goal, and diet object with macro percentages

    Raises:
        requests.HTTPError: If the API request fails
    """
    response = client.get("user")
    return response.json()


def fetch_all(client: YazioClient) -> dict[str, Any]:
    """
    Fetch all profile data: user, settings, dietary preferences.

    Args:
        client: YazioClient instance

    Returns:
        Combined profile data with keys: 'user', 'settings', 'dietary_preferences'

    Raises:
        requests.HTTPError: If any API request fails
    """
    return {
        "user": fetch_user(client),
        "settings": client.get("user/settings").json(),
        "dietary_preferences": client.get("user/dietary-preferences").json(),
    }
