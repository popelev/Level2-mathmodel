"""FastAPI application — health + local-vars + plan + Level2 import + UI."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from level2_mathmodel.api.bindings import router as bindings_router
from level2_mathmodel.api.imports import router as imports_router
from level2_mathmodel.api.local_vars import router as local_vars_router
from level2_mathmodel.api.plan import router as plan_router
from level2_mathmodel.level2_adapter import Level2Client
from level2_mathmodel.local_vars import LocalVarStore
from level2_mathmodel.tag_import import TagImportStore

SERVICE_NAME = "level2-mathmodel"
SERVICE_VERSION = "0.2.0-draft"

Level2ClientFactory = Callable[[], Level2Client]


def _mount_web_ui(app: FastAPI) -> None:
    """Serve built React UI from MATHMODEL_WEB_DIST when present (lab image)."""
    raw = os.environ.get("MATHMODEL_WEB_DIST", "").strip()
    if not raw:
        return
    dist = Path(raw)
    index = dist / "index.html"
    if not index.is_file():
        return

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="web-assets")

    @app.get("/", include_in_schema=False)
    def web_index() -> FileResponse:
        return FileResponse(index)


def create_app(
    store: LocalVarStore | None = None,
    *,
    tag_import_store: TagImportStore | None = None,
    level2_client_factory: Level2ClientFactory | None = None,
) -> FastAPI:
    """Build the ASGI app. Inject stores / Level2 factory for tests."""
    app = FastAPI(
        title="Level2 Mathmodel API",
        version=SERVICE_VERSION,
        description=(
            "Engine-owned local variables + Level2 tag catalog import; "
            "no PLC / Level2 write."
        ),
    )
    persist = os.environ.get("MATHMODEL_IMPORT_STATE_PATH", "").strip() or None
    app.state.local_vars = store or LocalVarStore()
    app.state.tag_import = tag_import_store or TagImportStore(persist_path=persist)
    if level2_client_factory is not None:
        app.state.level2_client_factory = level2_client_factory

    @app.get("/healthz", response_class=PlainTextResponse, tags=["health"])
    def healthz() -> str:
        return "ok"

    @app.get("/readyz", tags=["health"])
    def readyz() -> dict[str, Any]:
        """UI/BFF-compatible readiness (engine process is up)."""
        return {"ready": True, "service": SERVICE_NAME}

    @app.get("/api/v1/status", tags=["health"])
    def status() -> dict[str, Any]:
        local_store: LocalVarStore = app.state.local_vars
        import_store: TagImportStore = app.state.tag_import
        return {
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "mode": "planning",
            "level2_api_url": os.environ.get("LEVEL2_API_URL", ""),
            "local_var_count": local_store.count(),
            "tag_catalog_count": import_store.catalog_count(),
            "binding_count": import_store.binding_count(),
        }

    app.include_router(local_vars_router)
    app.include_router(plan_router)
    app.include_router(imports_router)
    app.include_router(bindings_router)
    _mount_web_ui(app)
    return app
