"""Normalize Level2 GET /tags rows into mathmodel TagCatalogEntry shape."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_level2_tag_row(row: dict[str, Any], *, seen_at: str | None = None) -> dict[str, Any]:
    """Map a Level2 TagValue (or flat export tag) into TagCatalogEntry.

    Supports:
    - Current Collector shape: ``{device_id, tag: {...}, sample, ...}``
    - Future integration export: flat ``{tag_id, device_id, path, ...}``
    """
    if not isinstance(row, dict):
        raise ValueError("tag row must be an object")

    tag_obj = row.get("tag") if isinstance(row.get("tag"), dict) else None
    tag_id = None
    if tag_obj and isinstance(tag_obj.get("id"), str):
        tag_id = tag_obj["id"]
    elif isinstance(row.get("tag_id"), str):
        tag_id = row["tag_id"]

    device_id = row.get("device_id")
    if not isinstance(device_id, str) or not device_id:
        raise ValueError("device_id is required on tag row")
    if not isinstance(tag_id, str) or not tag_id:
        raise ValueError("tag_id is required on tag row")

    src = tag_obj or row
    last_seen = seen_at or row.get("updated_at") or _utc_now_iso()
    if isinstance(row.get("sample"), dict) and row["sample"].get("time"):
        last_seen = row["sample"]["time"]

    entry: dict[str, Any] = {
        "tag_id": tag_id,
        "device_id": device_id,
        "last_seen_at": last_seen,
    }
    if src.get("path") is not None:
        entry["path"] = src["path"]
    if src.get("datatype") is not None:
        entry["datatype"] = src["datatype"]
    if src.get("enabled") is not None:
        entry["enabled"] = bool(src["enabled"])
    if src.get("writable") is not None:
        entry["writable"] = bool(src["writable"])
    if src.get("interval_ms") is not None:
        entry["interval_ms"] = src["interval_ms"]
    if src.get("node_id") is not None:
        entry["node_id"] = src["node_id"]

    # Keep a slim raw snapshot for debugging (not a Level2 write surface).
    entry["raw"] = {
        "source": "level2_tags" if tag_obj is not None else "level2_export",
        "poll_avg_ms": row.get("poll_avg_ms"),
    }
    return entry
