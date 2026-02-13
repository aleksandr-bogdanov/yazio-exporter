"""
Tests for data models.
"""

from yazio_exporter.models import (
    ConsumedItems,
    DailyNutrients,
    DailySummary,
    Exercises,
    Goals,
    WaterIntake,
)


def test_parse_nutrients_daily_response():
    """Feature #10: Parse nutrients-daily response into data model."""
    # Sample response from API spec - single day entry
    response_data = {
        "date": "2024-01-15",
        "energy": 1636.31,
        "carb": 51.79,
        "protein": 129.66,
        "fat": 96.11,
        "energy_goal": 2000.0,
    }

    # Parse into DailyNutrients dataclass
    nutrients = DailyNutrients(**response_data)

    # Verify date is a string
    assert isinstance(nutrients.date, str)
    assert nutrients.date == "2024-01-15"

    # Verify all nutrient fields are floats
    assert isinstance(nutrients.energy, float)
    assert nutrients.energy == 1636.31

    assert isinstance(nutrients.carb, float)
    assert nutrients.carb == 51.79

    assert isinstance(nutrients.protein, float)
    assert nutrients.protein == 129.66

    assert isinstance(nutrients.fat, float)
    assert nutrients.fat == 96.11

    # Verify energy_goal is optional and can be a float
    assert isinstance(nutrients.energy_goal, float)
    assert nutrients.energy_goal == 2000.0

    # Test with missing optional field
    response_without_goal = {
        "date": "2024-01-16",
        "energy": 1800.50,
        "carb": 60.00,
        "protein": 140.00,
        "fat": 90.00,
    }

    nutrients_no_goal = DailyNutrients(**response_without_goal)
    assert nutrients_no_goal.date == "2024-01-16"
    assert nutrients_no_goal.energy == 1800.50
    assert nutrients_no_goal.carb == 60.00
    assert nutrients_no_goal.protein == 140.00
    assert nutrients_no_goal.fat == 90.00
    assert nutrients_no_goal.energy_goal is None


def test_parse_consumed_items_with_products_and_recipes():
    """Feature #11: Parse consumed-items response with products and recipes."""
    # Sample response from API spec
    response_data = {
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
            },
            {
                "id": "recipe-uuid-2",
                "date": "2024-01-15 19:30:00",
                "daytime": "dinner",
                "type": "recipe_portion",
                "recipe_id": "recipe-uuid-2",
                "portion_count": 1,
            },
        ],
        "simple_products": [],
    }

    # Parse into ConsumedItems dataclass
    consumed = ConsumedItems(**response_data)

    # Verify products list is populated
    assert len(consumed.products) == 2
    assert consumed.products[0]["id"] == "prod-uuid-1"
    assert consumed.products[0]["date"] == "2024-01-15 13:29:04"
    assert consumed.products[0]["daytime"] == "lunch"
    assert consumed.products[0]["product_id"] == "product-uuid-1"
    assert consumed.products[0]["amount"] == 50
    assert consumed.products[0]["serving"] == "gram"

    assert consumed.products[1]["id"] == "prod-uuid-2"
    assert consumed.products[1]["daytime"] == "breakfast"
    assert consumed.products[1]["product_id"] == "product-uuid-2"

    # Verify recipe_portions list is populated
    assert len(consumed.recipe_portions) == 2
    assert consumed.recipe_portions[0]["id"] == "recipe-uuid-1"
    assert consumed.recipe_portions[0]["date"] == "2024-01-15 12:18:57"
    assert consumed.recipe_portions[0]["daytime"] == "lunch"
    assert consumed.recipe_portions[0]["recipe_id"] == "recipe-uuid-1"
    assert consumed.recipe_portions[0]["portion_count"] == 4

    assert consumed.recipe_portions[1]["id"] == "recipe-uuid-2"
    assert consumed.recipe_portions[1]["daytime"] == "dinner"
    assert consumed.recipe_portions[1]["recipe_id"] == "recipe-uuid-2"
    assert consumed.recipe_portions[1]["portion_count"] == 1

    # Verify simple_products is also available
    assert len(consumed.simple_products) == 0


def test_parse_goals_response():
    """Feature #12: Parse goals response into data model."""
    # Sample response from API spec
    response_data = {
        "energy.energy": 2000,
        "nutrient.protein": 156.1,
        "nutrient.fat": 113.98,
        "nutrient.carb": 73.17,
        "activity.step": 10000,
        "bodyvalue.weight": 61,
        "water": 2000,
    }

    # Parse into Goals dataclass
    goals = Goals(data=response_data)

    # Verify energy goal is extracted
    assert goals.data["energy.energy"] == 2000

    # Verify macro goals are extracted
    assert goals.data["nutrient.protein"] == 156.1
    assert goals.data["nutrient.fat"] == 113.98
    assert goals.data["nutrient.carb"] == 73.17

    # Verify step goal is extracted
    assert goals.data["activity.step"] == 10000

    # Verify additional goals are preserved
    assert goals.data["bodyvalue.weight"] == 61
    assert goals.data["water"] == 2000


