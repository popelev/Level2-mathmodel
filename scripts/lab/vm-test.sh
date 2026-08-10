#!/usr/bin/env bash
# Run engine pytest on VM via Docker (same style as Jenkins Engine Test).
set -euo pipefail
REMOTE_DIR="${REMOTE_DIR:-Level2-mathmodel}"

ssh -o BatchMode=yes -o ConnectTimeout=15 level2-vm bash -s <<EOF
set -euo pipefail
cd "\$HOME/${REMOTE_DIR}"
docker run --rm \
  -v "\$PWD":/src -w /src \
  python:3.12-bookworm \
  bash -lc 'pip install -q -r services/engine/requirements.txt && cd services/engine && pytest'
EOF
