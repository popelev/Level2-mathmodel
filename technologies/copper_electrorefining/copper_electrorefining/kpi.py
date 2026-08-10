"""Simple KPI helpers for copper electrorefining monitoring."""

from __future__ import annotations


def estimate_ampere_hours(
    current_a: float | None,
    time_hours: float | None,
) -> float | None:
    """Estimate ampere-hours as current * time when both values are present."""
    if current_a is None or time_hours is None:
        return None
    return float(current_a) * float(time_hours)


def estimate_cell_ampere_hours(
    current_a: float | None,
    age_hours: float | None,
) -> float | None:
    """Estimate delivered ampere-hours for a plate from cell current and age."""
    return estimate_ampere_hours(current_a, age_hours)
