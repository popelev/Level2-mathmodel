#!/usr/bin/env bash
# Compatibility wrapper — prefer scripts/lab/smoke-stub.sh
exec "$(dirname "$0")/smoke-stub.sh" "$@"
