# Codex Ratchet

Front-door routing for the active checkout. This file points to the current authority surfaces; it does not carry doctrine or current-state claims.

## Where things live

| What | Path |
|---|---|
| Codex authority and repo-local operating contract | `AGENTS.md` |
| Codex overlay/reference | `CODEX.md` |
| Claude authority/reference for Claude sessions | `CLAUDE.md` |
| Repo layout map | `REPO_LAYOUT.md` |
| Current v6 contract and layout | `system_v6/README.md` |
| Current state, queues, audits, and campaign receipts | `system_v6/receipts/` |
| Current receipt index | `system_v6/receipts/receipts_index_20260612.md` |
| Current standing queue | `system_v6/receipts/standing_queue_20260612.md` |
| Current v6 sims | `system_v6/sims/` |
| Current v6 probes | `system_v6/probes/` |
| Shared scripts, validators, and runners | `scripts/` |
| Legacy/reference process docs named by `AGENTS.md` | `system_v5/docs/` |
| Read-only legacy/reference corpus | `system_v5/READ ONLY Reference Docs/` |

## Read first (every session)

1. `AGENTS.md`
2. `CODEX.md` for Codex-specific overlay/reference
3. `CLAUDE.md` for Claude sessions and Claude/reference doctrine
4. `system_v6/README.md`
5. `system_v6/receipts/receipts_index_20260612.md`
6. `system_v6/receipts/standing_queue_20260612.md`
7. `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
8. `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
9. `system_v5/docs/LEGO_SIM_CONTRACT.md`

## Running sims

```
make <target>                  # entrypoints defined in Makefile
scripts/overnight_two_runner.sh # two-lane overnight runner
scripts/lint_sim_contract.py    # SIM contract gate
```

## Folders to ignore at root

- `work/` — scratch/audit temp (gitignored, large)
- `archive/` — historical artifacts
- `system_v3/` — legacy, superseded
- `obsidian_vault/` — ingested knowledge nodes
- `overnight_logs/` — runtime output from runner
