"""Import tags from Level2 into the mathmodel catalog (read-only)."""

from __future__ import annotations

from typing import Any

from level2_mathmodel.level2_adapter import Level2Client, Level2Error

from .normalize import normalize_level2_tag_row
from .store import TagImportStore


def fetch_and_normalize(client: Level2Client) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetch devices + tags from Level2 and normalize catalog entries."""
    devices = client.list_devices()
    tags = client.list_tags()
    entries: list[dict[str, Any]] = []
    for row in tags:
        entries.append(normalize_level2_tag_row(row))
    return devices, entries


def import_level2_tags(
    client: Level2Client,
    store: TagImportStore,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Fetch Level2 tags, optionally upsert into catalog, return counts.

    Raises Level2Error (or subclasses) when Level2 is unreachable / invalid.
    """
    devices, entries = fetch_and_normalize(client)
    if dry_run:
        return {
            "dry_run": True,
            "devices_seen": len(devices),
            "tags_fetched": len(entries),
            "inserted": 0,
            "updated": 0,
            "total": store.catalog_count(),
            "preview": entries,
        }

    counts = store.upsert_catalog(entries)
    return {
        "dry_run": False,
        "devices_seen": len(devices),
        "tags_fetched": len(entries),
        "inserted": counts["inserted"],
        "updated": counts["updated"],
        "total": counts["total"],
    }


# Re-export for callers that catch adapter errors.
__all__ = ["fetch_and_normalize", "import_level2_tags", "Level2Error"]
