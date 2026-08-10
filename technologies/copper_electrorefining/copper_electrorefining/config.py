"""Planner thresholds for copper electrorefining cycle planning."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PlannerConfig:
    """Age/threshold rules for cathode pull and anode change queues."""

    # Default cathode cycle ~7 days.
    cathode_max_age_hours: float = 168.0
    # Default anode campaign ~21 days.
    anode_max_age_hours: float = 504.0
    # Optional ampere-hour threshold for cathode pull (if ampere_hours present).
    cathode_ampere_hours_threshold: float | None = None
