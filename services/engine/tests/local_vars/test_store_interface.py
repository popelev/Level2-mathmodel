"""Wave 1 stubs: LocalVarStore interface exists but is not implemented yet."""

from __future__ import annotations

import pytest

from level2_mathmodel.local_vars import LocalVarStore


def test_list_not_implemented_yet() -> None:
    store = LocalVarStore()
    with pytest.raises(NotImplementedError):
        store.list()


def test_upsert_not_implemented_yet() -> None:
    store = LocalVarStore()
    with pytest.raises(NotImplementedError):
        store.upsert({"id": "x", "name": "X", "value": 1})
