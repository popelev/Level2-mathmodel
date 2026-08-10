"""HTTP routes for live input projection (read-only Level2 tags/samples)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from level2_mathmodel.api.imports import _client_factory
from level2_mathmodel.level2_adapter import Level2Error

router = APIRouter(tags=["live"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tag_id_from_row(row: dict[str, Any]) -> str | None:
    tag = row.get("tag")
    if isinstance(tag, dict) and tag.get("id") is not None:
        return str(tag["id"])
    sample = row.get("sample")
    if isinstance(sample, dict) and sample.get("tag_id") is not None:
        return str(sample["tag_id"])
    if row.get("tag_id") is not None:
        return str(row["tag_id"])
    return None


def summarize_live_inputs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Map Level2 GET /tags rows into LiveInputsSummary (OpenAPI)."""
    updated_at = _now_iso()
    tags: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        tag_id = _tag_id_from_row(row)
        if not tag_id:
            continue
        sample = row.get("sample") if isinstance(row.get("sample"), dict) else {}
        quality_raw = sample.get("quality", row.get("quality", 1))
        try:
            quality = int(quality_raw)
        except (TypeError, ValueError):
            quality = 1
        value_num = sample.get("value_num", row.get("value_num"))
        if value_num is not None:
            try:
                value_num = float(value_num)
            except (TypeError, ValueError):
                value_num = None
        time = sample.get("time") or row.get("updated_at") or row.get("time")
        device_id = row.get("device_id")
        tags.append(
            {
                "tag_id": tag_id,
                "device_id": str(device_id) if device_id is not None else None,
                "value_num": value_num,
                "quality": quality,
                "time": str(time) if time is not None else None,
            }
        )
        if isinstance(time, str) and time > updated_at:
            updated_at = time
    return {
        "source": "level2",
        "updated_at": updated_at,
        "tag_count": len(tags),
        "tags": tags,
    }


@router.get("/api/v1/live/inputs", response_model=None)
def live_inputs(request: Request) -> Any:
    """Read-only projection of Level2 tags/samples for the Live inputs UI."""
    factory = _client_factory(request)
    try:
        with factory() as client:
            rows = client.list_tags()
            return summarize_live_inputs(rows)
    except (Level2Error, httpx.HTTPError) as exc:
        # OpenAPI allows 502 for upstream; imports use 503 — keep 502 for live.
        detail = str(exc) or "Level2 unreachable"
        return JSONResponse(
            status_code=502,
            content={"error": "level2_unavailable", "detail": detail},
        )
