# Lab SSH workflow (Windows → Ubuntu VM)

## Host

| Item | Value |
|------|--------|
| SSH alias | `level2-vm` |
| IP | `192.168.157.128` |
| User | `level2` |
| OS | Ubuntu (Docker + Jenkins) |

Configure `~/.ssh/config` on Windows (example):

```
Host level2-vm
  HostName 192.168.157.128
  User level2
  IdentityFile ~/.ssh/id_ed25519
```

## Lab URLs (Wave 3)

| Service | URL |
|---------|-----|
| **Mathmodel UI + API** | `http://192.168.157.128:8090/` |
| Mathmodel health | `http://192.168.157.128:8090/healthz` |
| Level2 collector (do not change) | `http://192.168.157.128:8080/` |
| Jenkins | `http://192.168.157.128:8081/` |

Inside Docker (`smoke_default`), mathmodel reaches Level2 at
`LEVEL2_API_URL=http://level2-collector:8080` (see
[`deploy/platform/docker-compose.yml`](../deploy/platform/docker-compose.yml)).

## Roles

- **Windows**: edit code in this repo (`C:\Users\Admin\source\Level2-mathmodel`).
- **VM**: pull, run Docker tests/smoke, Jenkins Multibranch job `level2-mathmodel`.

## Safety vs Level2

- Use image/container name **`level2-mathmodel`** only.
- Host port **8090** (never 8080/8081 used by Level2).
- Join external Docker network **`smoke_default`** as a **client** (Level2 collector already there).
- Never `docker image prune` / `rmi` for `level2-collector*` or Jenkins images.
- Never `docker compose down` on Level2 projects.
- Prefer `docker compose up -d --no-deps mathmodel` so collector/Jenkins stay untouched.

## Helpers

From Windows (Git Bash / PowerShell with OpenSSH). All remote work uses
`ssh -o BatchMode=yes -o ConnectTimeout=15 level2-vm` with batched remote commands.

```bash
# Connectivity
scripts/lab/ssh-check.sh

# Clone or pull on VM to ~/Level2-mathmodel
scripts/lab/pull.sh

# Engine pytest via Docker on VM
scripts/lab/test-engine.sh

# Compose config only (no HTTP checks)
scripts/lab/smoke-stub.sh

# Full Wave 3 smoke: compose + mathmodel /healthz + Level2 tag-catalog (read-only)
scripts/lab/smoke.sh

# Same as smoke.sh; optional bring-up of mathmodel only:
# BRING_UP=1 scripts/lab/smoke.sh
```

Compatibility aliases: `vm-pull.sh`, `vm-test.sh`, `vm-smoke.sh` → `smoke.sh`.

### What `smoke.sh` checks

1. External network `smoke_default` exists.
2. `docker compose -f deploy/platform/docker-compose.yml config` validates
   (expects host **8090**, `LEVEL2_API_URL`, `smoke_default`).
3. `GET ${MATHMODEL_URL}/healthz` → HTTP 200 (default `http://127.0.0.1:8090`).
4. Level2 read-only: `GET /api/v1/integration/tag-catalog`, or fallback
   `GET /api/v1/tags` on 404 (default `http://127.0.0.1:8080`).

Set `BRING_UP=1` to run `docker compose up -d --no-deps mathmodel` before health checks
(still never restarts Level2).

Jenkins Multibranch setup for this repo: [`deploy/ci/README.md`](../deploy/ci/README.md)
(`http://192.168.157.128:8081`, job name `level2-mathmodel`).

Manual one-liner pattern:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=15 level2-vm 'hostname && docker network inspect smoke_default >/dev/null && echo OK'
```

## First-time VM clone

```bash
ssh level2-vm 'git clone https://github.com/popelev/Level2-mathmodel.git ~/Level2-mathmodel'
```

If the remote is empty until Wave 0 is pushed, push from Windows first, then pull on the VM.

## Rebuild mathmodel on the VM (safe)

```bash
ssh level2-vm 'cd ~/Level2-mathmodel && git pull --ff-only && cd deploy/platform && docker compose build mathmodel && docker compose up -d --no-deps mathmodel'
```

Then from Windows: `scripts/lab/smoke.sh`.
