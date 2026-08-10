"""Level2 HTTP client stub — read-only; no writes to Collector/PLC."""

from __future__ import annotations


class Level2Client:
    """Placeholder client. Wave 1 implements GET health/tags/devices only."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def healthz(self) -> str:
        raise NotImplementedError("Wave1: GET /healthz against Level2")

    def list_tags(self) -> list[dict]:
        raise NotImplementedError("Wave1: GET /api/v1/tags (read-only)")

    def list_devices(self) -> list[dict]:
        raise NotImplementedError("Wave1: GET /api/v1/devices (read-only)")
