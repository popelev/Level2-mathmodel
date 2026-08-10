"""Import tags from Level2 into the mathmodel catalog (read-only)."""

from __future__ import annotations

from typing import Any

from level2_mathmodel.level2_adapter import Level2Client, Level2Error, Level2HTTPError

from .normalize import normalize_level2_tag_row
from .store import TagImportStore


def fetch_and_normalize(
    client: Level2Client,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Fetch devices + tags from Level2 and normalize catalog entries.

    Prefers ``GET /api/v1/integration/tag-catalog`` (OpenAPI 1.4.0+).
    Falls back to ``GET /api/v1/devices`` + ``GET /api/v1/tags`` only when
    the catalog endpoint returns HTTP 404 (older Level2 builds).

    Returns ``(devices, entries, meta)`` where meta includes ``source`` and
    optional ``level2_api_version`` / ``exported_at``.
    """
    try:
        catalog = client.get_tag_catalog()
    except Level2HTTPError as exc:
        if exc.status_code != 404:
            raise
        devices = client.list_devices()
        tags = client.list_tags()
        entries = [normalize_level2_tag_row(row) for row in tags]
        return devices, entries, {"source": "tags_fallback"}

    devices = catalog["devices"]
    exported_at = catalog.get("exported_at")
    seen_at = exported_at if isinstance(exported_at, str) else None
    entries = [
        normalize_level2_tag_row(row, seen_at=seen_at) for row in catalog["tags"]
    ]
    meta: dict[str, Any] = {
        "source": "tag_catalog",
        "level2_api_version": catalog.get("level2_api_version"),
        "exported_at": exported_at,
    }
    return devices, entries, meta


def import_level2_tags(
    client: Level2Client,
    store: TagImportStore,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Fetch Level2 tags, optionally upsert into catalog, return counts.

    Raises Level2Error (or subclasses) when Level2 is unreachable / invalid.
    """
    devices, entries, meta = fetch_and_normalize(client)
    if dry_run:
        return {
            "dry_run": True,
            "devices_seen": len(devices),
            "tags_fetched": len(entries),
            "inserted": 0,
            "updated": 0,
            "total": store.catalog_count(),
            "preview": entries,
            **meta,
        }

    counts = store.upsert_catalog(entries)
    return {
        "dry_run": False,
        "devices_seen": len(devices),
        "tags_fetched": len(entries),
        "inserted": counts["inserted"],
        "updated": counts["updated"],
        "total": counts["total"],
        **meta,
    }


# Re-export for callers that catch adapter errors.
__all__ = ["fetch_and_normalize", "import_level2_tags", "Level2Error"]
