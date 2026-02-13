"""
Analytics engine: statistics and summary calculations.
"""

from datetime import datetime
from typing import Any


def calculate_calorie_stats(days_data: dict[str, Any]) -> dict[str, float]:
    """
    Calculate calorie statistics.

    Args:
        days_data: Days export data (dict mapping dates to day data with 'energy' key)

    Returns:
        Dict with avg, min, max calories
    """
    if not days_data:
        return {"avg": 0.0, "min": 0.0, "max": 0.0}

    # Extract energy values from all days
    energy_values = []
    for day_data in days_data.values():
        if isinstance(day_data, dict) and "energy" in day_data:
            energy = day_data["energy"]
            if energy is not None:
                energy_values.append(float(energy))

    if not energy_values:
        return {"avg": 0.0, "min": 0.0, "max": 0.0}

    return {
        "avg": sum(energy_values) / len(energy_values),
        "min": min(energy_values),
        "max": max(energy_values),
    }


def calculate_macro_ratios(days_data: dict[str, Any]) -> dict[str, float]:
    """
    Calculate macro ratios as percentages.

    Args:
        days_data: Days export data (dict mapping dates to day data with macro keys)

    Returns:
        Dict with carb_pct, protein_pct, fat_pct (percentages of total calories)
    """
    if not days_data:
        return {"carb_pct": 0.0, "protein_pct": 0.0, "fat_pct": 0.0}

    # Extract macro values and calculate total calories
    total_carb = 0.0
    total_protein = 0.0
    total_fat = 0.0

    for day_data in days_data.values():
        if isinstance(day_data, dict):
            if "carb" in day_data and day_data["carb"] is not None:
                total_carb += float(day_data["carb"])
            if "protein" in day_data and day_data["protein"] is not None:
                total_protein += float(day_data["protein"])
            if "fat" in day_data and day_data["fat"] is not None:
                total_fat += float(day_data["fat"])

    # Convert grams to calories (carb=4 cal/g, protein=4 cal/g, fat=9 cal/g)
    carb_cal = total_carb * 4.0
    protein_cal = total_protein * 4.0
    fat_cal = total_fat * 9.0

    total_cal = carb_cal + protein_cal + fat_cal

    if total_cal == 0.0:
        return {"carb_pct": 0.0, "protein_pct": 0.0, "fat_pct": 0.0}

    # Calculate percentages
    return {
        "carb_pct": (carb_cal / total_cal) * 100.0,
        "protein_pct": (protein_cal / total_cal) * 100.0,
        "fat_pct": (fat_cal / total_cal) * 100.0,
    }


def calculate_meal_distribution(summary_data: dict[str, Any]) -> dict[str, float]:
    """
    Calculate per-meal calorie distribution (average calories per meal across all days).

    Args:
        summary_data: Daily summary data (dict mapping dates to DailySummary or dict with 'meals' key)

    Returns:
        Dict with avg calories per meal (breakfast, lunch, dinner, snack)
    """
    if not summary_data:
        return {"breakfast": 0.0, "lunch": 0.0, "dinner": 0.0, "snack": 0.0}

    # Accumulate calories per meal across all days
    meal_totals = {"breakfast": 0.0, "lunch": 0.0, "dinner": 0.0, "snack": 0.0}
    meal_counts = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}

    for day_data in summary_data.values():
        # Handle both DailySummary objects and plain dicts
        meals = None
        if hasattr(day_data, "meals"):
            meals = day_data.meals
        elif isinstance(day_data, dict) and "meals" in day_data:
            meals = day_data["meals"]

        if meals:
            for meal_name in ["breakfast", "lunch", "dinner", "snack"]:
                if meal_name in meals:
                    meal_info = meals[meal_name]
                    # Extract energy from nutrients dict
                    if isinstance(meal_info, dict) and "nutrients" in meal_info:
                        nutrients = meal_info["nutrients"]
                        if "energy.energy" in nutrients and nutrients["energy.energy"] is not None:
                            energy = float(nutrients["energy.energy"])
                            meal_totals[meal_name] += energy
                            meal_counts[meal_name] += 1

    # Calculate averages
    result = {}
    for meal_name in ["breakfast", "lunch", "dinner", "snack"]:
        if meal_counts[meal_name] > 0:
            result[meal_name] = meal_totals[meal_name] / meal_counts[meal_name]
        else:
            result[meal_name] = 0.0

    return result


def calculate_water_stats(water_data: list[float], goal: float) -> dict[str, float]:
    """
    Calculate water intake statistics.

    Args:
        water_data: List of daily water intake values in ml
        goal: Daily water intake goal in ml

    Returns:
        Dict with avg_intake, days_meeting_goal, percentage
    """
    if not water_data:
        return {"avg_intake": 0.0, "days_meeting_goal": 0, "percentage": 0.0}

    avg_intake = sum(water_data) / len(water_data)
    days_meeting_goal = sum(1 for intake in water_data if intake >= goal)
    percentage = (days_meeting_goal / len(water_data)) * 100.0

    return {
        "avg_intake": avg_intake,
        "days_meeting_goal": days_meeting_goal,
        "percentage": percentage,
    }


