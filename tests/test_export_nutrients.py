"""
Tests for nutrient history export.
"""

import responses

from yazio_exporter.constants import ALL_MINERALS, ALL_VITAMINS
from yazio_exporter.export_nutrients import (
    fetch_all,
    fetch_multiple,
    fetch_nutrient,
)


@responses.activate
def test_fetch_nutrient_date_range(client, base_api_url):
    """Test fetching nutrient with date range parameters - Feature #37."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-15&end=2024-01-20&nutrient=vitamin.d",
        json={
            "2024-01-15": 0.045,
            "2024-01-16": 0.052,
            "2024-01-17": 0.048,
            "2024-01-18": 0.051,
            "2024-01-19": 0.047,
            "2024-01-20": 0.049,
        },
        status=200,
    )

    data = fetch_nutrient(client, "vitamin.d", "2024-01-15", "2024-01-20")

    assert len(responses.calls) == 1
    assert "start=2024-01-15" in responses.calls[0].request.url
    assert "end=2024-01-20" in responses.calls[0].request.url
    assert "nutrient=vitamin.d" in responses.calls[0].request.url

    assert len(data) == 6
    assert "2024-01-15" in data
    assert "2024-01-20" in data
    assert "2024-01-14" not in data
    assert "2024-01-21" not in data


@responses.activate
def test_fetch_nutrient_filters_nulls(client, base_api_url):
    """Test that null values are filtered out."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-01&end=2024-01-05&nutrient=mineral.iron",
        json={
            "2024-01-01": 12.5,
            "2024-01-02": None,
            "2024-01-03": 14.2,
            "2024-01-04": None,
            "2024-01-05": 13.8,
        },
        status=200,
    )

    data = fetch_nutrient(client, "mineral.iron", "2024-01-01", "2024-01-05")

    assert len(data) == 3
    assert data["2024-01-01"] == 12.5
    assert data["2024-01-03"] == 14.2
    assert data["2024-01-05"] == 13.8
    assert "2024-01-02" not in data
    assert "2024-01-04" not in data


@responses.activate
def test_fetch_nutrient_empty_response(client, base_api_url):
    """Test handling empty response."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-01&end=2024-01-05&nutrient=vitamin.b12",
        json={},
        status=200,
    )

    data = fetch_nutrient(client, "vitamin.b12", "2024-01-01", "2024-01-05")

    assert data == {}


@responses.activate
def test_fetch_multiple_nutrients(client, base_api_url):
    """Test fetching multiple nutrients concurrently - Feature #35."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-01&end=2024-01-31&nutrient=vitamin.d",
        json={"2024-01-01": 0.045, "2024-01-02": 0.048, "2024-01-03": 0.052},
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-01&end=2024-01-31&nutrient=mineral.iron",
        json={"2024-01-01": 12.5, "2024-01-02": 14.2, "2024-01-03": 13.8},
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-01&end=2024-01-31&nutrient=mineral.calcium",
        json={"2024-01-01": 800.0, "2024-01-02": 850.0, "2024-01-03": 820.0},
        status=200,
    )

    nutrients = ["vitamin.d", "mineral.iron", "mineral.calcium"]
    data = fetch_multiple(client, nutrients, "2024-01-01", "2024-01-31")

    assert len(data) == 3
    assert "vitamin.d" in data
    assert "mineral.iron" in data
    assert "mineral.calcium" in data

    assert isinstance(data["vitamin.d"], dict)
    assert isinstance(data["mineral.iron"], dict)
    assert isinstance(data["mineral.calcium"], dict)

    assert len(data["vitamin.d"]) == 3
    assert data["vitamin.d"]["2024-01-01"] == 0.045

    assert len(data["mineral.iron"]) == 3
    assert data["mineral.iron"]["2024-01-01"] == 12.5

    assert len(data["mineral.calcium"]) == 3
    assert data["mineral.calcium"]["2024-01-01"] == 800.0


