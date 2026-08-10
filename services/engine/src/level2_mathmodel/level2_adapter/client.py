"""Level2 HTTP/WS client — read-only; no writes to Collector/PLC."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Iterator
from typing import Any
from urllib.parse import quote, urlencode, urlparse, urlunparse

import httpx

from .models import Sample

# Callback for live Sample delivery (WS subscribe).
SampleHandler = Callable[[Sample], None]
ConnectionHandler = Callable[[bool], None]
StopPredicate = Callable[[], bool]
WsConnect = Callable[..., Any]

logger = logging.getLogger(__name__)


class Level2Error(RuntimeError):
    """Base error for Level2 adapter failures."""


class Level2HTTPError(Level2Error):
    """Non-success HTTP response from Level2."""

    def __init__(self, message: str, *, status_code: int, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class Level2Client:
    """Read-only client for Level2 Collector REST + WS API (OpenAPI 1.4.0).

    Intentionally has no PUT/POST write helpers for tag values or devices.
    Prefer ``get_tag_catalog`` for catalog import over ``list_tags``.
    """

    def __init__(
        self,
        base_url: str,
        *,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
        api_token: str | None = None,
        ws_connect: WsConnect | None = None,
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
        self._ws_connect = ws_connect

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

    def get_tag_catalog(self) -> dict[str, Any]:
        """GET /api/v1/integration/tag-catalog — flat export (OpenAPI 1.4.0+).

        Returns the raw catalog object with ``exported_at``, ``level2_api_version``,
        ``devices``, and ``tags`` (flat TagCatalogTag rows).
        """
        path = "/api/v1/integration/tag-catalog"
        response = self._client.get(f"{self.base_url}{path}")
        self._raise_for_status(response, f"GET {path}")
        data = response.json()
        if not isinstance(data, dict):
            raise Level2Error(f"GET {path}: expected JSON object")
        for key in ("exported_at", "level2_api_version", "devices", "tags"):
            if key not in data:
                raise Level2Error(f"GET {path}: missing field {key!r}")
        if not isinstance(data["devices"], list) or not isinstance(data["tags"], list):
            raise Level2Error(f"GET {path}: devices and tags must be arrays")
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

    def stream_url(self, tag_ids: list[str] | None = None) -> str:
        """Build ``ws(s)://…/api/v1/ws/stream`` URL with optional tag filter + token."""
        parsed = urlparse(self.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        path = (parsed.path.rstrip("/") + "/api/v1/ws/stream").replace("//", "/")
        if not path.startswith("/"):
            path = "/" + path
        query_items: list[tuple[str, str]] = []
        for tag_id in tag_ids or []:
            query_items.append(("tag_id", tag_id))
        if self._api_token:
            query_items.append(("token", self._api_token))
        query = urlencode(query_items)
        return urlunparse((scheme, parsed.netloc, path, "", query, ""))

    def subscribe(
        self,
        tag_ids: list[str] | None = None,
        *,
        on_sample: SampleHandler | None = None,
        on_connection_change: ConnectionHandler | None = None,
        should_stop: StopPredicate | None = None,
        reconnect: bool = True,
        initial_backoff_s: float = 0.5,
        max_backoff_s: float = 30.0,
    ) -> Iterator[Sample]:
        """Yield live Samples from ``GET /api/v1/ws/stream`` (WebSocket upgrade).

        Reconnects with exponential backoff when ``reconnect=True``. When
        ``LEVEL2_API_TOKEN`` / ``api_token`` is set, sends Bearer + X-API-Token
        headers and ``?token=`` query (Level2 WS auth).
        """
        connect = self._ws_connect
        if connect is None:
            from websockets.sync.client import connect as ws_connect

            connect = ws_connect

        ids = list(tag_ids or [])
        uri = self.stream_url(ids)
        headers: list[tuple[str, str]] = []
        if self._api_token:
            headers.append(("Authorization", f"Bearer {self._api_token}"))
            headers.append(("X-API-Token", self._api_token))

        backoff = max(0.05, float(initial_backoff_s))
        max_backoff = max(backoff, float(max_backoff_s))
        stop = should_stop or (lambda: False)

        while not stop():
            try:
                with connect(uri, additional_headers=headers) as ws:
                    if on_connection_change is not None:
                        on_connection_change(True)
                    backoff = max(0.05, float(initial_backoff_s))
                    if ids:
                        # Server also accepts query filter; subscribe message
                        # replaces the filter if the client needs to refresh.
                        ws.send(json.dumps({"subscribe": ids}))
                    for message in ws:
                        if stop():
                            return
                        sample = self._sample_from_ws_message(message)
                        if sample is None:
                            continue
                        if on_sample is not None:
                            on_sample(sample)
                        yield sample
            except Exception as exc:  # noqa: BLE001 — reconnect path
                if on_connection_change is not None:
                    on_connection_change(False)
                if stop() or not reconnect:
                    raise Level2Error(f"WS subscribe failed: {exc}") from exc
                logger.warning(
                    "Level2 WS disconnected (%s); reconnect in %.1fs",
                    exc,
                    backoff,
                )
                deadline = time.monotonic() + backoff
                while time.monotonic() < deadline:
                    if stop():
                        return
                    time.sleep(min(0.1, deadline - time.monotonic()))
                backoff = min(backoff * 2.0, max_backoff)
                continue

            # Clean server close — reconnect unless stopped.
            if on_connection_change is not None:
                on_connection_change(False)
            if stop() or not reconnect:
                return
            logger.info("Level2 WS stream ended; reconnect in %.1fs", backoff)
            deadline = time.monotonic() + backoff
            while time.monotonic() < deadline:
                if stop():
                    return
                time.sleep(min(0.1, deadline - time.monotonic()))
            backoff = min(backoff * 2.0, max_backoff)

    @staticmethod
    def _sample_from_ws_message(message: Any) -> Sample | None:
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        if not isinstance(message, str):
            return None
        text = message.strip()
        if not text:
            return None
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            logger.debug("Ignoring non-JSON WS message")
            return None
        if not isinstance(payload, dict):
            return None
        # Ignore control / ack frames that are not Samples.
        if "tag_id" not in payload or "quality" not in payload or "time" not in payload:
            return None
        try:
            return Sample.from_dict(payload)
        except (KeyError, TypeError, ValueError) as exc:
            logger.debug("Ignoring invalid WS Sample: %s", exc)
            return None

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
