"""
Tests for user profile export.
"""

import responses

from yazio_exporter.export_profile import fetch_all, fetch_user


@responses.activate
def test_fetch_user(client, base_api_url):
    """Test fetching user profile with all fields."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user",
        json={
            "email": "user@example.com",
            "premium_type": "pro",
            "sex": "male",
            "first_name": "John",
            "last_name": "Doe",
            "body_height": 180,
            "date_of_birth": "1990-05-15",
            "registration_date": "2020-01-01",
            "timezone_offset": 60,
            "unit_length": "cm",
            "unit_mass": "kg",
            "unit_energy": "kcal",
            "start_weight": 85,
            "activity_degree": "moderate",
            "goal": "lose",
            "weight_change_per_week": -0.5,
            "diet": {
                "carb_percentage": 50,
                "fat_percentage": 30,
                "protein_percentage": 20,
                "name": "balanced",
            },
            "uuid": "test-uuid-123",
        },
        status=200,
    )

    profile = fetch_user(client)

    assert profile["email"] == "user@example.com"
    assert profile["sex"] == "male"
    assert profile["first_name"] == "John"
    assert profile["body_height"] == 180
    assert profile["start_weight"] == 85
    assert profile["goal"] == "lose"

    assert "diet" in profile
    assert profile["diet"]["carb_percentage"] == 50
    assert profile["diet"]["fat_percentage"] == 30
    assert profile["diet"]["protein_percentage"] == 20
    assert profile["diet"]["name"] == "balanced"

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == f"{base_api_url}/user"


@responses.activate
def test_fetch_all(client, base_api_url):
    """Test fetching all profile data: user, settings, dietary preferences."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user",
        json={
            "email": "user@example.com",
            "sex": "female",
            "first_name": "Jane",
            "body_height": 165,
            "start_weight": 70,
            "goal": "maintain",
            "diet": {
                "carb_percentage": 40,
                "fat_percentage": 35,
                "protein_percentage": 25,
                "name": "high_protein",
            },
        },
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/settings",
        json={
            "has_water_tracker": True,
            "has_feelings": True,
            "has_fasting_tracker_reminders": False,
            "consume_activity_calories": True,
        },
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/dietary-preferences",
        json={"restriction": "vegetarian"},
        status=200,
    )

    profile_data = fetch_all(client)

    assert "user" in profile_data
    assert "settings" in profile_data
    assert "dietary_preferences" in profile_data

    assert profile_data["user"]["email"] == "user@example.com"
    assert profile_data["user"]["first_name"] == "Jane"
    assert profile_data["user"]["goal"] == "maintain"
    assert profile_data["user"]["diet"]["name"] == "high_protein"

    assert profile_data["settings"]["has_water_tracker"] is True
    assert profile_data["settings"]["consume_activity_calories"] is True

    assert profile_data["dietary_preferences"]["restriction"] == "vegetarian"

    assert len(responses.calls) == 3
    assert responses.calls[0].request.url == f"{base_api_url}/user"
    assert responses.calls[1].request.url == f"{base_api_url}/user/settings"
    assert responses.calls[2].request.url == f"{base_api_url}/user/dietary-preferences"
