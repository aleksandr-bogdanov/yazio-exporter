"""
Tests for analytics engine.
"""

import pytest

from yazio_exporter.analytics import (
    calculate_calorie_stats,
    calculate_exercise_stats,
    calculate_macro_ratios,
    calculate_meal_distribution,
    calculate_water_stats,
    calculate_weight_calorie_correlation,
    calculate_weight_trend,
    rank_products_by_frequency,
)


def test_calculate_water_stats_basic():
    """Test water stats with basic data."""
    # Test data: [2000, 1500, 2200, 1800, 2500] ml, goal=2000ml
    water_data = [2000, 1500, 2200, 1800, 2500]
    goal = 2000

    result = calculate_water_stats(water_data, goal)

    # Average: (2000 + 1500 + 2200 + 1800 + 2500) / 5 = 10000 / 5 = 2000
    assert result["avg_intake"] == 2000.0

    # Days >= 2000: 2000, 2200, 2500 = 3 days
    assert result["days_meeting_goal"] == 3

    # Percentage: 3/5 = 60%
    assert result["percentage"] == 60.0


def test_calculate_water_stats_empty_data():
    """Test water stats with empty data."""
    result = calculate_water_stats([], goal=2000)

    assert result["avg_intake"] == 0.0
    assert result["days_meeting_goal"] == 0
    assert result["percentage"] == 0.0


def test_calculate_water_stats_all_meeting_goal():
    """Test water stats when all days meet goal."""
    water_data = [2000, 2500, 3000]
    goal = 2000

    result = calculate_water_stats(water_data, goal)

    assert result["avg_intake"] == 2500.0
    assert result["days_meeting_goal"] == 3
    assert result["percentage"] == 100.0


def test_calculate_water_stats_none_meeting_goal():
    """Test water stats when no days meet goal."""
    water_data = [1000, 1200, 1500]
    goal = 2000

    result = calculate_water_stats(water_data, goal)

    assert result["avg_intake"] == pytest.approx(1233.33, rel=0.01)
    assert result["days_meeting_goal"] == 0
    assert result["percentage"] == 0.0


def test_calculate_calorie_stats_basic():
    """Test calorie stats with known values (Feature #51)."""
    # Sample days data: 1500, 1800, 2000, 1600, 1900 calories
    days_data = {
        "2024-01-15": {"energy": 1500.0},
        "2024-01-16": {"energy": 1800.0},
        "2024-01-17": {"energy": 2000.0},
        "2024-01-18": {"energy": 1600.0},
        "2024-01-19": {"energy": 1900.0},
    }

    result = calculate_calorie_stats(days_data)

    # Average: (1500 + 1800 + 2000 + 1600 + 1900) / 5 = 8800 / 5 = 1760
    assert result["avg"] == 1760.0
    # Minimum: 1500
    assert result["min"] == 1500.0
    # Maximum: 2000
    assert result["max"] == 2000.0


def test_calculate_calorie_stats_empty_data():
    """Test calorie stats with empty data."""
    result = calculate_calorie_stats({})

    assert result["avg"] == 0.0
    assert result["min"] == 0.0
    assert result["max"] == 0.0


def test_calculate_calorie_stats_single_day():
    """Test calorie stats with single day."""
    days_data = {"2024-01-15": {"energy": 2000.0}}

    result = calculate_calorie_stats(days_data)

    assert result["avg"] == 2000.0
    assert result["min"] == 2000.0
    assert result["max"] == 2000.0


def test_calculate_calorie_stats_with_additional_fields():
    """Test calorie stats ignores other fields."""
    days_data = {
        "2024-01-15": {"energy": 1500.0, "carb": 200.0, "protein": 80.0},
        "2024-01-16": {"energy": 2000.0, "carb": 250.0, "protein": 100.0},
    }

    result = calculate_calorie_stats(days_data)

    assert result["avg"] == 1750.0
    assert result["min"] == 1500.0
    assert result["max"] == 2000.0


