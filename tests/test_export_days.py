"""
Tests for days export.
"""

import datetime as dt
import time
from unittest.mock import patch

import pytest
import responses

from yazio_exporter.export_days import (
    auto_discover_months,
    discover_month,
    fetch_consumed,
    fetch_daily_summary,
    fetch_days_concurrent,
    fetch_exercises,
    fetch_goals,
    fetch_water,
)
from yazio_exporter.models import (
    ConsumedItems,
    DailySummary,
    Exercises,
    Goals,
    WaterIntake,
)


@responses.activate
def test_discover_month_with_data(client, base_api_url):
    """Test discovering days in a month with data."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-01-01&end=2024-01-31",
        json=[
            {
                "date": "2024-01-15",
                "energy": 1636.31,
                "carb": 51.79,
                "protein": 129.66,
                "fat": 96.11,
            },
            {
                "date": "2024-01-20",
                "energy": 1800.50,
                "carb": 60.00,
                "protein": 140.00,
                "fat": 90.00,
            },
        ],
        status=200,
    )

    dates = discover_month(client, 2024, 1)
    assert dates == ["2024-01-15", "2024-01-20"]


@responses.activate
def test_discover_month_empty(client, base_api_url):
    """Test discovering days in a month with no data."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-02-01&end=2024-02-29",
        json=[],
        status=200,
    )

    dates = discover_month(client, 2024, 2)
    assert dates == []


@responses.activate
def test_discover_month_date_format(client, base_api_url):
    """Test that dates are properly formatted as YYYY-MM-DD."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-03-01&end=2024-03-31",
        json=[{"date": "2024-03-01"}, {"date": "2024-03-15"}, {"date": "2024-03-31"}],
        status=200,
    )

    dates = discover_month(client, 2024, 3)
    assert len(dates) == 3
    for date_str in dates:
        parts = date_str.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4  # Year
        assert len(parts[1]) == 2  # Month
        assert len(parts[2]) == 2  # Day


@responses.activate
def test_discover_month_non_leap_year(client, base_api_url):
    """Test that February has correct number of days in non-leap year."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2023-02-01&end=2023-02-28",
        json=[],
        status=200,
    )

    dates = discover_month(client, 2023, 2)
    assert dates == []
    assert len(responses.calls) == 1
    assert "end=2023-02-28" in responses.calls[0].request.url


@responses.activate
def test_discover_month_leap_year(client, base_api_url):
    """Test that February has correct number of days in leap year."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-02-01&end=2024-02-29",
        json=[],
        status=200,
    )

    dates = discover_month(client, 2024, 2)
    assert dates == []
    assert len(responses.calls) == 1
    assert "end=2024-02-29" in responses.calls[0].request.url


@responses.activate
def test_fetch_consumed_items(client, base_api_url):
    """Feature #19: Fetch consumed items for a specific day."""
    mock_response = {
        "products": [
            {
                "id": "prod-uuid-1",
                "date": "2024-01-15 13:29:04",
                "daytime": "lunch",
                "type": "product",
                "product_id": "product-uuid-1",
                "amount": 50,
                "serving": "gram",
                "serving_quantity": 50,
            },
            {
                "id": "prod-uuid-2",
                "date": "2024-01-15 08:15:30",
                "daytime": "breakfast",
                "type": "product",
                "product_id": "product-uuid-2",
                "amount": 100,
                "serving": "gram",
                "serving_quantity": 100,
            },
        ],
        "recipe_portions": [
            {
                "id": "recipe-uuid-1",
                "date": "2024-01-15 12:18:57",
                "daytime": "lunch",
                "type": "recipe_portion",
                "recipe_id": "recipe-uuid-1",
                "portion_count": 4,
            }
        ],
        "simple_products": [],
    }

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items?date=2024-01-15",
        json=mock_response,
        status=200,
    )

    consumed = fetch_consumed(client, "2024-01-15")

    assert isinstance(consumed, ConsumedItems)

    assert len(consumed.products) == 2
    assert consumed.products[0]["id"] == "prod-uuid-1"
    assert consumed.products[0]["product_id"] == "product-uuid-1"
    assert consumed.products[0]["daytime"] == "lunch"
    assert consumed.products[0]["amount"] == 50
    assert consumed.products[0]["serving"] == "gram"

    assert consumed.products[1]["id"] == "prod-uuid-2"
    assert consumed.products[1]["product_id"] == "product-uuid-2"
    assert consumed.products[1]["daytime"] == "breakfast"

    assert len(consumed.recipe_portions) == 1
    assert consumed.recipe_portions[0]["id"] == "recipe-uuid-1"
    assert consumed.recipe_portions[0]["recipe_id"] == "recipe-uuid-1"
    assert consumed.recipe_portions[0]["daytime"] == "lunch"
    assert consumed.recipe_portions[0]["portion_count"] == 4

    assert len(consumed.simple_products) == 0

    assert len(responses.calls) == 1
    assert "consumed-items?date=2024-01-15" in responses.calls[0].request.url


