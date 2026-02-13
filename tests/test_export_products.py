"""
Tests for products export.
"""

import responses

from yazio_exporter.export_products import (
    extract_product_ids,
    extract_recipe_ids,
    fetch_all_concurrent,
    fetch_product,
    fetch_recipe,
)


def test_extract_product_ids_basic():
    """Feature #25: Extract unique product IDs from consumed items."""
    days_data = {
        "2024-01-15": {
            "consumed": {
                "products": [
                    {"id": "prod-uuid-1", "product_id": "product-uuid-1"},
                    {"id": "prod-uuid-2", "product_id": "product-uuid-2"},
                ],
                "recipe_portions": [],
                "simple_products": [],
            }
        },
        "2024-01-16": {
            "consumed": {
                "products": [
                    {"id": "prod-uuid-3", "product_id": "product-uuid-1"},
                    {"id": "prod-uuid-4", "product_id": "product-uuid-3"},
                ],
                "recipe_portions": [],
                "simple_products": [],
            }
        },
    }

    product_ids = extract_product_ids(days_data)

    assert isinstance(product_ids, set)
    assert product_ids == {"product-uuid-1", "product-uuid-2", "product-uuid-3"}
    assert len(product_ids) == 3


def test_extract_product_ids_empty():
    """Test extracting product IDs from empty days data."""
    assert isinstance(extract_product_ids({}), set)
    assert len(extract_product_ids({})) == 0


def test_extract_product_ids_no_products():
    """Test extracting product IDs when no products consumed."""
    days_data = {"2024-01-15": {"consumed": {"products": [], "recipe_portions": [], "simple_products": []}}}

    product_ids = extract_product_ids(days_data)
    assert isinstance(product_ids, set)
    assert len(product_ids) == 0


def test_extract_product_ids_missing_consumed_key():
    """Test extracting product IDs when consumed key is missing."""
    days_data = {"2024-01-15": {"exercises": {}}}

    product_ids = extract_product_ids(days_data)
    assert isinstance(product_ids, set)
    assert len(product_ids) == 0


def test_extract_recipe_ids_basic():
    """Feature #26: Extract unique recipe IDs from consumed items."""
    days_data = {
        "2024-01-15": {
            "consumed": {
                "products": [],
                "recipe_portions": [
                    {"id": "recipe-uuid-1", "recipe_id": "recipe-1"},
                    {"id": "recipe-uuid-2", "recipe_id": "recipe-2"},
                ],
                "simple_products": [],
            }
        },
        "2024-01-16": {
            "consumed": {
                "products": [],
                "recipe_portions": [
                    {"id": "recipe-uuid-3", "recipe_id": "recipe-1"},
                    {"id": "recipe-uuid-4", "recipe_id": "recipe-3"},
                ],
                "simple_products": [],
            }
        },
    }

    recipe_ids = extract_recipe_ids(days_data)

    assert isinstance(recipe_ids, set)
    assert recipe_ids == {"recipe-1", "recipe-2", "recipe-3"}
    assert len(recipe_ids) == 3


def test_extract_recipe_ids_empty():
    """Test extracting recipe IDs from empty days data."""
    assert isinstance(extract_recipe_ids({}), set)
    assert len(extract_recipe_ids({})) == 0


def test_extract_recipe_ids_no_recipes():
    """Test extracting recipe IDs when no recipes consumed."""
    days_data = {"2024-01-15": {"consumed": {"products": [], "recipe_portions": [], "simple_products": []}}}

    recipe_ids = extract_recipe_ids(days_data)
    assert isinstance(recipe_ids, set)
    assert len(recipe_ids) == 0


def test_extract_recipe_ids_missing_consumed_key():
    """Test extracting recipe IDs when consumed key is missing."""
    days_data = {"2024-01-15": {"exercises": {}}}

    recipe_ids = extract_recipe_ids(days_data)
    assert isinstance(recipe_ids, set)
    assert len(recipe_ids) == 0