def test_calculate_macro_ratios_basic():
    """Test macro ratio calculation with known values (Feature #52)."""
    # Sample data: carb=200g, protein=100g, fat=80g
    # carb: 200g * 4 cal/g = 800 cal
    # protein: 100g * 4 cal/g = 400 cal
    # fat: 80g * 9 cal/g = 720 cal
    # total: 1920 cal
    # carb_pct: 800/1920 * 100 = 41.67%
    # protein_pct: 400/1920 * 100 = 20.83%
    # fat_pct: 720/1920 * 100 = 37.5%
    days_data = {"2024-01-15": {"carb": 200.0, "protein": 100.0, "fat": 80.0}}

    result = calculate_macro_ratios(days_data)

    assert result["carb_pct"] == pytest.approx(41.67, rel=0.01)
    assert result["protein_pct"] == pytest.approx(20.83, rel=0.01)
    assert result["fat_pct"] == pytest.approx(37.5, rel=0.01)

    # Verify sum is 100%
    total = result["carb_pct"] + result["protein_pct"] + result["fat_pct"]
    assert total == pytest.approx(100.0, rel=0.01)


def test_calculate_macro_ratios_multiple_days():
    """Test macro ratio calculation across multiple days."""
    # Day 1: carb=150g, protein=80g, fat=60g
    # Day 2: carb=200g, protein=120g, fat=70g
    # Total: carb=350g, protein=200g, fat=130g
    # carb: 350g * 4 = 1400 cal
    # protein: 200g * 4 = 800 cal
    # fat: 130g * 9 = 1170 cal
    # total: 3370 cal
    days_data = {
        "2024-01-15": {"carb": 150.0, "protein": 80.0, "fat": 60.0},
        "2024-01-16": {"carb": 200.0, "protein": 120.0, "fat": 70.0},
    }

    result = calculate_macro_ratios(days_data)

    # carb_pct: 1400/3370 * 100 = 41.54%
    assert result["carb_pct"] == pytest.approx(41.54, rel=0.01)
    # protein_pct: 800/3370 * 100 = 23.74%
    assert result["protein_pct"] == pytest.approx(23.74, rel=0.01)
    # fat_pct: 1170/3370 * 100 = 34.72%
    assert result["fat_pct"] == pytest.approx(34.72, rel=0.01)

    # Verify sum is 100%
    total = result["carb_pct"] + result["protein_pct"] + result["fat_pct"]
    assert total == pytest.approx(100.0, rel=0.01)


def test_calculate_macro_ratios_empty_data():
    """Test macro ratios with empty data."""
    result = calculate_macro_ratios({})

    assert result["carb_pct"] == 0.0
    assert result["protein_pct"] == 0.0
    assert result["fat_pct"] == 0.0


def test_calculate_macro_ratios_zero_macros():
    """Test macro ratios when all macros are zero."""
    days_data = {"2024-01-15": {"carb": 0.0, "protein": 0.0, "fat": 0.0}}

    result = calculate_macro_ratios(days_data)

    assert result["carb_pct"] == 0.0
    assert result["protein_pct"] == 0.0
    assert result["fat_pct"] == 0.0


