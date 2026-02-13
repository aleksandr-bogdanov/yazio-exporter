"""
Tests for generate_reports module.
"""

from yazio_exporter.generate_reports import (
    _detect_active_range,
    _extract_daily_records,
    _food_stats,
    _get_products_map,
    _weekly_aggregate,
    generate_analysis,
    generate_llm_prompt,
)


def _make_day(kcal, protein=50, carbs=100, fat=40, products=None):
    """Helper to create a realistic day entry."""
    return {
        "daily_summary": {
            "meals": {
                "breakfast": {
                    "nutrients": {
                        "energy.energy": kcal * 0.3,
                        "nutrient.protein": protein * 0.3,
                        "nutrient.carb": carbs * 0.3,
                        "nutrient.fat": fat * 0.3,
                    }
                },
                "lunch": {
                    "nutrients": {
                        "energy.energy": kcal * 0.4,
                        "nutrient.protein": protein * 0.4,
                        "nutrient.carb": carbs * 0.4,
                        "nutrient.fat": fat * 0.4,
                    }
                },
                "dinner": {
                    "nutrients": {
                        "energy.energy": kcal * 0.3,
                        "nutrient.protein": protein * 0.3,
                        "nutrient.carb": carbs * 0.3,
                        "nutrient.fat": fat * 0.3,
                    }
                },
            },
            "goals": {"energy.energy": 2000},
        },
        "consumed": {"products": products or []},
    }


def _make_days_data():
    """Create a realistic multi-day dataset."""
    return {
        "2024-01-15": _make_day(1800, 120, 200, 60),
        "2024-01-16": _make_day(2100, 140, 220, 70),
        "2024-01-17": _make_day(1500, 100, 180, 50),
        "2024-01-18": _make_day(1900, 130, 210, 65),
        "2024-01-19": _make_day(2200, 150, 230, 75),
    }


def _make_weight_data():
    return {
        "2024-01-15": 80.0,
        "2024-01-17": 79.8,
        "2024-01-19": 79.5,
    }


def _make_products_data():
    return {
        "products": {
            "prod-1": {
                "name": "Oatmeal",
                "category": "grains",
                "nutrients": {"energy.energy": 3.5, "nutrient.protein": 0.12},
            },
            "prod-2": {
                "name": "Chicken Breast",
                "category": "meat",
                "nutrients": {"energy.energy": 1.65, "nutrient.protein": 0.31},
            },
        }
    }


def _make_profile_data():
    return {
        "body_height": 180,
        "sex": "male",
        "date_of_birth": "1990-05-15",
        "goal": "lose",
        "weight_change_per_week": -0.5,
        "diet": {"protein_percentage": 30, "carb_percentage": 40, "fat_percentage": 30},
    }


# ── generate_analysis tests ──


def test_generate_analysis_with_realistic_data():
    """generate_analysis returns markdown with expected sections."""
    result = generate_analysis(_make_days_data(), _make_weight_data(), _make_products_data(), _make_profile_data())

    assert result.startswith("# Nutrition Data Analysis")
    assert "## Overview" in result
    assert "## Calories" in result
    assert "## Macros" in result
    assert "## Day of Week" in result
    assert "## Top Foods" in result
    assert "## Extreme Days" in result
    assert "2024-01-15" in result


def test_generate_analysis_empty_data():
    """generate_analysis with empty data returns no-data message."""
    result = generate_analysis({}, {}, {}, {})
    assert "No tracked data" in result


def test_generate_analysis_all_below_threshold():
    """generate_analysis when all days are below 800 kcal."""
    days = {
        "2024-01-15": _make_day(500),
        "2024-01-16": _make_day(600),
    }
    result = generate_analysis(days, {}, {}, {})
    assert "No tracked data" in result or "No tracked days" in result


# ── generate_llm_prompt tests ──


