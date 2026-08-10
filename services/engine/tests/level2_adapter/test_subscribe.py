"""Level2Client.subscribe — mocked WebSocket messages."""

from __future__ import annotations

import json
from typing import Any

import pytest

from level2_mathmodel.level2_adapter.client import Level2Client, Level2Error
from level2_mathmodel.level2_adapter.models import Sample

BASE = "http://level2-collector:8080"


class _FakeWS:
    """Minimal sync websockets-like connection."""

    def __init__(self, messages: list[Any], *, fail_first: bool = False) -> None:
        self._messages = list(messages)
        self._fail_first = fail_first
        self.sent: list[str] = []
        self._entered = 0

    def __enter__(self) -> _FakeWS:
        self._entered += 1
        if self._fail_first and self._entered == 1:
            raise ConnectionError("boom")
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def send(self, data: str) -> None:
        self.sent.append(data)

    def __iter__(self):
        yield from self._messages


def test_stream_url_with_tags_and_token() -> None:
    client = Level2Client(BASE, api_token="secret")
    url = client.stream_url(["a", "b"])
    assert url.startswith("ws://level2-collector:8080/api/v1/ws/stream?")
    assert "tag_id=a" in url
    assert "tag_id=b" in url
    assert "token=secret" in url


def test_subscribe_yields_samples_and_sends_filter() -> None:
    payload = {
        "time": "2026-08-10T12:00:00Z",
        "tag_id": "Plant.Recalc.Flag",
        "quality": 0,
        "value_bool": True,
        "value_num": None,
        "value_text": None,
    }
    fake = _FakeWS([json.dumps(payload), "not-json", json.dumps({"hello": 1})])

    def connect(uri: str, additional_headers: Any = None, **kwargs: Any) -> _FakeWS:
        assert "/api/v1/ws/stream" in uri
        assert "tag_id=Plant.Recalc.Flag" in uri
        assert additional_headers is not None
        return fake

    client = Level2Client(BASE, api_token="tok", ws_connect=connect)
    samples = list(
        client.subscribe(
            ["Plant.Recalc.Flag"],
            reconnect=False,
            should_stop=lambda: False,
        )
    )
    assert len(samples) == 1
    assert samples[0].tag_id == "Plant.Recalc.Flag"
    assert samples[0].value_bool is True
    assert json.loads(fake.sent[0]) == {"subscribe": ["Plant.Recalc.Flag"]}


def test_subscribe_reconnects_after_disconnect() -> None:
    payload = {
        "time": "2026-08-10T12:00:01Z",
        "tag_id": "flag-1",
        "quality": 0,
        "value_bool": False,
    }
    fake = _FakeWS([json.dumps(payload)], fail_first=True)
    stops = {"n": 0}

    def should_stop() -> bool:
        # Allow one reconnect cycle then stop after first yielded sample path.
        return stops["n"] > 0

    def connect(uri: str, additional_headers: Any = None, **kwargs: Any) -> _FakeWS:
        return fake

    seen: list[Sample] = []

    def on_sample(sample: Sample) -> None:
        seen.append(sample)
        stops["n"] += 1

    client = Level2Client(BASE, ws_connect=connect)
    list(
        client.subscribe(
            ["flag-1"],
            on_sample=on_sample,
            should_stop=should_stop,
            reconnect=True,
            initial_backoff_s=0.01,
            max_backoff_s=0.02,
        )
    )
    assert len(seen) == 1
    assert fake._entered >= 2


def test_subscribe_raises_when_reconnect_disabled() -> None:
    def connect(uri: str, additional_headers: Any = None, **kwargs: Any) -> Any:
        raise OSError("refused")

    client = Level2Client(BASE, ws_connect=connect)
    with pytest.raises(Level2Error, match="WS subscribe failed"):
        next(client.subscribe(tag_ids=["x"], reconnect=False))


def test_https_base_uses_wss() -> None:
    client = Level2Client("https://level2.example", api_token=None)
    assert client.stream_url(["t"]).startswith("wss://level2.example/api/v1/ws/stream")
