"""Wave 2: copper electrorefining domain stubs."""

from __future__ import annotations

from copper_electrorefining.domain import (
    Anode,
    Cathode,
    Cell,
    Electrolyte,
    Section,
    plant_from_dict,
)


def test_section_cell_electrode_stubs() -> None:
    electrolyte = Electrolyte(temperature_c=62.0, cu_gpl=45.0, h2so4_gpl=180.0)
    anode = Anode(id="A1", age_hours=100.0, mass_kg=380.0)
    cathode = Cathode(id="K1", age_hours=48.0)
    cell = Cell(
        id="C01",
        current_a=28000.0,
        voltage_v=0.35,
        anodes=[anode],
        cathodes=[cathode],
        electrolyte=electrolyte,
    )
    section = Section(id="S1", name="Section 1", cells=[cell])

    assert section.id == "S1"
    assert section.cells[0].anodes[0].id == "A1"
    assert section.cells[0].cathodes[0].age_hours == 48.0
    assert section.cells[0].electrolyte is not None
    assert section.cells[0].electrolyte.temperature_c == 62.0


def test_plant_from_fixture_dict() -> None:
    raw = {
        "sections": [
            {
                "id": "S1",
                "cells": [
                    {
                        "id": "C1",
                        "current_a": 10.0,
                        "anodes": [{"id": "A1", "age_hours": 1.0}],
                        "cathodes": [{"id": "K1", "age_hours": 2.0}],
                    }
                ],
            }
        ]
    }
    plant = plant_from_dict(raw)
    assert len(plant) == 1
    assert plant[0].cells[0].id == "C1"
    assert plant[0].cells[0].anodes[0].id == "A1"
    assert plant[0].cells[0].cathodes[0].age_hours == 2.0
