#!/usr/bin/env bash
# Clone or pull Level2-mathmodel on the lab VM (does not touch Level2 repos).
set -euo pipefail
REMOTE_URL="${REMOTE_URL:-https://github.com/popelev/Level2-mathmodel.git}"
REMOTE_DIR="${REMOTE_DIR:-Level2-mathmodel}"

ssh -o BatchMode=yes -o ConnectTimeout=15 level2-vm bash -s <<EOF
set -euo pipefail
cd "\$HOME"
if [ -d "${REMOTE_DIR}/.git" ]; then
  git -C "${REMOTE_DIR}" pull --ff-only
else
  git clone "${REMOTE_URL}" "${REMOTE_DIR}"
fi
git -C "${REMOTE_DIR}" rev-parse --short HEAD
git -C "${REMOTE_DIR}" status -sb
EOF
