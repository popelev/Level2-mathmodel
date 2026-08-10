#!/usr/bin/env bash
# Check SSH BatchMode reachability to level2-vm.
set -euo pipefail
ssh -o BatchMode=yes -o ConnectTimeout=15 level2-vm 'echo "level2-vm OK: $(hostname) $(uname -s)"'
