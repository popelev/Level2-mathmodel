"""API app smoke — FastAPI wiring for Wave 1."""

from __future__ import annotations

from fastapi import FastAPI

from level2_mathmodel.api.app import create_app


def test_create_app_is_fastapi() -> None:
    app = create_app()
    assert isinstance(app, FastAPI)
    paths = set(app.openapi()["paths"])
    assert "/healthz" in paths
    assert "/api/v1/local-vars" in paths
    assert "/api/v1/status" in paths
    assert "/api/v1/plan" in paths
    assert "/api/v1/imports/level2/tags" in paths
    assert "/api/v1/imports/level2/catalog" in paths
    assert "/api/v1/bindings" in paths
