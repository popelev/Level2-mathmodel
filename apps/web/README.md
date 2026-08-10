# `apps/web`

React + Vite UI for Level2-mathmodel (Wave 1).

Screens: connection status, live inputs, local variables (list/edit), plan stub.

Talks to mock BFF (`apps/api`) via Vite proxy → `http://127.0.0.1:8090`.

## Commands

```bash
npm install
npm run build
npm test
npm run dev
```

Start the mock BFF first (`apps/api`: `npm run start`) for live API data in `dev`.
