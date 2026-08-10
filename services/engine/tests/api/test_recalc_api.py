"""Recalc triggers / status HTTP API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from level2_mathmodel.api.app import create_app
from level2_mathmodel.local_vars import LocalVarStore
from level2_mathmodel.recalc import (
    GENERIC_NOOP_HANDLER_ID,
    RecalcScheduler,
    TriggerStore,
)
from level2_mathmodel.tag_import import TagImportStore


def _client() -> TestClient:
    local = LocalVarStore()
    tags = TagImportStore()
    triggers = TriggerStore()
    scheduler = RecalcScheduler(
        local_vars=local,
        tag_import=tags,
        triggers=triggers,
        enabled=False,
        default_poll_interval_ms=1000,
    )
    app = create_app(
        store=local,
        tag_import_store=tags,
        trigger_store=triggers,
        recalc_scheduler=scheduler,
    )
    return TestClient(app)


def test_recalc_status_and_handlers() -> None:
    with _client() as client:
        st = client.get("/api/v1/recalc/status")
        assert st.status_code == 200
        body = st.json()
        assert body["enabled"] is False
        assert GENERIC_NOOP_HANDLER_ID in body["handler_ids"]
        assert "copper.plan_cathode_anode" in body["handler_ids"]

        handlers = client.get("/api/v1/recalc/handlers")
        assert handlers.status_code == 200
        assert "handler_ids" in handlers.json()


def test_put_triggers_upsert_and_engine_status() -> None:
    with _client() as client:
        resp = client.put(
            "/api/v1/recalc/triggers",
            json={
                "mode": "upsert",
                "triggers": [
                    {
                        "trigger_id": "t1",
                        "handler_id": GENERIC_NOOP_HANDLER_ID,
                        "logical_name": "recalc_trigger",
                        "edge_mode": "rising_bool",
                        "enabled": True,
                    }
                ],
            },
        )
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["trigger_id"] == "t1"
        assert "state" in rows[0]

        listed = client.get("/api/v1/recalc/triggers")
        assert listed.status_code == 200
        assert listed.json()[0]["handler_id"] == GENERIC_NOOP_HANDLER_ID

        status = client.get("/api/v1/status")
        assert status.status_code == 200
        assert status.json()["recalc_trigger_count"] == 1
        assert status.json()["recalc_poll_enabled"] is False


def test_manual_run_handler() -> None:
    with _client() as client:
        resp = client.post(f"/api/v1/recalc/run/{GENERIC_NOOP_HANDLER_ID}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["result"] == "ok"
        assert body["handler_id"] == GENERIC_NOOP_HANDLER_ID

        unknown = client.post("/api/v1/recalc/run/no.such.handler")
        assert unknown.status_code == 404


def test_put_triggers_validation() -> None:
    with _client() as client:
        bad = client.put(
            "/api/v1/recalc/triggers",
            json={"mode": "upsert", "triggers": [{"trigger_id": "x"}]},
        )
        assert bad.status_code == 400
