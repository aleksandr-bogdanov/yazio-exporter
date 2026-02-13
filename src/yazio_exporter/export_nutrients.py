"""
Nutrient history export: vitamins, minerals, and micronutrients.
"""

from yazio_exporter.client import YazioClient
from yazio_exporter.constants import ALL_MINERALS, ALL_VITAMINS, NUTRIENT_WORKERS
from yazio_exporter.utils import fetch_concurrent


def fetch_nutrient(
    client: YazioClient,
    nutrient_id: str,
    start: str,
    end: str,
) -> dict[str, float]:
    """
    Fetch a single nutrient's daily values over a date range.

    Args:
        client: YazioClient instance
        nutrient_id: Nutrient identifier (e.g., 'vitamin.d', 'mineral.iron')
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)

    Returns:
        Dictionary mapping date strings to nutrient values
    """
    response = client.get(
        f"/user/consumed-items/specific-nutrient-daily?start={start}&end={end}&nutrient={nutrient_id}"
    )

    try:
        data = response.json()
    except (ValueError, AttributeError):
        return {}

    if not isinstance(data, dict):
        return {}

    # Filter out null values
    return {k: v for k, v in data.items() if v is not None}


def fetch_multiple(
    client: YazioClient,
    nutrients: list[str],
    start: str,
    end: str,
    max_workers: int = NUTRIENT_WORKERS,
) -> dict[str, dict[str, float]]:
    """
    Fetch multiple nutrients concurrently.

    Args:
        client: YazioClient instance
        nutrients: List of nutrient IDs to fetch
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        max_workers: Number of concurrent workers

    Returns:
        Dictionary mapping nutrient ID to date->value mappings
    """
    successes, errors = fetch_concurrent(
        nutrients,
        lambda n: fetch_nutrient(client, n, start, end),
        max_workers=max_workers,
    )

    # Merge: successes get their data, errors get empty dict
    results = dict(successes)
    for nutrient in errors:
        results[nutrient] = {}

    return results


def fetch_all(
    client: YazioClient,
    start: str,
    end: str,
    max_workers: int = NUTRIENT_WORKERS,
) -> dict[str, dict[str, float]]:
    """
    Fetch complete micronutrient profile (all vitamins and minerals).

    Args:
        client: YazioClient instance
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        max_workers: Number of concurrent workers

    Returns:
        Dictionary mapping nutrient ID to date->value mappings for all nutrients
    """
    all_nutrients = ALL_VITAMINS + ALL_MINERALS
    return fetch_multiple(client, all_nutrients, start, end, max_workers)
