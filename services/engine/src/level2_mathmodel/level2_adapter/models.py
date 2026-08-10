"""DTO mapping for Level2 Collector read responses (Sample and related)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Sample:
    """Live or historian sample — maps OpenAPI `Sample` schema."""

    time: str
    tag_id: str
    quality: int
    value_num: float | None = None
    value_text: str | None = None
    value_bool: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Sample:
        return cls(
            time=str(data["time"]),
            tag_id=str(data["tag_id"]),
            quality=int(data["quality"]),
            value_num=_optional_float(data.get("value_num")),
            value_text=_optional_str(data.get("value_text")),
            value_bool=_optional_bool(data.get("value_bool")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "tag_id": self.tag_id,
            "value_num": self.value_num,
            "value_text": self.value_text,
            "value_bool": self.value_bool,
            "quality": self.quality,
        }


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)
