# Codex Ratchet

Front-door routing for the active checkout. The v9 stack is an authority overlay
that keeps five independently installable products separate and joins them only
through declared bridge contracts. Historical systems remain available as
source and evidence; v9 does not silently promote their claims.

## Where things live

| What | Path |
|---|---|
| Codex authority and repo-local operating contract | `AGENTS.md` |
| Codex overlay/reference | `CODEX.md` |
| Claude authority/reference for Claude sessions | `CLAUDE.md` |
| Repo layout map | `REPO_LAYOUT.md` |
| Current v9 stack contract and verifier | `system_v9/README.md`, `system_v9/verify_stack.py` |
| Current v9 exercised-state report | `system_v9/CURRENT_STATE_20260806.md` |
| Current v9 product and bridge manifest | `system_v9/STACK_MANIFEST.json` |
| Codex Ratchet v9 product boundary | `system_v9/codex_ratchet/` |
| Lean ConstraintBox product | `constraint_box/` |
| ClaimGate product | `claimgate_plugin/` |
| Portable simulation-engine estate | `sim_engines/` |
| Independent Holodeck scaffold | `holodeck/` |
| Explicit cross-product contracts | `system_v9/bridges/` |
| Historical v6 state and receipts | `system_v6/` |
| Shared scripts, validators, and runners | `scripts/` |
| Legacy/reference process docs named by `AGENTS.md` | `system_v5/docs/` |
| Read-only legacy/reference corpus | `system_v5/READ ONLY Reference Docs/` |

## Read first (every session)

1. `AGENTS.md`
2. `CODEX.md` for Codex-specific overlay/reference
3. `CLAUDE.md` for Claude sessions and Claude/reference doctrine
4. `system_v9/README.md`
5. `system_v9/architecture/SYSTEM_BOUNDARIES.md`
6. `system_v9/STACK_MANIFEST.json`
7. `system_v9/bridges/README.md`
8. `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
9. `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
10. `system_v5/docs/LEGO_SIM_CONTRACT.md`

## Running sims

```
make <target>                  # entrypoints defined in Makefile
scripts/overnight_two_runner.sh # two-lane overnight runner
scripts/lint_sim_contract.py    # SIM contract gate
```

For a portable tool inventory and live machine observation, use:

```bash
python3 sim_engines/install.py list
python3 sim_engines/doctor.py
python3 system_v9/verify_stack.py
```

These commands report installation, declared use, exercised integration, and
claim status separately. An installed package is not counted as an integrated
or load-bearing engine.

## Folders to ignore at root

- `work/` — scratch/audit temp (gitignored, large)
- `archive/` — historical artifacts
- `system_v3/` — legacy, superseded
- `obsidian_vault/` — ingested knowledge nodes
- `overnight_logs/` — runtime output from runner
