"""
Centralized constants for the yazio-exporter package.
"""

__all__ = [
    "BASE_URL",
    "API_VERSION",
    "REQUEST_TIMEOUT",
    "MAX_RETRIES",
    "DEFAULT_WORKERS",
    "NUTRIENT_WORKERS",
    "DISCOVERY_LOOKBACK_YEARS",
    "BODY_MEASUREMENT_TYPES",
    "ALL_VITAMINS",
    "ALL_MINERALS",
]

BASE_URL = "https://yzapi.yazio.com"
API_VERSION = "v15"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
DEFAULT_WORKERS = 10
NUTRIENT_WORKERS = 5
DISCOVERY_LOOKBACK_YEARS = 5

BODY_MEASUREMENT_TYPES = ["body_fat", "waist", "hip", "chest"]

ALL_VITAMINS = [
    "vitamin.a",
    "vitamin.b1",
    "vitamin.b2",
    "vitamin.b3",
    "vitamin.b5",
    "vitamin.b6",
    "vitamin.b7",
    "vitamin.b11",
    "vitamin.b12",
    "vitamin.c",
    "vitamin.d",
    "vitamin.e",
    "vitamin.k",
]

ALL_MINERALS = [
    "mineral.calcium",
    "mineral.iron",
    "mineral.potassium",
    "mineral.magnesium",
    "mineral.phosphorus",
    "mineral.zinc",
    "mineral.copper",
    "mineral.manganese",
    "mineral.selenium",
    "mineral.iodine",
    "mineral.fluoride",
    "mineral.chlorine",
    "mineral.choline",
]