def test_calculate_weight_trend_basic():
    """Test weight trend calculation (Feature #54)."""
    # Create weight data: start=85kg, current=75.5kg, over 12 weeks (84 days)
    weight_data = [
        {"date": "2024-01-01", "weight": 85.0},
        {"date": "2024-01-08", "weight": 84.2},
        {"date": "2024-01-15", "weight": 83.5},
        {"date": "2024-01-22", "weight": 82.8},
        {"date": "2024-01-29", "weight": 82.0},
        {"date": "2024-02-05", "weight": 81.3},
        {"date": "2024-02-12", "weight": 80.5},
        {"date": "2024-02-19", "weight": 79.8},
        {"date": "2024-02-26", "weight": 79.0},
        {"date": "2024-03-04", "weight": 78.2},
        {"date": "2024-03-11", "weight": 77.0},
        {"date": "2024-03-18", "weight": 76.2},
        {"date": "2024-03-25", "weight": 75.5},
    ]

    result = calculate_weight_trend(weight_data)

    # Verify starting weight
    assert result["starting_weight"] == 85.0

    # Verify current weight
    assert result["current_weight"] == 75.5

    # Verify total change
    assert result["total_change"] == -9.5

    # Verify weekly average change
    # Days: 2024-01-01 to 2024-03-25 = 84 days = 12 weeks
    # Weekly avg: -9.5 / 12 = -0.791666...
    assert result["weekly_avg_change"] == pytest.approx(-0.79, rel=0.01)


def test_calculate_weight_trend_empty_data():
    """Test weight trend with empty data."""
    result = calculate_weight_trend([])

    assert result["starting_weight"] == 0.0
    assert result["current_weight"] == 0.0
    assert result["total_change"] == 0.0
    assert result["weekly_avg_change"] == 0.0


def test_calculate_weight_trend_single_measurement():
    """Test weight trend with single measurement."""
    weight_data = [{"date": "2024-01-01", "weight": 80.0}]

    result = calculate_weight_trend(weight_data)

    assert result["starting_weight"] == 80.0
    assert result["current_weight"] == 80.0
    assert result["total_change"] == 0.0
    assert result["weekly_avg_change"] == 0.0


def test_calculate_weight_trend_weight_gain():
    """Test weight trend with weight gain."""
    # Weight gain over 4 weeks (28 days): 70kg to 75kg = +5kg
    weight_data = [
        {"date": "2024-01-01", "weight": 70.0},
        {"date": "2024-01-08", "weight": 71.2},
        {"date": "2024-01-15", "weight": 72.5},
        {"date": "2024-01-22", "weight": 73.8},
        {"date": "2024-01-29", "weight": 75.0},
    ]

    result = calculate_weight_trend(weight_data)

    assert result["starting_weight"] == 70.0
    assert result["current_weight"] == 75.0
    assert result["total_change"] == 5.0
    # 28 days = 4 weeks, +5kg / 4 weeks = +1.25 kg/week
    assert result["weekly_avg_change"] == pytest.approx(1.25, rel=0.01)


def test_calculate_weight_trend_filters_null_weights():
    """Test weight trend filters out null weight values."""
    weight_data = [
        {"date": "2024-01-01", "weight": 80.0},
        {"date": "2024-01-08", "weight": None},
        {"date": "2024-01-15", "weight": 78.5},
        {"date": "2024-01-22", "weight": None},
        {"date": "2024-01-29", "weight": 77.0},
    ]

    result = calculate_weight_trend(weight_data)

    assert result["starting_weight"] == 80.0
    assert result["current_weight"] == 77.0
    assert result["total_change"] == -3.0


def test_calculate_weight_trend_irregular_intervals():
    """Test weight trend with irregular measurement intervals."""
    # Measurements at irregular intervals over 3 weeks (21 days)
    weight_data = [
        {"date": "2024-01-01", "weight": 85.0},
        {"date": "2024-01-03", "weight": 84.8},
        {"date": "2024-01-10", "weight": 83.5},
        {"date": "2024-01-22", "weight": 82.0},
    ]

    result = calculate_weight_trend(weight_data)

    assert result["starting_weight"] == 85.0
    assert result["current_weight"] == 82.0
    assert result["total_change"] == -3.0
    # 21 days = 3 weeks, -3kg / 3 weeks = -1.0 kg/week
    assert result["weekly_avg_change"] == pytest.approx(-1.0, rel=0.01)


