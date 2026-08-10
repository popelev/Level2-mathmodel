"""HTTP routes for Level2 tag import (read-only from LEVEL2_API_URL)."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from level2_mathmodel.level2_adapter import Level2Client, Level2Error
from level2_mathmodel.tag_import import TagImportStore, import_level2_tags

router = APIRouter(tags=["imports"])

Level2ClientFactory = Callable[[], Level2Client]


def _catalog_store(request: Request) -> TagImportStore:
    return request.app.state.tag_import


def _client_factory(request: Request) -> Level2ClientFactory:
    factory = getattr(request.app.state, "level2_client_factory", None)
    if factory is not None:
        return factory
    return default_level2_client_factory


def default_level2_client_factory() -> Level2Client:
    """Build Level2Client from LEVEL2_API_URL (+ optional LEVEL2_API_TOKEN)."""
    base = os.environ.get("LEVEL2_API_URL", "").strip()
    if not base:
        raise Level2Error("LEVEL2_API_URL is not set")
    token = os.environ.get("LEVEL2_API_TOKEN", "").strip() or None
    return Level2Client(base, api_token=token)


def _level2_unavailable(exc: Exception) -> JSONResponse:
    detail = str(exc) or "Level2 unreachable"
    return JSONResponse(
        status_code=503,
        content={
            "error": "level2_unavailable",
            "detail": detail,
        },
    )


@router.post("/api/v1/imports/level2/tags", response_model=None)
def import_level2_tags_route(request: Request) -> Any:
    store = _catalog_store(request)
    factory = _client_factory(request)
    try:
        with factory() as client:
            return import_level2_tags(client, store, dry_run=False)
    except (Level2Error, httpx.HTTPError) as exc:
        return _level2_unavailable(exc)


@router.post("/api/v1/imports/level2/tags/preview", response_model=None)
def preview_level2_tags_route(request: Request) -> Any:
    store = _catalog_store(request)
    factory = _client_factory(request)
    try:
        with factory() as client:
            return import_level2_tags(client, store, dry_run=True)
    except (Level2Error, httpx.HTTPError) as exc:
        return _level2_unavailable(exc)


@router.get("/api/v1/imports/level2/catalog", response_model=None)
def list_level2_catalog(request: Request) -> list[dict[str, Any]]:
    return _catalog_store(request).list_catalog()
