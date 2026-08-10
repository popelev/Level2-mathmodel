"""In-memory local vars stub — full CRUD in Wave 1."""

from __future__ import annotations

from typing import Any


class LocalVarStore:
    """Placeholder store for engine-local variables."""

    def list(self) -> list[dict[str, Any]]:
        raise NotImplementedError("Wave1: list local vars")

    def get(self, var_id: str) -> dict[str, Any]:
        raise NotImplementedError("Wave1: get local var")

    def upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Wave1: create/update local var")

    def delete(self, var_id: str) -> None:
        raise NotImplementedError("Wave1: delete local var")
