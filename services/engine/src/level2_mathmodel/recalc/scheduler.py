"""Async poll scheduler: evaluate many triggers, invoke handlers, isolate errors."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import httpx

from level2_mathmodel.level2_adapter import Level2Client, Level2Error
from level2_mathmodel.local_vars import LocalVarStore
from level2_mathmodel.tag_import import TagImportStore

from .edge import (
    QUALITY_GOOD,
    detect_edge,
    sample_raw_value,
    update_edge_state,
)
from .handlers import HandlerRegistry
from .models import HandlerRunRecord, TriggerRule
from .store import TriggerStore

logger = logging.getLogger(__name__)

Level2ClientFactory = Callable[[], Level2Client]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class RecalcScheduler:
    """Poll Level2 flag tags and run registered handlers into local vars only.

    Default edge mode is rising_bool (false→true). Flag auto-clear is NOT done
    on Level2 (read-only client) — edge state is held in memory per trigger.
    """

    def __init__(
        self,
        *,
        local_vars: LocalVarStore,
        tag_import: TagImportStore,
        triggers: TriggerStore,
        handlers: HandlerRegistry | None = None,
        level2_client_factory: Level2ClientFactory | None = None,
        enabled: bool = False,
        default_poll_interval_ms: int = 1000,
    ) -> None:
        self.local_vars = local_vars
        self.tag_import = tag_import
        self.triggers = triggers
        self.handlers = handlers or HandlerRegistry()
        self._client_factory = level2_client_factory
        self.enabled = enabled
        self.default_poll_interval_ms = max(50, int(default_poll_interval_ms))
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()
        self._last_due: dict[str, float] = {}
        self._last_handler_runs: list[HandlerRunRecord] = []
        self._started_at: str | None = None
        self._last_loop_at: str | None = None
        self._loop_errors = 0

    def set_client_factory(self, factory: Level2ClientFactory | None) -> None:
        self._client_factory = factory

    def status_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "running": self._task is not None and not self._task.done(),
            "default_poll_interval_ms": self.default_poll_interval_ms,
            "trigger_count": self.triggers.count(),
            "handler_ids": self.handlers.list_ids(),
            "started_at": self._started_at,
            "last_loop_at": self._last_loop_at,
            "loop_errors": self._loop_errors,
            "triggers": self.triggers.list_with_state(),
            "last_handler_runs": [r.to_dict() for r in self._last_handler_runs[-20:]],
        }

    def resolve_tag_id(self, rule: TriggerRule) -> tuple[str | None, str]:
        """Resolve Level2 tag_id: binding logical_name first, then rule.tag_id."""
        if rule.logical_name:
            binding = self.tag_import.get_binding(rule.logical_name)
            if binding and binding.get("tag_id"):
                return str(binding["tag_id"]), "binding"
        if rule.tag_id:
            return rule.tag_id, "tag_id"
        return None, "none"

    def run_handler(
        self,
        handler_id: str,
        *,
        trigger_id: str | None = None,
    ) -> dict[str, Any]:
        """Manual or triggered handler invocation (local vars only)."""
        started = _utc_now_iso()
        record = HandlerRunRecord(
            handler_id=handler_id,
            trigger_id=trigger_id,
            started_at=started,
        )
        try:
            detail = self.handlers.run(
                handler_id,
                self.local_vars,
                trigger_id=trigger_id,
            )
            record.result = "ok"
            record.detail = detail if isinstance(detail, dict) else {"detail": detail}
            record.finished_at = _utc_now_iso()
            self._remember_run(record)
            return record.to_dict()
        except Exception as exc:  # noqa: BLE001 — isolate handler failures
            record.result = "error"
            record.error = str(exc) or exc.__class__.__name__
            record.finished_at = _utc_now_iso()
            self._remember_run(record)
            logger.exception(
                "recalc handler %s failed (trigger=%s)", handler_id, trigger_id
            )
            return record.to_dict()

    def tick_all(self) -> None:
        """Evaluate all enabled triggers that are due (sync; safe for tests)."""
        now_mono = time.monotonic()
        self._last_loop_at = _utc_now_iso()
        for rule in self.triggers.list_rules():
            if not rule.enabled:
                continue
            interval_ms = rule.poll_interval_ms or self.default_poll_interval_ms
            last = self._last_due.get(rule.trigger_id, 0.0)
            if (now_mono - last) * 1000.0 < interval_ms:
                continue
            self._last_due[rule.trigger_id] = now_mono
            try:
                self._evaluate_trigger(rule)
            except Exception as exc:  # noqa: BLE001 — never kill the loop
                self._loop_errors += 1
                state = self.triggers.get_state(rule.trigger_id)
                state.last_result = "error"
                state.last_error = str(exc) or exc.__class__.__name__
                state.last_skip_reason = None
                state.last_poll_at = _utc_now_iso()
                logger.exception("recalc trigger %s unexpected error", rule.trigger_id)

    def _evaluate_trigger(self, rule: TriggerRule) -> None:
        state = self.triggers.get_state(rule.trigger_id)
        state.last_poll_at = _utc_now_iso()

        tag_id, source = self.resolve_tag_id(rule)
        state.resolved_tag_id = tag_id
        if not tag_id:
            state.last_result = "skipped"
            state.last_skip_reason = "flag_unresolved"
            state.last_error = None
            return

        if self._client_factory is None:
            state.last_result = "skipped"
            state.last_skip_reason = "level2_client_unavailable"
            state.last_error = None
            return

        try:
            with self._client_factory() as client:
                sample = client.get_tag_value(tag_id)
        except (Level2Error, httpx.HTTPError, OSError) as exc:
            state.last_result = "skipped"
            state.last_skip_reason = "level2_error"
            state.last_error = str(exc) or exc.__class__.__name__
            logger.warning(
                "recalc trigger %s Level2 read failed (%s): %s",
                rule.trigger_id,
                source,
                exc,
            )
            return

        if sample.quality != QUALITY_GOOD:
            state.last_result = "skipped"
            state.last_skip_reason = "bad_quality"
            state.last_error = f"quality={sample.quality}"
            return

        raw = sample_raw_value(sample)
        if raw is None:
            state.last_result = "skipped"
            state.last_skip_reason = "empty_value"
            state.last_error = None
            # Do not advance edge state on empty reads.
            return

        fired = detect_edge(rule, state, raw)
        update_edge_state(rule, state, raw)
        if not fired:
            state.last_result = "skipped"
            state.last_skip_reason = "no_edge"
            state.last_error = None
            return

        state.last_trigger_at = _utc_now_iso()
        state.fire_count += 1
        logger.info(
            "recalc trigger %s fired → handler %s (tag=%s)",
            rule.trigger_id,
            rule.handler_id,
            tag_id,
        )
        run = self.run_handler(rule.handler_id, trigger_id=rule.trigger_id)
        if run.get("result") == "ok":
            state.last_result = "ok"
            state.last_error = None
            state.last_skip_reason = None
        else:
            state.last_result = "error"
            state.last_error = run.get("error")
            state.last_skip_reason = None

    async def run_loop(self) -> None:
        """Background asyncio loop; exits when stop() is requested."""
        interval_s = self.default_poll_interval_ms / 1000.0
        self._started_at = _utc_now_iso()
        logger.info(
            "recalc poll scheduler started (interval_ms=%s)",
            self.default_poll_interval_ms,
        )
        while not self._stop.is_set():
            try:
                self.tick_all()
            except Exception:  # noqa: BLE001
                self._loop_errors += 1
                logger.exception("recalc poll loop tick failed")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval_s)
            except TimeoutError:
                continue

    def start(self) -> asyncio.Task[None] | None:
        """Start background task when enabled. Idempotent."""
        if not self.enabled:
            return None
        if self._task is not None and not self._task.done():
            return self._task
        self._stop = asyncio.Event()
        self._task = asyncio.create_task(self.run_loop(), name="recalc-poll")
        return self._task

    async def stop(self) -> None:
        """Signal loop to stop and await the task."""
        self._stop.set()
        task = self._task
        self._task = None
        if task is not None:
            try:
                await asyncio.wait_for(task, timeout=5.0)
            except (TimeoutError, asyncio.CancelledError):
                task.cancel()

    def _remember_run(self, record: HandlerRunRecord) -> None:
        self._last_handler_runs.append(record)
        if len(self._last_handler_runs) > 50:
            self._last_handler_runs = self._last_handler_runs[-50:]