def calculate_weight_trend(weight_data: list[dict[str, Any]]) -> dict[str, float]:
    """
    Calculate weight trend statistics.

    Args:
        weight_data: List of weight measurements, each dict with 'date' and 'weight' keys
                    Dates should be in YYYY-MM-DD format, sorted chronologically

    Returns:
        Dict with starting_weight, current_weight, total_change, weekly_avg_change
    """
    if not weight_data:
        return {
            "starting_weight": 0.0,
            "current_weight": 0.0,
            "total_change": 0.0,
            "weekly_avg_change": 0.0,
        }

    # Filter out measurements without weight values
    valid_measurements = [m for m in weight_data if m.get("weight") is not None]

    if not valid_measurements:
        return {
            "starting_weight": 0.0,
            "current_weight": 0.0,
            "total_change": 0.0,
            "weekly_avg_change": 0.0,
        }

    # Get starting and current weights
    starting_weight = float(valid_measurements[0]["weight"])
    current_weight = float(valid_measurements[-1]["weight"])
    total_change = current_weight - starting_weight

    # Calculate time span in weeks
    start_date = datetime.strptime(valid_measurements[0]["date"], "%Y-%m-%d")
    end_date = datetime.strptime(valid_measurements[-1]["date"], "%Y-%m-%d")
    days_diff = (end_date - start_date).days
    weeks = days_diff / 7.0

    weekly_avg_change = total_change / weeks if weeks > 0 else 0.0

    return {
        "starting_weight": starting_weight,
        "current_weight": current_weight,
        "total_change": total_change,
        "weekly_avg_change": weekly_avg_change,
    }