def test_calculate_meal_distribution_basic():
    """Test meal distribution calculation with single day (Feature #53)."""
    # Sample data: breakfast=450, lunch=680, dinner=520, snack=180
    summary_data = {
        "2024-01-15": {
            "meals": {
                "breakfast": {
                    "energy_goal": 500,
                    "nutrients": {
                        "energy.energy": 450,
                        "nutrient.carb": 60,
                        "nutrient.protein": 25,
                    },
                },
                "lunch": {
                    "energy_goal": 700,
                    "nutrients": {
                        "energy.energy": 680,
                        "nutrient.carb": 85,
                        "nutrient.protein": 45,
                    },
                },
                "dinner": {
                    "energy_goal": 600,
                    "nutrients": {
                        "energy.energy": 520,
                        "nutrient.carb": 70,
                        "nutrient.protein": 40,
                    },
                },
                "snack": {
                    "energy_goal": 200,
                    "nutrients": {
                        "energy.energy": 180,
                        "nutrient.carb": 25,
                        "nutrient.protein": 8,
                    },
                },
            }
        }
    }

    result = calculate_meal_distribution(summary_data)

    # With single day, averages equal the values
    assert result["breakfast"] == 450.0
    assert result["lunch"] == 680.0
    assert result["dinner"] == 520.0
    assert result["snack"] == 180.0


def test_calculate_meal_distribution_multiple_days():
    """Test meal distribution across multiple days."""
    # Day 1: breakfast=400, lunch=600, dinner=500, snack=150
    # Day 2: breakfast=500, lunch=700, dinner=600, snack=200
    # Averages: breakfast=450, lunch=650, dinner=550, snack=175
    summary_data = {
        "2024-01-15": {
            "meals": {
                "breakfast": {"nutrients": {"energy.energy": 400}},
                "lunch": {"nutrients": {"energy.energy": 600}},
                "dinner": {"nutrients": {"energy.energy": 500}},
                "snack": {"nutrients": {"energy.energy": 150}},
            }
        },
        "2024-01-16": {
            "meals": {
                "breakfast": {"nutrients": {"energy.energy": 500}},
                "lunch": {"nutrients": {"energy.energy": 700}},
                "dinner": {"nutrients": {"energy.energy": 600}},
                "snack": {"nutrients": {"energy.energy": 200}},
            }
        },
    }

    result = calculate_meal_distribution(summary_data)

    assert result["breakfast"] == 450.0
    assert result["lunch"] == 650.0
    assert result["dinner"] == 550.0
    assert result["snack"] == 175.0


def test_calculate_meal_distribution_empty_data():
    """Test meal distribution with empty data."""
    result = calculate_meal_distribution({})

    assert result["breakfast"] == 0.0
    assert result["lunch"] == 0.0
    assert result["dinner"] == 0.0
    assert result["snack"] == 0.0


def test_calculate_meal_distribution_missing_meals():
    """Test meal distribution when some meals are missing."""
    summary_data = {
        "2024-01-15": {
            "meals": {
                "breakfast": {"nutrients": {"energy.energy": 400}},
                "lunch": {"nutrients": {"energy.energy": 600}},
                # dinner and snack missing
            }
        }
    }

    result = calculate_meal_distribution(summary_data)

    assert result["breakfast"] == 400.0
    assert result["lunch"] == 600.0
    assert result["dinner"] == 0.0  # Missing meal
    assert result["snack"] == 0.0  # Missing meal


