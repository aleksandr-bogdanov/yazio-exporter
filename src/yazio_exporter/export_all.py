"""
Complete export pipeline: orchestrates all export modules.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from yazio_exporter.client import YazioClient
from yazio_exporter.constants import DISCOVERY_LOOKBACK_YEARS
from yazio_exporter.export_body import fetch_weight_range
from yazio_exporter.export_days import auto_discover_months, fetch_days_concurrent
from yazio_exporter.export_nutrients import fetch_all as fetch_all_nutrients
from yazio_exporter.export_products import (
    extract_product_ids,
    extract_recipe_ids,
    fetch_all_concurrent,
)
from yazio_exporter.export_profile import fetch_user
from yazio_exporter.generate_reports import generate_analysis, generate_llm_prompt
from yazio_exporter.utils import print_stderr, serialize_day_data


def export_all(
    client: YazioClient,
    output_dir: str,
    format: str = "json",
) -> dict[str, Any]:
    """
    Execute complete export pipeline.

    Creates output directory and exports:
    - profile.{ext}: User profile data
    - days.{ext}: Daily nutrition data
    - weight.{ext}: Weight history
    - nutrients.{ext}: Micronutrient history
    - products.{ext}: Product database
    - summary.txt: Text summary of export

    Args:
        client: Authenticated YazioClient instance
        output_dir: Output directory path
        format: Export format (json, csv, sqlite)

    Returns:
        Dict with export statistics
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize statistics
    stats = {
        "days_exported": 0,
        "products_exported": 0,
        "weight_entries": 0,
        "nutrients_exported": 0,
        "output_dir": str(output_path.absolute()),
    }

    # Step 1: Export profile data
    print_stderr("Fetching user profile...")
    profile_data = fetch_user(client)

    profile_file = output_path / "profile.json"
    with open(profile_file, "w") as f:
        json.dump(profile_data, f, indent=2, sort_keys=True)

    # Step 2: Discover all historical months and fetch day data
    print_stderr("Discovering historical data...")
    now = datetime.now()

    start_year = now.year - DISCOVERY_LOOKBACK_YEARS
    all_dates = auto_discover_months(client, start_year, 1)
    print_stderr(f"Found {len(all_dates)} days with data")

    # Fetch full day data for all discovered dates
    days_data = {}
    if all_dates:
        print_stderr(f"Fetching daily data for {len(all_dates)} days...")
        data_types = ["consumed", "goals", "exercises", "water", "daily_summary"]
        raw_days = fetch_days_concurrent(client, all_dates, data_types)

        # Serialize dataclasses for JSON output
        for date_str, day_info in raw_days.items():
            days_data[date_str] = serialize_day_data(day_info)

    stats["days_exported"] = len(days_data)

    days_file = output_path / "days.json"
    with open(days_file, "w") as f:
        json.dump(days_data, f, indent=2, sort_keys=True)

    # Step 3: Export weight data over the full discovered range
    if all_dates:
        start_date = min(all_dates)
        end_date = max(all_dates)
    else:
        end_date = now.strftime("%Y-%m-%d")
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")

    print_stderr(f"Fetching weight data ({start_date} to {end_date})...")
    weight_measurements = fetch_weight_range(client, start_date, end_date)
    stats["weight_entries"] = len(weight_measurements)

    weight_file = output_path / "weight.json"
    with open(weight_file, "w") as f:
        json.dump(weight_measurements, f, indent=2, sort_keys=True)

    # Step 4: Export all nutrients over the full range
    print_stderr("Fetching nutrient history (all vitamins & minerals)...")
    nutrients_data = fetch_all_nutrients(client, start_date, end_date)
    stats["nutrients_exported"] = sum(len(v) for v in nutrients_data.values() if isinstance(v, dict))

    nutrients_file = output_path / "nutrients.json"
    with open(nutrients_file, "w") as f:
        json.dump(nutrients_data, f, indent=2, sort_keys=True)

    # Step 5: Extract product/recipe IDs from days data and resolve them
    print_stderr("Resolving products and recipes...")
    product_ids = extract_product_ids(days_data)
    recipe_ids = extract_recipe_ids(days_data)
    print_stderr(f"Found {len(product_ids)} products and {len(recipe_ids)} recipes to resolve")

    products_result = fetch_all_concurrent(client, product_ids, recipe_ids)

    # Filter out exceptions from products/recipes for JSON output
    clean_products = {}
    for pid, pdata in products_result.get("products", {}).items():
        if not isinstance(pdata, Exception):
            clean_products[pid] = pdata

    clean_recipes = {}
    for rid, rdata in products_result.get("recipes", {}).items():
        if not isinstance(rdata, Exception):
            clean_recipes[rid] = rdata

    products_data = {"products": clean_products, "recipes": clean_recipes}
    stats["products_exported"] = len(clean_products) + len(clean_recipes)

    products_file = output_path / "products.json"
    with open(products_file, "w") as f:
        json.dump(products_data, f, indent=2, sort_keys=True)

    # Create summary file
    summary_file = output_path / "summary.txt"
    with open(summary_file, "w") as f:
        f.write("Yazio Export Summary\n")
        f.write("====================\n\n")
        f.write(f"Date range: {start_date} to {end_date}\n")
        f.write(f"Days exported: {stats['days_exported']}\n")
        f.write(f"Products: {stats['products_exported']}\n")
        f.write(f"Weight entries: {stats['weight_entries']}\n")
        f.write(f"Nutrient data points: {stats['nutrients_exported']}\n")
        f.write(f"\nOutput directory: {stats['output_dir']}\n")

    # Generate analysis summary and LLM prompt
    print_stderr("Generating analysis reports...")
    analysis_md = generate_analysis(
        days_data,
        weight_measurements,
        products_data,
        profile_data,
    )
    analysis_file = output_path / "analysis.md"
    with open(analysis_file, "w") as f:
        f.write(analysis_md)

    llm_prompt = generate_llm_prompt(
        days_data,
        weight_measurements,
        products_data,
        profile_data,
    )
    prompt_file = output_path / "llm_prompt.txt"
    with open(prompt_file, "w") as f:
        f.write(llm_prompt)

    print_stderr("Export complete!")

    return stats


def print_summary(stats: dict[str, Any]) -> None:
    """
    Print export summary to stderr.

    Args:
        stats: Export statistics from export_all()
    """
    print_stderr("\nExport complete!")
    print_stderr(f"  {stats['days_exported']} days exported")
    print_stderr(f"  {stats['products_exported']} products")
    print_stderr(f"  {stats['weight_entries']} weight entries")
    print_stderr(f"\nOutput directory: {stats['output_dir']}")
