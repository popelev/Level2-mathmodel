"""GET /api/v1/live/inputs — Level2 tag projection for Web UI."""

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


def _tags_client(level2_fixtures_dir: Path) -> Level2Client:
    tags = json.loads(
        (level2_fixtures_dir / "tags_list.json").read_text(encoding="utf-8")
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/tags":
            return httpx.Response(200, json=tags)
        return httpx.Response(404, text="missing")

    http = httpx.Client(transport=httpx.MockTransport(handler))
    return Level2Client(BASE, client=http)


def test_live_inputs_maps_level2_tags(level2_fixtures_dir: Path) -> None:
    def factory() -> Level2Client:
        return _tags_client(level2_fixtures_dir)

    client = TestClient(
        create_app(
            store=LocalVarStore(),
            tag_import_store=TagImportStore(),
            level2_client_factory=factory,
        )
    )
    r = client.get("/api/v1/live/inputs")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "level2"
    assert body["tag_count"] == 2
    assert len(body["tags"]) == 2
    first = body["tags"][0]
    assert first["tag_id"] == "Cell.Current"
    assert first["device_id"] == "sim_device"
    assert first["value_num"] == 1250.5
    assert first["quality"] == 0


def test_live_inputs_level2_unavailable() -> None:
    def factory() -> Level2Client:
        raise Level2Error("LEVEL2_API_URL is not set")

    client = TestClient(
        create_app(
            store=LocalVarStore(),
            tag_import_store=TagImportStore(),
            level2_client_factory=factory,
        )
    )
    r = client.get("/api/v1/live/inputs")
    assert r.status_code == 502
    assert r.json()["error"] == "level2_unavailable"


def test_live_inputs_in_openapi_paths() -> None:
    paths = set(create_app().openapi()["paths"])
    assert "/api/v1/live/inputs" in paths
