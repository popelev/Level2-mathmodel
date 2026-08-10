"""Trigger / runtime models for multi-handler recalculation polling."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

EdgeMode = Literal["rising_bool", "value_changed", "equals"]
ALLOWED_EDGE_MODES: frozenset[str] = frozenset(
    {"rising_bool", "value_changed", "equals"}
)

TriggerResult = Literal["ok", "error", "skipped"]


@dataclass
class TriggerRule:
    """Config-driven flag → handler mapping (no Level2 writes)."""

    trigger_id: str
    handler_id: str
    logical_name: str | None = None
    tag_id: str | None = None
    device_id: str | None = None
    edge_mode: EdgeMode = "rising_bool"
    equals_value: Any = None
    enabled: bool = True
    poll_interval_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


@dataclass
class TriggerRuntimeState:
    """In-memory edge + last-run state for one trigger."""

    last_raw_value: Any = None
    last_bool: bool | None = None
    last_poll_at: str | None = None
    last_trigger_at: str | None = None
    last_result: TriggerResult | None = None
    last_error: str | None = None
    last_skip_reason: str | None = None
    fire_count: int = 0
    resolved_tag_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HandlerRunRecord:
    """Last manual or triggered handler execution summary."""

    handler_id: str
    trigger_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    result: TriggerResult | None = None
    error: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(asdict(self))


def normalize_trigger_rule(payload: dict[str, Any]) -> TriggerRule:
    """Validate/normalize a trigger rule dict."""
    if not isinstance(payload, dict):
        raise ValueError("trigger must be an object")
    trigger_id = payload.get("trigger_id")
    handler_id = payload.get("handler_id")
    if not isinstance(trigger_id, str) or not trigger_id.strip():
        raise ValueError("trigger_id is required")
    if not isinstance(handler_id, str) or not handler_id.strip():
        raise ValueError("handler_id is required")

    logical_name = payload.get("logical_name")
    tag_id = payload.get("tag_id")
    if logical_name is not None and (
        not isinstance(logical_name, str) or not logical_name.strip()
    ):
        raise ValueError("logical_name must be a non-empty string when set")
    if tag_id is not None and (not isinstance(tag_id, str) or not tag_id.strip()):
        raise ValueError("tag_id must be a non-empty string when set")
    if not logical_name and not tag_id:
        raise ValueError("logical_name and/or tag_id is required")

    edge_mode = payload.get("edge_mode", "rising_bool")
    if edge_mode not in ALLOWED_EDGE_MODES:
        raise ValueError(
            "edge_mode must be one of: rising_bool, value_changed, equals"
        )

    poll_interval_ms = payload.get("poll_interval_ms")
    if poll_interval_ms is not None:
        if not isinstance(poll_interval_ms, int) or isinstance(poll_interval_ms, bool):
            raise ValueError("poll_interval_ms must be an integer")
        if poll_interval_ms < 50:
            raise ValueError("poll_interval_ms must be >= 50")

    device_id = payload.get("device_id")
    if device_id is not None and not isinstance(device_id, str):
        raise ValueError("device_id must be a string when set")

    return TriggerRule(
        trigger_id=trigger_id.strip(),
        handler_id=handler_id.strip(),
        logical_name=logical_name.strip() if isinstance(logical_name, str) else None,
        tag_id=tag_id.strip() if isinstance(tag_id, str) else None,
        device_id=device_id if isinstance(device_id, str) else None,
        edge_mode=edge_mode,  # type: ignore[arg-type]
        equals_value=payload.get("equals_value"),
        enabled=bool(payload.get("enabled", True)),
        poll_interval_ms=poll_interval_ms,
    )
