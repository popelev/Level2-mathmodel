"""HTTP routes for logical tag bindings (catalog → model inputs)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from level2_mathmodel.tag_import import BindingNotFoundError, TagImportStore

router = APIRouter(prefix="/api/v1/bindings", tags=["bindings"])


def _store(request: Request) -> TagImportStore:
    return request.app.state.tag_import


@router.get("", response_model=None)
def list_bindings(request: Request) -> list[dict[str, Any]]:
    return _store(request).list_bindings()


@router.put("", response_model=None)
async def put_bindings(request: Request) -> Any:
    """Replace or upsert bindings.

    Body shapes:
    - ``[...bindings]`` — replace entire list
    - ``{"mode":"replace"|"upsert","bindings":[...]}`` — explicit mode
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "invalid JSON body"})

    store = _store(request)
    try:
        if isinstance(payload, list):
            return store.replace_bindings(payload)
        if isinstance(payload, dict):
            bindings = payload.get("bindings")
            if not isinstance(bindings, list):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "bindings array is required"},
                )
            mode = payload.get("mode", "replace")
            if mode == "upsert":
                return store.upsert_bindings(bindings)
            if mode == "replace":
                return store.replace_bindings(bindings)
            return JSONResponse(
                status_code=400,
                content={"detail": "mode must be replace or upsert"},
            )
        return JSONResponse(
            status_code=400,
            content={"detail": "body must be an array or object"},
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})


@router.delete("/{logical_name}", status_code=204, response_model=None)
def delete_binding(request: Request, logical_name: str) -> Response:
    try:
        _store(request).delete_binding(logical_name)
    except BindingNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "not found"})
    return Response(status_code=204)
