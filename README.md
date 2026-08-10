# Level2-mathmodel

Monitoring + planning MVP companion to **[Level2](https://github.com/popelev/level2)** (OPC UA collector).

---

## Role vs Level2

| | **Level2** | **Level2-mathmodel** (this repo) |
|---|------------|----------------------------------|
| Role | Collector / OPC UA / historian / Admin API | Math model: monitoring + planning |
| I/O in MVP | Owns PLC tags; optional write gates | **Read-only** client of Level2 API; **local vars only** (no PLC/Level2 write) |
| Port | 8080 / 8081 | **8090** |
| Images | `level2-collector` | `level2-mathmodel` |
| Network | Provides / uses `smoke_default` | Joins `smoke_default` as **client only** |

Wave 0 = **scaffold only** (contracts, engine package, CI, lab scripts). No full adapter/UI/copper yet.

### Lab

- Code edited on Windows; Docker/Jenkins on Ubuntu VM via SSH alias **`level2-vm`** (`192.168.157.128`, user `level2`).
- Docs: [`docs/lab-ssh.md`](docs/lab-ssh.md)
- Compose: [`deploy/platform/docker-compose.yml`](deploy/platform/docker-compose.yml) → `LEVEL2_API_URL=http://level2-collector:8080`
- Jenkins Multibranch: `level2-mathmodel` — see [`deploy/ci/README.md`](deploy/ci/README.md)
- Do not touch Level2/Jenkins images or run `docker compose down` on Level2 projects.

### Quick test (Docker, as CI)

```bash
docker run --rm -v "$PWD":/src -w /src python:3.12-bookworm \
  bash -lc 'pip install -q -r services/engine/requirements.txt && cd services/engine && pytest'
```

### Structure (Wave 0)

```
contracts/level2/          # pinned OpenAPI Level2 v1.2.1 + fixtures
contracts/mathmodel/       # draft own OpenAPI
services/engine/           # Python engine skeleton + pytest
apps/web/ apps/api/        # TS/React placeholders
technologies/copper_electrorefining/  # placeholder
deploy/platform/           # Dockerfile + compose :8090
deploy/ci/                 # Jenkins Multibranch notes
scripts/lab/               # ssh helpers to level2-vm
```

---

## Кратко (RU)

Компаньон к Level2: мониторинг + планирование, порт **8090**, только чтение API Level2 и локальные переменные (без записи в PLC). Лаба: Windows → SSH `level2-vm`. Подробности — в английской секции выше и [`docs/lab-ssh.md`](docs/lab-ssh.md).
