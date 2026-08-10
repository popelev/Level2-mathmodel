"""Domain stubs for copper electrorefining plant topology."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Electrolyte:
    """Electrolyte condition snapshot for a cell (stub fields)."""

    temperature_c: float | None = None
    cu_gpl: float | None = None
    h2so4_gpl: float | None = None


@dataclass(slots=True)
class Anode:
    """Anode plate stub used by monitoring and change planning."""

    id: str
    age_hours: float | None = None
    mass_kg: float | None = None


@dataclass(slots=True)
class Cathode:
    """Cathode plate stub used by monitoring and pull planning."""

    id: str
    age_hours: float | None = None
    ampere_hours: float | None = None


@dataclass(slots=True)
class Cell:
    """Electrorefining cell with anodes, cathodes, and optional electrolyte."""

    id: str
    current_a: float | None = None
    voltage_v: float | None = None
    anodes: list[Anode] = field(default_factory=list)
    cathodes: list[Cathode] = field(default_factory=list)
    electrolyte: Electrolyte | None = None


@dataclass(slots=True)
class Section:
    """Plant section grouping electrorefining cells."""

    id: str
    cells: list[Cell] = field(default_factory=list)
    name: str | None = None


def _electrolyte_from_dict(raw: dict[str, Any] | None) -> Electrolyte | None:
    if not raw:
        return None
    return Electrolyte(
        temperature_c=raw.get("temperature_c"),
        cu_gpl=raw.get("cu_gpl"),
        h2so4_gpl=raw.get("h2so4_gpl"),
    )


def _cell_from_dict(raw: dict[str, Any]) -> Cell:
    anodes = [
        Anode(
            id=str(item["id"]),
            age_hours=item.get("age_hours"),
            mass_kg=item.get("mass_kg"),
        )
        for item in raw.get("anodes") or []
    ]
    cathodes = [
        Cathode(
            id=str(item["id"]),
            age_hours=item.get("age_hours"),
            ampere_hours=item.get("ampere_hours"),
        )
        for item in raw.get("cathodes") or []
    ]
    return Cell(
        id=str(raw["id"]),
        current_a=raw.get("current_a"),
        voltage_v=raw.get("voltage_v"),
        anodes=anodes,
        cathodes=cathodes,
        electrolyte=_electrolyte_from_dict(raw.get("electrolyte")),
    )


def plant_from_dict(raw: dict[str, Any]) -> list[Section]:
    """Build section/cell stubs from a JSON-like plant snapshot."""
    sections: list[Section] = []
    for section_raw in raw.get("sections") or []:
        cells = [_cell_from_dict(cell) for cell in section_raw.get("cells") or []]
        sections.append(
            Section(
                id=str(section_raw["id"]),
                name=section_raw.get("name"),
                cells=cells,
            )
        )
    return sections
