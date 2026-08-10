"""In-memory trigger config store with optional JSON persistence."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .models import TriggerRule, TriggerRuntimeState, normalize_trigger_rule


class TriggerNotFoundError(KeyError):
    """Raised when a trigger_id is missing."""


class TriggerStore:
    """Config registry for recalc triggers (+ optional file persist)."""

    def __init__(self, persist_path: str | Path | None = None) -> None:
        self._rules: dict[str, TriggerRule] = {}
        self._states: dict[str, TriggerRuntimeState] = {}
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path is not None and self._persist_path.is_file():
            self._load()

    def list_rules(self) -> list[TriggerRule]:
        return [deepcopy(r) for r in self._rules.values()]

    def get_rule(self, trigger_id: str) -> TriggerRule:
        if trigger_id not in self._rules:
            raise TriggerNotFoundError(trigger_id)
        return deepcopy(self._rules[trigger_id])

    def get_state(self, trigger_id: str) -> TriggerRuntimeState:
        if trigger_id not in self._states:
            self._states[trigger_id] = TriggerRuntimeState()
        return self._states[trigger_id]

    def upsert(self, rules: list[dict[str, Any] | TriggerRule]) -> list[dict[str, Any]]:
        """Upsert rules by trigger_id (keep others)."""
        for raw in rules:
            rule = raw if isinstance(raw, TriggerRule) else normalize_trigger_rule(raw)
            self._rules[rule.trigger_id] = rule
            if rule.trigger_id not in self._states:
                self._states[rule.trigger_id] = TriggerRuntimeState()
        self._save()
        return self.list_with_state()

    def replace(self, rules: list[dict[str, Any] | TriggerRule]) -> list[dict[str, Any]]:
        """Replace entire trigger list."""
        next_rules: dict[str, TriggerRule] = {}
        for raw in rules:
            rule = raw if isinstance(raw, TriggerRule) else normalize_trigger_rule(raw)
            next_rules[rule.trigger_id] = rule
        self._rules = next_rules
        # Drop runtime state for removed triggers; keep for survivors.
        self._states = {
            tid: self._states.get(tid) or TriggerRuntimeState() for tid in self._rules
        }
        self._save()
        return self.list_with_state()

    def delete(self, trigger_id: str) -> None:
        if trigger_id not in self._rules:
            raise TriggerNotFoundError(trigger_id)
        del self._rules[trigger_id]
        self._states.pop(trigger_id, None)
        self._save()

    def list_with_state(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for rule in self._rules.values():
            state = self.get_state(rule.trigger_id)
            item = rule.to_dict()
            item["state"] = state.to_dict()
            out.append(item)
        return out

    def count(self) -> int:
        return len(self._rules)

    def seed_if_empty(self, rule: TriggerRule) -> bool:
        """Insert a default rule only when the store has no triggers."""
        if self._rules:
            return False
        self._rules[rule.trigger_id] = rule
        self._states[rule.trigger_id] = TriggerRuntimeState()
        self._save()
        return True

    def _load(self) -> None:
        assert self._persist_path is not None
        data = json.loads(self._persist_path.read_text(encoding="utf-8"))
        triggers = data.get("triggers") if isinstance(data, dict) else data
        if not isinstance(triggers, list):
            raise ValueError("recalc triggers file must contain a triggers array")
        for raw in triggers:
            rule = normalize_trigger_rule(raw)
            self._rules[rule.trigger_id] = rule
            self._states[rule.trigger_id] = TriggerRuntimeState()

    def _save(self) -> None:
        if self._persist_path is None:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"triggers": [r.to_dict() for r in self._rules.values()]}
        self._persist_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
