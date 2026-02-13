"""
Data models for API responses.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DailyNutrients:
    """Daily nutrition summary from nutrients-daily endpoint."""

    date: str
    energy: float
    carb: float
    protein: float
    fat: float
    energy_goal: float | None = None


@dataclass
class ConsumedItems:
    """Consumed items for a day."""

    products: list[dict[str, Any]] = field(default_factory=list)
    recipe_portions: list[dict[str, Any]] = field(default_factory=list)
    simple_products: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Goals:
    """Daily goals."""

    data: dict[str, float] = field(default_factory=dict)


@dataclass
class Exercises:
    """Exercise data for a day."""

    training: list[dict[str, Any]] = field(default_factory=list)
    custom_training: list[dict[str, Any]] = field(default_factory=list)
    activity: dict[str, Any] | None = None


@dataclass
class WaterIntake:
    """Water intake for a day."""

    water_intake: int = 0
    gateway: str | None = None
    source: str | None = None


@dataclass
class DailySummary:
    """Comprehensive daily summary with meal breakdowns."""

    meals: dict[str, dict[str, Any]] = field(default_factory=dict)
    activity_energy: float | None = None
    steps: int | None = None
    water_intake: int | None = None
    goals: dict[str, float] = field(default_factory=dict)
    units: dict[str, str] = field(default_factory=dict)
