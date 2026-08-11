# `apps/api`

TypeScript BFF for the mathmodel OpenAPI contract.

## Modes

| Mode | Env | Behavior |
|------|-----|----------|
| **Mock (default)** | unset | In-memory seed catalog on `POST /api/v1/imports/level2/tags`; local bindings store |
| **Engine proxy** | `MATHMODEL_ENGINE_URL=http://host:port` | Proxies `/api/v1/imports/*`, `/api/v1/bindings*`, `/api/v1/status`, `/healthz`, `/readyz` to the real Python engine |

The **production** Level2 import/bindings implementation is in `services/engine` (see [`docs/level2-import.md`](../../docs/level2-import.md)). This BFF exists so the Web UI can develop against OpenAPI-shaped responses without a live engine/Level2.

## Commands

```bash
npm install
npm run start    # http://127.0.0.1:8090
npm run dev      # watch mode
npm test
npm run build    # typecheck
```

Port: `PORT` / `MATHMODEL_PORT` (default **8090**).

## Endpoints

- `GET /healthz`, `GET /readyz`, `GET /api/v1/status`
- `GET /api/v1/live/inputs`
- `GET|POST /api/v1/local-vars`, `GET|PUT|DELETE /api/v1/local-vars/{id}`
- `POST /api/v1/imports/level2/tags`, `POST /api/v1/imports/level2/tags/preview`
- `GET /api/v1/imports/level2/catalog`
- `GET|PUT /api/v1/bindings`, `DELETE /api/v1/bindings/{logical_name}`
- `GET|POST /api/v1/plan`
