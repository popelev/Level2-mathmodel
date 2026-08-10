# Cross-repo coordination (Level2 ↔ Mathmodel)

## Channels

| Channel | Use |
|---------|-----|
| **Jira project [Level 2 / SCRUM](https://popelevfedor.atlassian.net/jira/software/projects/SCRUM/boards)** | File Level2 API gaps and platform asks here |
| Epic [SCRUM-17](https://popelevfedor.atlassian.net/browse/SCRUM-17) | Mathmodel as separate GitHub repo |
| [SCRUM-20](https://popelevfedor.atlassian.net/browse/SCRUM-20) | Level2 OpenAPI / contract hygiene for external models |
| GitHub [popelev/level2](https://github.com/popelev/level2) | Platform + OpenAPI source of truth |
| GitHub [popelev/Level2-mathmodel](https://github.com/popelev/Level2-mathmodel) | This repo (consumer) |

There is no direct agent-to-agent chat. Coordinate via Jira tickets and the pinned OpenAPI in `contracts/level2/`.

**Do not edit the Level2 git repository from mathmodel workstreams.** Platform changes are requested only via Jira for a Level2 agent.

## How mathmodel files API feedback

1. Prefer a **Task** under epic **SCRUM-5** (platform), prefix summary with `[Mathmodel]`.
2. Link / mention **SCRUM-17** and **SCRUM-20**.
3. Include: problem, ask, priority for mathmodel, link to this repo.
4. Keep asks additive under `/api/v1` when possible.

## Filed from mathmodel (2026-08-10)

| Key | Topic | Priority for MVP |
|-----|--------|------------------|
| [SCRUM-27](https://popelevfedor.atlassian.net/browse/SCRUM-27) | JSON error envelope | P2 |
| [SCRUM-28](https://popelevfedor.atlassian.net/browse/SCRUM-28) | Idempotency-Key for writes | P2 (later, write phase) |
| [SCRUM-29](https://popelevfedor.atlassian.net/browse/SCRUM-29) | Batch live GET by `tag_id` | P3 |
| [SCRUM-30](https://popelevfedor.atlassian.net/browse/SCRUM-30) | Stable `GET /api/v1/integration/tag-catalog` export (**Level2 agent**, label `ai-agent-level2`) | P2 (nice; use `GET /tags` today) |
| [SCRUM-31](https://popelevfedor.atlassian.net/browse/SCRUM-31) | Mathmodel import catalog/bindings (**`cursor-mathmodel`**, label `ai-agent-cursor-mathmodel`) | P1 for consumer |

## Local rules

- UI, code comments, and READMEs: **English**
- Chat with humans: Russian OK
- Mathmodel talks to the plant **only** via Level2 HTTP/WS (`LEVEL2_API_URL`)
