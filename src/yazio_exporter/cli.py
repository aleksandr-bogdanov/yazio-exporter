"""
CLI interface with argparse for all subcommands.
"""

import argparse
import json
import sys

from yazio_exporter import __version__
from yazio_exporter.exceptions import APIError, AuthenticationError
from yazio_exporter.utils import print_stderr, validate_date, validate_date_range


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="yazio-exporter",
        description="Export your Yazio nutrition data to JSON, CSV, or SQLite",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # login subcommand
    login_parser = subparsers.add_parser("login", help="Authenticate and save token")
    login_parser.add_argument("email", help="Yazio account email")
    login_parser.add_argument("password", help="Yazio account password")
    login_parser.add_argument("-o", "--output", default="token.txt", help="Token output file (default: %(default)s)")

    # profile subcommand
    profile_parser = subparsers.add_parser("profile", help="Export user profile")
    profile_parser.add_argument("-t", "--token", default="token.txt", help="Token file (default: %(default)s)")
    profile_parser.add_argument("-o", "--output", default="profile.json", help="Output file (default: %(default)s)")
    profile_parser.add_argument(
        "--format",
        choices=["json", "csv", "sqlite"],
        default="json",
        help="Output format (default: %(default)s)",
    )

    # days subcommand
    days_parser = subparsers.add_parser("days", help="Export daily diary data")
    days_parser.add_argument("-t", "--token", default="token.txt", help="Token file (default: %(default)s)")
    days_parser.add_argument(
        "-w",
        "--what",
        default="consumed,goals,exercises,water,daily_summary",
        help="Data types to export (comma-separated)",
    )
    days_parser.add_argument("-f", "--from-date", help="Start date (YYYY-MM-DD)")
    days_parser.add_argument("-e", "--end-date", help="End date (YYYY-MM-DD)")
    days_parser.add_argument("-o", "--output", default="days.json", help="Output file (default: %(default)s)")
    days_parser.add_argument(
        "--format",
        choices=["json", "csv", "sqlite"],
        default="json",
        help="Output format (default: %(default)s)",
    )

    # weight subcommand
    weight_parser = subparsers.add_parser("weight", help="Export weight and body measurements")
    weight_parser.add_argument("-t", "--token", default="token.txt", help="Token file (default: %(default)s)")
    weight_parser.add_argument("-f", "--from-date", help="Start date (YYYY-MM-DD)")
    weight_parser.add_argument("-e", "--end-date", help="End date (YYYY-MM-DD)")
    weight_parser.add_argument("-o", "--output", default="weight.json", help="Output file (default: %(default)s)")
    weight_parser.add_argument(
        "--format",
        choices=["json", "csv", "sqlite"],
        default="json",
        help="Output format (default: %(default)s)",
    )

    # nutrients subcommand
    nutrients_parser = subparsers.add_parser("nutrients", help="Export nutrient history")
    nutrients_parser.add_argument("-t", "--token", default="token.txt", help="Token file (default: %(default)s)")
    nutrients_parser.add_argument(
        "-n",
        "--nutrients",
        help="Specific nutrients (comma-separated, or omit for all)",
    )
    nutrients_parser.add_argument("-f", "--from-date", help="Start date (YYYY-MM-DD)")
    nutrients_parser.add_argument("-e", "--end-date", help="End date (YYYY-MM-DD)")
    nutrients_parser.add_argument("-o", "--output", default="nutrients.json", help="Output file (default: %(default)s)")
    nutrients_parser.add_argument(
        "--format",
        choices=["json", "csv", "sqlite"],
        default="json",
        help="Output format (default: %(default)s)",
    )

    # products subcommand
    products_parser = subparsers.add_parser("products", help="Resolve product details from days export")
    products_parser.add_argument("-t", "--token", default="token.txt", help="Token file (default: %(default)s)")
    products_parser.add_argument(
        "-f", "--from-file", default="days.json", help="Days export JSON file (default: %(default)s)"
    )
    products_parser.add_argument("-o", "--output", default="products.json", help="Output file (default: %(default)s)")
    products_parser.add_argument(
        "--format",
        choices=["json", "csv", "sqlite"],
        default="json",
        help="Output format (default: %(default)s)",
    )

    # summary subcommand
    summary_parser = subparsers.add_parser("summary", help="Generate analytics and statistics")
    summary_parser.add_argument(
        "-f", "--from-file", default="days.json", help="Days export JSON file (default: %(default)s)"
    )
    summary_parser.add_argument("-p", "--products", help="Products export JSON file")
    summary_parser.add_argument("-w", "--weight", help="Weight export JSON file")
    summary_parser.add_argument(
        "--period",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Aggregation period (default: %(default)s)",
    )
    summary_parser.add_argument(
        "--format",
        choices=["json", "csv", "table"],
        default="table",
        help="Output format (default: %(default)s)",
    )

    # export-all subcommand
    export_all_parser = subparsers.add_parser("export-all", help="Complete export pipeline")
    export_all_parser.add_argument("email", help="Yazio account email")
    export_all_parser.add_argument("password", help="Yazio account password")
    export_all_parser.add_argument("-o", "--output", default="output/", help="Output directory (default: %(default)s)")
    export_all_parser.add_argument(
        "--format",
        choices=["json", "csv", "sqlite"],
        default="json",
        help="Output format (default: %(default)s)",
    )

    # report subcommand
    report_parser = subparsers.add_parser("report", help="Generate analysis and LLM prompt from existing exports")
    report_parser.add_argument(
        "-d", "--dir", default="output/", help="Directory with exported JSON files (default: %(default)s)"
    )
    report_parser.add_argument("--start", help="Start date filter (YYYY-MM-DD)")
    report_parser.add_argument("--end", help="End date filter (YYYY-MM-DD)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "login":
            return cmd_login(args)
        elif args.command == "profile":
            return cmd_profile(args)
        elif args.command == "days":
            return cmd_days(args)
        elif args.command == "weight":
            return cmd_weight(args)
        elif args.command == "nutrients":
            return cmd_nutrients(args)
        elif args.command == "products":
            return cmd_products(args)
        elif args.command == "summary":
            return cmd_summary(args)
        elif args.command == "export-all":
            return cmd_export_all(args)
        elif args.command == "report":
            return cmd_report(args)
    except AuthenticationError as e:
        print_stderr(f"Authentication error: {e}")
        return 1
    except APIError as e:
        print_stderr(f"API error: {e}")
        return 1
    except FileNotFoundError as e:
        print_stderr(f"Error: {e}")
        return 1
    except ValueError as e:
        print_stderr(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        print_stderr("\nAborted.")
        return 130
    except Exception as e:
        print_stderr(f"Error: {e}")
        return 1

    return 0


def _get_client(args):
    """Create an authenticated YazioClient from args.token."""
    from yazio_exporter.auth import make_authenticated_client

    return make_authenticated_client(args.token)


def _get_date_range(args, default_days=365):
    """Extract and validate date range from args, with defaults."""
    from datetime import datetime, timedelta

    now = datetime.now()
    end_date = args.end_date or now.strftime("%Y-%m-%d")
    from_date = args.from_date or (now - timedelta(days=default_days)).strftime("%Y-%m-%d")

    validate_date(from_date)
    validate_date(end_date)
    validate_date_range(from_date, end_date)

    return from_date, end_date


def cmd_login(args):
    """Handle the login subcommand."""
    from yazio_exporter.auth import login_and_save

    print_stderr(f"Logging in as {args.email}...")
    login_and_save(args.email, args.password, args.output)
    print_stderr(f"Token saved to {args.output}")
    return 0


def cmd_profile(args):
    """Handle the profile subcommand."""
    from yazio_exporter.export_profile import fetch_all
    from yazio_exporter.formatters import to_json

    client = _get_client(args)
    print_stderr("Fetching profile...")
    profile_data = fetch_all(client)

    to_json(profile_data, args.output)
    print_stderr(f"Profile saved to {args.output}")
    return 0


def cmd_days(args):
    """Handle the days subcommand."""
    from datetime import datetime

    from yazio_exporter.constants import DISCOVERY_LOOKBACK_YEARS
    from yazio_exporter.export_days import (
        auto_discover_months,
        fetch_days_concurrent,
    )
    from yazio_exporter.formatters import to_json
    from yazio_exporter.utils import date_range, serialize_day_data

    client = _get_client(args)

    # Parse and validate dates
    data_types = [dt.strip() for dt in args.what.split(",")]

    if args.from_date and args.end_date:
        validate_date(args.from_date)
        validate_date(args.end_date)
        validate_date_range(args.from_date, args.end_date)
        dates = list(date_range(args.from_date, args.end_date))
    elif args.from_date or args.end_date:
        date_str = args.from_date or args.end_date
        validate_date(date_str)
        dates = [date_str]
    else:
        print_stderr("Discovering historical data...")
        now = datetime.now()
        start_year = now.year - DISCOVERY_LOOKBACK_YEARS
        dates = auto_discover_months(client, start_year, 1)
        print_stderr(f"Found {len(dates)} days with data")

    if not dates:
        print_stderr("No data found for the specified range.")
        to_json({}, args.output)
        return 0

    print_stderr(f"Fetching data for {len(dates)} days...")
    raw_days = fetch_days_concurrent(client, dates, data_types)

    days_data = {}
    for date_str, day_info in raw_days.items():
        days_data[date_str] = serialize_day_data(day_info)

    to_json(days_data, args.output)
    print_stderr(f"Days data saved to {args.output} ({len(days_data)} days)")
    return 0


def cmd_weight(args):
    """Handle the weight subcommand."""
    from yazio_exporter.export_body import fetch_weight_range
    from yazio_exporter.formatters import to_json

    client = _get_client(args)
    from_date, end_date = _get_date_range(args)

    print_stderr(f"Fetching weight data ({from_date} to {end_date})...")
    weight_data = fetch_weight_range(client, from_date, end_date)

    to_json(weight_data, args.output)
    print_stderr(f"Weight data saved to {args.output} ({len(weight_data)} entries)")
    return 0


def cmd_nutrients(args):
    """Handle the nutrients subcommand."""
    from yazio_exporter.export_nutrients import (
        fetch_all,
        fetch_multiple,
    )
    from yazio_exporter.formatters import to_json

    client = _get_client(args)
    from_date, end_date = _get_date_range(args)

    if args.nutrients:
        nutrient_list = [n.strip() for n in args.nutrients.split(",")]
        print_stderr(f"Fetching {len(nutrient_list)} nutrients ({from_date} to {end_date})...")
        nutrients_data = fetch_multiple(client, nutrient_list, from_date, end_date)
    else:
        print_stderr(f"Fetching all nutrients ({from_date} to {end_date})...")
        nutrients_data = fetch_all(client, from_date, end_date)

    to_json(nutrients_data, args.output)
    total_points = sum(len(v) for v in nutrients_data.values() if isinstance(v, dict))
    print_stderr(f"Nutrients saved to {args.output} ({total_points} data points)")
    return 0


def cmd_products(args):
    """Handle the products subcommand."""
    from yazio_exporter.export_products import (
        extract_product_ids,
        extract_recipe_ids,
        fetch_all_concurrent,
    )
    from yazio_exporter.formatters import to_json

    client = _get_client(args)

    # Load days data from file
    print_stderr(f"Loading days data from {args.from_file}...")
    with open(args.from_file) as f:
        days_data = json.load(f)

    product_ids = extract_product_ids(days_data)
    recipe_ids = extract_recipe_ids(days_data)
    print_stderr(f"Found {len(product_ids)} products and {len(recipe_ids)} recipes")

    print_stderr("Resolving product and recipe details...")
    results = fetch_all_concurrent(client, product_ids, recipe_ids)

    # Filter out exceptions
    clean_products = {
        pid: pdata for pid, pdata in results.get("products", {}).items() if not isinstance(pdata, Exception)
    }
    clean_recipes = {
        rid: rdata for rid, rdata in results.get("recipes", {}).items() if not isinstance(rdata, Exception)
    }

    output_data = {"products": clean_products, "recipes": clean_recipes}
    to_json(output_data, args.output)
    print_stderr(f"Products saved to {args.output} ({len(clean_products)} products, {len(clean_recipes)} recipes)")
    return 0


def cmd_summary(args):
    """Handle the summary subcommand."""
    from yazio_exporter.analytics import (
        calculate_calorie_stats,
        calculate_exercise_stats,
        calculate_macro_ratios,
        calculate_meal_distribution,
        calculate_weight_calorie_correlation,
        calculate_weight_trend,
        rank_products_by_frequency,
    )
    from yazio_exporter.formatters import to_table

    # Load days data
    with open(args.from_file) as f:
        days_data = json.load(f)

    analytics = {}

    # Calorie stats
    analytics["calorie_stats"] = calculate_calorie_stats(days_data)
    analytics["macro_ratios"] = calculate_macro_ratios(days_data)

    # Meal distribution from daily_summary data
    summary_data = {}
    for date_str, day_info in days_data.items():
        if isinstance(day_info, dict) and "daily_summary" in day_info:
            summary_data[date_str] = day_info["daily_summary"]
    analytics["meal_distribution"] = calculate_meal_distribution(summary_data)

    # Exercise stats
    exercise_data = {}
    for date_str, day_info in days_data.items():
        if isinstance(day_info, dict) and "exercises" in day_info:
            exercise_data[date_str] = day_info["exercises"]
    analytics["exercise_stats"] = calculate_exercise_stats(exercise_data)

    # Weight trend (if weight file provided)
    if args.weight:
        with open(args.weight) as f:
            weight_raw = json.load(f)
        # Convert {date: weight} to [{date, weight}]
        if isinstance(weight_raw, dict):
            weight_list = [{"date": d, "weight": w} for d, w in sorted(weight_raw.items()) if w is not None]
        else:
            weight_list = weight_raw
        analytics["weight_trend"] = calculate_weight_trend(weight_list)
        analytics["weight_calorie_correlation"] = calculate_weight_calorie_correlation(weight_list, days_data)

    # Top products (if products file provided)
    if args.products:
        with open(args.products) as f:
            products_data = json.load(f)
        products_lookup = products_data.get("products", {})
        analytics["top_products"] = rank_products_by_frequency(days_data, products_lookup)

    # Output
    fmt = args.format
    if fmt == "table":
        print(to_table(analytics))
    elif fmt == "json":
        print(json.dumps(analytics, indent=2, sort_keys=True))
    elif fmt == "csv":
        # For CSV summary, just output JSON (summary is not tabular)
        print(json.dumps(analytics, indent=2, sort_keys=True))

    return 0


def cmd_export_all(args):
    """Handle the export-all subcommand."""
    from yazio_exporter.auth import login
    from yazio_exporter.client import YazioClient
    from yazio_exporter.export_all import export_all, print_summary

    print_stderr(f"Logging in as {args.email}...")
    token = login(args.email, args.password)

    client = YazioClient()
    client.set_token(token)

    stats = export_all(client, args.output, format=args.format)
    print_summary(stats)
    return 0


def cmd_report(args):
    """Handle the report subcommand."""
    import os

    from yazio_exporter.generate_reports import generate_analysis, generate_llm_prompt

    output_dir = args.dir

    required = ["days.json", "weight.json", "products.json", "profile.json"]
    for fname in required:
        path = os.path.join(output_dir, fname)
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} not found. Run 'export-all' first.")

    def load_json(path):
        with open(path) as f:
            return json.load(f)

    days = load_json(os.path.join(output_dir, "days.json"))
    weight = load_json(os.path.join(output_dir, "weight.json"))
    products = load_json(os.path.join(output_dir, "products.json"))
    profile = load_json(os.path.join(output_dir, "profile.json"))

    if args.start:
        validate_date(args.start)
    if args.end:
        validate_date(args.end)
    if args.start and args.end:
        validate_date_range(args.start, args.end)

    if args.start or args.end:
        days = {
            d: v for d, v in days.items() if (not args.start or d >= args.start) and (not args.end or d <= args.end)
        }
        weight = {
            d: w for d, w in weight.items() if (not args.start or d >= args.start) and (not args.end or d <= args.end)
        }

    analysis = generate_analysis(days, weight, products, profile)
    analysis_path = os.path.join(output_dir, "analysis.md")
    with open(analysis_path, "w") as f:
        f.write(analysis)
    print_stderr(f"Saved {analysis_path}")

    prompt = generate_llm_prompt(days, weight, products, profile)
    prompt_path = os.path.join(output_dir, "llm_prompt.txt")
    with open(prompt_path, "w") as f:
        f.write(prompt)
    print_stderr(f"Saved {prompt_path}")

    print_stderr("\nCopy llm_prompt.txt and paste into any LLM for analysis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
