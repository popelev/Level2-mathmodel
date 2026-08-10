"""Level2 HTTP client — read-only; no writes to Collector/PLC."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any
from urllib.parse import quote

import httpx

from .models import Sample

# Callback for optional WS subscribe stub / future real stream.
SampleHandler = Callable[[Sample], None]


class Level2Error(RuntimeError):
    """Base error for Level2 adapter failures."""


class Level2HTTPError(Level2Error):
    """Non-success HTTP response from Level2."""

    def __init__(self, message: str, *, status_code: int, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class Level2Client:
    """Read-only client for Level2 Collector REST API (OpenAPI 1.2.1).

    Intentionally has no PUT/POST write helpers for tag values or devices.
    """

    def __init__(
        self,
        base_url: str,
        *,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
        api_token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._owns_client = client is None
        headers: dict[str, str] = {}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
            headers["X-API-Token"] = api_token
        # Prefer injecting a Client (e.g. MockTransport) in unit tests.
        self._client = client or httpx.Client(timeout=timeout, headers=headers)
        if client is not None and api_token:
            # Injected clients keep caller-owned headers; stash for documentation.
            self._api_token = api_token
        else:
            self._api_token = api_token

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Level2Client:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def healthz(self) -> str:
        """GET /healthz — liveness; returns response text (typically ``ok``)."""
        response = self._client.get(f"{self.base_url}/healthz")
        self._raise_for_status(response, "GET /healthz")
        return response.text.strip()

    def readyz(self) -> bool:
        """GET /readyz — True when HTTP 200, False when 503 (not connected)."""
        response = self._client.get(f"{self.base_url}/readyz")
        if response.status_code == 200:
            return True
        if response.status_code == 503:
            return False
        self._raise_for_status(response, "GET /readyz")
        return False  # pragma: no cover

    def list_tags(self, device_id: str | None = None) -> list[dict[str, Any]]:
        """GET /api/v1/tags — tag rows with live samples (raw TagValue dicts)."""
        params: dict[str, str] = {}
        if device_id is not None:
            params["device_id"] = device_id
        response = self._client.get(
            f"{self.base_url}/api/v1/tags",
            params=params or None,
        )
        self._raise_for_status(response, "GET /api/v1/tags")
        data = response.json()
        if not isinstance(data, list):
            raise Level2Error("GET /api/v1/tags: expected JSON array")
        return data

    def get_tag_value(self, tag_id: str) -> Sample:
        """GET /api/v1/tags/{id}/value — last live sample as Sample DTO."""
        path = f"/api/v1/tags/{quote(tag_id, safe='')}/value"
        response = self._client.get(f"{self.base_url}{path}")
        self._raise_for_status(response, f"GET {path}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise Level2Error(f"GET {path}: expected JSON object")
        return Sample.from_dict(payload)

    def list_devices(self) -> list[dict[str, Any]]:
        """GET /api/v1/devices — device rows (raw Device dicts)."""
        response = self._client.get(f"{self.base_url}/api/v1/devices")
        self._raise_for_status(response, "GET /api/v1/devices")
        data = response.json()
        if not isinstance(data, list):
            raise Level2Error("GET /api/v1/devices: expected JSON array")
        return data

    def get_history(
        self,
        tag_id: str,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
    ) -> list[Sample]:
        """GET /api/v1/tags/{id}/history — minimal historian query."""
        path = f"/api/v1/tags/{quote(tag_id, safe='')}/history"
        params: dict[str, str | int] = {}
        if from_time is not None:
            params["from"] = from_time
        if to_time is not None:
            params["to"] = to_time
        if limit is not None:
            params["limit"] = limit
        response = self._client.get(
            f"{self.base_url}{path}",
            params=params or None,
        )
        self._raise_for_status(response, f"GET {path}")
        data = response.json()
        if not isinstance(data, list):
            raise Level2Error(f"GET {path}: expected JSON array")
        return [Sample.from_dict(item) for item in data]

    def subscribe(
        self,
        tag_ids: list[str] | None = None,
        *,
        on_sample: SampleHandler | None = None,
    ) -> Iterator[Sample]:
        """WebSocket live stream stub — not wired in Wave 1 unit tests.

        Real Level2 endpoint: ``GET /api/v1/ws/stream`` (upgrade). Callers that
        need live samples today should poll ``get_tag_value`` / ``list_tags``.
        """
        del tag_ids, on_sample
        raise NotImplementedError(
            "Wave1: WebSocket subscribe stub — use REST get_tag_value/list_tags; "
            "real WS at GET /api/v1/ws/stream"
        )

    @staticmethod
    def _raise_for_status(response: httpx.Response, action: str) -> None:
        if response.is_success:
            return
        body = response.text[:500]
        raise Level2HTTPError(
            f"{action} failed: HTTP {response.status_code}",
            status_code=response.status_code,
            body=body,
        )
