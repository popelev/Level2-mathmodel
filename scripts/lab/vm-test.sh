#!/usr/bin/env bash
# Compatibility wrapper — prefer scripts/lab/test-engine.sh
exec "$(dirname "$0")/test-engine.sh" "$@"
