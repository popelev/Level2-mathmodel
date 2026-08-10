# Jenkins CI — Multibranch job `level2-mathmodel`

Lab Jenkins already runs on the Level2 VM at **`:8081`**. This repo gets its **own** Multibranch Pipeline — do **not** add this GitHub URL to the existing Level2 / collector Multibranch job.

| Item | Value |
|------|--------|
| Jenkins UI | `http://192.168.157.128:8081` (lab defaults often `admin` / `admin`) |
| Job name | **`level2-mathmodel`** |
| Repo | `https://github.com/popelev/Level2-mathmodel` |
| Jenkinsfile | repo root `Jenkinsfile` |
| Agent | same Docker-capable node as Level2 CI |
| Reserved ports | Level2 uses **8080/8081** — mathmodel deploy later uses **8090** only |

## Exact steps: create the Multibranch job

1. Open Jenkins: `http://192.168.157.128:8081` and sign in.
2. **New Item** → enter name exactly: `level2-mathmodel`.
3. Choose **Multibranch Pipeline** → **OK**.
4. **Branch Sources** → **Add source** → **GitHub** (preferred) or **Git**:
   - **GitHub**:
     - Credentials: use an existing GitHub PAT/SSH credential already configured on this Jenkins (same as Level2), or add one with `repo` read access to `popelev/Level2-mathmodel`.
     - Repository HTTPS URL: `https://github.com/popelev/Level2-mathmodel`
     - (If the UI asks for owner/repo separately: owner `popelev`, repository `Level2-mathmodel`.)
   - **Git** (fallback):
     - Repository URL: `https://github.com/popelev/Level2-mathmodel.git`
     - Credentials: same as above if the repo is private; omit if public.
5. **Behaviors** (typical lab setup):
   - Discover branches: all branches, or at least `main`.
   - Optionally: discover pull requests from origin (same style as Level2 job).
   - Do **not** filter this job to the Level2 / collector repository.
6. **Build configuration**:
   - Mode: **by Jenkinsfile**
   - Script Path: `Jenkinsfile` (repo root — leave default).
7. **Scan Multibranch Pipeline Triggers** (optional but useful):
   - Periodically if not set (e.g. every 5–15 minutes), or rely on manual **Scan Multibranch Pipeline Now**.
8. **Save**.
9. Open the job → **Scan Multibranch Pipeline Now**. Confirm branch `main` appears and the first build starts (or is available to run).
10. Open `main` → confirm stages: Checkout → Engine Test → Web Build (if `apps/web/package.json` exists) → Docker Build → Push/Deploy skipped unless parameters enabled.

### Verify from a workstation (read-only)

```bash
# List jobs (lab default creds — change if your VM differs)
curl -sS -u admin:admin \
  'http://192.168.157.128:8081/api/json?tree=jobs[name]'

# Job exists? HTTP 200 = yes, 404 = create it with the steps above
curl -sS -o /dev/null -w '%{http_code}\n' -u admin:admin \
  'http://192.168.157.128:8081/job/level2-mathmodel/api/json'
```

Do **not** use the Jenkins CLI/API to delete jobs, reconfigure Level2 jobs, or restart Jenkins as part of Wave 1 setup.

## Stages (Wave 0 / Wave 1 CI)

| Stage | What |
|-------|------|
| Checkout | SCM |
| Engine Test | `pytest` inside `python:3.12-bookworm` with repo mounted |
| Web Build | Runs if `apps/web/package.json` exists (`npm` build) |
| Docker Build | Tags `level2-mathmodel:ci-<GIT_COMMIT>` and `:ci-latest` |
| Push / Deploy | Disabled by default (`ENABLE_PUSH` / `ENABLE_DEPLOY`) |

## Safety

- Image name is **`level2-mathmodel`** — separate from `level2-collector`.
- Post-build prune removes only **`level2-mathmodel*:ci-*`** (keeps newest `CI_IMAGE_KEEP` + `ci-latest`). Pattern is scoped to this image family only.
- Never prune `level2-collector*` or Jenkins images.
- Never `docker compose down` Level2 stacks.
- Deploy (later) uses port **8090** and external network **`smoke_default`** only. Ports **8080/8081** stay reserved for Level2 / Jenkins.

## Lab helper scripts

From Windows (Git Bash / WSL / OpenSSH), after `Host level2-vm` is configured:

```bash
scripts/lab/pull.sh          # clone/pull ~/Level2-mathmodel on VM
scripts/lab/test-engine.sh   # Dockerized engine pytest on VM
scripts/lab/smoke-stub.sh    # network + compose config check (no up/down)
```

Aliases with the same behavior: `vm-pull.sh`, `vm-test.sh`, `vm-smoke.sh`. See [`docs/lab-ssh.md`](../../docs/lab-ssh.md).

## Related docs

- Lab SSH workflow: [`docs/lab-ssh.md`](../../docs/lab-ssh.md)
- Compose: [`deploy/platform/docker-compose.yml`](../platform/docker-compose.yml)