def test_calculate_weight_calorie_correlation_basic():
    """Test weight-calorie correlation with weight loss on deficit (Feature #55)."""
    # Scenario: Weight decreasing with calorie deficit
    weight_data = [
        {"date": "2024-01-01", "weight": 85.0},
        {"date": "2024-01-08", "weight": 84.2},
        {"date": "2024-01-15", "weight": 83.5},
        {"date": "2024-01-22", "weight": 82.8},
        {"date": "2024-01-29", "weight": 82.0},
    ]

    days_data = {
        "2024-01-01": {"energy": 1600.0, "energy_goal": 2000.0},  # -400 deficit
        "2024-01-08": {"energy": 1550.0, "energy_goal": 2000.0},  # -450 deficit
        "2024-01-15": {"energy": 1650.0, "energy_goal": 2000.0},  # -350 deficit
        "2024-01-22": {"energy": 1700.0, "energy_goal": 2000.0},  # -300 deficit
        "2024-01-29": {"energy": 1600.0, "energy_goal": 2000.0},  # -400 deficit
    }

    result = calculate_weight_calorie_correlation(weight_data, days_data)

    # Verify correlation coefficient is returned
    assert "correlation" in result
    assert isinstance(result["correlation"], float)

    # Verify trend description
    assert result["trend_description"] == "weight decreasing with calorie deficit"

    # Verify average deficit calculation
    # (-400 + -450 + -350 + -300 + -400) / 5 = -1900 / 5 = -380
    assert result["avg_deficit_surplus"] == pytest.approx(-380.0, rel=0.01)


def test_calculate_weight_calorie_correlation_empty_data():
    """Test correlation with empty data."""
    result = calculate_weight_calorie_correlation([], {})

    assert result["correlation"] == 0.0
    assert result["trend_description"] == "insufficient data"
    assert result["avg_deficit_surplus"] == 0.0


def test_calculate_weight_calorie_correlation_insufficient_aligned_data():
    """Test correlation when weight and calorie data don't overlap."""
    weight_data = [
        {"date": "2024-01-01", "weight": 85.0},
        {"date": "2024-01-08", "weight": 84.0},
    ]

    days_data = {
        "2024-01-15": {"energy": 1600.0, "energy_goal": 2000.0},
        "2024-01-22": {"energy": 1700.0, "energy_goal": 2000.0},
    }

    result = calculate_weight_calorie_correlation(weight_data, days_data)

    assert result["correlation"] == 0.0
    assert result["trend_description"] == "insufficient aligned data"
    assert result["avg_deficit_surplus"] == 0.0


def test_calculate_weight_calorie_correlation_weight_gain_with_surplus():
    """Test correlation with weight gain on calorie surplus."""
    weight_data = [
        {"date": "2024-01-01", "weight": 70.0},
        {"date": "2024-01-08", "weight": 70.8},
        {"date": "2024-01-15", "weight": 71.5},
        {"date": "2024-01-22", "weight": 72.2},
    ]

    days_data = {
        "2024-01-01": {"energy": 2400.0, "energy_goal": 2000.0},  # +400 surplus
        "2024-01-08": {"energy": 2500.0, "energy_goal": 2000.0},  # +500 surplus
        "2024-01-15": {"energy": 2350.0, "energy_goal": 2000.0},  # +350 surplus
        "2024-01-22": {"energy": 2450.0, "energy_goal": 2000.0},  # +450 surplus
    }

    result = calculate_weight_calorie_correlation(weight_data, days_data)

    assert result["trend_description"] == "weight increasing with calorie surplus"
    # (+400 + +500 + +350 + +450) / 4 = 1700 / 4 = 425
    assert result["avg_deficit_surplus"] == pytest.approx(425.0, rel=0.01)


def test_calculate_weight_calorie_correlation_stable_weight_balanced_calories():
    """Test correlation with stable weight and balanced calories."""
    weight_data = [
        {"date": "2024-01-01", "weight": 75.0},
        {"date": "2024-01-08", "weight": 75.1},
        {"date": "2024-01-15", "weight": 74.9},
        {"date": "2024-01-22", "weight": 75.0},
    ]

    days_data = {
        "2024-01-01": {"energy": 2000.0, "energy_goal": 2000.0},  # 0 balanced
        "2024-01-08": {"energy": 2050.0, "energy_goal": 2000.0},  # +50 small surplus
        "2024-01-15": {"energy": 1950.0, "energy_goal": 2000.0},  # -50 small deficit
        "2024-01-22": {"energy": 2000.0, "energy_goal": 2000.0},  # 0 balanced
    }

    result = calculate_weight_calorie_correlation(weight_data, days_data)

    assert result["trend_description"] == "weight stable with balanced calories"
    # (0 + 50 + -50 + 0) / 4 = 0
    assert result["avg_deficit_surplus"] == pytest.approx(0.0, abs=0.1)


