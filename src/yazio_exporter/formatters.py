"""
Output formatters: JSON, CSV, SQLite.
"""

import csv
import json
import sqlite3
from typing import Any


def to_json(data: dict[str, Any], output_file: str) -> None:
    """
    Export data to JSON format.

    Args:
        data: Data to export
        output_file: Output file path
    """
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def to_csv_days(data: dict[str, Any], output_file: str) -> None:
    """
    Export days data to CSV format.

    Creates a CSV with columns: date, energy, carb, protein, fat, energy_goal, water_intake, steps

    Args:
        data: Days data (dict mapping dates to day data dicts)
        output_file: Output file path (e.g., 'days.csv')
    """
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(
            [
                "date",
                "energy",
                "carb",
                "protein",
                "fat",
                "energy_goal",
                "water_intake",
                "steps",
            ]
        )

        # Sort dates chronologically for consistent output
        sorted_dates = sorted(data.keys())

        # Write data rows
        for date in sorted_dates:
            day_data = data[date]
            writer.writerow(
                [
                    date,
                    day_data.get("energy", ""),
                    day_data.get("carb", ""),
                    day_data.get("protein", ""),
                    day_data.get("fat", ""),
                    day_data.get("energy_goal", ""),
                    day_data.get("water_intake", ""),
                    day_data.get("steps", ""),
                ]
            )


def to_csv_nutrients(data: dict[str, dict[str, float]], output_file: str) -> None:
    """
    Export nutrients data to CSV format in long format.

    Creates a CSV with columns: date, nutrient_id, value
    One row per nutrient-date combination.

    Args:
        data: Nutrient data (dict mapping nutrient_id to dict of date->value)
        output_file: Output file path (e.g., 'nutrients.csv')
    """
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(["date", "nutrient_id", "value"])

        # Collect all rows for sorting
        rows = []
        for nutrient_id, date_values in data.items():
            for date, value in date_values.items():
                rows.append((date, nutrient_id, value))

        # Sort by date first, then nutrient_id for consistent output
        rows.sort(key=lambda x: (x[0], x[1]))

        # Write data rows
        for date, nutrient_id, value in rows:
            writer.writerow([date, nutrient_id, value])


def _scale_nutrients(nutrients, scale_factor):
    """Scale nutrient values by a factor. Returns (energy, carb, protein, fat)."""
    energy = nutrients.get("energy.energy", 0) * scale_factor if "energy.energy" in nutrients else ""
    carb = nutrients.get("nutrient.carb", 0) * scale_factor if "nutrient.carb" in nutrients else ""
    protein = nutrients.get("nutrient.protein", 0) * scale_factor if "nutrient.protein" in nutrients else ""
    fat = nutrients.get("nutrient.fat", 0) * scale_factor if "nutrient.fat" in nutrients else ""
    return energy, carb, protein, fat


