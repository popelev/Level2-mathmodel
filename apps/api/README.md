# `apps/api`

TypeScript **mock BFF** for Wave 1 — implements `contracts/mathmodel/openapi.yaml` with in-memory data.

Does **not** require live `services/engine` or Level2.

## Commands

```bash
npm install
npm run start    # http://127.0.0.1:8090
npm run dev      # watch mode
npm test
npm run build    # typecheck
```

Port: `PORT` / `MATHMODEL_PORT` (default **8090**).

## Endpoints (mock)

- `GET /healthz`, `GET /readyz`, `GET /api/v1/status`
- `GET /api/v1/live/inputs`
- `GET|POST /api/v1/local-vars`, `GET|PUT|DELETE /api/v1/local-vars/{id}`
- `GET|POST /api/v1/plan`
