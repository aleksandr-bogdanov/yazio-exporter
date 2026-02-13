"""
Body measurements export: weight and other body values.
"""

from datetime import datetime, timedelta
from typing import Any

from yazio_exporter.client import YazioClient
from yazio_exporter.constants import BODY_MEASUREMENT_TYPES, DEFAULT_WORKERS
from yazio_exporter.exceptions import APIError
from yazio_exporter.utils import fetch_concurrent


def fetch_weight(client: YazioClient, date: str) -> float | None:
    """
    Fetch weight for a specific day.

    Args:
        client: YazioClient instance
        date: Date string (YYYY-MM-DD)

    Returns:
        Weight value or None if no measurement
    """
    response = client.get(f"/user/bodyvalues/weight/last?date={date}")

    try:
        data = response.json()
    except (ValueError, AttributeError):
        return None

    # Handle null/missing value
    if data is None or not isinstance(data, dict) or "value" not in data:
        return None

    value = data.get("value")
    return float(value) if value is not None else None


def fetch_weight_range(
    client: YazioClient,
    start: str,
    end: str,
    max_workers: int = DEFAULT_WORKERS,
) -> dict[str, float]:
    """
    Fetch weight measurements over a date range concurrently.

    Args:
        client: YazioClient instance
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        max_workers: Maximum number of concurrent threads (default: 10)

    Returns:
        Dictionary mapping date strings to weight values (only dates with measurements)
    """
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")

    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    if not dates:
        return {}

    results, _errors = fetch_concurrent(
        dates,
        lambda d: fetch_weight(client, d),
        max_workers=max_workers,
    )

    # Filter out None values (dates without measurements); silently drop errors
    return {d: w for d, w in results.items() if w is not None}


def filter_null_values(data: dict[str, Any]) -> dict[str, Any]:
    """
    Filter out null or empty values from body measurements.

    Args:
        data: Dictionary of body measurements (date/type -> value)

    Returns:
        Dictionary with only non-null values
    """
    if not isinstance(data, dict):
        return {}

    return {k: v for k, v in data.items() if v is not None}


def probe_body_types(client: YazioClient, date: str) -> dict[str, Any]:
    """
    Probe for available body measurement types.

    Tries common body measurement types and returns only those available.
    Types that return 404 or have no data are excluded.

    Args:
        client: YazioClient instance
        date: Date string (YYYY-MM-DD)

    Returns:
        Dict of body type to value (only available types)
    """
    types_to_probe = BODY_MEASUREMENT_TYPES
    available_types = {}

    for body_type in types_to_probe:
        try:
            response = client.get(f"/user/bodyvalues/{body_type}/last?date={date}")

            try:
                data = response.json()
            except (ValueError, AttributeError):
                continue

            # Only include if there's a valid value
            if data and isinstance(data, dict) and "value" in data:
                value = data.get("value")
                if value is not None:
                    available_types[body_type] = value

        except APIError as e:
            # Skip 404s (type not available)
            if e.status_code == 404:
                continue
            continue

    return available_types
