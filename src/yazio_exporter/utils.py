"""
Utility functions: date helpers, validation, and concurrent fetching.
"""

import sys
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any


def date_range(start: str, end: str) -> Iterator[str]:
    """
    Generate date strings between start and end (inclusive).

    Args:
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)

    Yields:
        Date strings
    """
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()

    current = start_date
    while current <= end_date:
        yield current.strftime("%Y-%m-%d")
        current += timedelta(days=1)


def validate_date(date_str: str) -> str:
    """
    Validate a date string is in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate

    Returns:
        The validated date string

    Raises:
        ValueError: If the date format is invalid
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD (e.g., 2024-01-15)") from e
    return date_str


def validate_date_range(from_date: str, end_date: str) -> None:
    """
    Validate that from_date <= end_date.

    Args:
        from_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Raises:
        ValueError: If from_date > end_date
    """
    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    if start > end:
        raise ValueError(
            f"Start date ({from_date}) is after end date ({end_date}). Did you swap --from-date and --end-date?"
        )


def print_stderr(msg: str) -> None:
    """Print a message to stderr."""
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def fetch_concurrent(
    items: list[Any],
    fetch_fn: Callable[[Any], Any],
    max_workers: int = 10,
) -> tuple[dict[Any, Any], dict[Any, Exception]]:
    """
    Execute fetch_fn for each item concurrently using ThreadPoolExecutor.

    Args:
        items: List of items to fetch (used as keys in results)
        fetch_fn: Callable that takes an item and returns a result
        max_workers: Maximum number of concurrent threads

    Returns:
        Tuple of (results_dict, errors_dict) where:
            results_dict maps item -> fetch result (successes only)
            errors_dict maps item -> Exception (failures only)
    """
    results = {}
    errors = {}

    if not items:
        return results, errors

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {executor.submit(fetch_fn, item): item for item in items}

        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                results[item] = future.result()
            except Exception as e:
                errors[item] = e

    return results, errors


def serialize_day_data(day_data: dict[str, Any]) -> dict[str, Any]:
    """Convert dataclass instances in day data to plain dicts for JSON serialization."""
    result = {}
    for key, value in day_data.items():
        if isinstance(value, Exception):
            result[key] = {"error": str(value)}
        elif hasattr(value, "__dataclass_fields__"):
            result[key] = {k: getattr(value, k) for k in value.__dataclass_fields__}
        else:
            result[key] = value
    return result
