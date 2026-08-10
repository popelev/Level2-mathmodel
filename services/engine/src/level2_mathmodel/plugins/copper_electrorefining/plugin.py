"""Glue: run copper planner and persist results to LocalVarStore only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from copper_electrorefining.config import PlannerConfig
from copper_electrorefining.domain import Section, plant_from_dict
from copper_electrorefining.planner import build_queues, plan_to_local_payloads

from level2_mathmodel.local_vars import LocalVarStore

# technologies/copper_electrorefining/fixtures/plant_snapshot.json
# plugin.py -> .../src/level2_mathmodel/plugins/copper_electrorefining → repo root = parents[6]
_DEMO_FIXTURE = (
    Path(__file__).resolve().parents[6]
    / "technologies"
    / "copper_electrorefining"
    / "fixtures"
    / "plant_snapshot.json"
)


def load_demo_plant(path: Path | None = None) -> list[Section]:
    """Load plant snapshot fixture (unit-test / demo substitute for Level2 tags)."""
    fixture = path or _DEMO_FIXTURE
    return plant_from_dict(json.loads(fixture.read_text(encoding="utf-8")))


def run_copper_plan(
    store: LocalVarStore,
    plant: list[Section],
    config: PlannerConfig | None = None,
) -> dict[str, Any]:
    """Compute queues and upsert planner local variables. Never writes to Level2."""
    result = build_queues(plant, config)
    payloads = plan_to_local_payloads(result)
    written: list[str] = []
    for payload in payloads:
        store.upsert(payload)
        written.append(payload["id"])
    return {
        "status": "ready",
        "message": "Copper plan queues written to local variables",
        "local_var_ids": written,
        "cathode_pull_count": len(result.cathode_pull),
        "anode_change_count": len(result.anode_change),
    }
