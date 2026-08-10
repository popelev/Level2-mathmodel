"""Wave 2: cathode pull / anode change queues from age thresholds."""

from __future__ import annotations

import json
from pathlib import Path

from copper_electrorefining.config import PlannerConfig
from copper_electrorefining.domain import plant_from_dict
from copper_electrorefining.planner import build_queues, plan_to_local_payloads


FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "technologies"
    / "copper_electrorefining"
    / "fixtures"
    / "plant_snapshot.json"
)


def test_build_queues_orders_by_age_desc() -> None:
    plant = plant_from_dict(json.loads(FIXTURE.read_text(encoding="utf-8")))
    cfg = PlannerConfig(cathode_max_age_hours=168.0, anode_max_age_hours=504.0)
    result = build_queues(plant, cfg)

    cathode_ids = [item["cathode_id"] for item in result.cathode_pull]
    assert cathode_ids == ["S1-C02-K1", "S1-C02-K2", "S1-C01-K1"]
    assert all(item["age_hours"] >= 168.0 for item in result.cathode_pull)

    anode_ids = [item["anode_id"] for item in result.anode_change]
    assert anode_ids == ["S1-C01-A1"]
    assert result.anode_change[0]["age_hours"] == 520.0


def test_build_queues_empty_when_below_thresholds() -> None:
    plant = plant_from_dict(
        {
            "sections": [
                {
                    "id": "S1",
                    "cells": [
                        {
                            "id": "C1",
                            "anodes": [{"id": "A1", "age_hours": 10.0}],
                            "cathodes": [{"id": "K1", "age_hours": 10.0}],
                        }
                    ],
                }
            ]
        }
    )
    cfg = PlannerConfig(cathode_max_age_hours=168.0, anode_max_age_hours=504.0)
    result = build_queues(plant, cfg)
    assert result.cathode_pull == []
    assert result.anode_change == []


def test_plan_to_local_payloads_keys() -> None:
    plant = plant_from_dict(json.loads(FIXTURE.read_text(encoding="utf-8")))
    result = build_queues(plant, PlannerConfig())
    payloads = plan_to_local_payloads(result)
    ids = {p["id"] for p in payloads}
    assert "plan.cathode_pull.queue" in ids
    assert "plan.anode_change.queue" in ids
    assert "plan.cathode_pull.count" in ids
    assert "plan.anode_change.count" in ids

    queue_payload = next(p for p in payloads if p["id"] == "plan.cathode_pull.queue")
    assert queue_payload["type"] == "text"
    assert queue_payload["source"] == "planner"
    parsed = json.loads(queue_payload["value"])
    assert isinstance(parsed, list)
    assert parsed[0]["cathode_id"] == "S1-C02-K1"