@responses.activate
def test_fetch_product_details(client, base_api_url):
    """Feature #27: Fetch product details by ID."""
    product_id = "uuid123"
    mock_response = {
        "id": product_id,
        "name": "Potato",
        "category": "potatoproducts",
        "nutrients": {
            "energy.energy": 0.857,
            "nutrient.protein": 0.02,
            "nutrient.fat": 0.001,
            "nutrient.carb": 0.17,
        },
        "base_unit": "g",
        "servings": [
            {"name": "medium", "amount": 150},
            {"name": "large", "amount": 250},
        ],
    }

    responses.add(
        responses.GET,
        f"{base_api_url}/products/{product_id}",
        json=mock_response,
        status=200,
    )

    product_data = fetch_product(client, product_id)

    assert product_data is not None
    assert product_data["id"] == product_id
    assert product_data["name"] == "Potato"
    assert product_data["category"] == "potatoproducts"
    assert product_data["base_unit"] == "g"
    assert "nutrients" in product_data
    assert product_data["nutrients"]["energy.energy"] == 0.857
    assert len(product_data["servings"]) == 2


@responses.activate
def test_fetch_product_minimal_response(client, base_api_url):
    """Test fetching product with minimal fields."""
    product_id = "minimal-uuid"
    mock_response = {
        "id": product_id,
        "name": "Simple Product",
        "nutrients": {},
        "base_unit": "ml",
    }

    responses.add(
        responses.GET,
        f"{base_api_url}/products/{product_id}",
        json=mock_response,
        status=200,
    )

    product_data = fetch_product(client, product_id)

    assert product_data["id"] == product_id
    assert product_data["name"] == "Simple Product"
    assert product_data["nutrients"] == {}
    assert product_data["base_unit"] == "ml"


@responses.activate
def test_fetch_recipe_details(client, base_api_url):
    """Feature #28: Fetch recipe details by ID."""
    recipe_id = "uuid456"
    mock_response = {
        "id": recipe_id,
        "name": "Chicken Salad",
        "portion_count": 2,
        "nutrients": {
            "energy.energy": 1.234,
            "nutrient.protein": 0.25,
            "nutrient.fat": 0.10,
            "nutrient.carb": 0.15,
        },
        "servings": [
            {
                "product_id": "chicken-uuid",
                "name": "Chicken Breast",
                "amount": 200,
                "unit": "g",
            },
            {
                "product_id": "lettuce-uuid",
                "name": "Lettuce",
                "amount": 100,
                "unit": "g",
            },
        ],
    }

    responses.add(
        responses.GET,
        f"{base_api_url}/recipes/{recipe_id}",
        json=mock_response,
        status=200,
    )

    recipe_data = fetch_recipe(client, recipe_id)

    assert recipe_data["id"] == recipe_id
    assert recipe_data["name"] == "Chicken Salad"
    assert recipe_data["portion_count"] == 2
    assert recipe_data["nutrients"]["energy.energy"] == 1.234
    assert len(recipe_data["servings"]) == 2
    assert recipe_data["servings"][0]["product_id"] == "chicken-uuid"


@responses.activate
def test_fetch_recipe_minimal_response(client, base_api_url):
    """Test fetching recipe with minimal fields."""
    recipe_id = "minimal-recipe-uuid"
    mock_response = {
        "id": recipe_id,
        "name": "Simple Recipe",
        "portion_count": 1,
        "nutrients": {},
        "servings": [],
    }

    responses.add(
        responses.GET,
        f"{base_api_url}/recipes/{recipe_id}",
        json=mock_response,
        status=200,
    )

    recipe_data = fetch_recipe(client, recipe_id)

    assert recipe_data["id"] == recipe_id
    assert recipe_data["name"] == "Simple Recipe"
    assert recipe_data["portion_count"] == 1
    assert recipe_data["nutrients"] == {}
    assert recipe_data["servings"] == []


