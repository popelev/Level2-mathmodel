"""Wave 2: copper plugin writes plan queues into LocalVarStore only."""

from __future__ import annotations

import json
from pathlib import Path

from copper_electrorefining.config import PlannerConfig
from copper_electrorefining.domain import plant_from_dict
from level2_mathmodel.local_vars import LocalVarStore
from level2_mathmodel.plugins.copper_electrorefining import run_copper_plan


FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "technologies"
    / "copper_electrorefining"
    / "fixtures"
    / "plant_snapshot.json"
)


def test_run_copper_plan_upserts_local_var_keys() -> None:
    store = LocalVarStore()
    plant = plant_from_dict(json.loads(FIXTURE.read_text(encoding="utf-8")))
    summary = run_copper_plan(store, plant, PlannerConfig())

    assert summary["status"] == "ready"
    assert store.get("plan.cathode_pull.queue")["source"] == "planner"
    assert store.get("plan.anode_change.queue")["source"] == "planner"
    assert store.get("plan.cathode_pull.count")["value"] == 3
    assert store.get("plan.anode_change.count")["value"] == 1

    queue = json.loads(store.get("plan.cathode_pull.queue")["value"])
    assert queue[0]["cell_id"] == "S1-C02"


def test_run_copper_plan_is_idempotent_upsert() -> None:
    store = LocalVarStore()
    plant = plant_from_dict(json.loads(FIXTURE.read_text(encoding="utf-8")))
    run_copper_plan(store, plant, PlannerConfig())
    run_copper_plan(store, plant, PlannerConfig())
    assert store.count() == 4
