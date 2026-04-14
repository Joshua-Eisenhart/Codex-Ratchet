# Codex Ratchet

Nonclassical constraint-admissibility research system. Runs sim legos under the three-lane architecture (Lane A capability-probes → Lane B classical baselines → Lane C nonclassical canonical).

## Where things live

| What | Path |
|---|---|
| Session instructions | `CLAUDE.md` |
| Repo layout map | `REPO_LAYOUT.md` |
| **System docs** (plans, handoffs, research) | `system_v5/docs/` and `system_v5/new docs/` |
| Read-only reference docs | `system_v5/READ ONLY Reference Docs/` |
| Sim code + probes | `system_v4/probes/` |
| Sim results (canonical) | `system_v4/probes/a2_state/sim_results/` |
| Overnight runner + gates | `scripts/` |
| Runner logs | `overnight_logs/` |
| Tests | `system_v5/tests/` |

## Read first (every session)

1. `CLAUDE.md` — operating principles, status labels, lane rules
2. `system_v5/new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
3. `system_v5/new docs/LLM_CONTROLLER_CONTRACT.md`
4. `system_v5/new docs/LEGO_SIM_CONTRACT.md`

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
