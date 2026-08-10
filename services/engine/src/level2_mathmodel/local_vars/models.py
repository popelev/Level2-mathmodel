"""Local variable value types and sources (engine-owned only)."""

from __future__ import annotations

from typing import Any, Literal

LocalVarType = Literal["num", "bool", "text"]
LocalVarSource = Literal["planner", "operator", "model"]

ALLOWED_TYPES: frozenset[str] = frozenset({"num", "bool", "text"})
ALLOWED_SOURCES: frozenset[str] = frozenset({"planner", "operator", "model"})


def value_matches_type(var_type: str, value: Any) -> bool:
    """Return True if value is None or matches the declared type."""
    if value is None:
        return True
    if var_type == "num":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if var_type == "bool":
        return isinstance(value, bool)
    if var_type == "text":
        return isinstance(value, str)
    return False
