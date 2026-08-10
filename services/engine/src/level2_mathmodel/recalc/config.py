"""Environment helpers and default trigger seeding for recalc polling."""

from __future__ import annotations

import os

from .handlers import COPPER_PLAN_HANDLER_ID
from .models import TriggerRule
from .store import TriggerStore

DEFAULT_FLAG_LOGICAL_NAME = "recalc_trigger"
DEFAULT_TRIGGER_ID = "default_recalc_trigger"


def env_truthy(name: str, default: str = "") -> bool:
    raw = os.environ.get(name, default).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def poll_interval_ms_from_env(default: int = 1000) -> int:
    raw = os.environ.get("POLL_INTERVAL_MS", "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(50, value)


def triggers_path_from_env() -> str | None:
    path = os.environ.get("RECALC_TRIGGERS_PATH", "").strip()
    return path or None


def seed_default_trigger(store: TriggerStore) -> bool:
    """If empty, seed one copper trigger from env/binding hint.

    Preference for the seed rule:
    1. logical_name ``recalc_trigger`` (resolved at poll time via bindings)
    2. plus optional ``RECALC_FLAG_TAG_ID`` as fallback tag_id on the same rule
    """
    tag_id = os.environ.get("RECALC_FLAG_TAG_ID", "").strip() or None
    # Always offer a sensible default seed when poll is enabled and store empty;
    # callers decide whether to seed.
    rule = TriggerRule(
        trigger_id=DEFAULT_TRIGGER_ID,
        handler_id=COPPER_PLAN_HANDLER_ID,
        logical_name=DEFAULT_FLAG_LOGICAL_NAME,
        tag_id=tag_id,
        edge_mode="rising_bool",
        enabled=True,
    )
    return store.seed_if_empty(rule)