@responses.activate
def test_fetch_multiple_handles_errors(client, base_api_url):
    """Test that fetch_multiple handles individual nutrient failures gracefully."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-01&end=2024-01-31&nutrient=vitamin.d",
        json={"2024-01-01": 0.045},
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-01&end=2024-01-31&nutrient=mineral.iron",
        json={"error": "Not found"},
        status=404,
    )

    nutrients = ["vitamin.d", "mineral.iron"]
    data = fetch_multiple(client, nutrients, "2024-01-01", "2024-01-31")

    assert len(data) == 2
    assert "vitamin.d" in data
    assert "mineral.iron" in data

    assert len(data["vitamin.d"]) == 1

    assert data["mineral.iron"] == {}


@responses.activate
def test_fetch_nutrient_wide_date_range(client, base_api_url):
    """Test fetching nutrient with wide date range, then verifying filtering."""
    wide_range_data = {f"2024-01-{day:02d}": 0.040 + day * 0.001 for day in range(1, 32)}

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-01&end=2024-01-31&nutrient=vitamin.d",
        json=wide_range_data,
        status=200,
    )

    data = fetch_nutrient(client, "vitamin.d", "2024-01-01", "2024-01-31")

    assert len(data) == 31
    assert "2024-01-01" in data
    assert "2024-01-15" in data
    assert "2024-01-31" in data

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-15&end=2024-01-20&nutrient=vitamin.d",
        json={
            "2024-01-15": wide_range_data["2024-01-15"],
            "2024-01-16": wide_range_data["2024-01-16"],
            "2024-01-17": wide_range_data["2024-01-17"],
            "2024-01-18": wide_range_data["2024-01-18"],
            "2024-01-19": wide_range_data["2024-01-19"],
            "2024-01-20": wide_range_data["2024-01-20"],
        },
        status=200,
    )

    subset_data = fetch_nutrient(client, "vitamin.d", "2024-01-15", "2024-01-20")

    assert len(subset_data) == 6
    assert "2024-01-14" not in subset_data
    assert "2024-01-21" not in subset_data


@responses.activate
def test_fetch_nutrient_specific_nutrient_daily_values(client, base_api_url):
    """Test fetching specific nutrient daily values - Feature #34."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
        "?start=2024-01-01&end=2024-01-31&nutrient=vitamin.d",
        json={"2024-01-15": 0.005, "2024-01-16": 0.008},
        status=200,
    )

    result = fetch_nutrient(client, nutrient_id="vitamin.d", start="2024-01-01", end="2024-01-31")

    assert isinstance(result, dict)
    assert len(result) == 2
    assert result["2024-01-15"] == 0.005
    assert result["2024-01-16"] == 0.008


@responses.activate
def test_fetch_all_nutrients(client, base_api_url):
    """Test fetching complete micronutrient profile - Feature #36."""
    all_nutrients = ALL_VITAMINS + ALL_MINERALS

    for nutrient in all_nutrients:
        responses.add(
            responses.GET,
            f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
            f"?start=2024-01-01&end=2024-01-31&nutrient={nutrient}",
            json={"2024-01-15": 10.5, "2024-01-16": 12.3},
            status=200,
        )

    result = fetch_all(client, start="2024-01-01", end="2024-01-31")

    for vitamin in ALL_VITAMINS:
        assert vitamin in result, f"Missing vitamin: {vitamin}"
        assert isinstance(result[vitamin], dict)
        assert len(result[vitamin]) == 2

    for mineral in ALL_MINERALS:
        assert mineral in result, f"Missing mineral: {mineral}"
        assert isinstance(result[mineral], dict)
        assert len(result[mineral]) == 2

    expected_count = len(ALL_VITAMINS) + len(ALL_MINERALS)
    assert len(result) == expected_count
    assert len(result) >= 20


@responses.activate
def test_fetch_all_vitamins_present(client, base_api_url):
    """Test that fetch_all includes all vitamins from spec."""
    all_nutrients = ALL_VITAMINS + ALL_MINERALS

    for nutrient in all_nutrients:
        responses.add(
            responses.GET,
            f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
            f"?start=2024-01-01&end=2024-01-31&nutrient={nutrient}",
            json={"2024-01-15": 5.0},
            status=200,
        )

    result = fetch_all(client, start="2024-01-01", end="2024-01-31")

    expected_vitamins = [
        "vitamin.a",
        "vitamin.b1",
        "vitamin.b2",
        "vitamin.b3",
        "vitamin.b5",
        "vitamin.b6",
        "vitamin.b7",
        "vitamin.b11",
        "vitamin.b12",
        "vitamin.c",
        "vitamin.d",
        "vitamin.e",
        "vitamin.k",
    ]
    for vitamin in expected_vitamins:
        assert vitamin in result


@responses.activate
def test_fetch_all_minerals_present(client, base_api_url):
    """Test that fetch_all includes all minerals from spec."""
    all_nutrients = ALL_VITAMINS + ALL_MINERALS

    for nutrient in all_nutrients:
        responses.add(
            responses.GET,
            f"{base_api_url}/user/consumed-items/specific-nutrient-daily"
            f"?start=2024-01-01&end=2024-01-31&nutrient={nutrient}",
            json={"2024-01-15": 5.0},
            status=200,
        )

    result = fetch_all(client, start="2024-01-01", end="2024-01-31")

    expected_minerals = [
        "mineral.calcium",
        "mineral.iron",
        "mineral.potassium",
        "mineral.magnesium",
        "mineral.phosphorus",
        "mineral.zinc",
        "mineral.copper",
        "mineral.manganese",
        "mineral.selenium",
        "mineral.iodine",
        "mineral.fluoride",
        "mineral.chlorine",
        "mineral.choline",
    ]
    for mineral in expected_minerals:
        assert mineral in result
