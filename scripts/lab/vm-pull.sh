#!/usr/bin/env bash
# Compatibility wrapper — prefer scripts/lab/pull.sh
exec "$(dirname "$0")/pull.sh" "$@"
