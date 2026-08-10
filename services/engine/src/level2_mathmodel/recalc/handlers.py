"""Pluggable recalc handlers — write LocalVarStore only (never Level2)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from copper_electrorefining.config import PlannerConfig

from level2_mathmodel.local_vars import LocalVarStore
from level2_mathmodel.plugins.copper_electrorefining import load_demo_plant, run_copper_plan

HandlerFn = Callable[["HandlerContext"], dict[str, Any]]

COPPER_PLAN_HANDLER_ID = "copper.plan_cathode_anode"
GENERIC_NOOP_HANDLER_ID = "generic.noop"


@dataclass(frozen=True, slots=True)
class HandlerContext:
    """Context passed to a recalc handler."""

    store: LocalVarStore
    handler_id: str
    trigger_id: str | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def handle_copper_plan_cathode_anode(ctx: HandlerContext) -> dict[str, Any]:
    """Run copper cathode/anode planner into local variables."""
    plant = load_demo_plant()
    summary = run_copper_plan(ctx.store, plant, PlannerConfig())
    return {
        "status": "ok",
        "handler_id": ctx.handler_id,
        "trigger_id": ctx.trigger_id,
        "local_var_ids": summary.get("local_var_ids", []),
        "cathode_pull_count": summary.get("cathode_pull_count"),
        "anode_change_count": summary.get("anode_change_count"),
        "message": summary.get("message"),
    }


def handle_generic_noop(ctx: HandlerContext) -> dict[str, Any]:
    """Test/demo handler: upsert a namespaced heartbeat local var."""
    var_id = f"recalc.{ctx.handler_id}.last_run"
    if ctx.trigger_id:
        var_id = f"recalc.{ctx.trigger_id}.last_run"
    now = _utc_now_iso()
    ctx.store.upsert(
        {
            "id": var_id,
            "name": var_id,
            "type": "text",
            "value": now,
            "description": "Last noop recalc trigger time (local vars only)",
            "source": "model",
        }
    )
    return {
        "status": "ok",
        "handler_id": ctx.handler_id,
        "trigger_id": ctx.trigger_id,
        "local_var_ids": [var_id],
        "message": "noop handler wrote local heartbeat",
    }


class HandlerRegistry:
    """Map handler_id → callable. Built-ins registered by default."""

    def __init__(self) -> None:
        self._handlers: dict[str, HandlerFn] = {}
        self.register(COPPER_PLAN_HANDLER_ID, handle_copper_plan_cathode_anode)
        self.register(GENERIC_NOOP_HANDLER_ID, handle_generic_noop)

    def register(self, handler_id: str, fn: HandlerFn) -> None:
        if not handler_id or not handler_id.strip():
            raise ValueError("handler_id is required")
        self._handlers[handler_id.strip()] = fn

    def get(self, handler_id: str) -> HandlerFn | None:
        return self._handlers.get(handler_id)

    def require(self, handler_id: str) -> HandlerFn:
        fn = self.get(handler_id)
        if fn is None:
            raise KeyError(f"unknown handler_id: {handler_id}")
        return fn

    def list_ids(self) -> list[str]:
        return sorted(self._handlers)

    def run(
        self,
        handler_id: str,
        store: LocalVarStore,
        *,
        trigger_id: str | None = None,
    ) -> dict[str, Any]:
        fn = self.require(handler_id)
        return fn(HandlerContext(store=store, handler_id=handler_id, trigger_id=trigger_id))