def test_parse_exercises_response():
    """Feature #13: Parse exercises response into data model."""
    # Sample response from API spec
    response_data = {
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

    # Parse into Exercises dataclass
    exercises = Exercises(**response_data)

    # Verify training list is populated
    assert len(exercises.training) == 2

    # Verify first exercise has all required fields
    assert exercises.training[0]["name"] == "Running"
    assert exercises.training[0]["energy"] == 350
    assert exercises.training[0]["distance"] == 5.0
    assert exercises.training[0]["duration"] == 1800
    assert exercises.training[0]["steps"] == 6000
    assert exercises.training[0]["id"] == "uuid-training-1"
    assert exercises.training[0]["date"] == "2024-01-15"

    # Verify second exercise
    assert exercises.training[1]["name"] == "Cycling"
    assert exercises.training[1]["energy"] == 280
    assert exercises.training[1]["distance"] == 10.0
    assert exercises.training[1]["duration"] == 2400
    assert exercises.training[1]["steps"] == 0

    # Verify custom_training is available
    assert len(exercises.custom_training) == 0

    # Verify activity object is parsed
    assert exercises.activity is not None
    assert exercises.activity["energy"] == 250
    assert exercises.activity["distance"] == 3.0
    assert exercises.activity["duration"] == 3600
    assert exercises.activity["steps"] == 8500
    assert exercises.activity["source"] == "apple_health"


def test_parse_water_intake_response():
    """Feature #14: Parse water-intake response into data model."""
    # Sample response from API spec
    response_data = {"water_intake": 2000, "gateway": None, "source": None}

    # Parse into WaterIntake dataclass
    water = WaterIntake(**response_data)

    # Verify water_intake is an integer
    assert isinstance(water.water_intake, int)
    assert water.water_intake == 2000

    # Verify optional fields handle None
    assert water.gateway is None
    assert water.source is None

    # Test with values for optional fields
    response_with_source = {
        "water_intake": 2500,
        "gateway": "apple_health",
        "source": "healthkit",
    }

    water_with_source = WaterIntake(**response_with_source)
    assert water_with_source.water_intake == 2500
    assert water_with_source.gateway == "apple_health"
    assert water_with_source.source == "healthkit"


def test_parse_daily_summary_response():
    """Feature #15: Parse daily-summary response with meal breakdowns."""
    # Sample response from API spec - comprehensive daily summary
    response_data = {
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

    # Parse into DailySummary dataclass
    summary = DailySummary(
        meals=response_data["meals"],
        activity_energy=response_data["activity_energy"],
        steps=response_data["steps"],
        water_intake=response_data["water_intake"],
        goals=response_data["goals"],
        units=response_data["units"],
    )

    # Verify meals dictionary is populated
    assert len(summary.meals) == 4
    assert "breakfast" in summary.meals
    assert "lunch" in summary.meals
    assert "dinner" in summary.meals
    assert "snack" in summary.meals

    # Verify each meal has energy_goal and nutrients
    assert summary.meals["breakfast"]["energy_goal"] == 500
    assert "nutrients" in summary.meals["breakfast"]
    assert summary.meals["breakfast"]["nutrients"]["energy.energy"] == 450
    assert summary.meals["breakfast"]["nutrients"]["nutrient.carb"] == 60
    assert summary.meals["breakfast"]["nutrients"]["nutrient.protein"] == 25
    assert summary.meals["breakfast"]["nutrients"]["nutrient.fat"] == 15

    assert summary.meals["lunch"]["energy_goal"] == 700
    assert summary.meals["lunch"]["nutrients"]["energy.energy"] == 680
    assert summary.meals["lunch"]["nutrients"]["nutrient.carb"] == 85

    assert summary.meals["dinner"]["energy_goal"] == 600
    assert summary.meals["dinner"]["nutrients"]["energy.energy"] == 520

    assert summary.meals["snack"]["energy_goal"] == 200
    assert summary.meals["snack"]["nutrients"]["energy.energy"] == 180

    # Verify activity_energy, steps, water_intake are extracted
    assert summary.activity_energy == 250
    assert summary.steps == 8500
    assert summary.water_intake == 2000

    # Verify goals object is parsed
    assert len(summary.goals) == 6
    assert summary.goals["energy.energy"] == 2000
    assert summary.goals["nutrient.protein"] == 156
    assert summary.goals["nutrient.carb"] == 250
    assert summary.goals["nutrient.fat"] == 67
    assert summary.goals["activity.step"] == 10000
    assert summary.goals["water"] == 2000

    # Verify units object is parsed
    assert len(summary.units) == 4
    assert summary.units["unit_mass"] == "kg"
    assert summary.units["unit_energy"] == "kcal"
    assert summary.units["unit_serving"] == "metric"
    assert summary.units["unit_length"] == "cm"


def test_placeholder():
    """Placeholder test for models."""
    pass
