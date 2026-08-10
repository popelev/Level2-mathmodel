"""Level2Client read-only API — mocked HTTP via httpx.MockTransport + fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import httpx
import pytest

from level2_mathmodel.level2_adapter import (
    Level2Client,
    Level2HTTPError,
    Sample,
)

BASE = "http://level2-collector:8080"


def _load_fixture(fixtures_dir: Path, name: str) -> Any:
    return json.loads((fixtures_dir / name).read_text(encoding="utf-8"))


def _make_client(handler: Any) -> Level2Client:
    transport = handler if isinstance(handler, httpx.MockTransport) else httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    return Level2Client(BASE, client=http)


def test_client_requires_base_url() -> None:
    client = Level2Client("http://level2-collector:8080/")
    assert client.base_url == "http://level2-collector:8080"
    client.close()


def test_healthz_uses_fixture_text(level2_fixtures_dir: Path) -> None:
    wrapper = _load_fixture(level2_fixtures_dir, "healthz.json")
    status_text = wrapper["status_text"]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/healthz"
        return httpx.Response(200, text=status_text)

    with _make_client(handler) as client:
        assert client.healthz() == "ok"


def test_readyz_true_and_false() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/readyz"
        code = 200 if not calls else 503
        calls.append(code)
        return httpx.Response(code, text="ok" if code == 200 else "not ready")

    with _make_client(handler) as client:
        assert client.readyz() is True
        assert client.readyz() is False


def test_list_tags_from_fixture(level2_fixtures_dir: Path) -> None:
    payload = _load_fixture(level2_fixtures_dir, "tags_list.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/tags"
        assert request.url.params.get("device_id") == "sim_device"
        return httpx.Response(200, json=payload)

    with _make_client(handler) as client:
        tags = client.list_tags(device_id="sim_device")
    assert len(tags) == 2
    assert tags[0]["tag"]["id"] == "Cell.Current"
    assert tags[0]["sample"]["value_num"] == 1250.5


def test_get_tag_value_maps_sample_dto(level2_fixtures_dir: Path) -> None:
    payload = _load_fixture(level2_fixtures_dir, "sample_value.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/tags/Cell.Current/value"
        return httpx.Response(200, json=payload)

    with _make_client(handler) as client:
        sample = client.get_tag_value("Cell.Current")

    assert isinstance(sample, Sample)
    assert sample.time == "2026-08-10T08:00:00Z"
    assert sample.tag_id == "Cell.Current"
    assert sample.value_num == 1250.5
    assert sample.value_text is None
    assert sample.value_bool is None
    assert sample.quality == 0
    assert sample.to_dict()["tag_id"] == "Cell.Current"


def test_get_tag_value_encodes_special_ids(level2_fixtures_dir: Path) -> None:
    payload = _load_fixture(level2_fixtures_dir, "sample_value.json")
    payload = {**payload, "tag_id": "Cell Current"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert "Cell%20Current" in str(request.url)
        assert unquote(request.url.path).endswith("/Cell Current/value")
        return httpx.Response(200, json=payload)

    with _make_client(handler) as client:
        sample = client.get_tag_value("Cell Current")
    assert sample.tag_id == "Cell Current"


def test_list_devices_from_fixture(level2_fixtures_dir: Path) -> None:
    payload = _load_fixture(level2_fixtures_dir, "devices_list.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/devices"
        return httpx.Response(200, json=payload)

    with _make_client(handler) as client:
        devices = client.list_devices()
    assert devices[0]["id"] == "sim_device"
    assert devices[0]["connected"] is True


def test_get_history_minimal(level2_fixtures_dir: Path) -> None:
    payload = _load_fixture(level2_fixtures_dir, "history_samples.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/tags/Cell.Current/history"
        assert request.url.params.get("from") == "2026-08-10T07:00:00Z"
        assert request.url.params.get("to") == "2026-08-10T09:00:00Z"
        assert request.url.params.get("limit") == "10"
        return httpx.Response(200, json=payload)

    with _make_client(handler) as client:
        samples = client.get_history(
            "Cell.Current",
            from_time="2026-08-10T07:00:00Z",
            to_time="2026-08-10T09:00:00Z",
            limit=10,
        )
    assert len(samples) == 2
    assert all(isinstance(s, Sample) for s in samples)
    assert samples[-1].value_num == 1250.5


def test_http_error_on_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="unknown tag")

    with _make_client(handler) as client:
        with pytest.raises(Level2HTTPError) as exc:
            client.get_tag_value("missing")
    assert exc.value.status_code == 404


def test_subscribe_is_stub() -> None:
    with _make_client(lambda r: httpx.Response(500)) as client:
        with pytest.raises(NotImplementedError, match="WebSocket"):
            next(client.subscribe(tag_ids=["Cell.Current"]))


def test_client_has_no_write_methods() -> None:
    """Read-only adapter must not expose Level2 PUT/write helpers."""
    names = {n for n in dir(Level2Client) if not n.startswith("_")}
    forbidden = {
        "write",
        "write_tag",
        "put_tag_value",
        "set_tag_value",
        "batch_write",
        "create_device",
        "update_device",
        "delete_device",
    }
    assert names.isdisjoint(forbidden)


def test_sample_from_dict_bool_and_text() -> None:
    sample = Sample.from_dict(
        {
            "time": "2026-08-10T08:00:00Z",
            "tag_id": "Cell.Enable",
            "value_num": None,
            "value_text": "on",
            "value_bool": True,
            "quality": 1,
        }
    )
    assert sample.value_bool is True
    assert sample.value_text == "on"
    assert sample.quality == 1
