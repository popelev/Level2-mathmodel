"""LocalVarStore public interface smoke."""

from __future__ import annotations

from level2_mathmodel.local_vars import LocalVarStore, LocalVariablesStore


def test_store_alias() -> None:
    assert LocalVariablesStore is LocalVarStore


def test_crud_methods_exist() -> None:
    store = LocalVarStore()
    assert callable(store.list)
    assert callable(store.get)
    assert callable(store.create)
    assert callable(store.replace)
    assert callable(store.upsert)
    assert callable(store.delete)