@responses.activate
def test_fetch_all_concurrent(client, base_api_url):
    """Feature #29: Concurrent fetching of products and recipes."""
    product_ids = {f"product-{i}" for i in range(1, 21)}
    recipe_ids = {f"recipe-{i}" for i in range(1, 6)}

    for product_id in product_ids:
        responses.add(
            responses.GET,
            f"{base_api_url}/products/{product_id}",
            json={
                "id": product_id,
                "name": f"Product {product_id}",
                "nutrients": {"energy.energy": 1.0},
                "base_unit": "g",
            },
            status=200,
        )

    for recipe_id in recipe_ids:
        responses.add(
            responses.GET,
            f"{base_api_url}/recipes/{recipe_id}",
            json={
                "id": recipe_id,
                "name": f"Recipe {recipe_id}",
                "portion_count": 1,
                "nutrients": {"energy.energy": 2.0},
                "servings": [],
            },
            status=200,
        )

    results = fetch_all_concurrent(client, product_ids, recipe_ids)

    assert "products" in results
    assert "recipes" in results

    assert len(results["products"]) == 20
    for product_id in product_ids:
        assert product_id in results["products"]
        assert results["products"][product_id]["id"] == product_id

    assert len(results["recipes"]) == 5
    for recipe_id in recipe_ids:
        assert recipe_id in results["recipes"]
        assert results["recipes"][recipe_id]["id"] == recipe_id


@responses.activate
def test_fetch_all_concurrent_empty_sets(client):
    """Test concurrent fetching with empty product and recipe sets."""
    results = fetch_all_concurrent(client, set(), set())

    assert "products" in results
    assert "recipes" in results
    assert len(results["products"]) == 0
    assert len(results["recipes"]) == 0


@responses.activate
def test_fetch_all_concurrent_partial_failure(client, base_api_url):
    """Test concurrent fetching handles individual failures gracefully."""
    product_ids = {"product-1", "product-2", "product-3"}
    recipe_ids = {"recipe-1", "recipe-2"}

    responses.add(
        responses.GET,
        f"{base_api_url}/products/product-1",
        json={
            "id": "product-1",
            "name": "Product 1",
            "nutrients": {},
            "base_unit": "g",
        },
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/products/product-2",
        json={"error": "Not found"},
        status=404,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/products/product-3",
        json={
            "id": "product-3",
            "name": "Product 3",
            "nutrients": {},
            "base_unit": "g",
        },
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/recipes/recipe-1",
        json={
            "id": "recipe-1",
            "name": "Recipe 1",
            "portion_count": 1,
            "nutrients": {},
            "servings": [],
        },
        status=200,
    )

    responses.add(
        responses.GET,
        f"{base_api_url}/recipes/recipe-2",
        json={"error": "Server error"},
        status=500,
    )

    results = fetch_all_concurrent(client, product_ids, recipe_ids)

    assert len(results["products"]) == 3
    assert results["products"]["product-1"]["id"] == "product-1"
    assert results["products"]["product-3"]["id"] == "product-3"

    assert "product-2" in results["products"]
    assert isinstance(results["products"]["product-2"], Exception)

    assert len(results["recipes"]) == 2
    assert results["recipes"]["recipe-1"]["id"] == "recipe-1"

    assert "recipe-2" in results["recipes"]
    assert isinstance(results["recipes"]["recipe-2"], Exception)


@responses.activate
def test_missing_nutrients_return_empty_dict(client, base_api_url):
    """Feature #72: Missing nutrients return null/zero."""
    product_id = "incomplete-product-uuid"

    mock_response = {
        "id": product_id,
        "name": "Incomplete Product",
        "base_unit": "g",
        "nutrients": {"energy.energy": 1.5},
    }

    responses.add(
        responses.GET,
        f"{base_api_url}/products/{product_id}",
        json=mock_response,
        status=200,
    )

    product_data = fetch_product(client, product_id)

    assert product_data["id"] == product_id
    assert product_data["name"] == "Incomplete Product"
    assert product_data["nutrients"]["energy.energy"] == 1.5

    assert product_data["nutrients"].get("vitamin.d") is None
    assert product_data["nutrients"].get("nutrient.protein") is None
    assert product_data["nutrients"].get("nutrient.fat") is None
    assert product_data["nutrients"].get("nutrient.carb") is None
