"""Tag catalog and binding models for Level2 import (engine-owned)."""

from __future__ import annotations

from typing import Any, Literal

BindingRole = Literal["input", "output"]
ALLOWED_ROLES: frozenset[str] = frozenset({"input", "output"})


def catalog_key(tag_id: str, device_id: str) -> str:
    """Stable catalog key: tag_id + device_id."""
    return f"{device_id}\0{tag_id}"


def normalize_catalog_entry(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate/normalize a TagCatalogEntry dict."""
    if not isinstance(payload, dict):
        raise ValueError("catalog entry must be an object")
    tag_id = payload.get("tag_id")
    device_id = payload.get("device_id")
    if not isinstance(tag_id, str) or not tag_id:
        raise ValueError("tag_id is required")
    if not isinstance(device_id, str) or not device_id:
        raise ValueError("device_id is required")

    item: dict[str, Any] = {
        "tag_id": tag_id,
        "device_id": device_id,
    }
    for key in ("path", "datatype", "last_seen_at"):
        if key in payload and payload[key] is not None:
            item[key] = payload[key]
    if "enabled" in payload and payload["enabled"] is not None:
        item["enabled"] = bool(payload["enabled"])
    if "raw" in payload and payload["raw"] is not None:
        item["raw"] = payload["raw"]
    # Optional Level2 fields kept at top level when present (stable export shape).
    for key in ("writable", "interval_ms", "node_id"):
        if key in payload and payload[key] is not None:
            item[key] = payload[key]
    return item


def normalize_binding(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate/normalize a TagBinding dict."""
    if not isinstance(payload, dict):
        raise ValueError("binding must be an object")
    logical_name = payload.get("logical_name")
    tag_id = payload.get("tag_id")
    if not isinstance(logical_name, str) or not logical_name:
        raise ValueError("logical_name is required")
    if not isinstance(tag_id, str) or not tag_id:
        raise ValueError("tag_id is required")

    role = payload.get("role", "input")
    if role not in ALLOWED_ROLES:
        raise ValueError("role must be one of: input, output")

    item: dict[str, Any] = {
        "logical_name": logical_name,
        "tag_id": tag_id,
        "role": role,
    }
    if "device_id" in payload and payload["device_id"] is not None:
        item["device_id"] = payload["device_id"]
    for key in ("section_id", "cell_id", "signal"):
        if key in payload and payload[key] is not None:
            item[key] = payload[key]
    return item
