"""HTTP routes for local variables."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from level2_mathmodel.local_vars import (
    LocalVarExistsError,
    LocalVarNotFoundError,
    LocalVarStore,
    LocalVarValidationError,
)

router = APIRouter(prefix="/api/v1/local-vars", tags=["local_vars"])


def _store(request: Request) -> LocalVarStore:
    return request.app.state.local_vars


@router.get("", response_model=None)
def list_local_vars(request: Request) -> list[dict[str, Any]]:
    return _store(request).list()


@router.post("", status_code=201, response_model=None)
def create_local_var(request: Request, payload: dict[str, Any]) -> Any:
    try:
        return _store(request).create(payload)
    except LocalVarExistsError:
        return JSONResponse(status_code=409, content={"detail": "id already exists"})
    except LocalVarValidationError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})


@router.get("/{var_id}", response_model=None)
def get_local_var(request: Request, var_id: str) -> Any:
    try:
        return _store(request).get(var_id)
    except LocalVarNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "not found"})


@router.put("/{var_id}", response_model=None)
def replace_local_var(request: Request, var_id: str, payload: dict[str, Any]) -> Any:
    try:
        return _store(request).replace(var_id, payload)
    except LocalVarNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "not found"})
    except LocalVarValidationError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})


@router.delete("/{var_id}", status_code=204, response_model=None)
def delete_local_var(request: Request, var_id: str) -> Response:
    try:
        _store(request).delete(var_id)
    except LocalVarNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "not found"})
    return Response(status_code=204)
