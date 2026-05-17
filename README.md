# Codex Ratchet

Nonclassical constraint-admissibility research system. Sims are written, audited, and queued by agents, then executed by Python runners. Active build order is tool sims -> tool integrations -> bounded lego rows -> only later couplings; classical baselines are controls, not nonclassical evidence, and bridge, axis, engine, and broad integrated claims remain gated.

## Where things live

| What | Path |
|---|---|
| Codex authority | `AGENTS.md` |
| Claude reference/session guidance | `CLAUDE.md` |
| Repo layout map | `REPO_LAYOUT.md` |
| **System docs** (plans, handoffs, research) | `system_v5/docs/` and `system_v5/docs/` |
| Read-only reference docs | `system_v5/READ ONLY Reference Docs/` |
| Sim code + probes | `system_v4/probes/` |
| Sim results (canonical) | `system_v4/probes/a2_state/sim_results/` |
| Overnight runner + gates | `scripts/` |
| Runner logs | `overnight_logs/` |
| Tests | `system_v5/tests/` |

## Read first (every session)

1. `CLAUDE.md` — operating principles, status labels, lane rules
2. `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
3. `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
4. `system_v5/docs/LEGO_SIM_CONTRACT.md`

## Running sims

```
make <target>                  # entrypoints defined in Makefile
scripts/overnight_two_runner.sh # two-lane overnight runner
scripts/lint_sim_contract.py    # SIM contract gate
```

## Current Axis0 Boundary

Formal scouts may record raw pre-guard Axis0 router candidates, but downstream
geometry must consume only admitted candidates. Current subdense/MPS receipts
mask `path_entropy` and `holographic_boundary_interior_reconstruction` out of
load-bearing geometry while keeping them as diagnostic or branch-closure
surfaces.

## Folders to ignore at root

- `work/` — scratch/audit temp (gitignored, large)
- `archive/` — historical artifacts
- `system_v3/` — legacy, superseded
- `obsidian_vault/` — ingested knowledge nodes
- `overnight_logs/` — runtime output from runner
