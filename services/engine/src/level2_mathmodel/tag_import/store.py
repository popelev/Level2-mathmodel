"""In-memory tag catalog + bindings store (optional JSON persistence)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .models import catalog_key, normalize_binding, normalize_catalog_entry


class BindingNotFoundError(KeyError):
    """Raised when a binding logical_name is missing."""


class TagImportStore:
    """Catalog of imported Level2 tags and logical name bindings.

    Model/plan outputs stay in local_vars; this store only holds read-side
    catalog + bindings keyed by stable tag_id (+ device_id).
    """

    def __init__(self, persist_path: str | Path | None = None) -> None:
        self._catalog: dict[str, dict[str, Any]] = {}
        self._bindings: dict[str, dict[str, Any]] = {}
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path is not None and self._persist_path.is_file():
            self._load()

    def list_catalog(self) -> list[dict[str, Any]]:
        return [deepcopy(v) for v in self._catalog.values()]

    def catalog_count(self) -> int:
        return len(self._catalog)

    def upsert_catalog(self, entries: list[dict[str, Any]]) -> dict[str, int]:
        """Upsert catalog entries. Returns inserted/updated/total counts."""
        inserted = 0
        updated = 0
        for raw in entries:
            item = normalize_catalog_entry(raw)
            key = catalog_key(item["tag_id"], item["device_id"])
            if key in self._catalog:
                updated += 1
            else:
                inserted += 1
            self._catalog[key] = item
        self._save()
        return {
            "inserted": inserted,
            "updated": updated,
            "total": len(self._catalog),
        }

    def list_bindings(self) -> list[dict[str, Any]]:
        return [deepcopy(v) for v in self._bindings.values()]

    def replace_bindings(self, bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Replace entire bindings list."""
        next_map: dict[str, dict[str, Any]] = {}
        for raw in bindings:
            item = normalize_binding(raw)
            next_map[item["logical_name"]] = item
        self._bindings = next_map
        self._save()
        return self.list_bindings()

    def upsert_bindings(self, bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Upsert bindings by logical_name (keep others)."""
        for raw in bindings:
            item = normalize_binding(raw)
            self._bindings[item["logical_name"]] = item
        self._save()
        return self.list_bindings()

    def delete_binding(self, logical_name: str) -> None:
        if logical_name not in self._bindings:
            raise BindingNotFoundError(logical_name)
        del self._bindings[logical_name]
        self._save()

    def binding_count(self) -> int:
        return len(self._bindings)

    def _load(self) -> None:
        assert self._persist_path is not None
        data = json.loads(self._persist_path.read_text(encoding="utf-8"))
        catalog = data.get("catalog") or []
        bindings = data.get("bindings") or []
        for raw in catalog:
            item = normalize_catalog_entry(raw)
            self._catalog[catalog_key(item["tag_id"], item["device_id"])] = item
        for raw in bindings:
            item = normalize_binding(raw)
            self._bindings[item["logical_name"]] = item

    def _save(self) -> None:
        if self._persist_path is None:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "catalog": self.list_catalog(),
            "bindings": self.list_bindings(),
        }
        self._persist_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
