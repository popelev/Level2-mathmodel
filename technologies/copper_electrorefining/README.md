# Copper electrorefining

Technology pack for copper electrorefining monitoring + planning.

## Wave 2

Python package `copper_electrorefining`:

| Module | Role |
|--------|------|
| `domain` | Section / Cell / Anode / Cathode / Electrolyte stubs |
| `kpi` | Simple ampere-hour estimate (`current * time`) |
| `config` | Planner age/threshold defaults |
| `planner` | Cathode-pull and anode-change queues → local-var payloads |

Engine plugin: `level2_mathmodel.plugins.copper_electrorefining` writes plan results into **local variables only** (never Level2 / PLC).

### Local variable keys

| Key | Type | Meaning |
|-----|------|---------|
| `plan.cathode_pull.queue` | text (JSON) | Ordered cathode pull queue |
| `plan.anode_change.queue` | text (JSON) | Ordered anode change queue |
| `plan.cathode_pull.count` | num | Queue length |
| `plan.anode_change.count` | num | Queue length |

### Fixture

`fixtures/plant_snapshot.json` — demo plant used by unit tests and `POST /api/v1/plan` until real Level2 tag mapping lands.
