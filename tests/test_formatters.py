"""
Tests for output formatters.
"""

import csv
import json
import sqlite3

import pytest

from yazio_exporter.formatters import (
    create_sqlite_schema,
    to_csv_consumed,
    to_csv_days,
    to_csv_nutrients,
    to_csv_products,
    to_csv_weight,
    to_json,
    to_sqlite,
    to_table,
)


class TestJsonFormatter:
    """Tests for JSON formatter (Features #40, #41)."""

    def test_produces_pretty_printed_output(self, tmp_path):
        """Verify JSON output is readable with indent=2 (Feature #40)."""
        output_file = tmp_path / "output.json"
        data = {"name": "Test", "value": 123, "nested": {"key": "value"}}

        to_json(data, str(output_file))

        # Read the file and verify it has indentation
        with open(output_file) as f:
            content = f.read()

        # Pretty-printed JSON should have newlines and indentation
        assert "\n" in content
        assert "  " in content  # 2-space indent

        # Verify it's valid JSON
        parsed = json.loads(content)
        assert parsed["name"] == "Test"
        assert parsed["value"] == 123
        assert parsed["nested"]["key"] == "value"

    def test_round_trip_parsing(self, tmp_path):
        """Verify JSON can be parsed back (Feature #40)."""
        output_file = tmp_path / "output.json"
        data = {
            "days": [
                {"date": "2024-01-15", "energy": 2000.0},
                {"date": "2024-01-16", "energy": 1800.0},
            ],
            "products": [{"product_id": "123", "name": "Apple"}],
        }

        to_json(data, str(output_file))

        # Parse it back
        with open(output_file) as f:
            parsed = json.load(f)

        # Verify data integrity
        assert parsed == data
        assert len(parsed["days"]) == 2
        assert parsed["products"][0]["name"] == "Apple"

    def test_sorts_date_keys_chronologically(self, tmp_path):
        """Verify dates are sorted in chronological order (Feature #41)."""
        output_file = tmp_path / "output.json"
        # Create data with dates in random order
        data = {
            "2024-01-20": {"energy": 2000.0},
            "2024-01-15": {"energy": 1800.0},
            "2024-01-18": {"energy": 1900.0},
        }

        to_json(data, str(output_file))

        # Read the JSON string to check key order
        with open(output_file) as f:
            content = f.read()

        # Find positions of dates in the string
        pos_15 = content.find("2024-01-15")
        pos_18 = content.find("2024-01-18")
        pos_20 = content.find("2024-01-20")

        # All dates should be present
        assert pos_15 != -1
        assert pos_18 != -1
        assert pos_20 != -1

        # Dates should appear in sorted order
        assert pos_15 < pos_18 < pos_20

    def test_sorts_all_keys_alphabetically(self, tmp_path):
        """Verify all keys are sorted, not just dates (Feature #41)."""
        output_file = tmp_path / "output.json"
        data = {"zebra": 1, "apple": 2, "mango": 3, "banana": 4}

        to_json(data, str(output_file))

        # Read and parse to verify
        with open(output_file) as f:
            content = f.read()

        # Check key order in the string
        pos_apple = content.find('"apple"')
        pos_banana = content.find('"banana"')
        pos_mango = content.find('"mango"')
        pos_zebra = content.find('"zebra"')

        # Keys should appear in alphabetical order
        assert pos_apple < pos_banana < pos_mango < pos_zebra


