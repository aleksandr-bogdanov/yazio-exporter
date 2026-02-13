"""
Tests for body measurements export.
"""

import responses

from yazio_exporter.export_body import (
    fetch_weight,
    fetch_weight_range,
    filter_null_values,
    probe_body_types,
)


@responses.activate
def test_fetch_weight_with_value(client, base_api_url):
    """Test fetching weight when measurement exists."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-15",
        json={"date": "2024-01-15", "value": 75.5},
        status=200,
    )

    weight = fetch_weight(client, "2024-01-15")
    assert weight == 75.5


@responses.activate
def test_fetch_weight_null_value(client, base_api_url):
    """Test fetching weight when no measurement exists (null value)."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-16",
        json={"date": "2024-01-16", "value": None},
        status=200,
    )

    weight = fetch_weight(client, "2024-01-16")
    assert weight is None


@responses.activate
def test_fetch_weight_missing_value_field(client, base_api_url):
    """Test fetching weight when response doesn't contain value field."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-17",
        json={"date": "2024-01-17"},
        status=200,
    )

    weight = fetch_weight(client, "2024-01-17")
    assert weight is None


@responses.activate
def test_fetch_weight_null_response(client, base_api_url):
    """Test fetching weight when response is null."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-18",
        json=None,
        status=200,
    )

    weight = fetch_weight(client, "2024-01-18")
    assert weight is None


def test_filter_null_values_with_nulls():
    """Test filtering removes null values."""
    data = {
        "2024-01-01": 75.5,
        "2024-01-02": None,
        "2024-01-03": 76.0,
        "2024-01-04": None,
        "2024-01-05": 75.8,
    }

    filtered = filter_null_values(data)

    assert "2024-01-01" in filtered
    assert filtered["2024-01-01"] == 75.5
    assert "2024-01-02" not in filtered
    assert "2024-01-03" in filtered
    assert filtered["2024-01-03"] == 76.0
    assert "2024-01-04" not in filtered
    assert "2024-01-05" in filtered
    assert filtered["2024-01-05"] == 75.8
    assert len(filtered) == 3


def test_filter_null_values_all_valid():
    """Test filtering preserves all values when no nulls present."""
    data = {"2024-01-01": 75.5, "2024-01-02": 76.0, "2024-01-03": 75.8}

    filtered = filter_null_values(data)

    assert filtered == data
    assert len(filtered) == 3


def test_filter_null_values_all_null():
    """Test filtering returns empty dict when all values are null."""
    data = {"2024-01-01": None, "2024-01-02": None, "2024-01-03": None}

    filtered = filter_null_values(data)

    assert filtered == {}
    assert len(filtered) == 0


def test_filter_null_values_empty_dict():
    """Test filtering empty dict returns empty dict."""
    data = {}

    filtered = filter_null_values(data)

    assert filtered == {}


def test_filter_null_values_preserves_structure():
    """Test filtering preserves the dictionary structure and types."""
    data = {
        "weight": 75.5,
        "body_fat": None,
        "muscle_mass": 65.2,
        "water_percentage": None,
        "bone_mass": 3.5,
    }

    filtered = filter_null_values(data)

    assert isinstance(filtered, dict)
    assert filtered["weight"] == 75.5
    assert filtered["muscle_mass"] == 65.2
    assert filtered["bone_mass"] == 3.5
    assert "body_fat" not in filtered
    assert "water_percentage" not in filtered
    assert len(filtered) == 3


def test_filter_null_values_invalid_input():
    """Test filtering handles invalid input gracefully."""
    assert filter_null_values(None) == {}
    assert filter_null_values([1, 2, 3]) == {}
    assert filter_null_values("string") == {}
    assert filter_null_values(42) == {}


@responses.activate
def test_fetch_weight_range(client, base_api_url):
    """Test fetching weight over a date range with mixed results."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-01",
        json={"date": "2024-01-01", "value": 75.5},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-02",
        json={"date": "2024-01-02", "value": None},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-03",
        json={"date": "2024-01-03", "value": 76.0},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-04",
        json={"date": "2024-01-04", "value": None},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-05",
        json={"date": "2024-01-05", "value": 75.8},
        status=200,
    )

    result = fetch_weight_range(client, "2024-01-01", "2024-01-05")

    assert len(result) == 3
    assert result["2024-01-01"] == 75.5
    assert "2024-01-02" not in result
    assert result["2024-01-03"] == 76.0
    assert "2024-01-04" not in result
    assert result["2024-01-05"] == 75.8

    dates = sorted(result.keys())
    assert dates == ["2024-01-01", "2024-01-03", "2024-01-05"]


@responses.activate
def test_fetch_weight_range_all_null(client, base_api_url):
    """Test fetching weight range when all dates have null measurements."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-01",
        json={"date": "2024-01-01", "value": None},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-02",
        json={"date": "2024-01-02", "value": None},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/weight/last?date=2024-01-03",
        json={"date": "2024-01-03", "value": None},
        status=200,
    )

    result = fetch_weight_range(client, "2024-01-01", "2024-01-03")

    assert result == {}
    assert len(result) == 0


@responses.activate
def test_probe_body_types(client, base_api_url):
    """Test probing for available body measurement types."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/body_fat/last?date=2024-01-15",
        json={"date": "2024-01-15", "value": 18.5},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/waist/last?date=2024-01-15",
        json={"error": "not found"},
        status=404,
    )
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/hip/last?date=2024-01-15",
        json={"date": "2024-01-15", "value": 95.0},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_api_url}/user/bodyvalues/chest/last?date=2024-01-15",
        json={"date": "2024-01-15", "value": None},
        status=200,
    )

    result = probe_body_types(client, "2024-01-15")

    assert len(result) == 2
    assert "body_fat" in result
    assert result["body_fat"] == 18.5
    assert "hip" in result
    assert result["hip"] == 95.0

    assert "waist" not in result
    assert "chest" not in result
