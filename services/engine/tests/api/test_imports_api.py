"""Level2 tag import + bindings HTTP API (mocked Level2Client)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from level2_mathmodel.api.app import create_app
from level2_mathmodel.level2_adapter import Level2Client, Level2Error
from level2_mathmodel.local_vars import LocalVarStore
from level2_mathmodel.tag_import import TagImportStore

BASE = "http://level2-collector:8080"


def _fixture_client(level2_fixtures_dir: Path) -> Level2Client:
    tags = json.loads((level2_fixtures_dir / "tags_list.json").read_text(encoding="utf-8"))
    devices = json.loads(
        (level2_fixtures_dir / "devices_list.json").read_text(encoding="utf-8")
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/tags":
            return httpx.Response(200, json=tags)
        if request.url.path == "/api/v1/devices":
            return httpx.Response(200, json=devices)
        return httpx.Response(404, text="missing")

    http = httpx.Client(transport=httpx.MockTransport(handler))
    return Level2Client(BASE, client=http)


def _api(level2_fixtures_dir: Path) -> TestClient:
    store = TagImportStore()

    def factory() -> Level2Client:
        return _fixture_client(level2_fixtures_dir)

    return TestClient(
        create_app(
            store=LocalVarStore(),
            tag_import_store=store,
            level2_client_factory=factory,
        )
    )


def test_import_upserts_catalog(level2_fixtures_dir: Path) -> None:
    client = _api(level2_fixtures_dir)
    r = client.post("/api/v1/imports/level2/tags")
    assert r.status_code == 200
    body = r.json()
    assert body["dry_run"] is False
    assert body["devices_seen"] == 1
    assert body["tags_fetched"] == 2
    assert body["inserted"] == 2
    assert body["total"] == 2

    catalog = client.get("/api/v1/imports/level2/catalog")
    assert catalog.status_code == 200
    rows = catalog.json()
    assert len(rows) == 2
    assert {x["tag_id"] for x in rows} == {"Cell.Current", "Cell.Voltage"}

    again = client.post("/api/v1/imports/level2/tags")
    assert again.json()["updated"] == 2
    assert again.json()["inserted"] == 0


def test_preview_does_not_save(level2_fixtures_dir: Path) -> None:
    client = _api(level2_fixtures_dir)
    r = client.post("/api/v1/imports/level2/tags/preview")
    assert r.status_code == 200
    body = r.json()
    assert body["dry_run"] is True
    assert body["tags_fetched"] == 2
    assert len(body["preview"]) == 2
    assert client.get("/api/v1/imports/level2/catalog").json() == []


def test_import_503_when_level2_unreachable() -> None:
    def factory() -> Level2Client:
        raise Level2Error("connection refused")

    client = TestClient(
        create_app(
            tag_import_store=TagImportStore(),
            level2_client_factory=factory,
        )
    )
    r = client.post("/api/v1/imports/level2/tags")
    assert r.status_code == 503
    assert r.json()["error"] == "level2_unavailable"


def test_bindings_put_get_delete(level2_fixtures_dir: Path) -> None:
    client = _api(level2_fixtures_dir)
    put = client.put(
        "/api/v1/bindings",
        json=[
            {
                "logical_name": "cell_current",
                "tag_id": "Cell.Current",
                "device_id": "sim_device",
                "role": "input",
                "section_id": "A",
                "cell_id": "12",
                "signal": "current",
            }
        ],
    )
    assert put.status_code == 200
    assert put.json()[0]["logical_name"] == "cell_current"

    listed = client.get("/api/v1/bindings")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    upsert = client.put(
        "/api/v1/bindings",
        json={
            "mode": "upsert",
            "bindings": [
                {
                    "logical_name": "cell_voltage",
                    "tag_id": "Cell.Voltage",
                    "device_id": "sim_device",
                }
            ],
        },
    )
    assert upsert.status_code == 200
    assert len(upsert.json()) == 2

    deleted = client.delete("/api/v1/bindings/cell_current")
    assert deleted.status_code == 204
    assert len(client.get("/api/v1/bindings").json()) == 1
    assert client.delete("/api/v1/bindings/missing").status_code == 404


def test_status_includes_catalog_counts(level2_fixtures_dir: Path) -> None:
    client = _api(level2_fixtures_dir)
    client.post("/api/v1/imports/level2/tags")
    client.put(
        "/api/v1/bindings",
        json=[{"logical_name": "x", "tag_id": "Cell.Current", "device_id": "sim_device"}],
    )
    status = client.get("/api/v1/status").json()
    assert status["tag_catalog_count"] == 2
    assert status["binding_count"] == 1
