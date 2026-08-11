# `apps/web`

React + Vite UI for Level2-mathmodel.

## Screens (tab navigation)

| Tab | Purpose |
|-----|---------|
| **Status** | Engine/BFF readiness |
| **Live inputs** | Mock live tag snapshot |
| **Local variables** | List/edit local vars |
| **Import from Level2** | Catalog import + bindings editor (`logical_name` → `tag_id`) |
| **Plan** | Planning stub |

There is no client-side router: sections are in-app tabs on `/` (Vite default).

## API wiring

UI calls OpenAPI paths:

- `POST /api/v1/imports/level2/tags`
- `GET /api/v1/imports/level2/catalog`
- `GET|PUT /api/v1/bindings`
- `DELETE /api/v1/bindings/{logical_name}`

Vite proxies `/api`, `/healthz`, `/readyz` to `VITE_PROXY_TARGET` (default `http://127.0.0.1:8090` = mock BFF).

### Mock vs real engine

| Mode | How |
|------|-----|
| **Mock BFF (default)** | Start `apps/api` (`npm run start`). Seed catalog on Import. |
| **Proxy BFF → engine** | Run BFF with `MATHMODEL_ENGINE_URL=http://127.0.0.1:<engine-port>` so import/bindings hit the real Python engine. |
| **UI → engine directly** | Set `VITE_PROXY_TARGET` to the engine base URL (engine already exposes the same OpenAPI paths). |

The **real** Level2 import lives in `services/engine` (see [`docs/level2-import.md`](../../docs/level2-import.md)). The mock BFF mirrors those routes for local UI work without Level2.

## Commands

```bash
npm install
npm run build
npm test
npm run dev
```

Start the BFF first (`apps/api`: `npm run start`) for live API data in `dev`.
