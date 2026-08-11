#!/usr/bin/env bash
# Compatibility wrapper — prefer scripts/lab/smoke.sh
exec "$(dirname "$0")/smoke.sh" "$@"