def test_calculate_weight_calorie_correlation_filters_null_values():
    """Test correlation filters out null weight values."""
    weight_data = [
        {"date": "2024-01-01", "weight": 80.0},
        {"date": "2024-01-08", "weight": None},
        {"date": "2024-01-15", "weight": 79.0},
        {"date": "2024-01-22", "weight": None},
        {"date": "2024-01-29", "weight": 78.0},
    ]

    days_data = {
        "2024-01-01": {"energy": 1600.0, "energy_goal": 2000.0},
        "2024-01-15": {"energy": 1700.0, "energy_goal": 2000.0},
        "2024-01-29": {"energy": 1650.0, "energy_goal": 2000.0},
    }

    result = calculate_weight_calorie_correlation(weight_data, days_data)

    # Should use only valid weight measurements
    assert result["trend_description"] == "weight decreasing with calorie deficit"


def test_calculate_weight_calorie_correlation_handles_missing_goals():
    """Test correlation handles days without energy goals."""
    weight_data = [
        {"date": "2024-01-01", "weight": 80.0},
        {"date": "2024-01-08", "weight": 79.0},
    ]

    days_data = {
        "2024-01-01": {"energy": 1600.0, "energy_goal": 2000.0},
        "2024-01-08": {"energy": 1700.0},  # Missing energy_goal
    }

    result = calculate_weight_calorie_correlation(weight_data, days_data)

    # Should only use the one day with complete data, which is insufficient
    assert result["trend_description"] == "insufficient aligned data"


def test_calculate_exercise_stats_basic():
    """Test exercise stats calculation (Feature #58)."""
    # Create exercise data: 5 sessions, total 1250 calories burned
    # Most frequent activity: Running (3 times)
    exercise_data = {
        "2024-01-15": {
            "training": [
                {"name": "Running", "energy": 350, "distance": 5.0, "duration": 1800},
                {"name": "Cycling", "energy": 250, "distance": 10.0, "duration": 2400},
            ],
            "custom_training": [],
        },
        "2024-01-16": {
            "training": [{"name": "Running", "energy": 300, "distance": 4.5, "duration": 1600}],
            "custom_training": [],
        },
        "2024-01-17": {
            "training": [],
            "custom_training": [{"name": "Running", "energy": 200, "duration": 1200}],
        },
        "2024-01-18": {
            "training": [{"name": "Swimming", "energy": 150, "duration": 1000}],
            "custom_training": [],
        },
    }

    result = calculate_exercise_stats(exercise_data)

    # Verify total sessions = 5
    assert result["total_sessions"] == 5

    # Verify total calories = 350 + 250 + 300 + 200 + 150 = 1250
    assert result["total_calories"] == 1250

    # Verify most frequent activity = 'Running' (appears 3 times)
    assert result["most_frequent"] == "Running"


def test_calculate_exercise_stats_empty_data():
    """Test exercise stats with empty data."""
    result = calculate_exercise_stats({})

    assert result["total_sessions"] == 0
    assert result["total_calories"] == 0
    assert result["most_frequent"] is None


def test_calculate_exercise_stats_no_exercises():
    """Test exercise stats when days have no exercises."""
    exercise_data = {
        "2024-01-15": {"training": [], "custom_training": []},
        "2024-01-16": {"training": [], "custom_training": []},
    }

    result = calculate_exercise_stats(exercise_data)

    assert result["total_sessions"] == 0
    assert result["total_calories"] == 0
    assert result["most_frequent"] is None


