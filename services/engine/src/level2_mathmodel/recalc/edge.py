"""Flag value coercion and edge detection (in-memory; no Level2 clear)."""

from __future__ import annotations

from typing import Any

from level2_mathmodel.level2_adapter.models import Sample

from .models import EdgeMode, TriggerRuntimeState, TriggerRule

# Level2 sample quality: 0 = Good, 1 = Bad (contracts/mathmodel OpenAPI).
QUALITY_GOOD = 0


def sample_raw_value(sample: Sample) -> Any:
    """Prefer bool, then num, then text from a Level2 Sample."""
    if sample.value_bool is not None:
        return bool(sample.value_bool)
    if sample.value_num is not None:
        return float(sample.value_num)
    if sample.value_text is not None:
        return str(sample.value_text)
    return None


def coerce_bool(value: Any) -> bool | None:
    """Best-effort bool coercion for rising_bool edge mode."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off", ""}:
            return False
    return None


def values_equal(a: Any, b: Any) -> bool:
    if a is None and b is None:
        return True
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return a == b


def detect_edge(
    rule: TriggerRule,
    state: TriggerRuntimeState,
    raw_value: Any,
) -> bool:
    """Return True when the configured edge condition fires.

    Semantics:
    - rising_bool: previous False and current True (first sample never fires).
    - value_changed: raw value differs from previous (first sample never fires).
    - equals: current raw equals ``rule.equals_value`` and previous did not
      (or previous was unset) — rising into the equals match.
    """
    mode: EdgeMode = rule.edge_mode
    if mode == "rising_bool":
        current = coerce_bool(raw_value)
        previous = state.last_bool
        # Always update tracking after call site; detection uses previous.
        if previous is None or current is None:
            return False
        return (not previous) and current

    if mode == "value_changed":
        if state.last_raw_value is None:
            return False
        return not values_equal(state.last_raw_value, raw_value)

    if mode == "equals":
        matched = values_equal(raw_value, rule.equals_value)
        prev_matched = (
            values_equal(state.last_raw_value, rule.equals_value)
            if state.last_raw_value is not None
            else False
        )
        if state.last_raw_value is None:
            return False
        return matched and not prev_matched

    return False


def update_edge_state(rule: TriggerRule, state: TriggerRuntimeState, raw_value: Any) -> None:
    """Advance in-memory previous value after a successful good-quality read."""
    state.last_raw_value = raw_value
    if rule.edge_mode == "rising_bool":
        state.last_bool = coerce_bool(raw_value)
