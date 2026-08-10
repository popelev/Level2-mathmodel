"""Multi-trigger recalc scheduler — mocked Level2Client edge cases."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from level2_mathmodel.level2_adapter import Level2Error
from level2_mathmodel.level2_adapter.models import Sample
from level2_mathmodel.local_vars import LocalVarStore
from level2_mathmodel.recalc import (
    COPPER_PLAN_HANDLER_ID,
    GENERIC_NOOP_HANDLER_ID,
    HandlerRegistry,
    RecalcScheduler,
    TriggerRule,
    TriggerStore,
)
from level2_mathmodel.tag_import import TagImportStore


def _sample(
    tag_id: str,
    *,
    value_bool: bool | None = None,
    value_num: float | None = None,
    quality: int = 0,
) -> Sample:
    return Sample(
        time="2026-08-10T10:00:00Z",
        tag_id=tag_id,
        quality=quality,
        value_num=value_num,
        value_bool=value_bool,
    )


def _scheduler(
    *,
    rules: list[TriggerRule],
    get_tag_value: Any,
    bindings: list[dict[str, Any]] | None = None,
) -> RecalcScheduler:
    local = LocalVarStore()
    tags = TagImportStore()
    if bindings:
        tags.replace_bindings(bindings)
    store = TriggerStore()
    store.replace([r.to_dict() for r in rules])
    client = MagicMock()
    client.get_tag_value.side_effect = get_tag_value
    client.__enter__.return_value = client
    client.__exit__.return_value = None

    def factory() -> Any:
        return client

    return RecalcScheduler(
        local_vars=local,
        tag_import=tags,
        triggers=store,
        handlers=HandlerRegistry(),
        level2_client_factory=factory,
        enabled=False,
        default_poll_interval_ms=50,
    )


def test_two_triggers_independent_rising_edges() -> None:
    values = {
        "flag-a": False,
        "flag-b": False,
    }

    def get_tag_value(tag_id: str) -> Sample:
        return _sample(tag_id, value_bool=values[tag_id])

    sched = _scheduler(
        rules=[
            TriggerRule(
                trigger_id="t_a",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                tag_id="flag-a",
                edge_mode="rising_bool",
            ),
            TriggerRule(
                trigger_id="t_b",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                tag_id="flag-b",
                edge_mode="rising_bool",
            ),
        ],
        get_tag_value=get_tag_value,
    )

    # Prime previous=false (no fire on first sample).
    sched.tick_all()
    assert sched.triggers.get_state("t_a").fire_count == 0
    assert sched.triggers.get_state("t_b").fire_count == 0

    values["flag-a"] = True
    sched._last_due.clear()
    sched.tick_all()
    assert sched.triggers.get_state("t_a").fire_count == 1
    assert sched.triggers.get_state("t_a").last_result == "ok"
    assert sched.triggers.get_state("t_b").fire_count == 0
    assert sched.triggers.get_state("t_b").last_skip_reason == "no_edge"

    # Sustained true on A must not re-fire; rising B fires independently.
    sched._last_due.clear()
    sched.tick_all()
    assert sched.triggers.get_state("t_a").fire_count == 1

    values["flag-b"] = True
    sched._last_due.clear()
    sched.tick_all()
    assert sched.triggers.get_state("t_a").fire_count == 1
    assert sched.triggers.get_state("t_b").fire_count == 1
    assert "recalc.t_a.last_run" in {v["id"] for v in sched.local_vars.list()}
    assert "recalc.t_b.last_run" in {v["id"] for v in sched.local_vars.list()}


def test_different_handlers_copper_and_noop() -> None:
    values = {"plan-flag": False, "noop-flag": False}

    def get_tag_value(tag_id: str) -> Sample:
        return _sample(tag_id, value_bool=values[tag_id])

    sched = _scheduler(
        rules=[
            TriggerRule(
                trigger_id="copper_trig",
                handler_id=COPPER_PLAN_HANDLER_ID,
                tag_id="plan-flag",
            ),
            TriggerRule(
                trigger_id="noop_trig",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                tag_id="noop-flag",
            ),
        ],
        get_tag_value=get_tag_value,
    )
    sched.tick_all()
    values["plan-flag"] = True
    values["noop-flag"] = True
    sched._last_due.clear()
    sched.tick_all()

    assert sched.triggers.get_state("copper_trig").last_result == "ok"
    assert sched.triggers.get_state("noop_trig").last_result == "ok"
    ids = {v["id"] for v in sched.local_vars.list()}
    assert "plan.cathode_pull.queue" in ids
    assert "recalc.noop_trig.last_run" in ids


def test_no_edge_skips_handler() -> None:
    client_calls = {"n": 0}

    def get_tag_value(tag_id: str) -> Sample:
        client_calls["n"] += 1
        return _sample(tag_id, value_bool=True)

    sched = _scheduler(
        rules=[
            TriggerRule(
                trigger_id="t1",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                tag_id="flag-1",
            )
        ],
        get_tag_value=get_tag_value,
    )
    # First true: no previous false → no fire.
    sched.tick_all()
    assert sched.triggers.get_state("t1").fire_count == 0
    assert sched.triggers.get_state("t1").last_skip_reason == "no_edge"
    assert sched.local_vars.count() == 0


def test_bad_quality_skips_without_advancing_edge() -> None:
    quality = {"q": 1}
    flag = {"v": False}

    def get_tag_value(tag_id: str) -> Sample:
        return _sample(tag_id, value_bool=flag["v"], quality=quality["q"])

    sched = _scheduler(
        rules=[
            TriggerRule(
                trigger_id="t1",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                tag_id="flag-1",
            )
        ],
        get_tag_value=get_tag_value,
    )
    sched.tick_all()
    assert sched.triggers.get_state("t1").last_skip_reason == "bad_quality"
    assert sched.triggers.get_state("t1").last_bool is None

    # Good false then rising true must still fire (edge not poisoned by bad quality).
    quality["q"] = 0
    flag["v"] = False
    sched._last_due.clear()
    sched.tick_all()
    flag["v"] = True
    sched._last_due.clear()
    sched.tick_all()
    assert sched.triggers.get_state("t1").fire_count == 1


def test_level2_error_skips_other_triggers_continue() -> None:
    def get_tag_value(tag_id: str) -> Sample:
        if tag_id == "bad":
            raise Level2Error("down")
        return _sample(tag_id, value_bool=True)

    sched = _scheduler(
        rules=[
            TriggerRule(
                trigger_id="t_bad",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                tag_id="bad",
            ),
            TriggerRule(
                trigger_id="t_ok",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                tag_id="good",
            ),
        ],
        get_tag_value=get_tag_value,
    )
    # Prime good trigger with false first via direct state, then evaluate.
    # Force rising: set previous false, then read true.
    sched.triggers.get_state("t_ok").last_bool = False
    sched.triggers.get_state("t_ok").last_raw_value = False
    sched.tick_all()
    assert sched.triggers.get_state("t_bad").last_skip_reason == "level2_error"
    assert sched.triggers.get_state("t_ok").fire_count == 1


def test_binding_logical_name_preferred_over_tag_id() -> None:
    seen: list[str] = []

    def get_tag_value(tag_id: str) -> Sample:
        seen.append(tag_id)
        return _sample(tag_id, value_bool=False)

    sched = _scheduler(
        rules=[
            TriggerRule(
                trigger_id="t1",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                logical_name="recalc_trigger",
                tag_id="fallback-tag",
            )
        ],
        get_tag_value=get_tag_value,
        bindings=[
            {
                "logical_name": "recalc_trigger",
                "tag_id": "bound-tag",
                "device_id": "dev1",
                "role": "input",
            }
        ],
    )
    sched.tick_all()
    assert seen == ["bound-tag"]
    assert sched.triggers.get_state("t1").resolved_tag_id == "bound-tag"


def test_value_changed_and_equals_modes() -> None:
    value = {"n": 1.0}

    def get_tag_value(tag_id: str) -> Sample:
        return _sample(tag_id, value_num=value["n"])

    sched = _scheduler(
        rules=[
            TriggerRule(
                trigger_id="chg",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                tag_id="n1",
                edge_mode="value_changed",
            ),
            TriggerRule(
                trigger_id="eq",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                tag_id="n1",
                edge_mode="equals",
                equals_value=2.0,
            ),
        ],
        get_tag_value=get_tag_value,
    )
    sched.tick_all()
    assert sched.triggers.get_state("chg").fire_count == 0
    assert sched.triggers.get_state("eq").fire_count == 0

    value["n"] = 2.0
    sched._last_due.clear()
    sched.tick_all()
    assert sched.triggers.get_state("chg").fire_count == 1
    assert sched.triggers.get_state("eq").fire_count == 1


def test_handler_error_isolated() -> None:
    registry = HandlerRegistry()

    def boom(_ctx: Any) -> dict[str, Any]:
        raise RuntimeError("handler boom")

    registry.register("test.boom", boom)

    def get_tag_value(tag_id: str) -> Sample:
        return _sample(tag_id, value_bool=True)

    local = LocalVarStore()
    tags = TagImportStore()
    store = TriggerStore()
    store.replace(
        [
            TriggerRule(
                trigger_id="boom",
                handler_id="test.boom",
                tag_id="f1",
            ).to_dict(),
            TriggerRule(
                trigger_id="ok",
                handler_id=GENERIC_NOOP_HANDLER_ID,
                tag_id="f2",
            ).to_dict(),
        ]
    )
    client = MagicMock()
    client.get_tag_value.side_effect = get_tag_value
    client.__enter__.return_value = client
    client.__exit__.return_value = None

    sched = RecalcScheduler(
        local_vars=local,
        tag_import=tags,
        triggers=store,
        handlers=registry,
        level2_client_factory=lambda: client,
        enabled=False,
        default_poll_interval_ms=50,
    )
    sched.triggers.get_state("boom").last_bool = False
    sched.triggers.get_state("boom").last_raw_value = False
    sched.triggers.get_state("ok").last_bool = False
    sched.triggers.get_state("ok").last_raw_value = False
    sched.tick_all()
    assert sched.triggers.get_state("boom").last_result == "error"
    assert sched.triggers.get_state("ok").last_result == "ok"