def test_calculate_exercise_stats_single_activity():
    """Test exercise stats with single activity type."""
    exercise_data = {
        "2024-01-15": {
            "training": [{"name": "Walking", "energy": 100}],
            "custom_training": [],
        },
        "2024-01-16": {
            "training": [{"name": "Walking", "energy": 120}],
            "custom_training": [],
        },
    }

    result = calculate_exercise_stats(exercise_data)

    assert result["total_sessions"] == 2
    assert result["total_calories"] == 220
    assert result["most_frequent"] == "Walking"


def test_calculate_exercise_stats_tie_in_frequency():
    """Test exercise stats when multiple activities have same frequency (first alphabetically wins)."""
    exercise_data = {
        "2024-01-15": {
            "training": [
                {"name": "Running", "energy": 300},
                {"name": "Cycling", "energy": 250},
            ],
            "custom_training": [],
        }
    }

    result = calculate_exercise_stats(exercise_data)

    assert result["total_sessions"] == 2
    assert result["total_calories"] == 550
    # Both have frequency 1, max() will pick one (implementation defined)
    assert result["most_frequent"] in ["Running", "Cycling"]


def test_calculate_exercise_stats_missing_energy():
    """Test exercise stats handles sessions with missing energy values."""
    exercise_data = {
        "2024-01-15": {
            "training": [
                {"name": "Running", "energy": 300},
                {"name": "Yoga", "energy": None},  # No energy tracking
            ],
            "custom_training": [],
        }
    }

    result = calculate_exercise_stats(exercise_data)

    assert result["total_sessions"] == 2
    assert result["total_calories"] == 300  # Only counts the Running session
    # Both activities have frequency 1
    assert result["most_frequent"] in ["Running", "Yoga"]


def test_rank_products_by_frequency_basic():
    """Test product ranking by frequency (Feature #56)."""
    # Create consumed items data with repeated products
    consumed_data = {
        "2024-01-01": {
            "consumed": {
                "products": [
                    {"product_id": "A"},
                    {"product_id": "B"},
                    {"product_id": "A"},
                ]
            }
        },
        "2024-01-02": {
            "consumed": {
                "products": [
                    {"product_id": "A"},
                    {"product_id": "C"},
                    {"product_id": "B"},
                ]
            }
        },
        "2024-01-03": {"consumed": {"products": [{"product_id": "A"}, {"product_id": "A"}]}},
    }

    products_data = {
        "A": {"name": "Product A"},
        "B": {"name": "Product B"},
        "C": {"name": "Product C"},
    }

    result = rank_products_by_frequency(consumed_data, products_data)

    # Product A appears 5 times, B 2 times, C 1 time
    assert len(result) == 3
    assert result[0]["product_id"] == "A"
    assert result[0]["product_name"] == "Product A"
    assert result[0]["count"] == 5

    assert result[1]["product_id"] == "B"
    assert result[1]["product_name"] == "Product B"
    assert result[1]["count"] == 2

    assert result[2]["product_id"] == "C"
    assert result[2]["product_name"] == "Product C"
    assert result[2]["count"] == 1


