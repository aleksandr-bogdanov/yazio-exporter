"""
Product and recipe resolution from consumed items.
"""

from typing import Any

from yazio_exporter.client import YazioClient
from yazio_exporter.constants import DEFAULT_WORKERS
from yazio_exporter.utils import fetch_concurrent


def extract_product_ids(days_data: dict[str, Any]) -> set[str]:
    """
    Extract unique product IDs from days data.

    Args:
        days_data: Days export data with structure:
            {
                "2024-01-15": {
                    "consumed": {
                        "products": [{"product_id": "..."}],
                        ...
                    }
                },
                ...
            }

    Returns:
        Set of unique product IDs
    """
    product_ids = set()

    for _date, day_data in days_data.items():
        if not isinstance(day_data, dict):
            continue

        consumed = day_data.get("consumed", {})
        if not isinstance(consumed, dict):
            continue

        for product in consumed.get("products", []):
            if isinstance(product, dict) and "product_id" in product:
                product_ids.add(product["product_id"])

    return product_ids


def extract_recipe_ids(days_data: dict[str, Any]) -> set[str]:
    """
    Extract unique recipe IDs from days data.

    Args:
        days_data: Days export data with structure:
            {
                "2024-01-15": {
                    "consumed": {
                        "recipe_portions": [{"recipe_id": "..."}],
                        ...
                    }
                },
                ...
            }

    Returns:
        Set of unique recipe IDs
    """
    recipe_ids = set()

    for _date, day_data in days_data.items():
        if not isinstance(day_data, dict):
            continue

        consumed = day_data.get("consumed", {})
        if not isinstance(consumed, dict):
            continue

        for recipe in consumed.get("recipe_portions", []):
            if isinstance(recipe, dict) and "recipe_id" in recipe:
                recipe_ids.add(recipe["recipe_id"])

    return recipe_ids


def fetch_product(client: YazioClient, product_id: str) -> dict[str, Any]:
    """
    Fetch product details by ID.

    Args:
        client: YazioClient instance with valid token
        product_id: Product UUID to fetch

    Returns:
        Product data with name, nutrients, base_unit, servings, etc.

    Raises:
        APIError: If API request fails
    """
    response = client.get(f"/products/{product_id}")
    return response.json()


def fetch_recipe(client: YazioClient, recipe_id: str) -> dict[str, Any]:
    """
    Fetch recipe details by ID.

    Args:
        client: YazioClient instance with valid token
        recipe_id: Recipe UUID to fetch

    Returns:
        Recipe data with name, nutrients, servings (ingredients list), etc.

    Raises:
        APIError: If API request fails
    """
    response = client.get(f"/recipes/{recipe_id}")
    return response.json()


def fetch_all_concurrent(
    client: YazioClient,
    product_ids: set[str],
    recipe_ids: set[str],
    max_workers: int = DEFAULT_WORKERS,
) -> dict[str, dict[str, Any]]:
    """
    Fetch product and recipe details concurrently.

    Args:
        client: YazioClient instance with valid token
        product_ids: Set of product IDs to fetch
        recipe_ids: Set of recipe IDs to fetch
        max_workers: Maximum number of concurrent threads (default: 10)

    Returns:
        Dictionary with 'products' and 'recipes' keys:
        {
            'products': {product_id: product_data, ...},
            'recipes': {recipe_id: recipe_data, ...}
        }

        If a fetch fails, the exception is stored instead of the data.
    """
    product_successes, product_errors = fetch_concurrent(
        list(product_ids),
        lambda pid: fetch_product(client, pid),
        max_workers=max_workers,
    )

    recipe_successes, recipe_errors = fetch_concurrent(
        list(recipe_ids),
        lambda rid: fetch_recipe(client, rid),
        max_workers=max_workers,
    )

    # Merge successes and errors to preserve existing contract
    # (errors stored as Exception objects in the dict)
    products = dict(product_successes)
    for pid, err in product_errors.items():
        products[pid] = err

    recipes = dict(recipe_successes)
    for rid, err in recipe_errors.items():
        recipes[rid] = err

    return {"products": products, "recipes": recipes}
