# Recalc triggers (multi-flag / multi-handler)

Config-driven watching: many Level2 **flag tags** can fire many different
**recalculation handlers**. Handlers write **local variables only** — mathmodel
never writes back to Level2 / PLC.

Preferred path is a **WebSocket subscription** to Level2
`GET /api/v1/ws/stream?tag_id=…` (one JSON Sample per FanIn update). REST polling
remains available as an explicit mode or disconnect fallback.

## Trigger semantics

Default edge mode is **`rising_bool`**:

- Detect in-process transition **false → true**.
- Sustained `true` does **not** re-fire.
- First observed sample never fires (no previous value).
- Level2 flag auto-clear is **not** performed (read-only client); edge state is
  held in memory per `trigger_id`.

Other modes:

| `edge_mode` | Fires when |
|-------------|------------|
| `rising_bool` | bool false→true |
| `value_changed` | raw sample value differs from previous |
| `equals` | value becomes equal to `equals_value` (rising into match) |

Fail-safe per trigger (loop continues):

- Unresolved flag (no binding / tag_id)
- Level2 down / HTTP or WS error
- Bad quality (`quality != 0`)
- Empty sample value
- No edge

## Architecture

1. **Trigger registry** — rules (`trigger_id`, flag source, `edge_mode`,
   `handler_id`, `enabled`, optional `poll_interval_ms`).
2. **Handler registry** — pluggable callables by id.
3. **Watcher** — asyncio background task (FastAPI lifespan):
   - **`ws`** — `Level2Client.subscribe` on resolved tag ids; each Sample runs
     the same edge detect + handler path as poll.
   - **`poll`** — REST `get_tag_value` on an interval.
   - **`ws_with_poll_fallback`** — WS primary; light poll ticks while WS is
     disconnected.
4. Errors are isolated per trigger.

### Built-in handlers

| `handler_id` | Behavior |
|--------------|----------|
| `copper.plan_cathode_anode` | Copper planner → plan.* local vars |
| `generic.noop` | Heartbeat local var `recalc.<trigger_id>.last_run` |

## Flag resolution

For each rule, tag id is resolved as:

1. Binding `logical_name` → `tag_id` (preferred)
2. Else rule `tag_id`
3. Else skip (`flag_unresolved`)

Example binding:

```json
{
  "logical_name": "recalc_trigger",
  "tag_id": "Plant.Recalc.Flag",
  "device_id": "opc1",
  "role": "input"
}
```

## WebSocket vs poll

| Mode | How samples arrive | Latency | Notes |
|------|--------------------|---------|-------|
| `ws` | Level2 pushes Sample JSON on tag updates | Near real-time | Reconnect with exponential backoff; token via `LEVEL2_API_TOKEN` |
| `poll` | Engine calls REST every `POLL_INTERVAL_MS` | Up to interval | Useful for debugging / no WS |
| `ws_with_poll_fallback` | WS when connected; REST while down | Best-effort | Avoids missed edges during short disconnects |

## Environment

| Env | Default | Meaning |
|-----|---------|---------|
| `RECALC_POLL_ENABLED` | off | `1` / `true` starts the watcher |
| `RECALC_WATCH_MODE` | `ws` | `ws` \| `poll` \| `ws_with_poll_fallback` |
| `POLL_INTERVAL_MS` | `1000` | Poll interval / WS idle + fallback tick |
| `RECALC_TRIGGERS_PATH` | empty | Optional JSON persist for trigger config |
| `RECALC_FLAG_TAG_ID` | empty | Optional seed fallback tag on default trigger |
| `LEVEL2_API_TOKEN` | empty | Optional Bearer / X-API-Token / `?token=` for Level2 |

When the watcher is enabled and the trigger store is empty, a default rule is seeded:

- `trigger_id`: `default_recalc_trigger`
- `logical_name`: `recalc_trigger`
- `handler_id`: `copper.plan_cathode_anode`
- `tag_id`: from `RECALC_FLAG_TAG_ID` if set

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/recalc/status` | Watcher + last runs (`watch_mode`, `ws_connected`, …) |
| `GET` | `/api/v1/recalc/triggers` | Config + per-trigger state |
| `PUT` | `/api/v1/recalc/triggers` | Replace or upsert rules |
| `DELETE` | `/api/v1/recalc/triggers/{id}` | Remove one rule |
| `GET` | `/api/v1/recalc/handlers` | Registered handler ids |
| `POST` | `/api/v1/recalc/run/{handler_id}` | Manual run (local vars only) |

`GET /api/v1/status` also includes summary fields:
`recalc_poll_enabled`, `recalc_watch_mode`, `recalc_ws_connected`,
`recalc_trigger_count`, `recalc_last_trigger_at`, etc.

### Upsert example

```http
PUT /api/v1/recalc/triggers
Content-Type: application/json

{
  "mode": "upsert",
  "triggers": [
    {
      "trigger_id": "copper_on_flag",
      "logical_name": "recalc_trigger",
      "handler_id": "copper.plan_cathode_anode",
      "edge_mode": "rising_bool",
      "enabled": true
    },
    {
      "trigger_id": "noop_on_other",
      "tag_id": "Other.Flag",
      "handler_id": "generic.noop",
      "edge_mode": "rising_bool",
      "enabled": true
    }
  ]
}
```

## How to bind a flag (lab)

1. Import Level2 tags (`POST /api/v1/imports/level2/tags` or Import UI).
2. Create binding `logical_name=recalc_trigger` → your bool tag id.
3. Upsert a trigger rule pointing at that `logical_name` (or rely on the seeded default).
4. Set `RECALC_POLL_ENABLED=1` (and optionally `RECALC_WATCH_MODE=ws`) and rebuild/restart the mathmodel container.
5. Assert the Level2 flag false→true; check local vars / `GET /api/v1/recalc/status`.
