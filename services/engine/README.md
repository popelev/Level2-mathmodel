# Engine (`services/engine`)

Python package skeleton for Level2-mathmodel.

## Packages (Wave 0)

| Package | Role |
|---------|------|
| `level2_adapter` | Read-only client for Level2 Collector API |
| `local_vars` | Engine-owned local variables (no PLC write) |
| `tag_import` | Imported Level2 tag catalog + logical bindings |
| `api` | HTTP surface matching `contracts/mathmodel/openapi.yaml` |
| `plugins` | Technology plugins (e.g. copper electrorefining) |
| `recalc` | Multi-trigger flag poll → pluggable handlers → local vars |

See [`docs/level2-import.md`](../../docs/level2-import.md) for import/bindings routes.
See [`docs/recalc-triggers.md`](../../docs/recalc-triggers.md) for trigger/handler polling.

## Tests

```bash
# Local (from repo root or this directory)
pip install -r requirements.txt
pytest

# As Jenkins / lab VM will run (Docker)
docker run --rm -v "$PWD":/src -w /src/services/engine python:3.12-bookworm \
  bash -lc "pip install -q -r requirements.txt && pytest"
```
