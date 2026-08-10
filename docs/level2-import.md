# Level2 tag import (mathmodel)

Read-only import of Level2 tags into the mathmodel **catalog** and optional **bindings**.
Model/plan outputs stay in **local vars** only. Mathmodel never writes to Level2/PLC.

Platform asks for Level2 (stable export endpoint, etc.) are filed in Jira — see
[`docs/cross-repo-coord.md`](cross-repo-coord.md) (**SCRUM-30**). This repo only
consumes the existing Collector HTTP API until that lands. Do not modify the
Level2 git repository from mathmodel workstreams.

## Env

| Variable | Role |
|----------|------|
| `LEVEL2_API_URL` | Base URL of Level2 Collector (required for import) |
| `LEVEL2_API_TOKEN` | Optional; sent as Bearer + `X-API-Token` |
| `MATHMODEL_IMPORT_STATE_PATH` | Optional JSON file for catalog + bindings persistence |

## What we call on Level2 today

- `GET /api/v1/devices`
- `GET /api/v1/tags`

Rows are normalized into `TagCatalogEntry` (`tag_id` + `device_id` as stable key).

## Mathmodel API

| Method | Path | Behavior |
|--------|------|----------|
| `POST` | `/api/v1/imports/level2/tags` | Fetch Level2 tags, upsert catalog; return counts |
| `POST` | `/api/v1/imports/level2/tags/preview` | Dry-run; no save; includes `preview` rows |
| `GET` | `/api/v1/imports/level2/catalog` | List catalog |
| `GET` | `/api/v1/bindings` | List bindings |
| `PUT` | `/api/v1/bindings` | Replace array, or `{mode, bindings}` replace/upsert |
| `DELETE` | `/api/v1/bindings/{logical_name}` | Delete one binding |

If Level2 is unreachable or `LEVEL2_API_URL` is missing → **503** JSON:

```json
{ "error": "level2_unavailable", "detail": "..." }
```

### Binding shape

```json
{
  "logical_name": "cell_current",
  "tag_id": "Cell.Current",
  "device_id": "sim_device",
  "role": "input",
  "section_id": "A",
  "cell_id": "12",
  "signal": "current"
}
```

`role` defaults to `input`. Optional copper refs: `section_id`, `cell_id`, `signal`.

Contract: [`contracts/mathmodel/openapi.yaml`](../contracts/mathmodel/openapi.yaml).
