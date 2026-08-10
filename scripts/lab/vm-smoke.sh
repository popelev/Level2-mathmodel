#!/usr/bin/env bash
# Non-disruptive smoke on VM: network exists + compose config validates.
# Does NOT docker compose up/down Level2; does NOT prune images.
set -euo pipefail
REMOTE_DIR="${REMOTE_DIR:-Level2-mathmodel}"

ssh -o BatchMode=yes -o ConnectTimeout=15 level2-vm bash -s <<EOF
set -euo pipefail
cd "\$HOME/${REMOTE_DIR}"

echo "== docker network smoke_default =="
docker network inspect smoke_default >/dev/null
echo "smoke_default: OK"

echo "== ensure Level2 containers undisturbed (info only) =="
docker ps --format '{{.Names}}' | grep -E 'level2-collector|jenkins' || true

echo "== docker compose config (deploy/platform) =="
docker compose -f deploy/platform/docker-compose.yml config >/tmp/mathmodel-compose.validated.yml
echo "compose config: OK"
grep -E '8090|LEVEL2_API_URL|smoke_default' /tmp/mathmodel-compose.validated.yml || true

echo "== smoke stub done (no compose up) =="
EOF
