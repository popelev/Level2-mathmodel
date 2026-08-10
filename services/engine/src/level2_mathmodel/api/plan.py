"""Thin plan API — runs copper planner into local variables."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from copper_electrorefining.config import PlannerConfig
from level2_mathmodel.local_vars import LocalVarNotFoundError, LocalVarStore
from level2_mathmodel.plugins.copper_electrorefining import load_demo_plant, run_copper_plan

router = APIRouter(prefix="/api/v1/plan", tags=["plan"])


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _store(request: Request) -> LocalVarStore:
    return request.app.state.local_vars


def _count_or_zero(store: LocalVarStore, var_id: str) -> int:
    try:
        value = store.get(var_id)["value"]
    except LocalVarNotFoundError:
        return 0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    return 0


@router.get("", response_model=None)
def get_plan(request: Request) -> dict[str, Any]:
    store = _store(request)
    cathode_count = _count_or_zero(store, "plan.cathode_pull.count")
    anode_count = _count_or_zero(store, "plan.anode_change.count")
    has_plan = cathode_count > 0 or anode_count > 0
    try:
        store.get("plan.cathode_pull.queue")
        has_plan = True
    except LocalVarNotFoundError:
        pass
    return {
        "status": "ready" if has_plan else "pending",
        "message": (
            "Plan queues available in local variables"
            if has_plan
            else "No plan yet; POST /api/v1/plan to compute"
        ),
        "requested_at": _utc_now_iso(),
        "cathode_pull_count": cathode_count,
        "anode_change_count": anode_count,
        "local_var_ids": [
            "plan.cathode_pull.queue",
            "plan.anode_change.queue",
            "plan.cathode_pull.count",
            "plan.anode_change.count",
        ],
    }


@router.post("", status_code=202, response_model=None)
def post_plan(request: Request, payload: dict[str, Any] | None = None) -> Any:
    """Compute copper plan from demo plant snapshot; write local vars only."""
    body = payload or {}
    store = _store(request)
    plant = load_demo_plant()
    cfg = PlannerConfig()
    summary = run_copper_plan(store, plant, cfg)
    return JSONResponse(
        status_code=202,
        content={
            "status": summary["status"],
            "message": summary["message"],
            "requested_at": _utc_now_iso(),
            "horizon_hours": body.get("horizon_hours"),
            "local_var_ids": summary["local_var_ids"],
            "cathode_pull_count": summary["cathode_pull_count"],
            "anode_change_count": summary["anode_change_count"],
        },
    )
