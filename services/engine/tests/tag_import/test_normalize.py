"""Normalize Level2 tag rows into catalog entries."""

from __future__ import annotations

import json
from pathlib import Path

from level2_mathmodel.tag_import import normalize_level2_tag_row


def test_normalize_fixture_tag_row(level2_fixtures_dir: Path) -> None:
    rows = json.loads((level2_fixtures_dir / "tags_list.json").read_text(encoding="utf-8"))
    entry = normalize_level2_tag_row(rows[0])
    assert entry["tag_id"] == "Cell.Current"
    assert entry["device_id"] == "sim_device"
    assert entry["path"] == "Cell.Current"
    assert entry["datatype"] == "float64"
    assert entry["enabled"] is True
    assert entry["writable"] is False
    assert entry["interval_ms"] == 1000
    assert entry["node_id"] == "ns=2;s=Cell.Current"
    assert entry["last_seen_at"] == "2026-08-10T08:00:00Z"


def test_normalize_flat_export_shape() -> None:
    entry = normalize_level2_tag_row(
        {
            "tag_id": "cell_12_current",
            "device_id": "s7_1500",
            "path": "Cell.12.Current",
            "datatype": "float64",
            "enabled": True,
            "writable": False,
            "interval_ms": 1000,
            "node_id": "ns=4;i=4208",
        },
        seen_at="2026-08-10T12:00:00Z",
    )
    assert entry["tag_id"] == "cell_12_current"
    assert entry["device_id"] == "s7_1500"
    assert entry["last_seen_at"] == "2026-08-10T12:00:00Z"