def to_csv_consumed(days_data: dict[str, Any], products_data: dict[str, Any], output_file: str) -> None:
    """
    Export consumed items to CSV format with flattened items.

    Creates a CSV with columns: date, daytime, product_id, product_name, amount, serving, energy, carb, protein, fat
    Each consumed item becomes one row.

    Args:
        days_data: Days data (dict mapping dates to day data with 'consumed' key)
        products_data: Products lookup (dict with 'products' and 'recipes' keys)
        output_file: Output file path (e.g., 'consumed.csv')
    """
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(
            [
                "date",
                "daytime",
                "product_id",
                "product_name",
                "amount",
                "serving",
                "energy",
                "carb",
                "protein",
                "fat",
            ]
        )

        # Collect all rows for sorting
        rows = []

        # Iterate through all days
        for date, day_data in days_data.items():
            if not isinstance(day_data, dict) or "consumed" not in day_data:
                continue

            consumed = day_data["consumed"]
            if not isinstance(consumed, dict):
                continue

            # Process products
            products_list = consumed.get("products", [])

            for item in products_list:
                product_id = item.get("product_id", "")

                # Lookup product details for name and nutrients
                product_name = ""
                energy = ""
                carb = ""
                protein = ""
                fat = ""

                if products_data and "products" in products_data:
                    product_details = products_data["products"].get(product_id, {})
                    if isinstance(product_details, dict):
                        product_name = product_details.get("name", "")

                        amount = item.get("amount", 0)
                        if "nutrients" in product_details and amount:
                            energy, carb, protein, fat = _scale_nutrients(product_details["nutrients"], amount / 100.0)

                rows.append(
                    [
                        date,
                        item.get("daytime", ""),
                        product_id,
                        product_name,
                        item.get("amount", ""),
                        item.get("serving", ""),
                        energy,
                        carb,
                        protein,
                        fat,
                    ]
                )

            # Process recipe_portions
            recipes_list = consumed.get("recipe_portions", [])

            for item in recipes_list:
                recipe_id = item.get("recipe_id", "")

                # Lookup recipe details
                recipe_name = ""
                energy = ""
                carb = ""
                protein = ""
                fat = ""

                if products_data and "recipes" in products_data:
                    recipe_details = products_data["recipes"].get(recipe_id, {})
                    if isinstance(recipe_details, dict):
                        recipe_name = recipe_details.get("name", "")

                        portion_count = item.get("portion_count", 1)
                        if "nutrients" in recipe_details:
                            energy, carb, protein, fat = _scale_nutrients(recipe_details["nutrients"], portion_count)

                rows.append(
                    [
                        date,
                        item.get("daytime", ""),
                        recipe_id,
                        recipe_name,
                        item.get("portion_count", ""),
                        "portion",
                        energy,
                        carb,
                        protein,
                        fat,
                    ]
                )

        # Sort by date first, then daytime
        rows.sort(key=lambda x: (x[0], x[1]))

        # Write data rows
        for row in rows:
            writer.writerow(row)


def to_csv_products(data: list[dict[str, Any]], output_file: str) -> None:
    """
    Export products data to CSV format.

    Creates a CSV with columns: product_id, name, category, energy_per_100g,
    carb_per_100g, protein_per_100g, fat_per_100g

    Nutrients are normalized to per-100g values.

    Args:
        data: List of product dictionaries
        output_file: Output file path (e.g., 'products.csv')
    """
    if not data:
        # Create empty CSV with headers
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "product_id",
                    "name",
                    "category",
                    "energy_per_100g",
                    "carb_per_100g",
                    "protein_per_100g",
                    "fat_per_100g",
                ]
            )
        return

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(
            [
                "product_id",
                "name",
                "category",
                "energy_per_100g",
                "carb_per_100g",
                "protein_per_100g",
                "fat_per_100g",
            ]
        )

        # Write data rows
        for product in data:
            writer.writerow(
                [
                    product.get("product_id", ""),
                    product.get("name", ""),
                    product.get("category", ""),
                    product.get("energy_per_100g", ""),
                    product.get("carb_per_100g", ""),
                    product.get("protein_per_100g", ""),
                    product.get("fat_per_100g", ""),
                ]
            )


def to_csv_weight(data: list[dict[str, Any]], output_file: str) -> None:
    """
    Export weight/body measurements data to CSV format.

    Creates a CSV with columns: date, weight, body_fat, waist
    Null values are represented as empty strings.

    Args:
        data: List of measurement dictionaries with date and optional measurement fields
        output_file: Output file path (e.g., 'weight.csv')
    """
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(["date", "weight", "body_fat", "waist"])

        # Sort by date for consistent output
        sorted_data = sorted(data, key=lambda x: x.get("date", ""))

        # Write data rows
        for measurement in sorted_data:
            writer.writerow(
                [
                    measurement.get("date", ""),
                    measurement.get("weight", ""),
                    measurement.get("body_fat", ""),
                    measurement.get("waist", ""),
                ]
            )


