"""fetch_and_normalize prefers tag-catalog with documented fallback."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from level2_mathmodel.level2_adapter import Level2Client
from level2_mathmodel.tag_import import fetch_and_normalize

BASE = "http://level2-collector:8080"


def test_fetch_prefers_tag_catalog(level2_fixtures_dir: Path) -> None:
    catalog = json.loads(
        (level2_fixtures_dir / "tag_catalog.json").read_text(encoding="utf-8")
    )
    called: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        called.append(request.url.path)
        if request.url.path == "/api/v1/integration/tag-catalog":
            return httpx.Response(200, json=catalog)
        return httpx.Response(500, text="should not call fallback")

    with Level2Client(BASE, client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
        devices, entries, meta = fetch_and_normalize(client)

    assert called == ["/api/v1/integration/tag-catalog"]
    assert meta["source"] == "tag_catalog"
    assert meta["level2_api_version"] == "1.4.0"
    assert len(devices) == 1
    assert len(entries) == 2
    assert entries[0]["tag_id"] == "Cell.Current"
    assert entries[0]["last_seen_at"] == "2026-08-10T08:00:00Z"


def test_fetch_empty_tag_catalog(level2_fixtures_dir: Path) -> None:
    catalog = json.loads(
        (level2_fixtures_dir / "tag_catalog_empty.json").read_text(encoding="utf-8")
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=catalog)

    with Level2Client(BASE, client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
        devices, entries, meta = fetch_and_normalize(client)

    assert meta["source"] == "tag_catalog"
    assert devices == []
    assert entries == []


def test_fetch_falls_back_when_catalog_404(level2_fixtures_dir: Path) -> None:
    tags = json.loads((level2_fixtures_dir / "tags_list.json").read_text(encoding="utf-8"))
    devices = json.loads(
        (level2_fixtures_dir / "devices_list.json").read_text(encoding="utf-8")
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/integration/tag-catalog":
            return httpx.Response(404, text="not found")
        if request.url.path == "/api/v1/tags":
            return httpx.Response(200, json=tags)
        if request.url.path == "/api/v1/devices":
            return httpx.Response(200, json=devices)
        return httpx.Response(404, text="missing")

    with Level2Client(BASE, client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
        devices_out, entries, meta = fetch_and_normalize(client)

    assert meta["source"] == "tags_fallback"
    assert len(devices_out) == 1
    assert len(entries) == 2
    assert entries[0]["raw"]["source"] == "level2_tags"
