"""Wave 2: thin plan API runs copper planner into local vars."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from level2_mathmodel.api.app import create_app
from level2_mathmodel.local_vars import LocalVarStore


def test_post_plan_writes_local_queues() -> None:
    store = LocalVarStore()
    client = TestClient(create_app(store=store))
    response = client.post("/api/v1/plan", json={"horizon_hours": 8})
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "ready"
    assert "plan.cathode_pull.queue" in body["local_var_ids"]

    queue = json.loads(store.get("plan.cathode_pull.queue")["value"])
    assert isinstance(queue, list)
    assert store.get("plan.cathode_pull.count")["type"] == "num"


def test_get_plan_reads_local_queues() -> None:
    store = LocalVarStore()
    client = TestClient(create_app(store=store))
    client.post("/api/v1/plan", json={})
    response = client.get("/api/v1/plan")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["cathode_pull_count"] >= 0
    assert body["anode_change_count"] >= 0