@responses.activate
def test_fetch_exercises(client, base_api_url):
    """Feature #21: Fetch exercises for a specific day."""
    mock_response = {
        "training": [
            {
                "id": "uuid-training-1",
                "note": "Morning run",
                "date": "2024-01-15",
                "name": "Running",
                "energy": 350,
                "distance": 5.0,
                "duration": 1800,
                "source": None,
                "gateway": None,
                "steps": 6000,
            },
            {
                "id": "uuid-training-2",
                "note": "Evening workout",
                "date": "2024-01-15",
                "name": "Cycling",
                "energy": 280,
                "distance": 10.0,
                "duration": 2400,
                "source": "apple_health",
                "gateway": None,
                "steps": 0,
            },
        ],
        "custom_training": [],
        "activity": {
            "energy": 250,
            "distance": 3.0,
            "duration": 3600,
            "source": "apple_health",
            "gateway": None,
            "steps": 8500,
        },
    }

    responses.add(
        responses.GET,
        f"{base_api_url}/user/exercises?date=2024-01-15",
        json=mock_response,
        status=200,
    )

    exercises = fetch_exercises(client, "2024-01-15")

    assert isinstance(exercises, Exercises)

    assert len(exercises.training) == 2
    assert exercises.training[0]["id"] == "uuid-training-1"
    assert exercises.training[0]["name"] == "Running"
    assert exercises.training[0]["energy"] == 350
    assert exercises.training[0]["distance"] == 5.0
    assert exercises.training[0]["duration"] == 1800
    assert exercises.training[0]["steps"] == 6000

    assert exercises.training[1]["id"] == "uuid-training-2"
    assert exercises.training[1]["name"] == "Cycling"
    assert exercises.training[1]["energy"] == 280
    assert exercises.training[1]["distance"] == 10.0
    assert exercises.training[1]["duration"] == 2400
    assert exercises.training[1]["steps"] == 0

    assert len(exercises.custom_training) == 0

    assert exercises.activity is not None
    assert exercises.activity["energy"] == 250
    assert exercises.activity["distance"] == 3.0
    assert exercises.activity["duration"] == 3600
    assert exercises.activity["steps"] == 8500
    assert exercises.activity["source"] == "apple_health"

    assert len(responses.calls) == 1
    assert "exercises?date=2024-01-15" in responses.calls[0].request.url