def create_sqlite_schema(db_path: str) -> None:
    """
    Create SQLite database schema with proper foreign key constraints.

    Creates tables: users, days, consumed_items, products, recipes, goals,
    exercises, water_intake, weight_log, nutrient_daily, daily_summary

    Args:
        db_path: Database file path
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT,
            start_weight REAL,
            current_weight REAL,
            goal TEXT,
            sex TEXT,
            activity_degree TEXT
        )
    """)

    # Days table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS days (
            date TEXT PRIMARY KEY,
            energy REAL,
            carb REAL,
            protein REAL,
            fat REAL,
            energy_goal REAL
        )
    """)

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            energy_per_100g REAL,
            carb_per_100g REAL,
            protein_per_100g REAL,
            fat_per_100g REAL
        )
    """)

    # Recipes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            recipe_id TEXT PRIMARY KEY,
            name TEXT,
            portion_count INTEGER,
            energy_per_portion REAL,
            carb_per_portion REAL,
            protein_per_portion REAL,
            fat_per_portion REAL
        )
    """)

    # Consumed items table with foreign keys
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consumed_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            product_id TEXT NOT NULL,
            amount REAL,
            energy REAL,
            FOREIGN KEY (date) REFERENCES days(date),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # Goals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            date TEXT PRIMARY KEY,
            energy_goal REAL,
            protein_goal REAL,
            fat_goal REAL,
            carb_goal REAL,
            water_goal REAL,
            steps_goal INTEGER,
            weight_goal REAL
        )
    """)

    # Exercises table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            exercise_type TEXT,
            duration_minutes INTEGER,
            calories_burned REAL
        )
    """)

    # Water intake table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_intake (
            date TEXT PRIMARY KEY,
            water_ml INTEGER
        )
    """)

    # Weight log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weight_log (
            date TEXT PRIMARY KEY,
            weight REAL,
            body_fat REAL,
            waist REAL,
            hip REAL,
            chest REAL
        )
    """)

    # Nutrient daily table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nutrient_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            nutrient_id TEXT NOT NULL,
            value REAL
        )
    """)

    # Daily summary table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_summary (
            date TEXT PRIMARY KEY,
            total_energy REAL,
            total_carb REAL,
            total_protein REAL,
            total_fat REAL,
            breakfast_energy REAL,
            lunch_energy REAL,
            dinner_energy REAL,
            snack_energy REAL
        )
    """)

    # Create indexes only for non-PK columns used in lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_consumed_items_date ON consumed_items(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nutrient_daily_date ON nutrient_daily(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercises_date ON exercises(date)")

    conn.commit()
    conn.close()


def to_sqlite(data: dict[str, Any], db_path: str) -> None:
    """
    Export data to SQLite format.

    Creates schema and inserts data into all tables.

    Args:
        data: Data dictionary with keys like 'days', 'products', 'consumed_items',
              'weight', 'nutrients', 'profile', 'recipes', 'goals', 'exercises',
              'water', 'daily_summary'
        db_path: Database file path
    """
    # Create schema first
    create_sqlite_schema(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Insert user profile
    if "profile" in data and data["profile"]:
        profile = data["profile"]
        cursor.execute(
            """
            INSERT OR REPLACE INTO users (id, email, start_weight, current_weight, goal, sex, activity_degree)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                1,
                profile.get("email"),
                profile.get("start_weight"),
                profile.get("current_weight"),
                profile.get("goal"),
                profile.get("sex"),
                profile.get("activity_degree"),
            ),
        )

    # Insert days
    if "days" in data and data["days"]:
        for day in data["days"]:
            if isinstance(day, dict):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO days (date, energy, carb, protein, fat, energy_goal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        day.get("date"),
                        day.get("energy"),
                        day.get("carb"),
                        day.get("protein"),
                        day.get("fat"),
                        day.get("energy_goal"),
                    ),
                )

    # Insert products
    if "products" in data and data["products"]:
        for product in data["products"]:
            if isinstance(product, dict):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO products
                    (product_id, name, category, energy_per_100g, carb_per_100g, protein_per_100g, fat_per_100g)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        product.get("product_id"),
                        product.get("name"),
                        product.get("category"),
                        product.get("energy_per_100g"),
                        product.get("carb_per_100g"),
                        product.get("protein_per_100g"),
                        product.get("fat_per_100g"),
                    ),
                )

    # Insert recipes
    if "recipes" in data and data["recipes"]:
        for recipe in data["recipes"]:
            if isinstance(recipe, dict):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO recipes
                    (recipe_id, name, portion_count, energy_per_portion,
                     carb_per_portion, protein_per_portion, fat_per_portion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        recipe.get("recipe_id"),
                        recipe.get("name"),
                        recipe.get("portion_count"),
                        recipe.get("energy_per_portion"),
                        recipe.get("carb_per_portion"),
                        recipe.get("protein_per_portion"),
                        recipe.get("fat_per_portion"),
                    ),
                )

    # Insert consumed items
    if "consumed_items" in data and data["consumed_items"]:
        for item in data["consumed_items"]:
            if isinstance(item, dict):
                cursor.execute(
                    """
                    INSERT INTO consumed_items (date, product_id, amount, energy)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        item.get("date"),
                        item.get("product_id"),
                        item.get("amount"),
                        item.get("energy"),
                    ),
                )

    # Insert weight log
    if "weight" in data and data["weight"]:
        for entry in data["weight"]:
            if isinstance(entry, dict):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO weight_log (date, weight, body_fat, waist, hip, chest)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry.get("date"),
                        entry.get("weight"),
                        entry.get("body_fat"),
                        entry.get("waist"),
                        entry.get("hip"),
                        entry.get("chest"),
                    ),
                )

    # Insert nutrients
    if "nutrients" in data and data["nutrients"]:
        for nutrient_id, date_values in data["nutrients"].items():
            if isinstance(date_values, dict):
                for date_str, value in date_values.items():
                    cursor.execute(
                        """
                        INSERT INTO nutrient_daily (date, nutrient_id, value)
                        VALUES (?, ?, ?)
                    """,
                        (date_str, nutrient_id, value),
                    )

    # Insert water intake
    if "water" in data and data["water"]:
        for entry in data["water"]:
            if isinstance(entry, dict):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO water_intake (date, water_ml)
                    VALUES (?, ?)
                """,
                    (entry.get("date"), entry.get("water_ml")),
                )

    # Insert goals
    if "goals" in data and data["goals"]:
        for entry in data["goals"]:
            if isinstance(entry, dict):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO goals
                    (date, energy_goal, protein_goal, fat_goal, carb_goal, water_goal, steps_goal, weight_goal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry.get("date"),
                        entry.get("energy_goal"),
                        entry.get("protein_goal"),
                        entry.get("fat_goal"),
                        entry.get("carb_goal"),
                        entry.get("water_goal"),
                        entry.get("steps_goal"),
                        entry.get("weight_goal"),
                    ),
                )

    # Insert exercises
    if "exercises" in data and data["exercises"]:
        for entry in data["exercises"]:
            if isinstance(entry, dict):
                cursor.execute(
                    """
                    INSERT INTO exercises (date, exercise_type, duration_minutes, calories_burned)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        entry.get("date"),
                        entry.get("exercise_type"),
                        entry.get("duration_minutes"),
                        entry.get("calories_burned"),
                    ),
                )

    conn.commit()
    conn.close()


def to_table(data: dict[str, Any]) -> str:
    """
    Format analytics data as a human-readable table.

    Args:
        data: Analytics data dictionary with various statistics

    Returns:
        Formatted table string with aligned headers and data
    """
    lines = []
    lines.append("=" * 60)
    lines.append("YAZIO EXPORT SUMMARY")
    lines.append("=" * 60)
    lines.append("")

    # Calorie Statistics
    if "calorie_stats" in data:
        stats = data["calorie_stats"]
        lines.append("CALORIE STATISTICS")
        lines.append("-" * 60)
        lines.append(f"  Average Daily Intake:  {stats.get('avg', 0):.1f} kcal")
        lines.append(f"  Minimum Daily Intake:  {stats.get('min', 0):.1f} kcal")
        lines.append(f"  Maximum Daily Intake:  {stats.get('max', 0):.1f} kcal")
        lines.append("")

    # Macro Ratios
    if "macro_ratios" in data:
        ratios = data["macro_ratios"]
        lines.append("MACRONUTRIENT RATIOS")
        lines.append("-" * 60)
        lines.append(f"  Carbohydrates:  {ratios.get('carb_pct', 0):.1f}%")
        lines.append(f"  Protein:        {ratios.get('protein_pct', 0):.1f}%")
        lines.append(f"  Fat:            {ratios.get('fat_pct', 0):.1f}%")
        lines.append("")

    # Meal Distribution
    if "meal_distribution" in data:
        meals = data["meal_distribution"]
        lines.append("AVERAGE CALORIES PER MEAL")
        lines.append("-" * 60)
        lines.append(f"  Breakfast:  {meals.get('breakfast', 0):.1f} kcal")
        lines.append(f"  Lunch:      {meals.get('lunch', 0):.1f} kcal")
        lines.append(f"  Dinner:     {meals.get('dinner', 0):.1f} kcal")
        lines.append(f"  Snacks:     {meals.get('snack', 0):.1f} kcal")
        lines.append("")

    # Water Statistics
    if "water_stats" in data:
        water = data["water_stats"]
        lines.append("WATER INTAKE")
        lines.append("-" * 60)
        lines.append(f"  Average Daily Intake:      {water.get('avg_intake', 0):.0f} ml")
        lines.append(f"  Days Meeting Goal:         {water.get('days_meeting_goal', 0)}")
        lines.append(f"  Goal Achievement Rate:     {water.get('percentage', 0):.1f}%")
        lines.append("")

    # Weight Trend
    if "weight_trend" in data:
        weight = data["weight_trend"]
        lines.append("WEIGHT TREND")
        lines.append("-" * 60)
        lines.append(f"  Starting Weight:       {weight.get('starting_weight', 0):.1f} kg")
        lines.append(f"  Current Weight:        {weight.get('current_weight', 0):.1f} kg")
        lines.append(f"  Total Change:          {weight.get('total_change', 0):+.1f} kg")
        lines.append(f"  Weekly Avg Change:     {weight.get('weekly_avg_change', 0):+.2f} kg/week")
        lines.append("")

    # Weight-Calorie Correlation
    if "weight_calorie_correlation" in data:
        corr = data["weight_calorie_correlation"]
        lines.append("WEIGHT-CALORIE CORRELATION")
        lines.append("-" * 60)
        lines.append(f"  Correlation:           {corr.get('correlation', 0):.3f}")
        lines.append(f"  Trend:                 {corr.get('trend_description', 'N/A')}")
        lines.append(f"  Avg Deficit/Surplus:   {corr.get('avg_deficit_surplus', 0):+.0f} kcal")
        lines.append("")

    # Exercise Statistics
    if "exercise_stats" in data:
        exercise = data["exercise_stats"]
        lines.append("EXERCISE STATISTICS")
        lines.append("-" * 60)
        lines.append(f"  Total Sessions:        {exercise.get('total_sessions', 0)}")
        lines.append(f"  Total Calories Burned: {exercise.get('total_calories', 0)} kcal")
        most_freq = exercise.get("most_frequent", "N/A")
        lines.append(f"  Most Frequent:         {most_freq}")
        lines.append("")

    # Top Products
    if "top_products" in data:
        products = data["top_products"]
        if products:
            lines.append("TOP 10 MOST CONSUMED PRODUCTS")
            lines.append("-" * 60)
            for i, product in enumerate(products[:10], 1):
                name = product.get("product_name", "Unknown")
                count = product.get("count", 0)
                # Truncate long names
                if len(name) > 40:
                    name = name[:37] + "..."
                lines.append(f"  {i:2}. {name:40} ({count} times)")
            lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)