def calculate_weight_calorie_correlation(
    weight_data: list[dict[str, Any]], days_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Calculate correlation between weight changes and calorie intake.

    Args:
        weight_data: List of weight measurements with 'date' and 'weight' keys
        days_data: Dict mapping dates to day data with 'energy' and 'energy_goal' keys

    Returns:
        Dict with correlation, trend_description, avg_deficit_surplus
    """
    if not weight_data or not days_data:
        return {
            "correlation": 0.0,
            "trend_description": "insufficient data",
            "avg_deficit_surplus": 0.0,
        }

    # Filter valid weight measurements
    valid_weights = [m for m in weight_data if m.get("weight") is not None]

    if len(valid_weights) < 2:
        return {
            "correlation": 0.0,
            "trend_description": "insufficient data",
            "avg_deficit_surplus": 0.0,
        }

    # Build aligned data: dates with both weight and calorie data
    aligned_data = []
    for weight_entry in valid_weights:
        date = weight_entry["date"]
        if date in days_data:
            day_data = days_data[date]
            energy = day_data.get("energy")
            energy_goal = day_data.get("energy_goal")

            if energy is not None and energy_goal is not None:
                aligned_data.append(
                    {
                        "date": date,
                        "weight": float(weight_entry["weight"]),
                        "energy": float(energy),
                        "energy_goal": float(energy_goal),
                        "deficit_surplus": float(energy) - float(energy_goal),
                    }
                )

    if len(aligned_data) < 2:
        return {
            "correlation": 0.0,
            "trend_description": "insufficient aligned data",
            "avg_deficit_surplus": 0.0,
        }

    # Sort by date
    aligned_data.sort(key=lambda x: x["date"])

    # Calculate weight changes (differences between consecutive measurements)
    weight_changes = []
    for i in range(1, len(aligned_data)):
        weight_change = aligned_data[i]["weight"] - aligned_data[i - 1]["weight"]
        weight_changes.append(weight_change)

    # Get deficit/surplus values (skip first since we're comparing changes)
    deficits = [aligned_data[i]["deficit_surplus"] for i in range(1, len(aligned_data))]

    # Calculate average deficit/surplus
    avg_deficit_surplus = sum(d["deficit_surplus"] for d in aligned_data) / len(aligned_data)

    # Calculate correlation coefficient using Pearson correlation
    if len(weight_changes) < 2:
        correlation = 0.0
    else:
        # Calculate means
        mean_weight_change = sum(weight_changes) / len(weight_changes)
        mean_deficit = sum(deficits) / len(deficits)

        # Calculate correlation
        numerator = sum(
            (weight_changes[i] - mean_weight_change) * (deficits[i] - mean_deficit) for i in range(len(weight_changes))
        )

        sum_sq_weight = sum((wc - mean_weight_change) ** 2 for wc in weight_changes)
        sum_sq_deficit = sum((d - mean_deficit) ** 2 for d in deficits)

        denominator = (sum_sq_weight * sum_sq_deficit) ** 0.5

        correlation = 0.0 if denominator == 0 else numerator / denominator

    # Determine trend description
    total_weight_change = aligned_data[-1]["weight"] - aligned_data[0]["weight"]

    if avg_deficit_surplus < -100:  # Calorie deficit
        if total_weight_change < -0.5:
            trend_description = "weight decreasing with calorie deficit"
        elif total_weight_change > 0.5:
            trend_description = "weight increasing despite calorie deficit"
        else:
            trend_description = "weight stable with calorie deficit"
    elif avg_deficit_surplus > 100:  # Calorie surplus
        if total_weight_change > 0.5:
            trend_description = "weight increasing with calorie surplus"
        elif total_weight_change < -0.5:
            trend_description = "weight decreasing despite calorie surplus"
        else:
            trend_description = "weight stable with calorie surplus"
    else:  # Balanced
        if total_weight_change < -0.5:
            trend_description = "weight decreasing with balanced calories"
        elif total_weight_change > 0.5:
            trend_description = "weight increasing with balanced calories"
        else:
            trend_description = "weight stable with balanced calories"

    return {
        "correlation": correlation,
        "trend_description": trend_description,
        "avg_deficit_surplus": avg_deficit_surplus,
    }


def calculate_exercise_stats(exercise_data: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate exercise statistics.

    Args:
        exercise_data: Dict mapping dates to exercise data with 'training' and 'custom_training' lists

    Returns:
        Dict with total_sessions, total_calories, most_frequent activity
    """
    if not exercise_data:
        return {"total_sessions": 0, "total_calories": 0, "most_frequent": None}

    # Collect all exercise sessions
    all_sessions = []
    activity_counts = {}

    for _date, day_exercises in exercise_data.items():
        # Handle both Exercises objects and plain dicts
        training = []
        custom_training = []

        if hasattr(day_exercises, "training"):
            training = day_exercises.training or []
        elif isinstance(day_exercises, dict) and "training" in day_exercises:
            training = day_exercises["training"] or []

        if hasattr(day_exercises, "custom_training"):
            custom_training = day_exercises.custom_training or []
        elif isinstance(day_exercises, dict) and "custom_training" in day_exercises:
            custom_training = day_exercises["custom_training"] or []

        # Process training sessions
        for session in training:
            all_sessions.append(session)
            activity_name = session.get("name")
            if activity_name:
                activity_counts[activity_name] = activity_counts.get(activity_name, 0) + 1

        # Process custom training sessions
        for session in custom_training:
            all_sessions.append(session)
            activity_name = session.get("name")
            if activity_name:
                activity_counts[activity_name] = activity_counts.get(activity_name, 0) + 1

    # Calculate total sessions
    total_sessions = len(all_sessions)

    # Calculate total calories burned
    total_calories = 0
    for session in all_sessions:
        energy = session.get("energy")
        if energy is not None:
            total_calories += int(energy)

    # Find most frequent activity
    most_frequent = None
    if activity_counts:
        most_frequent = max(activity_counts.items(), key=lambda x: x[1])[0]

    return {
        "total_sessions": total_sessions,
        "total_calories": total_calories,
        "most_frequent": most_frequent,
    }


def rank_products_by_frequency(consumed_data: dict[str, Any], products_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Rank products by consumption frequency.

    Args:
        consumed_data: Dict mapping dates to consumed items with 'products' and 'recipe_portions'
        products_data: Dict mapping product IDs to product details with 'name'

    Returns:
        List of dicts with product_id, product_name, count (sorted by count descending)
    """
    if not consumed_data:
        return []

    # Count product occurrences
    product_counts: dict[str, int] = {}

    for _date, day_data in consumed_data.items():
        if not isinstance(day_data, dict):
            continue

        # Get consumed items from the day
        consumed = day_data.get("consumed", {})
        if not isinstance(consumed, dict):
            continue

        # Count products
        products = consumed.get("products", [])
        if isinstance(products, list):
            for product in products:
                if isinstance(product, dict):
                    product_id = product.get("product_id")
                    if product_id:
                        product_counts[product_id] = product_counts.get(product_id, 0) + 1

        # Count recipe portions (recipes are also products)
        recipe_portions = consumed.get("recipe_portions", [])
        if isinstance(recipe_portions, list):
            for recipe in recipe_portions:
                if isinstance(recipe, dict):
                    recipe_id = recipe.get("recipe_id")
                    if recipe_id:
                        # Recipes are counted separately (could be treated as products too)
                        product_counts[recipe_id] = product_counts.get(recipe_id, 0) + 1

    # Build ranking list with product names
    ranking = []
    for product_id, count in product_counts.items():
        # Get product name from products_data
        product_name = "Unknown"
        if products_data and product_id in products_data:
            product_info = products_data[product_id]
            if isinstance(product_info, dict):
                product_name = product_info.get("name", "Unknown")

        ranking.append({"product_id": product_id, "product_name": product_name, "count": count})

    # Sort by count descending
    ranking.sort(key=lambda x: x["count"], reverse=True)

    return ranking