@responses.activate
def test_fetch_daily_summary(client, base_api_url):
    """Feature #23: Fetch daily summary with meal breakdowns."""
    mock_response = {
        "activity_energy": 250,
        "consume_activity_energy": True,
        "steps": 8500,
        "water_intake": 2000,
        "active_fasting_countdown_template_key": None,
        "goals": {
            "energy.energy": 2000,
            "nutrient.protein": 156,
            "nutrient.carb": 250,
            "nutrient.fat": 67,
            "activity.step": 10000,
            "water": 2000,
        },
        "units": {
            "unit_mass": "kg",
            "unit_energy": "kcal",
            "unit_serving": "metric",
            "unit_length": "cm",
        },
        "meals": {
            "breakfast": {
                "energy_goal": 500,
                "nutrients": {
                    "energy.energy": 450,
                    "nutrient.carb": 60,
                    "nutrient.protein": 25,
                    "nutrient.fat": 15,
                },
            },
            "lunch": {
                "energy_goal": 700,
                "nutrients": {
                    "energy.energy": 680,
                    "nutrient.carb": 85,
                    "nutrient.protein": 45,
                    "nutrient.fat": 20,
                },
            },
            "dinner": {
                "energy_goal": 600,
                "nutrients": {
                    "energy.energy": 520,
                    "nutrient.carb": 70,
                    "nutrient.protein": 40,
                    "nutrient.fat": 18,
                },
            },
            "snack": {
                "energy_goal": 200,
                "nutrients": {
                    "energy.energy": 180,
                    "nutrient.carb": 25,
                    "nutrient.protein": 8,
                    "nutrient.fat": 5,
                },
            },
        },
        "user": {
            "start_weight": 85,
            "current_weight": 75.5,
            "goal": "lose",
            "sex": "male",
        },
    }

    responses.add(
        responses.GET,
        f"{base_api_url}/user/widgets/daily-summary?date=2024-01-15",
        json=mock_response,
        status=200,
    )

    summary = fetch_daily_summary(client, "2024-01-15")

    assert isinstance(summary, DailySummary)

    assert len(summary.meals) == 4
    assert "breakfast" in summary.meals
    assert "lunch" in summary.meals
    assert "dinner" in summary.meals
    assert "snack" in summary.meals

    assert summary.meals["breakfast"]["energy_goal"] == 500
    assert summary.meals["breakfast"]["nutrients"]["energy.energy"] == 450
    assert summary.meals["breakfast"]["nutrients"]["nutrient.carb"] == 60
    assert summary.meals["breakfast"]["nutrients"]["nutrient.protein"] == 25
    assert summary.meals["breakfast"]["nutrients"]["nutrient.fat"] == 15

    assert summary.meals["lunch"]["energy_goal"] == 700
    assert summary.meals["lunch"]["nutrients"]["energy.energy"] == 680

    assert summary.meals["dinner"]["energy_goal"] == 600
    assert summary.meals["dinner"]["nutrients"]["energy.energy"] == 520

    assert summary.meals["snack"]["energy_goal"] == 200
    assert summary.meals["snack"]["nutrients"]["energy.energy"] == 180

    assert summary.activity_energy == 250
    assert summary.steps == 8500
    assert summary.water_intake == 2000

    assert summary.goals["energy.energy"] == 2000
    assert summary.goals["nutrient.protein"] == 156
    assert summary.goals["nutrient.carb"] == 250
    assert summary.goals["nutrient.fat"] == 67
    assert summary.goals["activity.step"] == 10000
    assert summary.goals["water"] == 2000

    assert summary.units["unit_mass"] == "kg"
    assert summary.units["unit_energy"] == "kcal"
    assert summary.units["unit_serving"] == "metric"
    assert summary.units["unit_length"] == "cm"

    assert len(responses.calls) == 1
    assert "daily-summary?date=2024-01-15" in responses.calls[0].request.url


@responses.activate
def test_fetch_goals(client, base_api_url):
    """Feature #20: Fetch goals for a specific day."""
    mock_response = {
        "energy.energy": 2000,
        "nutrient.protein": 156.1,
        "nutrient.fat": 113.98,
        "nutrient.carb": 73.17,
        "activity.step": 10000,
        "bodyvalue.weight": 61,
        "water": 2000,
    }

    responses.add(
        responses.GET,
        f"{base_api_url}/user/goals?date=2024-01-15",
        json=mock_response,
        status=200,
    )

    goals = fetch_goals(client, "2024-01-15")

    assert isinstance(goals, Goals)

    assert goals.data["energy.energy"] == 2000
    assert goals.data["nutrient.protein"] == 156.1
    assert goals.data["nutrient.fat"] == 113.98
    assert goals.data["nutrient.carb"] == 73.17
    assert goals.data["activity.step"] == 10000
    assert goals.data["bodyvalue.weight"] == 61
    assert goals.data["water"] == 2000

    assert len(responses.calls) == 1
    assert "goals?date=2024-01-15" in responses.calls[0].request.url


@responses.activate
def test_fetch_water(client, base_api_url):
    """Feature #22: Fetch water intake for a specific day."""
    mock_response = {"water_intake": 2000, "gateway": None, "source": None}

    responses.add(
        responses.GET,
        f"{base_api_url}/user/water-intake?date=2024-01-15",
        json=mock_response,
        status=200,
    )

    water = fetch_water(client, "2024-01-15")

    assert isinstance(water, WaterIntake)

    assert water.water_intake == 2000
    assert water.gateway is None
    assert water.source is None

    assert len(responses.calls) == 1
    assert "water-intake?date=2024-01-15" in responses.calls[0].request.url


@responses.activate
def test_fetch_days_concurrent(client, base_api_url):
    """Feature #24: Concurrent fetching of multiple days works correctly."""
    dates = [f"2024-01-{str(i).zfill(2)}" for i in range(1, 11)]

    for date in dates:
        responses.add(
            responses.GET,
            f"{base_api_url}/user/consumed-items?date={date}",
            json={
                "products": [{"id": f"prod-{date}", "product_id": "test-product"}],
                "recipe_portions": [],
                "simple_products": [],
            },
            status=200,
        )

    for date in dates:
        responses.add(
            responses.GET,
            f"{base_api_url}/user/goals?date={date}",
            json={
                "energy.energy": 2000,
                "nutrient.protein": 150,
                "nutrient.carb": 250,
                "nutrient.fat": 65,
            },
            status=200,
        )

    start_time = time.time()

    results = fetch_days_concurrent(client, dates=dates, data_types=["consumed", "goals"])

    execution_time = time.time() - start_time

    assert len(results) == 10
    for date in dates:
        assert date in results

    for date in dates:
        assert "consumed" in results[date]
        assert "goals" in results[date]

        assert isinstance(results[date]["consumed"], ConsumedItems)
        assert len(results[date]["consumed"].products) == 1
        assert results[date]["consumed"].products[0]["id"] == f"prod-{date}"

        assert isinstance(results[date]["goals"], Goals)
        assert results[date]["goals"].data["energy.energy"] == 2000
        assert results[date]["goals"].data["nutrient.protein"] == 150

    assert len(responses.calls) == 20

    assert execution_time < 5.0


