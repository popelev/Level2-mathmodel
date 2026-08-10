"""FastAPI application — health + local-vars + plan + Level2 import + UI."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from level2_mathmodel.api.bindings import router as bindings_router
from level2_mathmodel.api.imports import default_level2_client_factory, router as imports_router
from level2_mathmodel.api.live import router as live_router
from level2_mathmodel.api.local_vars import router as local_vars_router
from level2_mathmodel.api.plan import router as plan_router
from level2_mathmodel.api.recalc import router as recalc_router
from level2_mathmodel.level2_adapter import Level2Client
from level2_mathmodel.local_vars import LocalVarStore
from level2_mathmodel.recalc import (
    RecalcScheduler,
    TriggerStore,
    env_truthy,
    poll_interval_ms_from_env,
    seed_default_trigger,
    triggers_path_from_env,
    watch_mode_from_env,
)
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
    trigger_store: TriggerStore | None = None,
    recalc_scheduler: RecalcScheduler | None = None,
) -> FastAPI:
    """Build the ASGI app. Inject stores / Level2 factory for tests."""
    local_store = store or LocalVarStore()
    persist = os.environ.get("MATHMODEL_IMPORT_STATE_PATH", "").strip() or None
    import_store = tag_import_store or TagImportStore(persist_path=persist)

    poll_enabled = env_truthy("RECALC_POLL_ENABLED")
    factory = level2_client_factory

    if recalc_scheduler is not None:
        scheduler = recalc_scheduler
        triggers = scheduler.triggers
        if factory is not None:
            scheduler.set_client_factory(factory)
    else:
        triggers = trigger_store or TriggerStore(persist_path=triggers_path_from_env())
        if poll_enabled:
            seed_default_trigger(triggers)
        scheduler = RecalcScheduler(
            local_vars=local_store,
            tag_import=import_store,
            triggers=triggers,
            level2_client_factory=factory or default_level2_client_factory,
            enabled=poll_enabled,
            default_poll_interval_ms=poll_interval_ms_from_env(),
            watch_mode=watch_mode_from_env(),
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        sched: RecalcScheduler = app.state.recalc_scheduler
        sched.start()
        try:
            yield
        finally:
            await sched.stop()

    app = FastAPI(
        title="Level2 Mathmodel API",
        version=SERVICE_VERSION,
        description=(
            "Engine-owned local variables + Level2 tag catalog import; "
            "multi-trigger recalc watch (WS/poll); no PLC / Level2 write."
        ),
        lifespan=lifespan,
    )
    app.state.local_vars = local_store
    app.state.tag_import = import_store
    app.state.trigger_store = triggers
    app.state.recalc_scheduler = scheduler
    if factory is not None:
        app.state.level2_client_factory = factory

    @app.get("/healthz", response_class=PlainTextResponse, tags=["health"])
    def healthz() -> str:
        return "ok"

    @app.get("/readyz", tags=["health"])
    def readyz() -> dict[str, Any]:
        """UI/BFF-compatible readiness (engine process is up)."""
        return {"ready": True, "service": SERVICE_NAME}

    @app.get("/api/v1/status", tags=["health"])
    def status() -> dict[str, Any]:
        local: LocalVarStore = app.state.local_vars
        imports: TagImportStore = app.state.tag_import
        sched: RecalcScheduler = app.state.recalc_scheduler
        recalc = sched.status_dict()
        last_ok = None
        last_error = None
        last_trigger_at = None
        for item in recalc.get("triggers") or []:
            state = item.get("state") or {}
            ts = state.get("last_trigger_at")
            if ts and (last_trigger_at is None or ts > last_trigger_at):
                last_trigger_at = ts
            if state.get("last_result") == "ok":
                last_ok = ts or state.get("last_poll_at")
            if state.get("last_result") == "error":
                last_error = state.get("last_error")
        return {
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "mode": "planning",
            "level2_api_url": os.environ.get("LEVEL2_API_URL", ""),
            "local_var_count": local.count(),
            "tag_catalog_count": imports.catalog_count(),
            "binding_count": imports.binding_count(),
            "recalc_poll_enabled": recalc["enabled"],
            "recalc_poll_running": recalc["running"],
            "recalc_watch_mode": recalc.get("watch_mode"),
            "recalc_ws_connected": recalc.get("ws_connected"),
            "recalc_trigger_count": recalc["trigger_count"],
            "recalc_last_trigger_at": last_trigger_at,
            "recalc_last_ok_at": last_ok,
            "recalc_last_error": last_error,
        }

    app.include_router(local_vars_router)
    app.include_router(plan_router)
    app.include_router(imports_router)
    app.include_router(bindings_router)
    app.include_router(live_router)
    app.include_router(recalc_router)
    _mount_web_ui(app)
    return app
