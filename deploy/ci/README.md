# Jenkins CI — Multibranch job `level2-mathmodel`

## Job setup (lab VM)

1. In Jenkins (same host as Level2 CI), create a **Multibranch Pipeline** named **`level2-mathmodel`**.
2. Branch source: GitHub `https://github.com/popelev/Level2-mathmodel.git` (or SSH equivalent).
3. Build configuration: **by Jenkinsfile** at repo root (`Jenkinsfile`).
4. Discover branches (`main` + PRs as needed). Do **not** reuse the Level2 Multibranch job.

## Stages (Wave 0)

| Stage | What |
|-------|------|
| Checkout | SCM |
| Engine Test | `pytest` inside `python:3.12-bookworm` with repo mounted |
| Web Build | Runs if `apps/web/package.json` exists (`npm` build) |
| Docker Build | Tags `level2-mathmodel:ci-<GIT_COMMIT>` and `:ci-latest` |
| Push / Deploy | Disabled by default (`ENABLE_PUSH` / `ENABLE_DEPLOY`) |

## Safety

- Image name is **`level2-mathmodel`** — separate from `level2-collector`.
- Post-build prune removes only **`level2-mathmodel:ci-*`** (keeps newest `CI_IMAGE_KEEP` + `ci-latest`).
- Never prune `level2-collector*` or Jenkins images.
- Deploy (later) uses port **8090** and external network **`smoke_default`** only.

## Related docs

- Lab SSH workflow: [`docs/lab-ssh.md`](../../docs/lab-ssh.md)
- Compose: [`deploy/platform/docker-compose.yml`](../platform/docker-compose.yml)
