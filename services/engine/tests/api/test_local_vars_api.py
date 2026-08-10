"""Wave 1: HTTP API for local variables (+ healthz)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from level2_mathmodel.api.app import create_app
from level2_mathmodel.local_vars import LocalVarStore


def _client(store: LocalVarStore | None = None) -> TestClient:
    return TestClient(create_app(store=store or LocalVarStore()))


def _body(**overrides):
    base = {
        "id": "sp_current",
        "name": "Setpoint current",
        "type": "num",
        "value": 12.5,
        "source": "model",
    }
    base.update(overrides)
    return base


def test_healthz() -> None:
    client = _client()
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.text == "ok"


def test_list_empty() -> None:
    client = _client()
    r = client.get("/api/v1/local-vars")
    assert r.status_code == 200
    assert r.json() == []


def test_create_get_list() -> None:
    client = _client()
    created = client.post("/api/v1/local-vars", json=_body())
    assert created.status_code == 201
    body = created.json()
    assert body["id"] == "sp_current"
    assert body["type"] == "num"
    assert body["source"] == "model"
    assert "updated_at" in body

    got = client.get("/api/v1/local-vars/sp_current")
    assert got.status_code == 200
    assert got.json() == body

    listed = client.get("/api/v1/local-vars")
    assert listed.status_code == 200
    assert listed.json() == [body]


def test_create_conflict() -> None:
    client = _client()
    assert client.post("/api/v1/local-vars", json=_body()).status_code == 201
    r = client.post("/api/v1/local-vars", json=_body())
    assert r.status_code == 409


def test_create_invalid_body() -> None:
    client = _client()
    r = client.post(
        "/api/v1/local-vars",
        json={"id": "x", "name": "X", "type": "num", "value": "bad", "source": "model"},
    )
    assert r.status_code == 400


def test_get_not_found() -> None:
    client = _client()
    assert client.get("/api/v1/local-vars/missing").status_code == 404


def test_put_replace() -> None:
    client = _client()
    client.post("/api/v1/local-vars", json=_body(value=1.0))
    r = client.put(
        "/api/v1/local-vars/sp_current",
        json=_body(value=2.0, source="operator"),
    )
    assert r.status_code == 200
    assert r.json()["value"] == 2.0
    assert r.json()["source"] == "operator"


def test_put_not_found() -> None:
    client = _client()
    r = client.put("/api/v1/local-vars/missing", json=_body(id="missing"))
    assert r.status_code == 404


def test_delete() -> None:
    client = _client()
    client.post("/api/v1/local-vars", json=_body())
    r = client.delete("/api/v1/local-vars/sp_current")
    assert r.status_code == 204
    assert client.get("/api/v1/local-vars/sp_current").status_code == 404


def test_delete_not_found() -> None:
    client = _client()
    assert client.delete("/api/v1/local-vars/missing").status_code == 404


def test_status_includes_local_var_count() -> None:
    client = _client()
    client.post("/api/v1/local-vars", json=_body())
    r = client.get("/api/v1/status")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "level2-mathmodel"
    assert data["local_var_count"] == 1
