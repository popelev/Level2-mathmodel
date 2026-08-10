"""Wave 1 stubs: Level2Client interface exists but is not implemented yet."""

from __future__ import annotations

import pytest

from level2_mathmodel.level2_adapter import Level2Client


def test_client_requires_base_url() -> None:
    client = Level2Client("http://level2-collector:8080")
    assert client.base_url == "http://level2-collector:8080"


def test_healthz_not_implemented_yet() -> None:
    client = Level2Client("http://level2-collector:8080")
    with pytest.raises(NotImplementedError):
        client.healthz()


def test_list_tags_not_implemented_yet() -> None:
    client = Level2Client("http://level2-collector:8080")
    with pytest.raises(NotImplementedError):
        client.list_tags()