def test_rank_products_by_frequency_feature_spec():
    """Test product ranking matches feature spec exactly (Feature #56)."""
    # Product A appears 15 times, Product B 10 times, Product C 8 times
    consumed_data = {}

    # Add Product A 15 times across multiple days
    for i in range(15):
        date = f"2024-01-{i + 1:02d}"
        consumed_data[date] = {"consumed": {"products": [{"product_id": "A"}]}}

    # Add Product B 10 times (days 16-25)
    for i in range(10):
        date = f"2024-01-{i + 16:02d}"
        if date not in consumed_data:
            consumed_data[date] = {"consumed": {"products": []}}
        consumed_data[date]["consumed"]["products"].append({"product_id": "B"})

    # Add Product C 8 times (days 26-31, plus 2 more on day 1 and 2)
    consumed_data["2024-01-01"]["consumed"]["products"].extend([{"product_id": "C"}, {"product_id": "C"}])
    for i in range(6):
        date = f"2024-01-{i + 26:02d}"
        if date not in consumed_data:
            consumed_data[date] = {"consumed": {"products": []}}
        consumed_data[date]["consumed"]["products"].append({"product_id": "C"})

    products_data = {
        "A": {"name": "Product A"},
        "B": {"name": "Product B"},
        "C": {"name": "Product C"},
    }

    result = rank_products_by_frequency(consumed_data, products_data)

    # Verify top 3 are A (15), B (10), C (8)
    assert len(result) >= 3
    assert result[0]["product_id"] == "A"
    assert result[0]["count"] == 15
    assert result[1]["product_id"] == "B"
    assert result[1]["count"] == 10
    assert result[2]["product_id"] == "C"
    assert result[2]["count"] == 8

    # Verify sorting is descending
    for i in range(len(result) - 1):
        assert result[i]["count"] >= result[i + 1]["count"]


def test_rank_products_by_frequency_empty_data():
    """Test ranking with empty data."""
    result = rank_products_by_frequency({}, {})
    assert result == []


def test_rank_products_by_frequency_includes_recipes():
    """Test ranking includes recipe portions."""
    consumed_data = {
        "2024-01-01": {
            "consumed": {
                "products": [{"product_id": "P1"}],
                "recipe_portions": [{"recipe_id": "R1"}, {"recipe_id": "R1"}],
            }
        },
        "2024-01-02": {
            "consumed": {
                "products": [{"product_id": "P1"}],
                "recipe_portions": [{"recipe_id": "R1"}],
            }
        },
    }

    products_data = {"P1": {"name": "Product 1"}, "R1": {"name": "Recipe 1"}}

    result = rank_products_by_frequency(consumed_data, products_data)

    # Recipe R1 appears 3 times, Product P1 appears 2 times
    assert len(result) == 2
    assert result[0]["product_id"] == "R1"
    assert result[0]["count"] == 3
    assert result[1]["product_id"] == "P1"
    assert result[1]["count"] == 2


def test_rank_products_by_frequency_missing_product_names():
    """Test ranking handles missing product names."""
    consumed_data = {"2024-01-01": {"consumed": {"products": [{"product_id": "P1"}, {"product_id": "P2"}]}}}

    products_data = {
        "P1": {"name": "Known Product"}
        # P2 is missing
    }

    result = rank_products_by_frequency(consumed_data, products_data)

    assert len(result) == 2
    # P1 has a known name
    p1_entry = [r for r in result if r["product_id"] == "P1"][0]
    assert p1_entry["product_name"] == "Known Product"

    # P2 should have "Unknown" as name
    p2_entry = [r for r in result if r["product_id"] == "P2"][0]
    assert p2_entry["product_name"] == "Unknown"


def test_rank_products_by_frequency_sorts_descending():
    """Test ranking is sorted in descending order."""
    consumed_data = {
        "2024-01-01": {
            "consumed": {
                "products": [
                    {"product_id": "Low"},
                    {"product_id": "High"},
                    {"product_id": "High"},
                    {"product_id": "High"},
                    {"product_id": "Medium"},
                    {"product_id": "Medium"},
                ]
            }
        }
    }

    products_data = {
        "Low": {"name": "Low Frequency"},
        "Medium": {"name": "Medium Frequency"},
        "High": {"name": "High Frequency"},
    }

    result = rank_products_by_frequency(consumed_data, products_data)

    # Verify descending order
    assert result[0]["product_id"] == "High"
    assert result[0]["count"] == 3
    assert result[1]["product_id"] == "Medium"
    assert result[1]["count"] == 2
    assert result[2]["product_id"] == "Low"
    assert result[2]["count"] == 1
