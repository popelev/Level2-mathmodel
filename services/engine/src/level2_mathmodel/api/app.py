"""FastAPI application — health + local-vars (Wave 1)."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from level2_mathmodel.api.local_vars import router as local_vars_router
from level2_mathmodel.local_vars import LocalVarStore

SERVICE_NAME = "level2-mathmodel"
SERVICE_VERSION = "0.1.0-draft"


def create_app(store: LocalVarStore | None = None) -> FastAPI:
    """Build the ASGI app. Inject ``store`` for tests."""
    app = FastAPI(
        title="Level2 Mathmodel API",
        version=SERVICE_VERSION,
        description="Engine-owned local variables; no PLC / Level2 write.",
    )
    app.state.local_vars = store or LocalVarStore()

    @app.get("/healthz", response_class=PlainTextResponse, tags=["health"])
    def healthz() -> str:
        return "ok"

    @app.get("/api/v1/status", tags=["health"])
    def status() -> dict[str, Any]:
        local_store: LocalVarStore = app.state.local_vars
        return {
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "mode": "monitoring",
            "level2_api_url": os.environ.get("LEVEL2_API_URL", ""),
            "local_var_count": local_store.count(),
        }

    app.include_router(local_vars_router)
    return app
