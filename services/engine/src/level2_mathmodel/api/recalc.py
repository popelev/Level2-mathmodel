"""HTTP routes for multi-trigger recalc config and status."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from level2_mathmodel.recalc.scheduler import RecalcScheduler
from level2_mathmodel.recalc.store import TriggerNotFoundError

router = APIRouter(prefix="/api/v1/recalc", tags=["recalc"])


def _scheduler(request: Request) -> RecalcScheduler:
    return request.app.state.recalc_scheduler


@router.get("/status", response_model=None)
def get_recalc_status(request: Request) -> dict[str, Any]:
    return _scheduler(request).status_dict()


@router.get("/triggers", response_model=None)
def list_triggers(request: Request) -> list[dict[str, Any]]:
    return _scheduler(request).triggers.list_with_state()


@router.get("/handlers", response_model=None)
def list_handlers(request: Request) -> dict[str, Any]:
    return {"handler_ids": _scheduler(request).handlers.list_ids()}


@router.put("/triggers", response_model=None)
async def put_triggers(request: Request) -> Any:
    """Replace or upsert trigger rules.

    Body shapes:
    - ``[...triggers]`` — replace entire list
    - ``{"mode":"replace"|"upsert","triggers":[...]}`` — explicit mode
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "invalid JSON body"})

    store = _scheduler(request).triggers
    try:
        if isinstance(payload, list):
            return store.replace(payload)
        if isinstance(payload, dict):
            triggers = payload.get("triggers")
            if not isinstance(triggers, list):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "triggers array is required"},
                )
            mode = payload.get("mode", "replace")
            if mode == "upsert":
                return store.upsert(triggers)
            if mode == "replace":
                return store.replace(triggers)
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


@router.delete("/triggers/{trigger_id}", status_code=204, response_model=None)
def delete_trigger(request: Request, trigger_id: str) -> Any:
    try:
        _scheduler(request).triggers.delete(trigger_id)
    except TriggerNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "not found"})
    return Response(status_code=204)


@router.post("/run/{handler_id}", response_model=None)
def run_handler(request: Request, handler_id: str) -> Any:
    """Manually run a registered handler into local vars (no Level2 write)."""
    scheduler = _scheduler(request)
    if scheduler.handlers.get(handler_id) is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"unknown handler_id: {handler_id}"},
        )
    result = scheduler.run_handler(handler_id, trigger_id=None)
    status_code = 200 if result.get("result") == "ok" else 500
    return JSONResponse(status_code=status_code, content=result)
