"""Wave 1: LocalVarStore CRUD (num/bool/text + timestamp + source)."""

from __future__ import annotations

import pytest

from level2_mathmodel.local_vars import (
    LocalVarExistsError,
    LocalVarNotFoundError,
    LocalVarStore,
    LocalVarValidationError,
)


def _payload(**overrides):
    base = {
        "id": "sp_current",
        "name": "Setpoint current",
        "type": "num",
        "value": 12.5,
        "source": "model",
    }
    base.update(overrides)
    return base


def test_list_empty() -> None:
    store = LocalVarStore()
    assert store.list() == []


def test_create_and_get_roundtrip() -> None:
    store = LocalVarStore()
    created = store.create(_payload())
    assert created["id"] == "sp_current"
    assert created["type"] == "num"
    assert created["value"] == 12.5
    assert created["source"] == "model"
    assert "updated_at" in created
    assert created["updated_at"].endswith("Z") or "+" in created["updated_at"]

    got = store.get("sp_current")
    assert got == created
    assert store.list() == [created]


def test_create_duplicate_raises() -> None:
    store = LocalVarStore()
    store.create(_payload())
    with pytest.raises(LocalVarExistsError):
        store.create(_payload())


def test_get_missing_raises() -> None:
    store = LocalVarStore()
    with pytest.raises(LocalVarNotFoundError):
        store.get("missing")


def test_replace_updates_value_and_timestamp() -> None:
    store = LocalVarStore()
    first = store.create(_payload(value=1.0, source="planner"))
    replaced = store.replace("sp_current", _payload(value=2.0, source="operator"))
    assert replaced["value"] == 2.0
    assert replaced["source"] == "operator"
    assert replaced["updated_at"] >= first["updated_at"]
    assert store.get("sp_current")["value"] == 2.0


def test_replace_missing_raises() -> None:
    store = LocalVarStore()
    with pytest.raises(LocalVarNotFoundError):
        store.replace("missing", _payload(id="missing"))


def test_delete_removes() -> None:
    store = LocalVarStore()
    store.create(_payload())
    store.delete("sp_current")
    assert store.list() == []
    with pytest.raises(LocalVarNotFoundError):
        store.delete("sp_current")


def test_upsert_creates_then_updates() -> None:
    store = LocalVarStore()
    a = store.upsert(_payload(value=1))
    b = store.upsert(_payload(value=9, source="operator"))
    assert a["id"] == b["id"]
    assert b["value"] == 9
    assert len(store.list()) == 1


@pytest.mark.parametrize(
    "type_,value",
    [
        ("num", 3),
        ("num", 3.14),
        ("bool", True),
        ("bool", False),
        ("text", "ok"),
        ("text", ""),
    ],
)
def test_accepts_typed_values(type_: str, value: object) -> None:
    store = LocalVarStore()
    item = store.create(_payload(id=f"v_{type_}", type=type_, value=value))
    assert item["type"] == type_
    assert item["value"] == value


@pytest.mark.parametrize(
    "type_,value",
    [
        ("num", "nope"),
        ("num", True),
        ("bool", 1),
        ("bool", "true"),
        ("text", 12),
        ("text", False),
    ],
)
def test_rejects_mismatched_value_type(type_: str, value: object) -> None:
    store = LocalVarStore()
    with pytest.raises(LocalVarValidationError):
        store.create(_payload(type=type_, value=value))


@pytest.mark.parametrize("bad", ["float", "string", "", None])
def test_rejects_bad_type(bad: object) -> None:
    store = LocalVarStore()
    with pytest.raises(LocalVarValidationError):
        store.create(_payload(type=bad))


@pytest.mark.parametrize("bad", ["system", "plc", "", None])
def test_rejects_bad_source(bad: object) -> None:
    store = LocalVarStore()
    with pytest.raises(LocalVarValidationError):
        store.create(_payload(source=bad))


def test_create_requires_id_and_name() -> None:
    store = LocalVarStore()
    with pytest.raises(LocalVarValidationError):
        store.create({"name": "X", "type": "num", "value": 1, "source": "model"})
    with pytest.raises(LocalVarValidationError):
        store.create({"id": "x", "type": "num", "value": 1, "source": "model"})


def test_null_value_allowed() -> None:
    store = LocalVarStore()
    item = store.create(_payload(value=None))
    assert item["value"] is None
