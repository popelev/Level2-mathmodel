#!/usr/bin/env bash
# Wave 3 lab smoke (read-only vs Level2): compose + mathmodel :8090 + Level2 catalog.
# Does NOT docker compose down Level2; does NOT prune images; does NOT restart collector/Jenkins.
set -euo pipefail
REMOTE_DIR="${REMOTE_DIR:-Level2-mathmodel}"
MATHMODEL_URL="${MATHMODEL_URL:-http://127.0.0.1:8090}"
LEVEL2_URL="${LEVEL2_URL:-http://127.0.0.1:8080}"
BRING_UP="${BRING_UP:-0}"

ssh -o BatchMode=yes -o ConnectTimeout=15 level2-vm \
  env REMOTE_DIR="$REMOTE_DIR" MATHMODEL_URL="$MATHMODEL_URL" LEVEL2_URL="$LEVEL2_URL" BRING_UP="$BRING_UP" \
  bash -s <<'EOF'
set -euo pipefail
cd "$HOME/${REMOTE_DIR}"

echo "== docker network smoke_default =="
docker network inspect smoke_default >/dev/null
echo "smoke_default: OK"

echo "== Level2 containers (info only; do not touch) =="
docker ps --format '{{.Names}} {{.Status}}' | grep -E 'level2-collector|jenkins' || true

echo "== docker compose config (deploy/platform) =="
docker compose -f deploy/platform/docker-compose.yml config >/tmp/mathmodel-compose.validated.yml
echo "compose config: OK"
grep -E '8090|LEVEL2_API_URL|smoke_default' /tmp/mathmodel-compose.validated.yml

if [ "${BRING_UP}" = "1" ]; then
  echo "== bring up mathmodel only (no Level2 deps restart) =="
  docker compose -f deploy/platform/docker-compose.yml up -d --no-deps mathmodel
fi

echo "== mathmodel healthz (${MATHMODEL_URL}) =="
ok=0
for i in 1 2 3 4 5 6 7 8 9 10; do
  code=$(curl -sS -o /tmp/mathmodel-healthz.txt -w "%{http_code}" --max-time 5 \
    "${MATHMODEL_URL}/healthz" || echo fail)
  echo "healthz attempt ${i}: ${code}"
  if [ "${code}" = "200" ]; then
    ok=1
    break
  fi
  sleep 2
done
if [ "${ok}" != "1" ]; then
  echo "FAIL: mathmodel /healthz not OK"
  cat /tmp/mathmodel-healthz.txt 2>/dev/null || true
  exit 1
fi
body=$(tr -d '\r\n' </tmp/mathmodel-healthz.txt || true)
echo "healthz body: ${body}"

echo "== Level2 tag-catalog (read-only, ${LEVEL2_URL}) =="
cat_code=$(curl -sS -o /tmp/level2-catalog.json -w "%{http_code}" --max-time 30 \
  "${LEVEL2_URL}/api/v1/integration/tag-catalog" || echo fail)
echo "tag-catalog HTTP ${cat_code}"
if [ "${cat_code}" = "200" ]; then
  python3 - <<'PY'
import json
from pathlib import Path
raw = Path("/tmp/level2-catalog.json").read_text(encoding="utf-8")
data = json.loads(raw)
# Accept list or wrapped {"tags":[...]} / {"items":[...]}
if isinstance(data, list):
    n = len(data)
elif isinstance(data, dict):
    tags = data.get("tags") or data.get("items") or data.get("entries")
    n = len(tags) if isinstance(tags, list) else len(data)
else:
    n = 0
print(f"tag-catalog entries≈{n}")
if n < 1:
    raise SystemExit("FAIL: empty tag-catalog")
PY
elif [ "${cat_code}" = "404" ]; then
  echo "tag-catalog 404 — fallback GET /api/v1/tags"
  tags_code=$(curl -sS -o /tmp/level2-tags.json -w "%{http_code}" --max-time 30 \
    "${LEVEL2_URL}/api/v1/tags" || echo fail)
  echo "tags HTTP ${tags_code}"
  if [ "${tags_code}" != "200" ]; then
    echo "FAIL: Level2 tags unreachable"
    head -c 400 /tmp/level2-tags.json 2>/dev/null || true
    echo
    exit 1
  fi
else
  echo "FAIL: Level2 tag-catalog unreachable"
  head -c 400 /tmp/level2-catalog.json 2>/dev/null || true
  echo
  exit 1
fi

echo "== UI root (optional) =="
ui_code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 10 "${MATHMODEL_URL}/" || echo fail)
echo "UI / HTTP ${ui_code}"

echo "== smoke OK =="
echo "Mathmodel UI: ${MATHMODEL_URL}/"
echo "Mathmodel API: ${MATHMODEL_URL}/healthz"
EOF
