"""Rule-based queues for cathode pull and anode change."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .config import PlannerConfig
from .domain import Section
from .kpi import estimate_cell_ampere_hours


@dataclass(slots=True)
class PlanQueues:
    """Planner output queues (oldest / most overdue first)."""

    cathode_pull: list[dict[str, Any]]
    anode_change: list[dict[str, Any]]


def _cathode_due(age_hours: float | None, ampere_hours: float | None, cfg: PlannerConfig) -> bool:
    if age_hours is not None and age_hours >= cfg.cathode_max_age_hours:
        return True
    if (
        cfg.cathode_ampere_hours_threshold is not None
        and ampere_hours is not None
        and ampere_hours >= cfg.cathode_ampere_hours_threshold
    ):
        return True
    return False


def build_queues(plant: list[Section], config: PlannerConfig | None = None) -> PlanQueues:
    """Build cathode-pull and anode-change queues from age/threshold rules."""
    cfg = config or PlannerConfig()
    cathode_pull: list[dict[str, Any]] = []
    anode_change: list[dict[str, Any]] = []

    for section in plant:
        for cell in section.cells:
            for cathode in cell.cathodes:
                ampere_hours = cathode.ampere_hours
                if ampere_hours is None:
                    ampere_hours = estimate_cell_ampere_hours(cell.current_a, cathode.age_hours)
                if _cathode_due(cathode.age_hours, ampere_hours, cfg):
                    cathode_pull.append(
                        {
                            "section_id": section.id,
                            "cell_id": cell.id,
                            "cathode_id": cathode.id,
                            "age_hours": cathode.age_hours,
                            "ampere_hours": ampere_hours,
                        }
                    )
            for anode in cell.anodes:
                if anode.age_hours is not None and anode.age_hours >= cfg.anode_max_age_hours:
                    anode_change.append(
                        {
                            "section_id": section.id,
                            "cell_id": cell.id,
                            "anode_id": anode.id,
                            "age_hours": anode.age_hours,
                            "mass_kg": anode.mass_kg,
                        }
                    )

    cathode_pull.sort(key=lambda item: item.get("age_hours") or 0.0, reverse=True)
    anode_change.sort(key=lambda item: item.get("age_hours") or 0.0, reverse=True)
    return PlanQueues(cathode_pull=cathode_pull, anode_change=anode_change)


# Local variable keys written by the planner (engine-owned only).
PLAN_CATHODE_PULL_QUEUE = "plan.cathode_pull.queue"
PLAN_ANODE_CHANGE_QUEUE = "plan.anode_change.queue"
PLAN_CATHODE_PULL_COUNT = "plan.cathode_pull.count"
PLAN_ANODE_CHANGE_COUNT = "plan.anode_change.count"


def plan_to_local_payloads(result: PlanQueues) -> list[dict[str, Any]]:
    """Serialize plan queues into LocalVarStore upsert payloads (text/num)."""
    return [
        {
            "id": PLAN_CATHODE_PULL_QUEUE,
            "name": "Cathode pull queue",
            "type": "text",
            "value": json.dumps(result.cathode_pull, separators=(",", ":")),
            "source": "planner",
            "description": "Ordered cathode pull queue (JSON list)",
        },
        {
            "id": PLAN_ANODE_CHANGE_QUEUE,
            "name": "Anode change queue",
            "type": "text",
            "value": json.dumps(result.anode_change, separators=(",", ":")),
            "source": "planner",
            "description": "Ordered anode change queue (JSON list)",
        },
        {
            "id": PLAN_CATHODE_PULL_COUNT,
            "name": "Cathode pull count",
            "type": "num",
            "value": len(result.cathode_pull),
            "source": "planner",
            "description": "Number of cathodes due for pull",
        },
        {
            "id": PLAN_ANODE_CHANGE_COUNT,
            "name": "Anode change count",
            "type": "num",
            "value": len(result.anode_change),
            "source": "planner",
            "description": "Number of anodes due for change",
        },
    ]