@responses.activate
def test_fetch_days_concurrent_with_all_data_types(client, base_api_url):
    """Test concurrent fetching with all supported data types."""
    dates = ["2024-01-15", "2024-01-16"]

    for date in dates:
        responses.add(
            responses.GET,
            f"{base_api_url}/user/consumed-items?date={date}",
            json={"products": [], "recipe_portions": [], "simple_products": []},
            status=200,
        )

        responses.add(
            responses.GET,
            f"{base_api_url}/user/goals?date={date}",
            json={"energy.energy": 2000},
            status=200,
        )

        responses.add(
            responses.GET,
            f"{base_api_url}/user/exercises?date={date}",
            json={"training": [], "custom_training": [], "activity": None},
            status=200,
        )

        responses.add(
            responses.GET,
            f"{base_api_url}/user/widgets/daily-summary?date={date}",
            json={
                "meals": {},
                "activity_energy": None,
                "steps": None,
                "water_intake": None,
                "goals": {},
                "units": {},
            },
            status=200,
        )

    results = fetch_days_concurrent(
        client,
        dates=dates,
        data_types=["consumed", "goals", "exercises", "daily_summary"],
    )

    assert len(results) == 2
    for date in dates:
        assert len(results[date]) == 4
        assert isinstance(results[date]["consumed"], ConsumedItems)
        assert isinstance(results[date]["goals"], Goals)
        assert isinstance(results[date]["exercises"], Exercises)
        assert isinstance(results[date]["daily_summary"], DailySummary)

    assert len(responses.calls) == 8


@responses.activate
def test_fetch_days_concurrent_invalid_data_type(client):
    """Test that invalid data type raises ValueError."""
    with pytest.raises(ValueError, match="Unknown data type: invalid"):
        fetch_days_concurrent(client, dates=["2024-01-15"], data_types=["consumed", "invalid"])


@responses.activate
def test_fetch_days_concurrent_partial_failure(client, base_api_url):
    """Feature #64: Individual failures don't abort entire export."""
    dates = [f"2024-01-{str(i).zfill(2)}" for i in range(1, 11)]

    for i, date in enumerate(dates, start=1):
        if i == 5:
            for _ in range(3):
                responses.add(
                    responses.GET,
                    f"{base_api_url}/user/consumed-items?date={date}",
                    json={"error": "Internal server error"},
                    status=500,
                )
        else:
            responses.add(
                responses.GET,
                f"{base_api_url}/user/consumed-items?date={date}",
                json={
                    "products": [{"id": f"prod-{date}"}],
                    "recipe_portions": [],
                    "simple_products": [],
                },
                status=200,
            )

    results = fetch_days_concurrent(client, dates=dates, data_types=["consumed"])

    assert len(results) == 10
    for date in dates:
        assert date in results

    successful_count = 0
    failed_count = 0

    for i, date in enumerate(dates, start=1):
        if i == 5:
            assert "consumed" in results[date]
            assert isinstance(results[date]["consumed"], Exception)
            failed_count += 1
        else:
            assert "consumed" in results[date]
            assert isinstance(results[date]["consumed"], ConsumedItems)
            assert len(results[date]["consumed"].products) == 1
            successful_count += 1

    assert successful_count == 9
    assert failed_count == 1

    assert len(responses.calls) == 12


@responses.activate
def test_fetch_days_concurrent_multiple_failures(client, base_api_url):
    """Test handling multiple failures across different days."""
    dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items?date=2024-01-01",
        json={"error": "Not found"},
        status=404,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items?date=2024-01-02",
        json={"products": [], "recipe_portions": [], "simple_products": []},
        status=200,
    )

    for _ in range(3):
        responses.add(
            responses.GET,
            f"{base_api_url}/user/consumed-items?date=2024-01-03",
            json={"error": "Timeout"},
            status=500,
        )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items?date=2024-01-04",
        json={"products": [], "recipe_portions": [], "simple_products": []},
        status=200,
    )

    results = fetch_days_concurrent(client, dates=dates, data_types=["consumed"])

    assert len(results) == 4

    assert isinstance(results["2024-01-01"]["consumed"], Exception)
    assert isinstance(results["2024-01-03"]["consumed"], Exception)

    assert isinstance(results["2024-01-02"]["consumed"], ConsumedItems)
    assert isinstance(results["2024-01-04"]["consumed"], ConsumedItems)


