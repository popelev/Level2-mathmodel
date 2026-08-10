"""In-memory local variables store — CRUD for engine outputs only."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .models import ALLOWED_SOURCES, ALLOWED_TYPES, value_matches_type


class LocalVarNotFoundError(KeyError):
    """Raised when a local variable id is missing."""


class LocalVarExistsError(ValueError):
    """Raised when creating a local variable whose id already exists."""


class LocalVarValidationError(ValueError):
    """Raised when payload type/source/value are invalid."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class LocalVarStore:
    """Engine-owned local variables (never written to PLC / Level2)."""

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def list(self) -> list[dict[str, Any]]:
        return [deepcopy(v) for v in self._items.values()]

    def get(self, var_id: str) -> dict[str, Any]:
        try:
            return deepcopy(self._items[var_id])
        except KeyError as exc:
            raise LocalVarNotFoundError(var_id) from exc

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        item = self._normalize(payload, require_id=True)
        var_id = item["id"]
        if var_id in self._items:
            raise LocalVarExistsError(var_id)
        item["updated_at"] = _utc_now_iso()
        self._items[var_id] = item
        return deepcopy(item)

    def replace(self, var_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if var_id not in self._items:
            raise LocalVarNotFoundError(var_id)
        data = dict(payload)
        data["id"] = var_id
        item = self._normalize(data, require_id=True)
        item["updated_at"] = _utc_now_iso()
        self._items[var_id] = item
        return deepcopy(item)

    def upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        item = self._normalize(payload, require_id=True)
        var_id = item["id"]
        if var_id in self._items:
            return self.replace(var_id, item)
        return self.create(item)

    def delete(self, var_id: str) -> None:
        if var_id not in self._items:
            raise LocalVarNotFoundError(var_id)
        del self._items[var_id]

    def count(self) -> int:
        return len(self._items)

    def _normalize(self, payload: dict[str, Any], *, require_id: bool) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise LocalVarValidationError("payload must be an object")

        var_id = payload.get("id")
        name = payload.get("name")
        var_type = payload.get("type")
        source = payload.get("source")
        value = payload.get("value", None)

        if require_id and (not isinstance(var_id, str) or not var_id):
            raise LocalVarValidationError("id is required")
        if not isinstance(name, str) or not name:
            raise LocalVarValidationError("name is required")
        if var_type not in ALLOWED_TYPES:
            raise LocalVarValidationError("type must be one of: num, bool, text")
        if source not in ALLOWED_SOURCES:
            raise LocalVarValidationError("source must be one of: planner, operator, model")
        if not value_matches_type(var_type, value):
            raise LocalVarValidationError(f"value does not match type {var_type!r}")

        item: dict[str, Any] = {
            "id": var_id,
            "name": name,
            "type": var_type,
            "value": value,
            "source": source,
        }
        if "unit" in payload and payload["unit"] is not None:
            item["unit"] = payload["unit"]
        if "description" in payload and payload["description"] is not None:
            item["description"] = payload["description"]
        return item


# Alias used in Wave 1 track naming.
LocalVariablesStore = LocalVarStore
