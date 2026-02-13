"""
Export daily diary data: discovery, fetching, and concurrent scraping.
"""

import calendar
from datetime import date
from typing import Any

from yazio_exporter.client import YazioClient
from yazio_exporter.constants import DEFAULT_WORKERS
from yazio_exporter.models import (
    ConsumedItems,
    DailySummary,
    Exercises,
    Goals,
    WaterIntake,
)
from yazio_exporter.utils import fetch_concurrent


def discover_month(client: YazioClient, year: int, month: int) -> list[str]:
    """
    Discover days with data in a specific month.

    Args:
        client: YazioClient instance
        year: Year
        month: Month (1-12)

    Returns:
        List of date strings (YYYY-MM-DD)
    """
    # Get first and last day of the month
    first_day = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)

    # Format dates as YYYY-MM-DD
    start_date = first_day.strftime("%Y-%m-%d")
    end_date = last_day.strftime("%Y-%m-%d")

    # Call nutrients-daily endpoint
    endpoint = f"/user/consumed-items/nutrients-daily?start={start_date}&end={end_date}"
    response = client.get(endpoint)

    data = response.json()

    # Extract dates from the response
    if not isinstance(data, list):
        return []

    dates = []
    for entry in data:
        if isinstance(entry, dict) and "date" in entry:
            dates.append(entry["date"])

    return dates


def fetch_consumed(client: YazioClient, date: str) -> ConsumedItems:
    """
    Fetch consumed items for a specific day.

    Args:
        client: YazioClient instance
        date: Date string in YYYY-MM-DD format

    Returns:
        ConsumedItems model with products and recipe_portions
    """
    response = client.get(f"/user/consumed-items?date={date}")
    data = response.json()
    return ConsumedItems(
        products=data.get("products", []),
        recipe_portions=data.get("recipe_portions", []),
        simple_products=data.get("simple_products", []),
    )


def fetch_exercises(client: YazioClient, date: str) -> Exercises:
    """
    Fetch exercises for a specific day.

    Args:
        client: YazioClient instance
        date: Date string in YYYY-MM-DD format

    Returns:
        Exercises model with training, custom_training, and activity
    """
    response = client.get(f"/user/exercises?date={date}")
    data = response.json()
    return Exercises(
        training=data.get("training", []),
        custom_training=data.get("custom_training", []),
        activity=data.get("activity"),
    )


def fetch_daily_summary(client: YazioClient, date: str) -> DailySummary:
    """
    Fetch comprehensive daily summary with meal breakdowns.

    Args:
        client: YazioClient instance
        date: Date string in YYYY-MM-DD format

    Returns:
        DailySummary model with meals, activity_energy, steps, water_intake, goals, and units
    """
    response = client.get(f"/user/widgets/daily-summary?date={date}")
    data = response.json()
    return DailySummary(
        meals=data.get("meals", {}),
        activity_energy=data.get("activity_energy"),
        steps=data.get("steps"),
        water_intake=data.get("water_intake"),
        goals=data.get("goals", {}),
        units=data.get("units", {}),
    )


def fetch_goals(client: YazioClient, date: str) -> Goals:
    """
    Fetch daily goals for a specific day.

    Args:
        client: YazioClient instance
        date: Date string in YYYY-MM-DD format

    Returns:
        Goals model with all daily goal values
    """
    response = client.get(f"/user/goals?date={date}")
    data = response.json()
    return Goals(data=data)


def fetch_water(client: YazioClient, date: str) -> WaterIntake:
    """
    Fetch water intake for a specific day.

    Args:
        client: YazioClient instance
        date: Date string in YYYY-MM-DD format

    Returns:
        WaterIntake model with water_intake value
    """
    response = client.get(f"/user/water-intake?date={date}")
    data = response.json()
    return WaterIntake(
        water_intake=data.get("water_intake", 0),
        gateway=data.get("gateway"),
        source=data.get("source"),
    )


def fetch_days_concurrent(
    client: YazioClient,
    dates: list[str],
    data_types: list[str],
    max_workers: int = DEFAULT_WORKERS,
) -> dict[str, dict[str, Any]]:
    """
    Fetch data for multiple days concurrently using ThreadPoolExecutor.

    Args:
        client: YazioClient instance
        dates: List of date strings in YYYY-MM-DD format
        data_types: List of data types to fetch
            (e.g., ['consumed', 'goals', 'exercises', 'water', 'daily_summary'])
        max_workers: Maximum number of concurrent threads (default: 10)

    Returns:
        Dictionary mapping dates to their fetched data.
        Each date entry is a dict with keys matching data_types.
        Example: {"2024-01-01": {"consumed": ConsumedItems(...), "goals": Goals(...)}}
    """
    results: dict[str, dict[str, Any]] = {date: {} for date in dates}

    # Map data type names to fetch functions
    fetch_functions = {
        "consumed": fetch_consumed,
        "goals": fetch_goals,
        "exercises": fetch_exercises,
        "water": fetch_water,
        "daily_summary": fetch_daily_summary,
        "summary": fetch_daily_summary,
    }

    # Validate data types
    for dtype in data_types:
        if dtype not in fetch_functions:
            raise ValueError(f"Unknown data type: {dtype}. Must be one of {list(fetch_functions.keys())}")

    # Create tasks: (date, data_type) tuples
    tasks = [(d, dtype) for d in dates for dtype in data_types]

    def _fetch_task(task):
        d, dtype = task
        return fetch_functions[dtype](client, d)

    successes, errors = fetch_concurrent(tasks, _fetch_task, max_workers=max_workers)

    # Regroup results by date
    for (d, dtype), value in successes.items():
        results[d][dtype] = value

    for (d, dtype), err in errors.items():
        results[d][dtype] = err

    return results


def auto_discover_months(client: YazioClient, start_year: int, start_month: int) -> list[str]:
    """
    Auto-discover all months with data by scanning every month from start to now.

    Scans every month from start_year/start_month through the current month.
    No early termination — handles arbitrary gaps in tracking history.

    Args:
        client: YazioClient instance
        start_year: Starting year
        start_month: Starting month (1-12)

    Returns:
        List of all discovered dates
    """
    all_dates = []
    current_year = start_year
    current_month = start_month
    today = date.today()

    while (current_year, current_month) <= (today.year, today.month):
        dates = discover_month(client, current_year, current_month)
        if dates:
            all_dates.extend(dates)

        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    return all_dates
