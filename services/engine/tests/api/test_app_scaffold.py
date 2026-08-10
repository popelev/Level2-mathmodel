"""API app smoke — FastAPI wiring for Wave 1."""

from __future__ import annotations

from fastapi import FastAPI

from level2_mathmodel.api.app import create_app


def test_create_app_is_fastapi() -> None:
    app = create_app()
    assert isinstance(app, FastAPI)
    paths = {route.path for route in app.routes}
    assert "/healthz" in paths
    assert "/api/v1/local-vars" in paths
    assert "/api/v1/status" in paths
