"""TagImportStore catalog + bindings."""

from __future__ import annotations

from pathlib import Path

import pytest

from level2_mathmodel.tag_import import BindingNotFoundError, TagImportStore


def test_upsert_catalog_counts() -> None:
    store = TagImportStore()
    first = store.upsert_catalog(
        [
            {"tag_id": "a", "device_id": "d1", "datatype": "float64"},
            {"tag_id": "b", "device_id": "d1"},
        ]
    )
    assert first == {"inserted": 2, "updated": 0, "total": 2}
    second = store.upsert_catalog(
        [{"tag_id": "a", "device_id": "d1", "datatype": "int32"}]
    )
    assert second == {"inserted": 0, "updated": 1, "total": 2}
    listed = store.list_catalog()
    assert len(listed) == 2
    a = next(x for x in listed if x["tag_id"] == "a")
    assert a["datatype"] == "int32"


def test_bindings_replace_upsert_delete() -> None:
    store = TagImportStore()
    store.replace_bindings(
        [
            {
                "logical_name": "cell_current",
                "tag_id": "Cell.Current",
                "device_id": "sim_device",
                "role": "input",
            }
        ]
    )
    assert store.binding_count() == 1
    store.upsert_bindings(
        [
            {
                "logical_name": "cell_voltage",
                "tag_id": "Cell.Voltage",
                "device_id": "sim_device",
            }
        ]
    )
    assert {b["logical_name"] for b in store.list_bindings()} == {
        "cell_current",
        "cell_voltage",
    }
    store.delete_binding("cell_current")
    assert store.binding_count() == 1
    with pytest.raises(BindingNotFoundError):
        store.delete_binding("missing")


def test_persist_json_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "import_state.json"
    store = TagImportStore(persist_path=path)
    store.upsert_catalog([{"tag_id": "t1", "device_id": "d1", "path": "T1"}])
    store.replace_bindings(
        [{"logical_name": "in1", "tag_id": "t1", "device_id": "d1", "role": "input"}]
    )
    assert path.is_file()

    reloaded = TagImportStore(persist_path=path)
    assert reloaded.catalog_count() == 1
    assert reloaded.list_bindings()[0]["logical_name"] == "in1"
