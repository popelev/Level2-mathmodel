"""Wave 2: simple copper KPI helpers."""

from __future__ import annotations

from copper_electrorefining.kpi import estimate_ampere_hours, estimate_cell_ampere_hours


def test_estimate_ampere_hours_from_current_and_time() -> None:
    assert estimate_ampere_hours(100.0, 2.5) == 250.0
    assert estimate_ampere_hours(28000.0, 10.0) == 280_000.0


def test_estimate_ampere_hours_missing_data_returns_none() -> None:
    assert estimate_ampere_hours(None, 2.0) is None
    assert estimate_ampere_hours(10.0, None) is None
    assert estimate_ampere_hours(None, None) is None


def test_estimate_cell_ampere_hours_uses_current_and_age() -> None:
    assert estimate_cell_ampere_hours(current_a=100.0, age_hours=3.0) == 300.0
    assert estimate_cell_ampere_hours(current_a=None, age_hours=3.0) is None