class TestCsvProducts:
    """Tests for CSV products formatter (Feature #46)."""

    def test_creates_correct_header(self, tmp_path):
        """Verify CSV has correct header row."""
        output_file = tmp_path / "products.csv"
        data = [
            {
                "product_id": "123",
                "name": "Apple",
                "category": "Fruits",
                "energy_per_100g": 52.0,
                "carb_per_100g": 14.0,
                "protein_per_100g": 0.3,
                "fat_per_100g": 0.2,
            }
        ]

        to_csv_products(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == [
                "product_id",
                "name",
                "category",
                "energy_per_100g",
                "carb_per_100g",
                "protein_per_100g",
                "fat_per_100g",
            ]

    def test_exports_product_data(self, tmp_path):
        """Verify product data is exported correctly."""
        output_file = tmp_path / "products.csv"
        data = [
            {
                "product_id": "123",
                "name": "Apple",
                "category": "Fruits",
                "energy_per_100g": 52.0,
                "carb_per_100g": 14.0,
                "protein_per_100g": 0.3,
                "fat_per_100g": 0.2,
            },
            {
                "product_id": "456",
                "name": "Banana",
                "category": "Fruits",
                "energy_per_100g": 89.0,
                "carb_per_100g": 23.0,
                "protein_per_100g": 1.1,
                "fat_per_100g": 0.3,
            },
        ]

        to_csv_products(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            assert len(rows) == 2
            assert rows[0] == ["123", "Apple", "Fruits", "52.0", "14.0", "0.3", "0.2"]
            assert rows[1] == ["456", "Banana", "Fruits", "89.0", "23.0", "1.1", "0.3"]

    def test_handles_empty_data(self, tmp_path):
        """Verify empty data creates CSV with header only."""
        output_file = tmp_path / "products.csv"
        data = []

        to_csv_products(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 1  # Header only
            assert rows[0] == [
                "product_id",
                "name",
                "category",
                "energy_per_100g",
                "carb_per_100g",
                "protein_per_100g",
                "fat_per_100g",
            ]

    def test_handles_missing_fields(self, tmp_path):
        """Verify missing fields are handled gracefully."""
        output_file = tmp_path / "products.csv"
        data = [
            {
                "product_id": "123",
                "name": "Apple",
                # Missing other fields
            }
        ]

        to_csv_products(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)
            assert row[0] == "123"  # product_id
            assert row[1] == "Apple"  # name
            assert row[2] == ""  # category (missing)
            assert row[3] == ""  # energy_per_100g (missing)


class TestCsvDays:
    """Tests for CSV days formatter (Feature #42)."""

    def test_creates_correct_header(self, tmp_path):
        """Verify CSV has correct header row (Feature #42)."""
        output_file = tmp_path / "days.csv"
        data = {
            "2024-01-15": {
                "energy": 2000.0,
                "carb": 250.0,
                "protein": 80.0,
                "fat": 70.0,
                "energy_goal": 2200.0,
                "water_intake": 2000,
                "steps": 8000,
            }
        }

        to_csv_days(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == [
                "date",
                "energy",
                "carb",
                "protein",
                "fat",
                "energy_goal",
                "water_intake",
                "steps",
            ]

    def test_exports_days_data(self, tmp_path):
        """Verify days data is exported correctly (Feature #42)."""
        output_file = tmp_path / "days.csv"
        data = {
            "2024-01-15": {
                "energy": 2000.0,
                "carb": 250.0,
                "protein": 80.0,
                "fat": 70.0,
                "energy_goal": 2200.0,
                "water_intake": 2000,
                "steps": 8000,
            },
            "2024-01-16": {
                "energy": 1800.0,
                "carb": 220.0,
                "protein": 75.0,
                "fat": 65.0,
                "energy_goal": 2200.0,
                "water_intake": 1800,
                "steps": 7500,
            },
        }

        to_csv_days(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            assert len(rows) == 2
            assert rows[0] == [
                "2024-01-15",
                "2000.0",
                "250.0",
                "80.0",
                "70.0",
                "2200.0",
                "2000",
                "8000",
            ]
            assert rows[1] == [
                "2024-01-16",
                "1800.0",
                "220.0",
                "75.0",
                "65.0",
                "2200.0",
                "1800",
                "7500",
            ]

    def test_sorts_dates_chronologically(self, tmp_path):
        """Verify dates are sorted chronologically in CSV output (Feature #42)."""
        output_file = tmp_path / "days.csv"
        # Create data with dates in random order
        data = {
            "2024-01-20": {
                "energy": 2100.0,
                "carb": 260.0,
                "protein": 85.0,
                "fat": 72.0,
            },
            "2024-01-15": {
                "energy": 2000.0,
                "carb": 250.0,
                "protein": 80.0,
                "fat": 70.0,
            },
            "2024-01-18": {
                "energy": 1900.0,
                "carb": 240.0,
                "protein": 78.0,
                "fat": 68.0,
            },
        }

        to_csv_days(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            # Dates should be sorted chronologically
            assert rows[0][0] == "2024-01-15"
            assert rows[1][0] == "2024-01-18"
            assert rows[2][0] == "2024-01-20"

    def test_handles_missing_fields(self, tmp_path):
        """Verify missing fields are handled gracefully (Feature #42)."""
        output_file = tmp_path / "days.csv"
        data = {
            "2024-01-15": {
                "energy": 2000.0,
                "carb": 250.0,
                # Missing protein, fat, energy_goal, water_intake, steps
            }
        }

        to_csv_days(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)
            assert row[0] == "2024-01-15"  # date
            assert row[1] == "2000.0"  # energy
            assert row[2] == "250.0"  # carb
            assert row[3] == ""  # protein (missing)
            assert row[4] == ""  # fat (missing)
            assert row[5] == ""  # energy_goal (missing)
            assert row[6] == ""  # water_intake (missing)
            assert row[7] == ""  # steps (missing)

    def test_numeric_formatting(self, tmp_path):
        """Verify numeric values are formatted correctly (Feature #42)."""
        output_file = tmp_path / "days.csv"
        data = {
            "2024-01-15": {
                "energy": 2000.5,
                "carb": 250.75,
                "protein": 80.25,
                "fat": 70.125,
                "energy_goal": 2200.0,
                "water_intake": 2000,
                "steps": 8000,
            }
        }

        to_csv_days(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

            # Floats should preserve decimal values
            assert row[1] == "2000.5"
            assert row[2] == "250.75"
            assert row[3] == "80.25"
            assert row[4] == "70.125"
            # Integers should be represented as integers
            assert row[6] == "2000"
            assert row[7] == "8000"


class TestCsvNutrients:
    """Tests for CSV nutrients formatter (Feature #45)."""

    def test_creates_correct_header(self, tmp_path):
        """Verify CSV has header: date,nutrient_id,value."""
        output_file = tmp_path / "nutrients.csv"
        data = {"vitamin.d": {"2024-01-15": 0.005}}

        to_csv_nutrients(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ["date", "nutrient_id", "value"]

    def test_long_format_one_row_per_nutrient_day(self, tmp_path):
        """Verify one row per nutrient per day (long format)."""
        output_file = tmp_path / "nutrients.csv"
        data = {
            "vitamin.d": {"2024-01-15": 0.005, "2024-01-16": 0.003},
            "mineral.iron": {"2024-01-15": 15.2},
        }

        to_csv_nutrients(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            # Should have 3 rows total (2 for vitamin.d + 1 for mineral.iron)
            assert len(rows) == 3

    def test_correct_data_format(self, tmp_path):
        """Verify format: date,nutrient_id,value."""
        output_file = tmp_path / "nutrients.csv"
        data = {"vitamin.d": {"2024-01-15": 0.005}}

        to_csv_nutrients(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

            assert row[0] == "2024-01-15"  # date
            assert row[1] == "vitamin.d"  # nutrient_id
            assert row[2] == "0.005"  # value

    def test_sorts_by_date_then_nutrient(self, tmp_path):
        """Verify rows are sorted by date first, then nutrient_id."""
        output_file = tmp_path / "nutrients.csv"
        data = {
            "vitamin.d": {"2024-01-20": 0.005, "2024-01-15": 0.003},
            "mineral.iron": {"2024-01-15": 15.2, "2024-01-20": 18.0},
        }

        to_csv_nutrients(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            # Should be sorted by date first
            assert rows[0][0] == "2024-01-15"  # First date
            assert rows[1][0] == "2024-01-15"  # First date
            assert rows[2][0] == "2024-01-20"  # Second date
            assert rows[3][0] == "2024-01-20"  # Second date

            # Within same date, sorted by nutrient_id
            assert rows[0][1] == "mineral.iron"  # 'm' comes before 'v'
            assert rows[1][1] == "vitamin.d"
            assert rows[2][1] == "mineral.iron"
            assert rows[3][1] == "vitamin.d"

    def test_handles_empty_data(self, tmp_path):
        """Verify empty data creates CSV with header only."""
        output_file = tmp_path / "nutrients.csv"
        data = {}

        to_csv_nutrients(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 1  # Header only
            assert rows[0] == ["date", "nutrient_id", "value"]

    def test_handles_multiple_nutrients(self, tmp_path):
        """Verify handling of many nutrients across multiple days."""
        output_file = tmp_path / "nutrients.csv"
        data = {
            "vitamin.a": {"2024-01-15": 800.0, "2024-01-16": 750.0},
            "vitamin.d": {"2024-01-15": 0.005, "2024-01-16": 0.006},
            "mineral.iron": {"2024-01-15": 15.2, "2024-01-16": 14.8},
            "mineral.calcium": {"2024-01-15": 1000.0, "2024-01-16": 950.0},
        }

        to_csv_nutrients(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            # 4 nutrients × 2 days = 8 rows
            assert len(rows) == 8

            # Verify all nutrients are present
            nutrient_ids = {row[1] for row in rows}
            assert nutrient_ids == {
                "vitamin.a",
                "vitamin.d",
                "mineral.iron",
                "mineral.calcium",
            }

            # Verify all dates are present
            dates = {row[0] for row in rows}
            assert dates == {"2024-01-15", "2024-01-16"}


class TestCsvConsumed:
    """Tests for CSV consumed items formatter (Feature #43)."""

    def test_creates_correct_header(self, tmp_path):
        """Verify CSV has correct header row (Feature #43)."""
        output_file = tmp_path / "consumed.csv"
        days_data = {"2024-01-15": {"consumed": {"products": [], "recipe_portions": []}}}
        products_data = {"products": {}, "recipes": {}}

        to_csv_consumed(days_data, products_data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == [
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

    def test_flattens_consumed_items_to_rows(self, tmp_path):
        """Verify each consumed item becomes one row (Feature #43)."""
        output_file = tmp_path / "consumed.csv"
        days_data = {
            "2024-01-15": {
                "consumed": {
                    "products": [
                        {
                            "product_id": "prod-123",
                            "daytime": "breakfast",
                            "amount": 100,
                            "serving": "gram",
                        },
                        {
                            "product_id": "prod-456",
                            "daytime": "lunch",
                            "amount": 50,
                            "serving": "gram",
                        },
                    ],
                    "recipe_portions": [],
                }
            }
        }
        products_data = {"products": {}, "recipes": {}}

        to_csv_consumed(days_data, products_data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            assert len(rows) == 2
            assert rows[0][0] == "2024-01-15"  # date
            assert rows[0][1] == "breakfast"  # daytime
            assert rows[0][2] == "prod-123"  # product_id
            assert rows[1][2] == "prod-456"  # product_id

    def test_joins_product_details(self, tmp_path):
        """Verify product data is joined correctly (Feature #43)."""
        output_file = tmp_path / "consumed.csv"
        days_data = {
            "2024-01-15": {
                "consumed": {
                    "products": [
                        {
                            "product_id": "prod-123",
                            "daytime": "breakfast",
                            "amount": 100,
                            "serving": "gram",
                        }
                    ],
                    "recipe_portions": [],
                }
            }
        }
        products_data = {
            "products": {
                "prod-123": {
                    "name": "Apple",
                    "nutrients": {
                        "energy.energy": 52.0,
                        "nutrient.carb": 14.0,
                        "nutrient.protein": 0.3,
                        "nutrient.fat": 0.2,
                    },
                }
            },
            "recipes": {},
        }

        to_csv_consumed(days_data, products_data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

            assert row[3] == "Apple"  # product_name
            assert row[6] == "52.0"  # energy (100g * 52.0/100g)
            assert row[7] == "14.0"  # carb
            assert row[8] == "0.3"  # protein
            assert row[9] == "0.2"  # fat

    def test_scales_nutrients_by_amount(self, tmp_path):
        """Verify nutrients are scaled by amount (Feature #43)."""
        output_file = tmp_path / "consumed.csv"
        days_data = {
            "2024-01-15": {
                "consumed": {
                    "products": [
                        {
                            "product_id": "prod-123",
                            "daytime": "breakfast",
                            "amount": 50,  # Half of 100g
                            "serving": "gram",
                        }
                    ],
                    "recipe_portions": [],
                }
            }
        }
        products_data = {
            "products": {
                "prod-123": {
                    "name": "Apple",
                    "nutrients": {
                        "energy.energy": 52.0,  # Per 100g
                        "nutrient.carb": 14.0,
                        "nutrient.protein": 0.3,
                        "nutrient.fat": 0.2,
                    },
                }
            },
            "recipes": {},
        }

        to_csv_consumed(days_data, products_data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

            # Should be half of the per-100g values
            assert float(row[6]) == 26.0  # energy
            assert float(row[7]) == 7.0  # carb
            assert float(row[8]) == 0.15  # protein
            assert float(row[9]) == 0.1  # fat

    def test_includes_recipe_portions(self, tmp_path):
        """Verify recipe portions are included (Feature #43)."""
        output_file = tmp_path / "consumed.csv"
        days_data = {
            "2024-01-15": {
                "consumed": {
                    "products": [],
                    "recipe_portions": [
                        {
                            "recipe_id": "recipe-789",
                            "daytime": "dinner",
                            "portion_count": 2,
                        }
                    ],
                }
            }
        }
        products_data = {
            "products": {},
            "recipes": {
                "recipe-789": {
                    "name": "Pasta Carbonara",
                    "nutrients": {
                        "energy.energy": 400.0,  # Per portion
                        "nutrient.carb": 50.0,
                        "nutrient.protein": 15.0,
                        "nutrient.fat": 12.0,
                    },
                }
            },
        }

        to_csv_consumed(days_data, products_data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

            assert row[2] == "recipe-789"  # product_id (recipe_id)
            assert row[3] == "Pasta Carbonara"  # product_name (recipe name)
            assert row[4] == "2"  # amount (portion_count)
            assert row[5] == "portion"  # serving
            # Nutrients scaled by portion_count
            assert float(row[6]) == 800.0  # energy
            assert float(row[7]) == 100.0  # carb
            assert float(row[8]) == 30.0  # protein
            assert float(row[9]) == 24.0  # fat

    def test_sorts_by_date_and_daytime(self, tmp_path):
        """Verify rows are sorted by date then daytime (Feature #43)."""
        output_file = tmp_path / "consumed.csv"
        days_data = {
            "2024-01-16": {
                "consumed": {
                    "products": [
                        {
                            "product_id": "p1",
                            "daytime": "breakfast",
                            "amount": 100,
                            "serving": "g",
                        }
                    ],
                    "recipe_portions": [],
                }
            },
            "2024-01-15": {
                "consumed": {
                    "products": [
                        {
                            "product_id": "p2",
                            "daytime": "lunch",
                            "amount": 100,
                            "serving": "g",
                        },
                        {
                            "product_id": "p3",
                            "daytime": "breakfast",
                            "amount": 100,
                            "serving": "g",
                        },
                    ],
                    "recipe_portions": [],
                }
            },
        }
        products_data = {"products": {}, "recipes": {}}

        to_csv_consumed(days_data, products_data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            # Should be sorted by date first, then daytime
            assert rows[0][0] == "2024-01-15"
            assert rows[0][1] == "breakfast"
            assert rows[1][0] == "2024-01-15"
            assert rows[1][1] == "lunch"
            assert rows[2][0] == "2024-01-16"
            assert rows[2][1] == "breakfast"

    def test_handles_missing_product_details(self, tmp_path):
        """Verify missing product details are handled gracefully (Feature #43)."""
        output_file = tmp_path / "consumed.csv"
        days_data = {
            "2024-01-15": {
                "consumed": {
                    "products": [
                        {
                            "product_id": "unknown-prod",
                            "daytime": "breakfast",
                            "amount": 100,
                            "serving": "gram",
                        }
                    ],
                    "recipe_portions": [],
                }
            }
        }
        products_data = {"products": {}, "recipes": {}}  # Product not in lookup

        to_csv_consumed(days_data, products_data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

            assert row[2] == "unknown-prod"  # product_id
            assert row[3] == ""  # product_name (missing)
            assert row[6] == ""  # energy (missing)
            assert row[7] == ""  # carb (missing)


class TestCsvWeight:
    """Tests for CSV weight formatter (Feature #44)."""

    def test_creates_correct_header(self, tmp_path):
        """Verify CSV has correct header row (Feature #44)."""
        output_file = tmp_path / "weight.csv"
        data = [{"date": "2024-01-15", "weight": 75.5, "body_fat": 18.5, "waist": 85.0}]

        to_csv_weight(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ["date", "weight", "body_fat", "waist"]

    def test_exports_weight_data(self, tmp_path):
        """Verify weight data is exported correctly (Feature #44)."""
        output_file = tmp_path / "weight.csv"
        data = [
            {"date": "2024-01-15", "weight": 75.5, "body_fat": 18.5, "waist": 85.0},
            {"date": "2024-01-16", "weight": 75.3, "body_fat": 18.4, "waist": 84.8},
        ]

        to_csv_weight(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            assert len(rows) == 2
            assert rows[0] == ["2024-01-15", "75.5", "18.5", "85.0"]
            assert rows[1] == ["2024-01-16", "75.3", "18.4", "84.8"]

    def test_handles_null_values(self, tmp_path):
        """Verify null values are empty strings (Feature #44)."""
        output_file = tmp_path / "weight.csv"
        data = [
            {
                "date": "2024-01-15",
                "weight": 75.5,
                # Missing body_fat and waist
            },
            {
                "date": "2024-01-16",
                "weight": 75.3,
                "body_fat": 18.4,
                # Missing waist
            },
        ]

        to_csv_weight(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            # First row has only weight
            assert rows[0][0] == "2024-01-15"
            assert rows[0][1] == "75.5"
            assert rows[0][2] == ""  # body_fat (missing)
            assert rows[0][3] == ""  # waist (missing)

            # Second row has weight and body_fat
            assert rows[1][0] == "2024-01-16"
            assert rows[1][1] == "75.3"
            assert rows[1][2] == "18.4"
            assert rows[1][3] == ""  # waist (missing)

    def test_sorts_by_date(self, tmp_path):
        """Verify rows are sorted by date (Feature #44)."""
        output_file = tmp_path / "weight.csv"
        # Create data in random order
        data = [
            {"date": "2024-01-18", "weight": 75.0},
            {"date": "2024-01-15", "weight": 75.5},
            {"date": "2024-01-20", "weight": 74.8},
            {"date": "2024-01-16", "weight": 75.3},
        ]

        to_csv_weight(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

            # Should be sorted chronologically
            assert rows[0][0] == "2024-01-15"
            assert rows[1][0] == "2024-01-16"
            assert rows[2][0] == "2024-01-18"
            assert rows[3][0] == "2024-01-20"

    def test_handles_empty_data(self, tmp_path):
        """Verify empty data creates CSV with header only (Feature #44)."""
        output_file = tmp_path / "weight.csv"
        data = []

        to_csv_weight(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 1  # Header only
            assert rows[0] == ["date", "weight", "body_fat", "waist"]

    def test_preserves_decimal_precision(self, tmp_path):
        """Verify decimal values are preserved correctly (Feature #44)."""
        output_file = tmp_path / "weight.csv"
        data = [
            {
                "date": "2024-01-15",
                "weight": 75.567,
                "body_fat": 18.432,
                "waist": 85.123,
            }
        ]

        to_csv_weight(data, str(output_file))

        with open(output_file) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

            assert row[1] == "75.567"
            assert row[2] == "18.432"
            assert row[3] == "85.123"


class TestSqliteFormatters:
    """Tests for SQLite formatters (Features #47, #48, #49)."""

    def test_schema_creates_all_required_tables(self, tmp_path):
        """Verify schema creation creates all required tables (Feature #47)."""
        db_path = tmp_path / "test.db"

        # Step 1: Call create_sqlite_schema()
        create_sqlite_schema(str(db_path))

        # Step 2: Verify database file is created
        assert db_path.exists()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Step 3: Query sqlite_master for table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        # Step 4: Verify expected tables exist
        expected_tables = {
            "users",
            "days",
            "consumed_items",
            "products",
            "recipes",
            "goals",
            "exercises",
            "water_intake",
            "weight_log",
            "nutrient_daily",
            "daily_summary",
        }

        assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

        # Verify each individual table
        assert "users" in tables
        assert "days" in tables
        assert "consumed_items" in tables
        assert "products" in tables
        assert "recipes" in tables
        assert "goals" in tables
        assert "exercises" in tables
        assert "water_intake" in tables
        assert "weight_log" in tables
        assert "nutrient_daily" in tables
        assert "daily_summary" in tables

        # Step 5: Verify at least 10 tables are present
        assert len(tables) >= 10, f"Expected at least 10 tables, got {len(tables)}: {tables}"

        conn.close()

    def test_schema_creates_tables(self, tmp_path):
        """Verify schema creation creates all tables."""
        db_path = tmp_path / "test.db"

        create_sqlite_schema(str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        assert "days" in tables
        assert "products" in tables
        assert "consumed_items" in tables

        conn.close()

    def test_foreign_keys_exist(self, tmp_path):
        """Verify foreign key constraints are created (Feature #49)."""
        db_path = tmp_path / "test.db"

        create_sqlite_schema(str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check foreign keys on consumed_items
        cursor.execute("PRAGMA foreign_key_list(consumed_items)")
        fks = cursor.fetchall()

        # Should have 2 foreign keys
        assert len(fks) == 2

        # Extract referenced tables
        fk_tables = {fk[2] for fk in fks}  # Column 2 is the referenced table
        assert "days" in fk_tables
        assert "products" in fk_tables

        conn.close()

    def test_indexes_created_for_performance(self, tmp_path):
        """Verify indexes are created on date columns (Feature #50)."""
        db_path = tmp_path / "test.db"

        # Step 1: Create schema
        create_sqlite_schema(str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Step 2: Query sqlite_master for indexes
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
        indexes = cursor.fetchall()

        # Convert to dict for easier checking
        index_dict = {row[0]: row[1] for row in indexes}

        # Verify indexes on non-PK date columns (PK columns are auto-indexed)
        assert "idx_consumed_items_date" in index_dict
        assert index_dict["idx_consumed_items_date"] == "consumed_items"

        assert "idx_nutrient_daily_date" in index_dict
        assert index_dict["idx_nutrient_daily_date"] == "nutrient_daily"

        assert "idx_exercises_date" in index_dict
        assert index_dict["idx_exercises_date"] == "exercises"

        # Redundant indexes on PK columns (days, weight_log, goals, water_intake)
        # are not created — SQLite auto-indexes PRIMARY KEY columns
        assert "idx_days_date" not in index_dict
        assert "idx_weight_log_date" not in index_dict
        assert "idx_goals_date" not in index_dict
        assert "idx_water_intake_date" not in index_dict

        conn.close()

    def test_inserts_days_data(self, tmp_path):
        """Verify days data is inserted correctly (Feature #48)."""
        db_path = tmp_path / "test.db"
        data = {
            "days": [
                {
                    "date": "2024-01-15",
                    "energy": 2000.0,
                    "carb": 250.0,
                    "protein": 80.0,
                    "fat": 70.0,
                    "energy_goal": 2200.0,
                }
            ]
        }

        to_sqlite(data, str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM days")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][0] == "2024-01-15"  # date
        assert rows[0][1] == 2000.0  # energy
        assert rows[0][2] == 250.0  # carb

        conn.close()

    def test_inserts_products_data(self, tmp_path):
        """Verify products data is inserted correctly (Feature #48)."""
        db_path = tmp_path / "test.db"
        data = {
            "products": [
                {
                    "product_id": "123",
                    "name": "Apple",
                    "category": "Fruits",
                    "energy_per_100g": 52.0,
                    "carb_per_100g": 14.0,
                    "protein_per_100g": 0.3,
                    "fat_per_100g": 0.2,
                }
            ]
        }

        to_sqlite(data, str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][0] == "123"  # product_id
        assert rows[0][1] == "Apple"  # name
        assert rows[0][3] == 52.0  # energy_per_100g

        conn.close()

    def test_inserts_consumed_items_with_fk(self, tmp_path):
        """Verify consumed items are inserted with foreign keys (Feature #48)."""
        db_path = tmp_path / "test.db"
        data = {
            "days": [
                {
                    "date": "2024-01-15",
                    "energy": 2000.0,
                    "carb": 250.0,
                    "protein": 80.0,
                    "fat": 70.0,
                }
            ],
            "products": [
                {
                    "product_id": "123",
                    "name": "Apple",
                    "category": "Fruits",
                    "energy_per_100g": 52.0,
                    "carb_per_100g": 14.0,
                    "protein_per_100g": 0.3,
                    "fat_per_100g": 0.2,
                }
            ],
            "consumed_items": [
                {
                    "date": "2024-01-15",
                    "product_id": "123",
                    "amount": 150.0,
                    "energy": 78.0,
                }
            ],
        }

        to_sqlite(data, str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM consumed_items")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][1] == "2024-01-15"  # date (FK to days)
        assert rows[0][2] == "123"  # product_id (FK to products)
        assert rows[0][3] == 150.0  # amount

        conn.close()

    def test_foreign_key_constraint_enforced(self, tmp_path):
        """Verify FK constraint prevents invalid inserts (Feature #49)."""
        db_path = tmp_path / "test.db"
        data = {
            "products": [
                {
                    "product_id": "123",
                    "name": "Apple",
                    "category": "Fruits",
                    "energy_per_100g": 52.0,
                    "carb_per_100g": 14.0,
                    "protein_per_100g": 0.3,
                    "fat_per_100g": 0.2,
                }
            ],
            "consumed_items": [
                {
                    "date": "2024-01-15",  # This date doesn't exist in days table
                    "product_id": "123",
                    "amount": 150.0,
                    "energy": 78.0,
                }
            ],
        }

        # Should raise an error due to FK constraint violation
        with pytest.raises(sqlite3.IntegrityError):
            to_sqlite(data, str(db_path))

    def test_handles_empty_data(self, tmp_path):
        """Verify empty data creates schema without errors."""
        db_path = tmp_path / "test.db"
        data = {}

        to_sqlite(data, str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Tables should exist but be empty
        cursor.execute("SELECT COUNT(*) FROM days")
        assert cursor.fetchone()[0] == 0

        cursor.execute("SELECT COUNT(*) FROM products")
        assert cursor.fetchone()[0] == 0

        cursor.execute("SELECT COUNT(*) FROM consumed_items")
        assert cursor.fetchone()[0] == 0

        conn.close()


class TestTableFormatter:
    """Tests for table formatter (Feature #69)."""

    def test_table_structure_with_headers(self):
        """Verify table output has proper headers and structure."""
        data = {"calorie_stats": {"avg": 2000.5, "min": 1500.0, "max": 2500.0}}

        result = to_table(data)

        # Verify table has headers
        assert "YAZIO EXPORT SUMMARY" in result
        assert "CALORIE STATISTICS" in result
        assert "=" * 60 in result
        assert "-" * 60 in result

    def test_table_has_calorie_stats(self):
        """Verify calorie statistics are formatted correctly."""
        data = {"calorie_stats": {"avg": 2123.4, "min": 1456.8, "max": 2890.1}}

        result = to_table(data)

        # Check calorie stats are present and formatted
        assert "Average Daily Intake:  2123.4 kcal" in result
        assert "Minimum Daily Intake:  1456.8 kcal" in result
        assert "Maximum Daily Intake:  2890.1 kcal" in result

    def test_table_has_macro_ratios(self):
        """Verify macro ratios are formatted correctly."""
        data = {"macro_ratios": {"carb_pct": 45.5, "protein_pct": 25.0, "fat_pct": 29.5}}

        result = to_table(data)

        assert "MACRONUTRIENT RATIOS" in result
        assert "Carbohydrates:  45.5%" in result
        assert "Protein:        25.0%" in result
        assert "Fat:            29.5%" in result

    def test_table_has_meal_distribution(self):
        """Verify meal distribution is formatted correctly."""
        data = {
            "meal_distribution": {
                "breakfast": 450.0,
                "lunch": 650.0,
                "dinner": 700.0,
                "snack": 200.0,
            }
        }

        result = to_table(data)

        assert "AVERAGE CALORIES PER MEAL" in result
        assert "Breakfast:  450.0 kcal" in result
        assert "Lunch:      650.0 kcal" in result
        assert "Dinner:     700.0 kcal" in result
        assert "Snacks:     200.0 kcal" in result

    def test_table_has_water_stats(self):
        """Verify water stats are formatted correctly."""
        data = {
            "water_stats": {
                "avg_intake": 2345.0,
                "days_meeting_goal": 15,
                "percentage": 75.5,
            }
        }

        result = to_table(data)

        assert "WATER INTAKE" in result
        assert "Average Daily Intake:      2345 ml" in result
        assert "Days Meeting Goal:         15" in result
        assert "Goal Achievement Rate:     75.5%" in result

    def test_table_has_weight_trend(self):
        """Verify weight trend is formatted correctly."""
        data = {
            "weight_trend": {
                "starting_weight": 85.5,
                "current_weight": 82.3,
                "total_change": -3.2,
                "weekly_avg_change": -0.4,
            }
        }

        result = to_table(data)

        assert "WEIGHT TREND" in result
        assert "Starting Weight:       85.5 kg" in result
        assert "Current Weight:        82.3 kg" in result
        assert "Total Change:          -3.2 kg" in result
        assert "Weekly Avg Change:     -0.40 kg/week" in result

    def test_table_has_weight_calorie_correlation(self):
        """Verify weight-calorie correlation is formatted correctly."""
        data = {
            "weight_calorie_correlation": {
                "correlation": 0.876,
                "trend_description": "weight decreasing with calorie deficit",
                "avg_deficit_surplus": -250.0,
            }
        }

        result = to_table(data)

        assert "WEIGHT-CALORIE CORRELATION" in result
        assert "Correlation:           0.876" in result
        assert "Trend:                 weight decreasing with calorie deficit" in result
        assert "Avg Deficit/Surplus:   -250 kcal" in result

    def test_table_has_exercise_stats(self):
        """Verify exercise stats are formatted correctly."""
        data = {
            "exercise_stats": {
                "total_sessions": 45,
                "total_calories": 15000,
                "most_frequent": "Running",
            }
        }

        result = to_table(data)

        assert "EXERCISE STATISTICS" in result
        assert "Total Sessions:        45" in result
        assert "Total Calories Burned: 15000 kcal" in result
        assert "Most Frequent:         Running" in result

    def test_table_has_top_products(self):
        """Verify top products are formatted correctly."""
        data = {
            "top_products": [
                {"product_id": "1", "product_name": "Banana", "count": 25},
                {"product_id": "2", "product_name": "Apple", "count": 20},
                {"product_id": "3", "product_name": "Chicken Breast", "count": 15},
            ]
        }

        result = to_table(data)

        assert "TOP 10 MOST CONSUMED PRODUCTS" in result
        assert "Banana" in result
        assert "(25 times)" in result
        assert "Apple" in result
        assert "(20 times)" in result
        assert "Chicken Breast" in result
        assert "(15 times)" in result

    def test_table_alignment_with_spaces(self):
        """Verify table has proper alignment with spaces."""
        data = {
            "calorie_stats": {"avg": 2000.0, "min": 1500.0, "max": 2500.0},
            "macro_ratios": {"carb_pct": 50.0, "protein_pct": 25.0, "fat_pct": 25.0},
        }

        result = to_table(data)

        # Verify lines have proper structure (not ragged)
        lines = result.split("\n")

        # Check section headers are separated
        assert any("CALORIE STATISTICS" in line for line in lines)
        assert any("MACRONUTRIENT RATIOS" in line for line in lines)

        # Check values are aligned with spaces (indented with 2 spaces)
        assert any(line.startswith("  ") and "kcal" in line for line in lines)
        assert any(line.startswith("  ") and "%" in line for line in lines)

    def test_table_readability_with_all_sections(self):
        """Verify complete table is human-readable with all sections."""
        data = {
            "calorie_stats": {"avg": 2000.0, "min": 1800.0, "max": 2200.0},
            "macro_ratios": {"carb_pct": 50.0, "protein_pct": 25.0, "fat_pct": 25.0},
            "meal_distribution": {
                "breakfast": 500.0,
                "lunch": 700.0,
                "dinner": 600.0,
                "snack": 200.0,
            },
            "water_stats": {
                "avg_intake": 2500.0,
                "days_meeting_goal": 20,
                "percentage": 80.0,
            },
            "weight_trend": {
                "starting_weight": 85.0,
                "current_weight": 82.0,
                "total_change": -3.0,
                "weekly_avg_change": -0.5,
            },
            "weight_calorie_correlation": {
                "correlation": 0.8,
                "trend_description": "weight decreasing",
                "avg_deficit_surplus": -200.0,
            },
            "exercise_stats": {
                "total_sessions": 30,
                "total_calories": 10000,
                "most_frequent": "Cycling",
            },
            "top_products": [{"product_id": "1", "product_name": "Banana", "count": 50}],
        }

        result = to_table(data)

        # Verify all sections are present
        assert "CALORIE STATISTICS" in result
        assert "MACRONUTRIENT RATIOS" in result
        assert "AVERAGE CALORIES PER MEAL" in result
        assert "WATER INTAKE" in result
        assert "WEIGHT TREND" in result
        assert "WEIGHT-CALORIE CORRELATION" in result
        assert "EXERCISE STATISTICS" in result
        assert "TOP 10 MOST CONSUMED PRODUCTS" in result

        # Verify separators create clear sections
        assert result.count("=" * 60) >= 2  # Header and footer
        assert result.count("-" * 60) >= 7  # Section separators

        # Verify output has newlines for readability
        lines = result.split("\n")
        assert len(lines) > 30  # Should have many lines for readability

    def test_table_handles_empty_data(self):
        """Verify table handles empty data gracefully."""
        data = {}

        result = to_table(data)

        # Should still have header and footer
        assert "YAZIO EXPORT SUMMARY" in result
        assert "=" * 60 in result

        # Should be a valid string
        assert isinstance(result, str)
        assert len(result) > 0

    def test_table_truncates_long_product_names(self):
        """Verify long product names are truncated for alignment."""
        data = {
            "top_products": [
                {
                    "product_id": "1",
                    "product_name": "This is a very long product name that should be truncated for table alignment",
                    "count": 10,
                }
            ]
        }

        result = to_table(data)

        # Product name should be truncated with ellipsis
        assert "..." in result
        # Should not exceed expected width
        lines = result.split("\n")
        product_lines = [line for line in lines if "times)" in line]
        assert len(product_lines) > 0
        # Line length should be reasonable (not exceeding 100 chars typically)
        for line in product_lines:
            assert len(line) < 100