@responses.activate
def test_auto_discover_months_scans_all_months(client, base_api_url):
    """Auto-discovery scans every month from start through current month."""

    class FakeDate(dt.date):
        @classmethod
        def today(cls):
            return dt.date(2024, 4, 15)

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-01-01&end=2024-01-31",
        json=[{"date": "2024-01-15"}, {"date": "2024-01-20"}],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-02-01&end=2024-02-29",
        json=[],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-03-01&end=2024-03-31",
        json=[],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-04-01&end=2024-04-30",
        json=[],
        status=200,
    )

    with patch("yazio_exporter.export_days.date", FakeDate):
        dates = auto_discover_months(client, start_year=2024, start_month=1)

    assert dates == ["2024-01-15", "2024-01-20"]

    # All 4 months scanned (Jan–Apr), no early termination
    assert len(responses.calls) == 4

    assert "start=2024-01-01" in responses.calls[0].request.url
    assert "start=2024-02-01" in responses.calls[1].request.url
    assert "start=2024-03-01" in responses.calls[2].request.url
    assert "start=2024-04-01" in responses.calls[3].request.url


@responses.activate
def test_auto_discover_months_multiple_data_months(client, base_api_url):
    """Test auto-discovery with multiple months containing data and gaps."""

    class FakeDate(dt.date):
        @classmethod
        def today(cls):
            return dt.date(2024, 6, 15)

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-01-01&end=2024-01-31",
        json=[{"date": "2024-01-15"}, {"date": "2024-01-20"}],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-02-01&end=2024-02-29",
        json=[],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-03-01&end=2024-03-31",
        json=[{"date": "2024-03-10"}],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-04-01&end=2024-04-30",
        json=[],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-05-01&end=2024-05-31",
        json=[],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-06-01&end=2024-06-30",
        json=[],
        status=200,
    )

    with patch("yazio_exporter.export_days.date", FakeDate):
        dates = auto_discover_months(client, start_year=2024, start_month=1)

    assert dates == ["2024-01-15", "2024-01-20", "2024-03-10"]

    assert len(responses.calls) == 6


@responses.activate
def test_auto_discover_months_crosses_year_boundary(client, base_api_url):
    """Test auto-discovery crosses from one year to the next."""

    class FakeDate(dt.date):
        @classmethod
        def today(cls):
            return dt.date(2024, 2, 15)

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2023-11-01&end=2023-11-30",
        json=[{"date": "2023-11-15"}],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2023-12-01&end=2023-12-31",
        json=[],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-01-01&end=2024-01-31",
        json=[],
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items/nutrients-daily?start=2024-02-01&end=2024-02-29",
        json=[],
        status=200,
    )

    with patch("yazio_exporter.export_days.date", FakeDate):
        dates = auto_discover_months(client, start_year=2023, start_month=11)

    assert dates == ["2023-11-15"]

    assert len(responses.calls) == 4

    assert "start=2023-11-01" in responses.calls[0].request.url
    assert "start=2023-12-01" in responses.calls[1].request.url
    assert "start=2024-01-01" in responses.calls[2].request.url
    assert "start=2024-02-01" in responses.calls[3].request.url


@responses.activate
def test_empty_date_range_returns_empty_result(client):
    """Feature #70: Empty date range returns empty result."""
    results = fetch_days_concurrent(
        client,
        dates=[],
        data_types=["consumed", "goals"],
    )

    assert results == {}
    assert isinstance(results, dict)

    assert len(responses.calls) == 0


@responses.activate
def test_days_with_no_consumed_items_handled_gracefully(client, base_api_url):
    """Feature #71: Days with no consumed items handled gracefully."""
    responses.add(
        responses.GET,
        f"{base_api_url}/user/consumed-items?date=2024-01-15",
        json={"products": [], "recipe_portions": [], "simple_products": []},
        status=200,
    )

    consumed = fetch_consumed(client, "2024-01-15")

    assert isinstance(consumed, ConsumedItems)

    assert consumed.products == []
    assert consumed.recipe_portions == []
    assert consumed.simple_products == []
    assert len(consumed.products) == 0
    assert len(consumed.recipe_portions) == 0
    assert len(consumed.simple_products) == 0

    assert len(responses.calls) == 1
