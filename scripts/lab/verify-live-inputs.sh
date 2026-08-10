#!/usr/bin/env bash
# Verify mathmodel live-inputs on the lab VM (run via ssh level2-vm bash -s < this file).
set -euo pipefail

echo "== healthz =="
curl -sS -o /dev/null -w "HTTP %{http_code}\n" --max-time 10 http://127.0.0.1:8090/healthz

echo "== GET /api/v1/live/inputs =="
code=$(curl -sS -o /tmp/live.json -w "%{http_code}" --max-time 90 http://127.0.0.1:8090/api/v1/live/inputs)
echo "HTTP ${code}"
if [ "${code}" != "200" ]; then
  head -c 400 /tmp/live.json || true
  echo
  exit 1
fi

python3 <<'PY'
import json
d = json.load(open("/tmp/live.json", encoding="utf-8"))
assert d.get("source") == "level2", d.get("source")
assert isinstance(d.get("tags"), list) and len(d["tags"]) > 0
print("source=", d["source"])
print("tag_count=", d.get("tag_count", len(d["tags"])))
print("updated_at=", d.get("updated_at"))
t = d["tags"][0]
print("first_tag=", t.get("tag_id"), "value=", t.get("value_num"), "quality=", t.get("quality"))
PY

echo "== UI bundle (no BFF mock wording) =="
docker exec level2-mathmodel sh -c '
  if grep -R -F "BFF mock data" /app/web/dist/assets/*.js >/dev/null 2>&1; then
    echo "FAIL: BFF mock data still in UI bundle"
    exit 1
  fi
  if grep -R -F "Read-only projection from Level2 via engine" /app/web/dist/assets/*.js >/dev/null 2>&1; then
    echo "OK: engine live-inputs copy present"
  else
    echo "WARN: expected UI copy string not found (check rebuild)"
  fi
'

echo "== done =="