def test_generate_llm_prompt_with_realistic_data():
    """generate_llm_prompt returns string with instructions and data."""
    result = generate_llm_prompt(_make_days_data(), _make_weight_data(), _make_products_data(), _make_profile_data())

    assert "sports nutritionist" in result
    assert "# Client Profile" in result
    assert "# Daily Data" in result or "# Weekly Data" in result
    assert "Top" in result
    assert "2024-01-15" in result


def test_generate_llm_prompt_empty_data():
    """generate_llm_prompt with empty data returns no-data message."""
    result = generate_llm_prompt({}, {}, {}, {})
    assert "No tracked data" in result


def test_generate_llm_prompt_all_below_threshold():
    """generate_llm_prompt when all days are below 800 kcal."""
    days = {
        "2024-01-15": _make_day(500),
        "2024-01-16": _make_day(600),
    }
    result = generate_llm_prompt(days, {}, {}, {})
    assert "No tracked" in result


# ── _detect_active_range tests ──


def test_detect_active_range_finds_correct_dates():
    """_detect_active_range returns first and last tracked dates."""
    days = _make_days_data()
    start, end = _detect_active_range(days)
    assert start == "2024-01-15"
    assert end == "2024-01-19"


def test_detect_active_range_all_below_threshold():
    """_detect_active_range returns (None, None) when all below 800 kcal."""
    days = {
        "2024-01-15": _make_day(500),
        "2024-01-16": _make_day(700),
    }
    start, end = _detect_active_range(days)
    assert start is None
    assert end is None


# ── _extract_daily_records tests ──


def test_extract_daily_records_correct_fields():
    """_extract_daily_records extracts expected fields."""
    days = _make_days_data()
    products = _make_products_data()["products"]
    records = _extract_daily_records(days, _make_weight_data(), products, "2024-01-15", "2024-01-19")

    assert len(records) == 5
    r = records[0]
    assert r["date"] == "2024-01-15"
    assert r["kcal"] == 1800
    assert r["protein"] == 120
    assert r["carbs"] == 200
    assert r["fat"] == 60
    assert r["weight"] == 80.0
    assert r["tracked"] is True
    assert "dow" in r
    assert "weekday" in r


# ── _food_stats tests ──


def test_food_stats_correct_aggregation():
    """_food_stats correctly counts frequency and calories."""
    products = _make_products_data()["products"]
    records = [
        {"products": [{"product_id": "prod-1", "amount": 100}], "tracked": True},
        {
            "products": [{"product_id": "prod-1", "amount": 50}, {"product_id": "prod-2", "amount": 200}],
            "tracked": True,
        },
    ]

    result = _food_stats(records, products, count=10)

    assert len(result) == 2
    oatmeal = next(f for f in result if f["name"] == "Oatmeal")
    assert oatmeal["count"] == 2
    assert oatmeal["total_kcal"] == round(3.5 * 100 + 3.5 * 50)
    assert oatmeal["category"] == "grains"

    chicken = next(f for f in result if f["name"] == "Chicken Breast")
    assert chicken["count"] == 1


# ── _weekly_aggregate tests ──


def test_weekly_aggregate_correct_rollup():
    """_weekly_aggregate produces correct weekly summaries."""
    days = _make_days_data()
    products = _make_products_data()["products"]
    records = _extract_daily_records(days, _make_weight_data(), products, "2024-01-15", "2024-01-19")

    weekly = _weekly_aggregate(records)
    assert len(weekly) == 1  # all within same week
    w = weekly[0]
    assert w["tracked"] == 5
    assert w["total"] == 5
    assert w["avg_kcal"] > 0


# ── _get_products_map tests ──


def test_get_products_map_nested_format():
    """_get_products_map unwraps nested {'products': {...}} format."""
    data = {"products": {"p1": {"name": "Test"}}, "recipes": {}}
    result = _get_products_map(data)
    assert "p1" in result
    assert result["p1"]["name"] == "Test"


def test_get_products_map_flat_format():
    """_get_products_map handles flat {pid: {...}} format."""
    data = {"p1": {"name": "Test"}}
    result = _get_products_map(data)
    assert "p1" in result
    assert result["p1"]["name"] == "Test"
